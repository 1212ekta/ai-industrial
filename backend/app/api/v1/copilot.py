"""AI Copilot (RAG) chat endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.session import get_db
from app.models.query_log import QueryLog
from app.schemas.copilot import CopilotChatRequest, CopilotChatResponse
from app.services.rag.copilot_service import CopilotService

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/chat", response_model=CopilotChatResponse)
async def copilot_chat(
    payload: CopilotChatRequest, db: AsyncSession = Depends(get_db)
) -> CopilotChatResponse:
    try:
        service = CopilotService()
        response = service.ask(
            question=payload.question,
            equipment_tag=payload.equipment_tag,
            top_k=payload.top_k,
        )
    except Exception as exc:
        logger.error(f"Copilot chat failed: {exc}")
        raise HTTPException(status_code=502, detail="Copilot backend unavailable") from exc

    log_entry = QueryLog(
        query_type="copilot",
        query_text=payload.question,
        response_summary=response.answer[:500],
        confidence=response.confidence,
    )
    log_entry.set_source_ids(response.source_documents)
    db.add(log_entry)
    await db.commit()

    return response
