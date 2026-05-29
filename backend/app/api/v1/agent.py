from __future__ import annotations

from fastapi import APIRouter

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    user_id: str
    message: str = Field(..., min_length=1, max_length=2000)


class AgentChatResponse(BaseModel):
    user_id: str
    reply: str
    model_used: str


router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(payload: AgentChatRequest) -> AgentChatResponse:
    from app.services.agent_service import agent_service

    reply, model_used = agent_service.chat(payload.user_id, payload.message)

    return AgentChatResponse(
        user_id=payload.user_id,
        reply=reply,
        model_used=model_used,
    )
