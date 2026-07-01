from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.features import TicketStatusEnum

class TicketBase(BaseModel):
    subject: str = Field(..., title="Sujet", min_length=3, max_length=255)
    description: Optional[str] = Field(None, title="Description détaillée")

class TicketCreate(TicketBase):
    target_employee_id: Optional[int] = None

class TicketUpdateStatus(BaseModel):
    status: TicketStatusEnum

class TicketAssign(BaseModel):
    assigned_to: int

class UserBasicInfo(BaseModel):
    id: int
    nom: str
    prenom: str
    
    class Config:
        from_attributes = True

class TicketResponse(TicketBase):
    id: int
    employee_id: int
    status: TicketStatusEnum
    assigned_to: Optional[int] = None
    created_at: datetime
    
    # Informations optionnelles pour l'affichage
    employee: Optional[UserBasicInfo] = None
    assignee: Optional[UserBasicInfo] = None

    class Config:
        from_attributes = True
