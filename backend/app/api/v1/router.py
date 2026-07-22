"""Aggregates all v1 API routers into a single APIRouter."""
from fastapi import APIRouter

from app.api.v1 import copilot, dashboard, documents, graph, rca, search

api_router = APIRouter()
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(copilot.router)
api_router.include_router(rca.router)
api_router.include_router(graph.router)
api_router.include_router(dashboard.router)
