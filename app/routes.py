from fastapi import APIRouter
from pydantic import BaseModel
from services.ai_client import ai_chat

router = APIRouter(prefix="/api")

class ChatRequest(BaseModel):
    userId: str
    message: str

class ChatResponse(BaseModel):
    response: str
    intent: str
    tool_used: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    return await ai_chat(request.message, request.userId)
