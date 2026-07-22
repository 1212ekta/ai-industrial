"""Orchestrates the full document processing pipeline, run as a background task
after upload: parse -> chunk -> embed -> upsert vectors -> extract entities ->
write graph -> mark document indexed.
"""
from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.chunk import DocumentChunk
from app.models.document import Document, DocumentStatus
from app.models.entity import Entity
from app.models.equipment import Equipment
from app.services.embeddings.embedder import EmbeddingService
from app.services.extraction.entity_extractor import EntityExtractionService
from app.services.graph_store.neo4j_client import Neo4jService
from app.services.ingestion.chunker import TextChunker
from app.services.ingestion.parser import DocumentParser
from app.services.vector_store.qdrant_client import QdrantService

# Entity types that map onto graph node categories with dedicated Neo4j handling.
EQUIPMENT_ENTITY_TYPES = {"Equipment", "Pump", "Valve", "Motor", "Boiler", "Compressor"}


def _normalize_tag(value: str) -> str:
    return re.sub(r"[\s\-]", "", value.strip().upper())


class IngestionPipeline:
    def __init__(self):
        self._parser = DocumentParser()
        self._chunker = TextChunker()
        self._embedder = EmbeddingService()
        self._qdrant = QdrantService()
        self._extractor = EntityExtractionService()

    async def process_document(self, db: AsyncSession, document_id: str) -> None:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if document is None:
            logger.error(f"process_document: document {document_id} not found")
            return

        try:
            await self._run_parse_and_chunk(db, document)
            await self._run_embedding(db, document)
            await self._run_entity_extraction_and_graph(db, document)

            document.status = DocumentStatus.INDEXED
            from datetime import datetime

            document.indexed_at = datetime.utcnow()
            await db.commit()
            logger.info(f"Document {document_id} fully indexed.")
        except Exception as exc:
            logger.exception(f"Pipeline failed for document {document_id}: {exc}")
            document.status = DocumentStatus.FAILED
            document.error_message = str(exc)[:2000]
            await db.commit()

    # ------------------------------------------------------------- Parse+chunk
    async def _run_parse_and_chunk(self, db: AsyncSession, document: Document) -> None:
        document.status = DocumentStatus.PARSING
        await db.commit()

        parsed = self._parser.parse(document.storage_path, document.file_type)
        document.page_count = parsed.page_count

        text_chunks = self._chunker.chunk_document(parsed)
        for tc in text_chunks:
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=tc.chunk_index,
                    page_number=tc.page_number,
                    content=tc.content,
                    token_count=tc.token_count,
                )
            )
        await db.commit()

    # ---------------------------------------------------------------- Embed
    async def _run_embedding(self, db: AsyncSession, document: Document) -> None:
        document.status = DocumentStatus.EMBEDDING
        await db.commit()

        result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
        chunks = list(result.scalars().all())
        if not chunks:
            return

        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            vectors = self._embedder.embed_texts([c.content for c in batch])
            payloads = [
                {
                    "chunk_id": c.id,
                    "document_id": document.id,
                    "filename": document.filename,
                    "page_number": c.page_number,
                    "content": c.content,
                    "equipment_tag": document.equipment_tag,
                    "document_type": document.document_type,
                }
                for c in batch
            ]
            point_ids = self._qdrant.upsert_chunks(
                chunk_ids=[c.id for c in batch], vectors=vectors, payloads=payloads
            )
            for c, point_id in zip(batch, point_ids):
                c.qdrant_point_id = point_id
        await db.commit()

    # ------------------------------------------------------- Extract + graph
    async def _run_entity_extraction_and_graph(self, db: AsyncSession, document: Document) -> None:
        document.status = DocumentStatus.EXTRACTING
        await db.commit()

        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = list(result.scalars().all())

        neo4j = Neo4jService()
        neo4j.upsert_document_node(document.id, document.filename, document.document_type)

        context_summary = ""
        all_entities_for_context: list = []

        try:
            for chunk in chunks:
                extraction = self._extractor.extract(chunk.content, context_summary=context_summary)

                for entity in extraction.entities:
                    db.add(
                        Entity(
                            document_id=document.id,
                            chunk_id=chunk.id,
                            entity_type=entity.entity_type,
                            entity_value=entity.value,
                            normalized_value=_normalize_tag(entity.value)
                            if entity.entity_type in EQUIPMENT_ENTITY_TYPES
                            else entity.value,
                            confidence=entity.confidence,
                            page_number=chunk.page_number,
                        )
                    )

                    if entity.entity_type in EQUIPMENT_ENTITY_TYPES:
                        tag = _normalize_tag(entity.value)
                        await self._upsert_equipment_registry(db, tag, entity.entity_type, document)
                        neo4j.upsert_equipment(
                            tag=tag,
                            equipment_type=entity.entity_type,
                            plant=document.plant,
                            risk_level=None,
                        )
                        neo4j.link_equipment_mentioned_in(tag, document.id, chunk.page_number)
                    elif entity.entity_type == "Engineer":
                        neo4j.upsert_engineer(entity.value, department=document.department)
                    elif entity.entity_type in {"Vendor", "OEM"}:
                        neo4j.upsert_vendor(entity.value)
                    elif entity.entity_type == "FailureType":
                        eq_tag = document.equipment_tag or self._first_equipment_tag(extraction.entities)
                        if eq_tag:
                            neo4j.create_failure(
                                failure_id=str(uuid.uuid4()),
                                equipment_tag=_normalize_tag(eq_tag),
                                failure_type=entity.value,
                                document_id=document.id,
                                page=chunk.page_number,
                            )
                    elif entity.entity_type == "InspectionReport":
                        eq_tag = document.equipment_tag or self._first_equipment_tag(extraction.entities)
                        if eq_tag:
                            neo4j.create_inspection(
                                inspection_id=str(uuid.uuid4()),
                                equipment_tag=_normalize_tag(eq_tag),
                                document_id=document.id,
                                page=chunk.page_number,
                            )

                # Relations extracted directly by the LLM (best-effort — only wired
                # for relation types with an unambiguous Neo4j mapping).
                for relation in extraction.relations:
                    self._apply_relation(neo4j, relation, document)

                all_entities_for_context.extend(extraction.entities)
                context_summary = self._extractor.summarize_for_context(all_entities_for_context)

            await db.commit()
        finally:
            neo4j.close()

    async def _upsert_equipment_registry(
        self, db: AsyncSession, tag: str, equipment_type: str, document: Document
    ) -> None:
        result = await db.execute(select(Equipment).where(Equipment.tag == tag))
        existing = result.scalar_one_or_none()
        if existing is None:
            db.add(
                Equipment(
                    tag=tag,
                    equipment_type=equipment_type,
                    plant=document.plant,
                    department=document.department,
                )
            )

    @staticmethod
    def _first_equipment_tag(entities) -> str | None:
        for e in entities:
            if e.entity_type in EQUIPMENT_ENTITY_TYPES:
                return e.value
        return None

    @staticmethod
    def _apply_relation(neo4j: Neo4jService, relation, document: Document) -> None:
        try:
            if relation.relation == "MAINTAINED_BY":
                neo4j.link_maintained_by(_normalize_tag(relation.source), relation.target, date=None)
            elif relation.relation == "INSPECTED_BY":
                neo4j.link_inspected_by(_normalize_tag(relation.source), relation.target, date=None)
            elif relation.relation == "SUPPLIED_BY":
                neo4j.link_supplied_by(_normalize_tag(relation.source), relation.target)
            elif relation.relation == "CONNECTED_TO":
                neo4j.connect_equipment(_normalize_tag(relation.source), _normalize_tag(relation.target))
        except Exception as exc:
            logger.warning(f"Failed applying relation {relation}: {exc}")
