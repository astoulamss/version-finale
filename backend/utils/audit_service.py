"""
Service utilitaire pour écrire dans le journal d'audit.
Appelé depuis les différents routers pour tracer les actions.
"""
from sqlalchemy.orm import Session
from models.audit_log import AuditLog
from fastapi import Request
from typing import Optional


def log_action(
    db: Session,
    action: str,
    severity: str = "LOW",
    status: str = "SUCCESS",
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    resource: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """
    Enregistrer une entrée dans le journal d'audit.
    """
    try:
        entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource=resource,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            severity=severity,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except Exception as e:
        # Ne jamais bloquer l'action principale en cas d'erreur d'audit
        db.rollback()
        print(f"[AUDIT WARNING] Failed to log action '{action}': {e}")
        return None


def get_client_info(request: Request) -> dict:
    """
    Extraire l'IP et le user-agent de la requête.
    """
    ip = request.client.host if request.client else "unknown"
    # Gérer les proxies (X-Forwarded-For)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    user_agent = request.headers.get("User-Agent", "unknown")
    return {"ip_address": ip, "user_agent": user_agent}


# Constantes pour les noms d'actions
class AuditAction:
    # Auth
    USER_LOGIN_SUCCESS = "USER_LOGIN_SUCCESS"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    USER_LOGOUT = "USER_LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"

    # Gestion des utilisateurs
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    USER_DELETED = "USER_DELETED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET_ADMIN = "PASSWORD_RESET_ADMIN"

    # Accès refusés
    ACCESS_DENIED = "ACCESS_DENIED"


# Constantes pour la sévérité
class AuditSeverity:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Constantes pour le statut
class AuditStatus:
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
