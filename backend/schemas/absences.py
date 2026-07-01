from pydantic import BaseModel, computed_field
from datetime import datetime
from typing import Optional, List
from models.absences import AbsenceTypeEnum, AbsenceStatusEnum


class AbsenceCreate(BaseModel):
    employee_id: int
    absence_type: AbsenceTypeEnum
    start_date: datetime
    end_date: datetime
    reason: Optional[str] = None


class AbsenceUpdate(BaseModel):
    absence_type: Optional[AbsenceTypeEnum] = None
    status: Optional[AbsenceStatusEnum] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    reason: Optional[str] = None
    is_archived: Optional[bool] = None


class AbsenceResponse(BaseModel):
    id: int
    employee_id: int
    absence_type: AbsenceTypeEnum
    status: AbsenceStatusEnum
    start_date: datetime
    end_date: datetime
    reason: Optional[str]
    created_at: datetime
    is_archived: bool
    
    # Optionnels pour l'affichage du nom de l'employé
    nom: Optional[str] = None
    prenom: Optional[str] = None

    @computed_field
    @property
    def duration_hours(self) -> float:
        delta = self.end_date - self.start_date
        return max(0.0, delta.total_seconds() / 3600.0)

    class Config:
        from_attributes = True


class AbsencesListResponse(BaseModel):
    absences: list[AbsenceResponse]
    total_hours: float


class AbsenceStatsByType(BaseModel):
    absence_type: str
    count: int
    total_hours: float


class AbsenceStats(BaseModel):
    total_absences: int
    total_hours: float
    by_type: List[AbsenceStatsByType]
    most_affected_employees: List[dict]
    rate: Optional[float] = None
