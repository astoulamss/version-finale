from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
from models.features import OnboardingStatusEnum, OnboardingPlanTypeEnum, OnboardingTaskStatusEnum

# ── Onboarding Task ──────────────────────────────────────────
class OnboardingTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    assigned_to: Optional[int] = None
    status: OnboardingTaskStatusEnum = OnboardingTaskStatusEnum.TODO

class OnboardingTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    assigned_to: Optional[int] = None
    status: Optional[OnboardingTaskStatusEnum] = None

class OnboardingTaskResponse(BaseModel):
    id: int
    plan_id: int
    step_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: OnboardingTaskStatusEnum
    assigned_to: Optional[int] = None
    assigned_nom: Optional[str] = None
    assigned_prenom: Optional[str] = None

    class Config:
        from_attributes = True

# ── Onboarding Feedback ──────────────────────────────────────
class OnboardingFeedbackCreate(BaseModel):
    comment: str

class OnboardingFeedbackResponse(BaseModel):
    id: int
    onboarding_id: int
    author_id: int
    author_nom: Optional[str] = None
    author_prenom: Optional[str] = None
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True

# ── Onboarding Plan ──────────────────────────────────────────
class OnboardingPlanCreate(BaseModel):
    employee_id: int
    start_date: date
    end_date: date
    plan_type: OnboardingPlanTypeEnum
    status: OnboardingStatusEnum = OnboardingStatusEnum.PENDING

class OnboardingPlanUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    plan_type: Optional[OnboardingPlanTypeEnum] = None
    status: Optional[OnboardingStatusEnum] = None

class OnboardingPlanResponse(BaseModel):
    id: int
    employee_id: int
    start_date: date
    end_date: date
    status: OnboardingStatusEnum
    plan_type: OnboardingPlanTypeEnum
    created_at: datetime
    employee_nom: Optional[str] = None
    employee_prenom: Optional[str] = None
    employee_email: Optional[str] = None
    employee_role: Optional[str] = None
    tasks: List[OnboardingTaskResponse] = []
    feedbacks: List[OnboardingFeedbackResponse] = []

    class Config:
        from_attributes = True
