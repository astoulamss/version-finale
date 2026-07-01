from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func as sqlfunc
from database.db import get_db
from models.audit_log import AuditLog
from models.user import User, RoleEnum
from core.security import get_current_user
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/audit", tags=["Audit"])


# ─── Schémas de réponse ───────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_email: Optional[str]
    action: str
    resource: Optional[str]
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    status: str
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditStatsResponse(BaseModel):
    total_logs: int
    logs_today: int
    logs_this_week: int
    critical_count: int
    high_count: int
    failed_logins_today: int
    suspicious_ips: List[dict]
    top_actions: List[dict]
    severity_breakdown: dict


# ─── Endpoints ───────────────────────────────────────────────────────────────

def _require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seul l'administrateur peut consulter le journal d'audit."
        )
    return current_user


@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(None, description="Filtrer par type d'action"),
    severity: Optional[str] = Query(None, description="Filtrer par sévérité (LOW/MEDIUM/HIGH/CRITICAL)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrer par statut (SUCCESS/FAILURE)"),
    user_email: Optional[str] = Query(None, description="Filtrer par email utilisateur"),
    date_from: Optional[str] = Query(None, description="Date de début (ISO 8601)"),
    date_to: Optional[str] = Query(None, description="Date de fin (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """
    Récupérer le journal d'audit avec filtres. Réservé à l'administrateur.
    """
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if severity:
        query = query.filter(AuditLog.severity == severity.upper())
    if status_filter:
        query = query.filter(AuditLog.status == status_filter.upper())
    if user_email:
        query = query.filter(AuditLog.user_email.ilike(f"%{user_email}%"))
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            query = query.filter(AuditLog.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            query = query.filter(AuditLog.created_at <= dt_to)
        except ValueError:
            pass

    logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
    return logs


@router.get("/stats", response_model=AuditStatsResponse)
def get_audit_stats(
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """
    Statistiques résumées du journal d'audit.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    total_logs = db.query(AuditLog).count()
    logs_today = db.query(AuditLog).filter(AuditLog.created_at >= today_start).count()
    logs_this_week = db.query(AuditLog).filter(AuditLog.created_at >= week_start).count()

    critical_count = db.query(AuditLog).filter(AuditLog.severity == "CRITICAL").count()
    high_count = db.query(AuditLog).filter(AuditLog.severity == "HIGH").count()

    failed_logins_today = db.query(AuditLog).filter(
        and_(
            AuditLog.action == "USER_LOGIN_FAILED",
            AuditLog.created_at >= today_start
        )
    ).count()

    # IPs suspectes : celles ayant eu des échecs de connexion dans les 24h
    suspicious_ip_rows = db.query(
        AuditLog.ip_address,
        sqlfunc.count(AuditLog.id).label("count")
    ).filter(
        and_(
            AuditLog.action == "USER_LOGIN_FAILED",
            AuditLog.created_at >= today_start,
            AuditLog.ip_address.isnot(None)
        )
    ).group_by(AuditLog.ip_address).order_by(desc("count")).limit(5).all()
    suspicious_ips = [{"ip": row.ip_address, "count": row.count} for row in suspicious_ip_rows]

    # Top actions des 7 derniers jours
    top_action_rows = db.query(
        AuditLog.action,
        sqlfunc.count(AuditLog.id).label("count")
    ).filter(
        AuditLog.created_at >= week_start
    ).group_by(AuditLog.action).order_by(desc("count")).limit(8).all()
    top_actions = [{"action": row.action, "count": row.count} for row in top_action_rows]

    # Répartition par sévérité
    severity_rows = db.query(
        AuditLog.severity,
        sqlfunc.count(AuditLog.id).label("count")
    ).filter(AuditLog.created_at >= week_start).group_by(AuditLog.severity).all()
    severity_breakdown = {row.severity: row.count for row in severity_rows}

    return AuditStatsResponse(
        total_logs=total_logs,
        logs_today=logs_today,
        logs_this_week=logs_this_week,
        critical_count=critical_count,
        high_count=high_count,
        failed_logins_today=failed_logins_today,
        suspicious_ips=suspicious_ips,
        top_actions=top_actions,
        severity_breakdown=severity_breakdown,
    )


@router.get("/suspicious", response_model=List[AuditLogResponse])
def get_suspicious_activity(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """
    Retourner uniquement les activités suspectes ou à risque élevé.
    """
    logs = db.query(AuditLog).filter(
        or_(
            AuditLog.severity.in_(["HIGH", "CRITICAL"]),
            AuditLog.status == "FAILURE",
        )
    ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
    return logs
