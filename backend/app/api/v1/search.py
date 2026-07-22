"""Semantic search endpoint over document chunks (Qdrant)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.logging import logger
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from app.services.embeddings.embedder import EmbeddingService
from app.services.vector_store.qdrant_client import QdrantService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def semantic_search(payload: SearchRequest) -> SearchResponse:
    try:
        embedder = EmbeddingService()
        vector = embedder.embed_text(payload.query)

        qdrant = QdrantService()
        filters = {
            "equipment_tag": payload.equipment_tag,
            "document_type": payload.document_type,
        }
        raw_results = qdrant.search(query_vector=vector, top_k=payload.top_k, filter_conditions=filters)
    except Exception as exc:
        logger.error(f"Semantic search failed: {exc}")
        raise HTTPException(status_code=502, detail="Search backend unavailable") from exc

    results = [
        SearchResultItem(
            chunk_id=r["payload"].get("chunk_id", ""),
            document_id=r["payload"].get("document_id", ""),
            filename=r["payload"].get("filename", "unknown"),
            page_number=r["payload"].get("page_number"),
            content=r["payload"].get("content", ""),
            score=r["score"],
        )
        for r in raw_results
    ]
    return SearchResponse(query=payload.query, results=results)
