from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from pydantic import BaseModel
from app.services.embeddings import search_chunks

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

@router.post("/")
def search(request: SearchRequest):
    results = search_chunks(request.query, limit=request.limit)
    response = []
    for r in results:
        response.append({
            "score": r.score,
            "document_id": r.payload["document_id"],
            "filename": r.payload["filename"],
            "page_number": r.payload["page_number"],
            "text": r.payload["text"]
        })
    return response
