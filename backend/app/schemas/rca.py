"""Pydantic schemas for the Root Cause Analysis endpoint."""
from pydantic import BaseModel, Field


class RCARequest(BaseModel):
    equipment_name: str = Field(..., min_length=1, max_length=200)
    problem_description: str = Field(..., min_length=1, max_length=4000)


class SupportingEvidence(BaseModel):
    document_id: str
    filename: str
    page_number: int | None
    excerpt: str


class RootCause(BaseModel):
    cause: str
    probability: float
    explanation: str
    supporting_evidence: list[SupportingEvidence]


class RCAResponse(BaseModel):
    equipment_name: str
    root_causes: list[RootCause]
    recommended_actions: list[str]
    overall_confidence: float
