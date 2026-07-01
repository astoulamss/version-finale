from pydantic import BaseModel
from typing import Optional, Any


class ChatRequest(BaseModel):
    query: str
    history: Optional[list[dict[str, str]]] = None
    conversation_id: Optional[int] = None


class ChatDocumentInfo(BaseModel):
    id: int
    title: str
    document_type: str
    pdf_url: str
    status: str


class SourceInfo(BaseModel):
    title: str
    page: int
    snippet: str


class ChatResponse(BaseModel):
    response: str
    sources: Optional[list[SourceInfo]] = None
    document: Optional[ChatDocumentInfo] = None
    chart: Optional[str] = None
    conversation_id: Optional[int] = None



class ChatHistoryItem(BaseModel):
    role: str
    content: str
