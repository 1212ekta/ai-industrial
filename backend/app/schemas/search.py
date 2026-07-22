"""Pydantic schemas for semantic search."""
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=50)
    equipment_tag: str | None = None
    document_type: str | None = None


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None
    content: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
