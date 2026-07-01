from pydantic import BaseModel
from typing import Optional
from datetime import date


class OnboardingRequest(BaseModel):
    employee_id: int
    plan_type: str = "30_days"  # 7_days, 30_days, 90_days
    start_date: Optional[str] = None  # YYYY-MM-DD, defaults to today


class OnboardingResponse(BaseModel):
    type: str  # onboarding or offboarding
    checklist: str
    employee_name: str
    plan_id: Optional[int] = None


class OffboardingRequest(BaseModel):
    employee_id: int
    departure_date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    departure_reason: Optional[str] = None
