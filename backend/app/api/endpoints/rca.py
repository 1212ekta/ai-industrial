from fastapi import APIRouter
from app.schemas.domain import RCARequest, RCAResponse
from app.services.graph_service import get_equipment_context
from app.services.embeddings import search_chunks
from app.services.llm_service import generate_rca

router = APIRouter()

@router.post("/", response_model=RCAResponse)
def perform_rca(request: RCARequest):
    graph_context = get_equipment_context(request.equipment)
    
    # Also get some similar docs from vector DB
    query = f"Failure root cause for {request.equipment} {request.problem_description}"
    results = search_chunks(query, limit=3)
    
    vector_context = ""
    evidence = []
    for res in results:
        payload = res.payload
        vector_context += f"{payload['filename']}: {payload['text']}\n"
        evidence.append({
            "document_name": payload['filename'],
            "page_number": payload['page_number'],
            "text_snippet": payload['text'][:150]
        })
        
    rca_result = generate_rca(request.equipment, request.problem_description, graph_context, vector_context)
    
    return RCAResponse(
        likely_causes=rca_result.get("likely_causes", []),
        recommendations=rca_result.get("recommendations", []),
        evidence=evidence
    )
