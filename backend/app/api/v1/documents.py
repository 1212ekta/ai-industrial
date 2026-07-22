"""Document upload, listing, retrieval, and deletion endpoints."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.session import AsyncSessionLocal, get_db
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.schemas.document import (
    ChunkRead,
    DocumentListResponse,
    DocumentRead,
    DocumentUploadResponse,
)
from app.services.graph_store.neo4j_client import Neo4jService
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.vector_store.qdrant_client import QdrantService
from app.utils.storage import is_supported_file, new_document_id, save_upload

router = APIRouter(prefix="/documents", tags=["documents"])


async def _run_pipeline_background(document_id: str) -> None:
    """Runs in a background task with its own DB session (the request's session
    is closed by the time this executes)."""
    async with AsyncSessionLocal() as db:
        pipeline = IngestionPipeline()
        await pipeline.process_document(db, document_id)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    equipment_tag: str | None = None,
    plant: str | None = None,
    department: str | None = None,
    document_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    if not file.filename or not is_supported_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed: pdf, docx, txt, png, jpg, xlsx",
        )

    document_id = new_document_id()
    try:
        storage_path, size_bytes = await save_upload(document_id, file.filename, file)
    except Exception as exc:
        logger.error(f"Failed saving upload {file.filename}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to store uploaded file") from exc

    ext = file.filename.rsplit(".", 1)[-1].lower()
    document = Document(
        id=document_id,
        filename=file.filename,
        file_type=ext,
        storage_path=storage_path,
        file_size_bytes=size_bytes,
        document_type=document_type,
        equipment_tag=equipment_tag,
        plant=plant,
        department=department,
    )
    db.add(document)
    await db.commit()

    background_tasks.add_task(_run_pipeline_background, document_id)

    return DocumentUploadResponse(document_id=document_id, status=document.status, filename=file.filename)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    equipment_tag: str | None = None,
    plant: str | None = None,
    department: str | None = None,
    document_type: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    query = select(Document)
    if equipment_tag:
        query = query.where(Document.equipment_tag == equipment_tag)
    if plant:
        query = query.where(Document.plant == plant)
    if department:
        query = query.where(Document.department == department)
    if document_type:
        query = query.where(Document.document_type == document_type)
    if status:
        query = query.where(Document.status == status)

    result = await db.execute(query.order_by(Document.uploaded_at.desc()).offset(offset).limit(limit))
    documents = list(result.scalars().all())

    count_result = await db.execute(query)
    total = len(list(count_result.scalars().all()))

    return DocumentListResponse(
        items=[DocumentRead.model_validate(d) for d in documents], total=total
    )


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)) -> DocumentRead:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentRead.model_validate(document)


@router.get("/{document_id}/file")
async def get_document_file(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(document.storage_path, filename=document.filename)


@router.get("/{document_id}/chunks", response_model=list[ChunkRead])
async def get_document_chunks(document_id: str, db: AsyncSession = Depends(get_db)) -> list[ChunkRead]:
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = list(result.scalars().all())
    return [ChunkRead.model_validate(c) for c in chunks]


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        QdrantService().delete_by_document_id(document_id)
    except Exception as exc:
        logger.warning(f"Qdrant cleanup failed for {document_id}: {exc}")

    neo4j = Neo4jService()
    try:
        neo4j.delete_document_and_orphans(document_id)
    except Exception as exc:
        logger.warning(f"Neo4j cleanup failed for {document_id}: {exc}")
    finally:
        neo4j.close()

    await db.delete(document)
    await db.commit()
    return {"document_id": document_id, "deleted": True}
