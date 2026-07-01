from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class ManagerTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: int
    due_date: Optional[date] = None
    priority: str = "medium"
    status: str = "todo"


class ManagerTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class ManagerTaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    assigned_to: int
    created_by: int
    due_date: Optional[date] = None
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime

    # Enrichissement des noms
    assignee_nom: Optional[str] = None
    assignee_prenom: Optional[str] = None
    assignee_department: Optional[str] = None
    creator_nom: Optional[str] = None
    creator_prenom: Optional[str] = None

    class Config:
        from_attributes = True
