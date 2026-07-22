"""Root Cause Analysis endpoint, powered by the LangGraph RCA agent."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.session import get_db
from app.models.query_log import QueryLog
from app.schemas.rca import RCARequest, RCAResponse
from app.services.rca.graph_workflow import RCAWorkflowService

router = APIRouter(prefix="/rca", tags=["root-cause-analysis"])


@router.post("", response_model=RCAResponse)
async def analyze_root_cause(payload: RCARequest, db: AsyncSession = Depends(get_db)) -> RCAResponse:
    try:
        service = RCAWorkflowService()
        response = service.run(
            equipment_name=payload.equipment_name,
            problem_description=payload.problem_description,
        )
    except Exception as exc:
        logger.error(f"RCA analysis failed: {exc}")
        raise HTTPException(status_code=502, detail="RCA backend unavailable") from exc

    log_entry = QueryLog(
        query_type="rca",
        query_text=f"{payload.equipment_name}: {payload.problem_description}",
        response_summary=f"{len(response.root_causes)} candidate cause(s) identified",
        confidence=response.overall_confidence,
    )
    log_entry.set_source_ids(
        sorted(
            {
                e.document_id
                for c in response.root_causes
                for e in c.supporting_evidence
            }
        )
    )
    db.add(log_entry)
    await db.commit()

    return response
