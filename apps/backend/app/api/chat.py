from fastapi import APIRouter
from pydantic import BaseModel

from apps.backend.app.services.conversation import ConversationService

router = APIRouter()

service = ConversationService()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    reply = await service.chat(request.message)

    return ChatResponse(response=reply)