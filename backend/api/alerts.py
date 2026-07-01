from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database.db import get_db
from core.security import get_current_user, require_role
from models.user import User, RoleEnum
from models.features import Alert, AlertHistory, AlertStatusEnum, Recommendation, RiskScore
from models.employees import Employee
from utils.notifications import notify_role, create_notification

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

# --- Schemas ---

class AlertActionCreate(BaseModel):
    action: str
    resolve_alert: bool = False

class AlertUpdate(BaseModel):
    status: Optional[AlertStatusEnum] = None
    severity: Optional[str] = None

class AlertHistoryResponse(BaseModel):
    id: int
    action: str
    performed_by: int
    performer_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    department_name: Optional[str]
    alert_type: str
    severity: str
    description: Optional[str]
    status: str
    created_at: datetime
    recommendations: List[str] = []
    employee_status: str = "active"

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("", response_model=List[AlertResponse])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL, RoleEnum.MANAGER]))
):
    """Récupère toutes les alertes (avec filtrage d'équipe pour Manager)"""
    query = db.query(Alert).join(Employee, Employee.user_id == Alert.employee_id).filter(Employee.status == "active")
    
    if current_user.role == RoleEnum.MANAGER:
        managed_employees = db.query(Employee).filter(Employee.manager_id == current_user.id).all()
        managed_user_ids = [e.user_id for e in managed_employees]
        query = query.filter(Alert.employee_id.in_(managed_user_ids))
        query = query.filter(Alert.alert_type.ilike('%Désengagement%'))
    elif current_user.role == RoleEnum.MEDECINE_TRAVAIL:
        query = query.filter(Alert.alert_type.in_(["Risque de Burnout", "Risque Médical", "Risque Social", "Risque Psychosocial"]))
    elif current_user.role == RoleEnum.RH:
        from sqlalchemy import or_
        query = query.outerjoin(AlertHistory, Alert.id == AlertHistory.alert_id)
        query = query.filter(
            or_(
                ~Alert.alert_type.in_(["Risque de Burnout", "Risque Médical", "Risque Social", "Risque Psychosocial"]),
                AlertHistory.action.like("[ESCALADE RH]%")
            )
        ).distinct()
    elif current_user.role == RoleEnum.DIRECTION:
        query = query.filter(Alert.alert_type != "Risque de Burnout")
        query = query.filter(Alert.severity.in_(["HIGH", "CRITICAL"]))
        
    alerts = query.order_by(desc(Alert.created_at)).all()
    
    result = []
    for alert in alerts:
        # Load employee profile
        emp = db.query(Employee).filter(Employee.user_id == alert.employee_id).first()
        dept_name = emp.department.name if emp and emp.department else "N/A"
        
        # Load recommendations associated to this employee's latest risk score
        recommendations = []
        latest_risk = db.query(RiskScore).filter(RiskScore.employee_id == alert.employee_id).order_by(desc(RiskScore.generated_at)).first()
        if latest_risk:
            recs = db.query(Recommendation).filter(Recommendation.risk_score_id == latest_risk.id).all()
            recommendations = [r.recommendation for r in recs]

        # Check escalation status
        is_escalated = False
        if current_user.role == RoleEnum.RH:
            histories = db.query(AlertHistory).filter(AlertHistory.alert_id == alert.id).all()
            if any(h.action.startswith("[ESCALADE RH]") for h in histories):
                is_escalated = True
                
        # Anonymize for RH if not escalated (all types of alerts)
        if current_user.role == RoleEnum.RH and not is_escalated:
            display_name = "Employé Anonyme"
            dept_name = "Département Masqué"
        elif current_user.role == RoleEnum.MANAGER:
            display_name = "Collaborateur anonymisé"
            dept_name = "Mon Équipe"
        else:
            display_name = f"{alert.employee.prenom} {alert.employee.nom}" if alert.employee else "Inconnu"

        result.append(AlertResponse(
            id=alert.id,
            employee_id=alert.employee_id,
            employee_name=display_name,
            department_name=dept_name,
            alert_type=alert.alert_type,
            severity=alert.severity,
            description=alert.description,
            status=alert.status.value if hasattr(alert.status, 'value') else alert.status,
            created_at=alert.created_at,
            recommendations=recommendations,
            employee_status=emp.status.value if (emp and hasattr(emp.status, 'value')) else (emp.status if emp else 'N/A')
        ))
        
    return result

