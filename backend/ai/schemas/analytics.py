from pydantic import BaseModel
from typing import Optional
from datetime import date


class RiskAnalysisRequest(BaseModel):
    analysis_type: str = "turnover"  # turnover, absenteeism, engagement
    department_id: Optional[int] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class RiskAnalysisResponse(BaseModel):
    analysis_type: str
    risk_level: str  # low, medium, high
    risk_score: float
    factors: list[str]
    recommendations: list[str]
    disclaimer: str
