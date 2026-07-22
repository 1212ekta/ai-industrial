"""Hybrid retrieval: vector search (Qdrant) + structured graph facts (Neo4j)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.embeddings.embedder import EmbeddingService
from app.services.graph_store.neo4j_client import Neo4jService
from app.services.vector_store.qdrant_client import QdrantService

EQUIPMENT_TAG_PATTERN = re.compile(r"\b([A-Z]{1,4}-?\d{2,5})\b")


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None
    content: str
    score: float


class HybridRetriever:
    def __init__(self):
        self._embedder = EmbeddingService()
        self._qdrant = QdrantService()

    @staticmethod
    def detect_equipment_tag(text: str) -> str | None:
        match = EQUIPMENT_TAG_PATTERN.search(text.upper())
        return match.group(1).replace("-", "") if match else None

    def retrieve_chunks(
        self, query: str, top_k: int = 6, equipment_tag: str | None = None
    ) -> list[RetrievedChunk]:
        vector = self._embedder.embed_text(query)
        filters = {"equipment_tag": equipment_tag} if equipment_tag else None
        raw_results = self._qdrant.search(query_vector=vector, top_k=top_k, filter_conditions=filters)

        chunks = []
        for r in raw_results:
            payload = r["payload"] or {}
            chunks.append(
                RetrievedChunk(
                    chunk_id=payload.get("chunk_id", ""),
                    document_id=payload.get("document_id", ""),
                    filename=payload.get("filename", "unknown"),
                    page_number=payload.get("page_number"),
                    content=payload.get("content", ""),
                    score=r["score"],
                )
            )
        return chunks

    def retrieve_graph_facts(self, equipment_tag: str | None) -> dict:
        if not equipment_tag:
            return {}
        neo4j = Neo4jService()
        try:
            return neo4j.get_equipment_subgraph(equipment_tag)
        finally:
            neo4j.close()

    @staticmethod
    def format_chunk_excerpts(chunks: list[RetrievedChunk]) -> str:
        lines = []
        for c in chunks:
            lines.append(f"[Doc: {c.filename}, p.{c.page_number}] {c.content.strip()[:800]}")
        return "\n\n".join(lines)

    @staticmethod
    def format_graph_facts(graph_data: dict) -> str:
        if not graph_data or not graph_data.get("equipment"):
            return ""
        lines = [f"Equipment: {graph_data['equipment']}"]
        if graph_data.get("failures"):
            lines.append(f"Known failures: {graph_data['failures']}")
        if graph_data.get("inspectors"):
            lines.append(f"Inspected by: {graph_data['inspectors']}")
        if graph_data.get("maintainers"):
            lines.append(f"Maintained by: {graph_data['maintainers']}")
        if graph_data.get("vendors"):
            lines.append(f"Supplied by: {graph_data['vendors']}")
        return "\n".join(lines)
