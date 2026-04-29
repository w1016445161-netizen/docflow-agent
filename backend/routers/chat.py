from typing import Optional, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.llm_service import llm_service


router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    model: str
    content: str
    usage: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = llm_service.chat(
        user_prompt=request.message,
        system_prompt=request.system_prompt,
    )
    return result