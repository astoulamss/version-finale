from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class HistoryLogResponse(BaseModel):
    id: int
    record_type: str
    record_id: int
    action: str
    performed_by: Optional[int]
    details: Optional[str]
    created_at: datetime
    
    performer_nom: Optional[str] = None
    performer_prenom: Optional[str] = None

    class Config:
        from_attributes = True
