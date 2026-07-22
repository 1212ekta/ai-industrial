"""Thin wrapper around the Qdrant client for chunk vector storage and search."""
from __future__ import annotations

import uuid

from app.core.config import get_settings
from app.core.logging import logger


class QdrantService:
    def __init__(self):
        from qdrant_client import QdrantClient

        settings = get_settings()
        self._settings = settings
        self._client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        self._collection = settings.qdrant_collection
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        from qdrant_client.http.models import Distance, VectorParams

        existing = [c.name for c in self._client.get_collections().collections]
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(
                    size=self._settings.openai_embedding_dimensions, distance=Distance.COSINE
                ),
            )
            logger.info(f"Created Qdrant collection '{self._collection}'")

    def upsert_chunks(
        self,
        chunk_ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> list[str]:
        """Upsert chunk vectors. Returns the Qdrant point IDs used (UUIDs)."""
        from qdrant_client.http.models import PointStruct

        point_ids = [str(uuid.uuid4()) for _ in chunk_ids]
        points = [
            PointStruct(id=point_ids[i], vector=vectors[i], payload=payloads[i])
            for i in range(len(chunk_ids))
        ]
        self._client.upsert(collection_name=self._collection, points=points)
        return point_ids

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_conditions: dict | None = None,
    ) -> list[dict]:
        from qdrant_client.http.models import FieldCondition, Filter, MatchValue

        qdrant_filter = None
        if filter_conditions:
            must = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_conditions.items()
                if v is not None
            ]
            if must:
                qdrant_filter = Filter(must=must)

        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [{"score": r.score, "payload": r.payload, "point_id": r.id} for r in results]

    def delete_by_document_id(self, document_id: str) -> None:
        from qdrant_client.http.models import FieldCondition, Filter, MatchValue

        self._client.delete(
            collection_name=self._collection,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
        )
