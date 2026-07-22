"""Pydantic schemas for the AI Copilot (RAG) endpoint."""
from pydantic import BaseModel, Field


class CopilotChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    equipment_tag: str | None = None
    top_k: int = Field(default=6, ge=1, le=20)


class Citation(BaseModel):
    document_id: str
    filename: str
    page_number: int | None
    excerpt: str


class CopilotChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float
    source_documents: list[str]
