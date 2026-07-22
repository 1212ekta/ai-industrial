from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    file_type: str
    upload_date: datetime
    status: str

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str

class Citation(BaseModel):
    document_name: str
    page_number: int
    text_snippet: str

class ChatResponse(BaseModel):
    answer: str
    confidence_score: float
    sources: List[Citation]

class RCARequest(BaseModel):
    equipment: str
    problem_description: str

class CauseProbability(BaseModel):
    cause: str
    probability: float

class RCAResponse(BaseModel):
    likely_causes: List[CauseProbability]
    recommendations: List[str]
    evidence: List[Citation]

class DashboardStats(BaseModel):
    total_documents: int
    equipment_count: int
    failures_count: int
    recent_uploads: List[DocumentResponse]
