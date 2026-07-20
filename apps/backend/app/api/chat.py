from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from apps.backend.app.services.conversation import ConversationService

router = APIRouter()

service = ConversationService()


class ChatRequest(BaseModel):
    message: str


class ResponseMetrics(BaseModel):
    response_time_sec: float = 0.0
    tokens_generated: int = 0
    prompt_tokens: int = 0
    tokens_per_sec: float = 0.0
    model: str = ""


class ChatResponse(BaseModel):
    response: str
    metrics: Optional[ResponseMetrics] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await service.chat(request.message)

    return ChatResponse(
        response=result["reply"],
        metrics=ResponseMetrics(**result.get("metrics", {})),
    )