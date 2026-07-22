"""Knowledge graph read endpoints (equipment subgraph, stats) and extracted entities."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.session import get_db
from app.models.entity import Entity
from app.services.graph_store.neo4j_client import Neo4jService

router = APIRouter(tags=["graph"])


@router.get("/graph/equipment/{tag}")
async def get_equipment_subgraph(tag: str) -> dict:
    neo4j = Neo4jService()
    try:
        subgraph = neo4j.get_equipment_subgraph(tag.upper())
    except Exception as exc:
        logger.error(f"Graph read failed for {tag}: {exc}")
        raise HTTPException(status_code=502, detail="Graph backend unavailable") from exc
    finally:
        neo4j.close()

    if not subgraph or not subgraph.get("equipment"):
        raise HTTPException(status_code=404, detail=f"No graph data found for equipment '{tag}'")
    return subgraph


@router.get("/graph/stats")
async def get_graph_stats() -> dict:
    neo4j = Neo4jService()
    try:
        return neo4j.get_graph_stats()
    except Exception as exc:
        logger.error(f"Graph stats read failed: {exc}")
        raise HTTPException(status_code=502, detail="Graph backend unavailable") from exc
    finally:
        neo4j.close()


@router.get("/entities")
async def list_entities(document_id: str, db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Entity).where(Entity.document_id == document_id))
    entities = list(result.scalars().all())
    return [
        {
            "id": e.id,
            "entity_type": e.entity_type,
            "entity_value": e.entity_value,
            "normalized_value": e.normalized_value,
            "confidence": e.confidence,
            "page_number": e.page_number,
        }
        for e in entities
    ]
