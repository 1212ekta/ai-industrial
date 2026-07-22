from fastapi import APIRouter
from app.schemas.domain import ChatRequest, ChatResponse
from app.services.langgraph_agent import run_copilot

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def copilot_chat(request: ChatRequest):
    result = run_copilot(request.message)
    return result
