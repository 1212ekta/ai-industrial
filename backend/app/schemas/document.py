"""Pydantic request/response schemas for document endpoints."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    filename: str


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    document_type: str | None = None
    equipment_tag: str | None = None
    plant: str | None = None
    department: str | None = None
    status: str
    error_message: str | None = None
    page_count: int | None = None
    uploaded_at: datetime
    indexed_at: datetime | None = None


class DocumentListResponse(BaseModel):
    items: list[DocumentRead]
    total: int


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    chunk_index: int
    page_number: int | None = None
    content: str


class DocumentFilters(BaseModel):
    equipment_tag: str | None = None
    plant: str | None = None
    department: str | None = None
    document_type: str | None = None
    status: str | None = None
