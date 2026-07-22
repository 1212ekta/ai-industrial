"""Dashboard summary endpoint — aggregate counts and recent activity."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.session import get_db
from app.models.document import Document
from app.models.equipment import Equipment
from app.models.query_log import QueryLog
from app.schemas.dashboard import (
    DashboardResponse,
    DashboardStats,
    RecentQueryItem,
    RecentUploadItem,
)
from app.services.graph_store.neo4j_client import Neo4jService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> DashboardResponse:
    doc_count_result = await db.execute(select(func.count()).select_from(Document))
    documents_uploaded = doc_count_result.scalar_one()

    equipment_count_result = await db.execute(select(func.count()).select_from(Equipment))
    equipment_count = equipment_count_result.scalar_one()

    failure_count = 0
    maintenance_count = 0
    try:
        neo4j = Neo4jService()
        try:
            graph_stats = neo4j.get_graph_stats()
            failure_count = graph_stats.get("failure_count", 0)
            maintenance_count = graph_stats.get("maintenance_count", 0)
        finally:
            neo4j.close()
    except Exception as exc:
        logger.warning(f"Neo4j unavailable for dashboard stats: {exc}")

    # Simple compliance heuristic for the MVP: proportion of successfully-indexed
    # documents out of all uploaded documents (a stand-in for a real compliance model).
    indexed_result = await db.execute(
        select(func.count()).select_from(Document).where(Document.status == "indexed")
    )
    indexed_count = indexed_result.scalar_one()
    compliance_score = round((indexed_count / documents_uploaded) * 100, 1) if documents_uploaded else 0.0

    recent_uploads_result = await db.execute(
        select(Document).order_by(Document.uploaded_at.desc()).limit(5)
    )
    recent_uploads = [
        RecentUploadItem(
            document_id=d.id, filename=d.filename, status=d.status, uploaded_at=d.uploaded_at
        )
        for d in recent_uploads_result.scalars().all()
    ]

    recent_queries_result = await db.execute(
        select(QueryLog).order_by(QueryLog.created_at.desc()).limit(5)
    )
    recent_queries = [
        RecentQueryItem(
            query_id=q.id,
            query_type=q.query_type,
            query_text=q.query_text,
            confidence=q.confidence,
            created_at=q.created_at,
        )
        for q in recent_queries_result.scalars().all()
    ]

    return DashboardResponse(
        stats=DashboardStats(
            documents_uploaded=documents_uploaded,
            equipment_count=equipment_count,
            maintenance_records=maintenance_count,
            failure_count=failure_count,
            compliance_score=compliance_score,
        ),
        recent_uploads=recent_uploads,
        recent_queries=recent_queries,
    )
