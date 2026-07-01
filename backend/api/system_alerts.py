from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database.db import get_db
from core.security import get_current_user, require_role
from models.user import User, RoleEnum
from models.system_alerts import SystemAlert, SystemAlertHistory, SystemAlertStatusEnum

router = APIRouter(prefix="/api/system-alerts", tags=["System Alerts"])

# --- Schemas ---

class SystemAlertActionCreate(BaseModel):
    action: str
    resolve_alert: bool = False

class SystemAlertUpdate(BaseModel):
    status: Optional[SystemAlertStatusEnum] = None
    severity: Optional[str] = None

class SystemAlertHistoryResponse(BaseModel):
    id: int
    action: str
    performed_by: int
    performer_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SystemAlertResponse(BaseModel):
    id: int
    title: str
    severity: str
    description: Optional[str]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True

class SystemAlertCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str

# --- Endpoints ---

@router.get("", response_model=List[SystemAlertResponse])
def list_system_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN]))
):
    """Récupère toutes les alertes système (Admin seulement)"""
    alerts = db.query(SystemAlert).order_by(desc(SystemAlert.created_at)).all()
    
    result = []
    for alert in alerts:
        result.append(SystemAlertResponse(
            id=alert.id,
            title=alert.title,
            severity=alert.severity,
            description=alert.description,
            status=alert.status.value if hasattr(alert.status, 'value') else alert.status,
            created_at=alert.created_at,
            resolved_at=alert.resolved_at
        ))
        
    return result

@router.post("", response_model=SystemAlertResponse)
def create_test_system_alert(
    data: SystemAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN]))
):
    """Créer une alerte système (Endpoint utilisé pour tester le dashboard Admin)"""
    alert = SystemAlert(
        title=data.title,
        description=data.description,
        severity=data.severity,
        status=SystemAlertStatusEnum.NEW
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return SystemAlertResponse(
        id=alert.id,
        title=alert.title,
        severity=alert.severity,
        description=alert.description,
        status=alert.status.value if hasattr(alert.status, 'value') else alert.status,
        created_at=alert.created_at,
        resolved_at=alert.resolved_at
    )

@router.put("/{alert_id}", response_model=SystemAlertResponse)
def update_system_alert(
    alert_id: int,
    data: SystemAlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN]))
):
    """Mettre à jour le statut ou la sévérité d'une alerte système"""
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte système non trouvée")
        
    if data.status:
        alert.status = data.status
        if data.status == SystemAlertStatusEnum.RESOLVED:
            alert.resolved_at = datetime.now()
    if data.severity:
        alert.severity = data.severity
        
    db.commit()
    db.refresh(alert)
    
    return SystemAlertResponse(
        id=alert.id,
        title=alert.title,
        severity=alert.severity,
        description=alert.description,
        status=alert.status.value if hasattr(alert.status, 'value') else alert.status,
        created_at=alert.created_at,
        resolved_at=alert.resolved_at
    )

@router.post("/{alert_id}/actions", response_model=SystemAlertHistoryResponse)
def take_corrective_action(
    alert_id: int,
    data: SystemAlertActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN]))
):
    """Enregistre une action corrective sur une alerte système"""
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte système non trouvée")
        
    history = SystemAlertHistory(
        alert_id=alert.id,
        action=data.action,
        performed_by=current_user.id
    )
    db.add(history)
    
    if data.resolve_alert:
        alert.status = SystemAlertStatusEnum.RESOLVED
        alert.resolved_at = datetime.now()
        
    db.commit()
    db.refresh(history)
    
    return SystemAlertHistoryResponse(
        id=history.id,
        action=history.action,
        performed_by=history.performed_by,
        performer_name=f"{current_user.prenom} {current_user.nom}",
        created_at=history.created_at
    )

@router.get("/{alert_id}/history", response_model=List[SystemAlertHistoryResponse])
def get_system_alert_history(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN]))
):
    """Consulte l'historique de traitement d'une alerte système"""
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte système non trouvée")
        
    history_records = db.query(SystemAlertHistory).filter(SystemAlertHistory.alert_id == alert_id).order_by(desc(SystemAlertHistory.created_at)).all()
    
    result = []
    for h in history_records:
        result.append(SystemAlertHistoryResponse(
            id=h.id,
            action=h.action,
            performed_by=h.performed_by,
            performer_name=f"{h.performer.prenom} {h.performer.nom}" if h.performer else "Inconnu",
            created_at=h.created_at
        ))
        
    return result
