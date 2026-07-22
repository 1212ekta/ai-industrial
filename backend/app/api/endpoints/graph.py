from fastapi import APIRouter
from app.services.graph_service import get_graph_data

router = APIRouter()

@router.get("/")
def get_graph():
    return get_graph_data()
