from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database.db import get_db
from core.security import require_role
from models.user import User, RoleEnum
from models.employees import Employee
from models.features import RiskScore, Recommendation, RecommendationStatusEnum

router = APIRouter(prefix="/api/manager/risks", tags=["Team Risks"])

# Schemas
class RecommendationResponse(BaseModel):
    id: int
    recommendation: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class TeamRiskResponse(BaseModel):
    employee_id: int
    user_id: int
    employee_name: str
    department_name: Optional[str]
    turnover_risk: Optional[float]
    burnout_risk: Optional[float]
    engagement_risk: Optional[float]
    generated_at: Optional[datetime]
    recommendations: List[RecommendationResponse] = []

class UpdateRecommendationStatus(BaseModel):
    status: RecommendationStatusEnum

# Helper to get team user ids
def _get_team_user_ids(db: Session, manager_id: int) -> List[int]:
    subordinates = db.query(Employee).filter(Employee.manager_id == manager_id).all()
    return [emp.user_id for emp in subordinates]

@router.get("", response_model=List[TeamRiskResponse])
def get_team_risks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION]))
):
    team_user_ids = _get_team_user_ids(db, current_user.id)
    if not team_user_ids:
        return []
    
    # Identify employees to include
    employees = db.query(Employee).filter(Employee.user_id.in_(team_user_ids)).all()
    
    # Restrict to the same department as the manager to avoid cross-department bleeding from bad seed data
    manager_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if manager_emp and manager_emp.department_id:
        employees = [emp for emp in employees if emp.department_id == manager_emp.department_id]

    result = []
    for emp in employees:
        if emp.user and emp.user.role in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION]:
            continue
        if emp.status != "active":
            continue

        # Get latest risk score
        latest_risk = (
            db.query(RiskScore)
            .filter(RiskScore.employee_id == emp.user_id)
            .order_by(RiskScore.generated_at.desc())
            .first()
        )
        
        if latest_risk:
            recs = db.query(Recommendation).filter(Recommendation.risk_score_id == latest_risk.id).all()
            dept_name = emp.department.name if emp.department else "N/A"
            emp_name = f"{emp.user.prenom} {emp.user.nom}" if emp.user else "Inconnu"
            
            result.append(TeamRiskResponse(
                employee_id=emp.id,
                user_id=emp.user_id,
                employee_name=emp_name,
                department_name=dept_name,
                turnover_risk=float(latest_risk.turnover_risk) if latest_risk.turnover_risk and current_user.role != RoleEnum.MANAGER else None,
                burnout_risk=float(latest_risk.burnout_risk) if latest_risk.burnout_risk else None,
                engagement_risk=float(latest_risk.engagement_risk) if latest_risk.engagement_risk and current_user.role != RoleEnum.MANAGER else None,
                generated_at=latest_risk.generated_at,
                recommendations=[
                    RecommendationResponse(
                        id=r.id,
                        recommendation=r.recommendation,
                        status=r.status.value if hasattr(r.status, "value") else r.status,
                        created_at=r.created_at
                    ) for r in recs
                ]
            ))

    # sort by highest composite risk approximately (or turnover)
    result.sort(key=lambda x: (x.turnover_risk or 0) + (x.burnout_risk or 0) + (x.engagement_risk or 0), reverse=True)
    return result

@router.put("/recommendations/{rec_id}/status", response_model=RecommendationResponse)
def update_recommendation_status(
    rec_id: int,
    data: UpdateRecommendationStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.RH]))
):
    rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommandation introuvable")

    if current_user.role == RoleEnum.MANAGER:
        team_user_ids = _get_team_user_ids(db, current_user.id)
        if rec.employee_id not in team_user_ids:
            raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à modifier cette recommandation")

    rec.status = data.status
    db.commit()
    db.refresh(rec)
    
    return RecommendationResponse(
        id=rec.id,
        recommendation=rec.recommendation,
        status=rec.status.value if hasattr(rec.status, "value") else rec.status,
        created_at=rec.created_at
    )
