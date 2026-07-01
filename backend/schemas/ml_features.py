from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

class TimesheetCreate(BaseModel):
    is_overtime: Optional[bool] = False

class TimesheetResponse(BaseModel):
    id: int
    employee_id: int
    date: date
    clock_in: Optional[datetime]
    clock_out: Optional[datetime]
    hours_worked: Optional[float]
    is_overtime: bool
    status: str
    ip_address: Optional[str] = None
    employee_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PerformanceReviewBase(BaseModel):
    employee_id: int
    review_date: date
    performance_rating: int
    comments: Optional[str] = None

class PerformanceReviewCreate(PerformanceReviewBase):
    pass

class PerformanceReviewResponse(PerformanceReviewBase):
    id: int
    evaluator_id: int
    created_at: datetime

    class Config:
        from_attributes = True
