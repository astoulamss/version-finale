from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Conversation ───────────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, example="Question sur mes congés")


class ConversationOut(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Message ────────────────────────────────────────────────────────────────

class MessageSend(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, example="Combien de jours de congé me reste-t-il ?")


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    user_id: Optional[int]
    sender: str   # "user" | "bot"
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationOut):
    """Conversation avec tous ses messages."""
    messages: List[MessageOut] = []


# ─── Logs (admin only) ───────────────────────────────────────────────────────

class ChatbotLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    conversation_id: Optional[int]
    query: str
    response: str
    response_status: Optional[str]
    risk_level: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