@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL, RoleEnum.MANAGER]))
):
    """Qualifie une alerte (change le statut ou la sévérité)"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
        
    if current_user.role == RoleEnum.MANAGER:
        emp = db.query(Employee).filter(Employee.user_id == alert.employee_id).first()
        if not emp or emp.manager_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès refusé. Cet employé n'est pas dans votre équipe.")
        
    if current_user.role == RoleEnum.MEDECINE_TRAVAIL and alert.alert_type not in ["Risque de Burnout", "Risque Médical", "Risque Social", "Risque Psychosocial"]:
        raise HTTPException(status_code=403, detail="Accès refusé. Vous ne pouvez gérer que les alertes de santé.")
        
    if data.status:
        alert.status = data.status
    if data.severity:
        alert.severity = data.severity
        
    db.commit()
    db.refresh(alert)
    
    # Return updated (simplified, omitting employee specifics for speed, but we can reconstruct it)
    emp = db.query(Employee).filter(Employee.user_id == alert.employee_id).first()
    dept_name = emp.department.name if emp and emp.department else "N/A"
    
    is_escalated = False
    if current_user.role == RoleEnum.RH:
        histories = db.query(AlertHistory).filter(AlertHistory.alert_id == alert.id).all()
        if any(h.action.startswith("[ESCALADE RH]") for h in histories):
            is_escalated = True
            
    if current_user.role == RoleEnum.RH and not is_escalated:
        display_name = "Employé Anonyme"
        dept_name = "Département Masqué"
    elif current_user.role == RoleEnum.MANAGER:
        display_name = "Collaborateur anonymisé"
        dept_name = "Mon Équipe"
    else:
        display_name = f"{alert.employee.prenom} {alert.employee.nom}" if alert.employee else "Inconnu"
    
    return AlertResponse(
        id=alert.id,
        employee_id=alert.employee_id,
        employee_name=display_name,
        department_name=dept_name,
        alert_type=alert.alert_type,
        severity=alert.severity,
        description=alert.description,
        status=alert.status.value if hasattr(alert.status, 'value') else alert.status,
        created_at=alert.created_at,
        recommendations=[]
    )

@router.post("/{alert_id}/actions", response_model=AlertHistoryResponse)
def take_corrective_action(
    alert_id: int,
    data: AlertActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL, RoleEnum.MANAGER]))
):
    """Enregistre une action corrective (Historisation du traitement)"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
        
    if current_user.role == RoleEnum.MANAGER:
        emp = db.query(Employee).filter(Employee.user_id == alert.employee_id).first()
        if not emp or emp.manager_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès refusé. Cet employé n'est pas dans votre équipe.")
        
    if current_user.role == RoleEnum.MEDECINE_TRAVAIL and alert.alert_type not in ["Risque de Burnout", "Risque Médical", "Risque Social", "Risque Psychosocial"]:
        raise HTTPException(status_code=403, detail="Accès refusé. Vous ne pouvez gérer que les alertes de santé.")
        
    # Create history entry
    history = AlertHistory(
        alert_id=alert.id,
        action=data.action,
        performed_by=current_user.id
    )
    db.add(history)
    
    # Optionally resolve the alert
    if data.resolve_alert:
        alert.status = AlertStatusEnum.RESOLVED
        
    # Notify RH if this is an escalation
    if data.action.startswith("[ESCALADE RH]"):
        notify_role(db, RoleEnum.RH, f"Nouvelle alerte santé escaladée par la Médecine du Travail pour l'employé(e) {alert.employee.prenom} {alert.employee.nom}.")
        
    # Notify Employee if an appointment is scheduled
    if data.action.startswith("[RDV MÉDICAL]"):
        create_notification(db, alert.employee_id, f"La Médecine du Travail a planifié un rendez-vous pour vous : {data.action.replace('[RDV MÉDICAL] ', '')}")
        
    db.commit()
    db.refresh(history)
    
    return AlertHistoryResponse(
        id=history.id,
        action=history.action,
        performed_by=history.performed_by,
        performer_name=f"{current_user.prenom} {current_user.nom}",
        created_at=history.created_at
    )

@router.get("/{alert_id}/history", response_model=List[AlertHistoryResponse])
def get_alert_history(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL]))
):
    """Consulte l'historique de traitement d'une alerte spécifique"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if current_user.role == RoleEnum.MEDECINE_TRAVAIL and alert and alert.alert_type not in ["Risque de Burnout", "Risque Médical", "Risque Social", "Risque Psychosocial"]:
        raise HTTPException(status_code=403, detail="Accès refusé.")
        
    history_records = db.query(AlertHistory).filter(AlertHistory.alert_id == alert_id).order_by(desc(AlertHistory.created_at)).all()
    
    result = []
    for h in history_records:
        result.append(AlertHistoryResponse(
            id=h.id,
            action=h.action,
            performed_by=h.performed_by,
            performer_name=f"{h.performer.prenom} {h.performer.nom}" if h.performer else "Inconnu",
            created_at=h.created_at
        ))
        
    return result
