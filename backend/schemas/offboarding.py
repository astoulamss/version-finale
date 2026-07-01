from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
from models.features import OffboardingStatusEnum, OffboardingTaskStatusEnum

# ── Offboarding Task ──────────────────────────────────────────
class OffboardingTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    assigned_to: Optional[int] = None
    status: OffboardingTaskStatusEnum = OffboardingTaskStatusEnum.TODO

class OffboardingTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    assigned_to: Optional[int] = None
    status: Optional[OffboardingTaskStatusEnum] = None

class OffboardingTaskResponse(BaseModel):
    id: int
    plan_id: int
    step_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: OffboardingTaskStatusEnum
    assigned_to: Optional[int] = None
    assigned_nom: Optional[str] = None
    assigned_prenom: Optional[str] = None

    class Config:
        from_attributes = True

# ── Offboarding Feedback ──────────────────────────────────────
class OffboardingFeedbackCreate(BaseModel):
    comment: str

class OffboardingFeedbackResponse(BaseModel):
    id: int
    plan_id: int
    author_id: int
    author_nom: Optional[str] = None
    author_prenom: Optional[str] = None
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True

# ── Offboarding Plan ──────────────────────────────────────────
class OffboardingPlanCreate(BaseModel):
    employee_id: int
    departure_date: date
    departure_reason: Optional[str] = None
    status: OffboardingStatusEnum = OffboardingStatusEnum.PENDING
    equipment_returned: bool = False
    administrative_closed: bool = False

class OffboardingPlanUpdate(BaseModel):
    departure_date: Optional[date] = None
    departure_reason: Optional[str] = None
    status: Optional[OffboardingStatusEnum] = None
    equipment_returned: Optional[bool] = None
    administrative_closed: Optional[bool] = None

class OffboardingPlanResponse(BaseModel):
    id: int
    employee_id: int
    departure_date: date
    departure_reason: Optional[str] = None
    status: OffboardingStatusEnum
    equipment_returned: bool
    administrative_closed: bool
    created_at: datetime
    employee_nom: Optional[str] = None
    employee_prenom: Optional[str] = None
    employee_email: Optional[str] = None
    employee_role: Optional[str] = None
    tasks: List[OffboardingTaskResponse] = []
    feedbacks: List[OffboardingFeedbackResponse] = []

    class Config:
        from_attributes = True
