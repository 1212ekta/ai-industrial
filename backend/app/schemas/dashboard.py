"""Pydantic schemas for dashboard summary endpoint."""
from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    documents_uploaded: int
    equipment_count: int
    maintenance_records: int
    failure_count: int
    compliance_score: float


class RecentUploadItem(BaseModel):
    document_id: str
    filename: str
    status: str
    uploaded_at: datetime


class RecentQueryItem(BaseModel):
    query_id: str
    query_type: str
    query_text: str
    confidence: float | None
    created_at: datetime


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_uploads: list[RecentUploadItem]
    recent_queries: list[RecentQueryItem]
