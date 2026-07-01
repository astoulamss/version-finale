"""
Modèle AuditLog — Journal d'audit des actions système
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from database.db import Base


class SeverityEnum:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class StatusEnum:
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Qui a effectué l'action
    user_id = Column(Integer, nullable=True)           # Peut être NULL (ex: connexion échouée)
    user_email = Column(String(255), nullable=True)    # Snapshot email au moment de l'action

    # L'action
    action = Column(String(100), nullable=False, index=True)   # ex: USER_CREATED, USER_LOGIN
    resource = Column(String(255), nullable=True)               # ex: User#42
    details = Column(JSON, nullable=True)                       # Données supplémentaires (avant/après, IP...)

    # Contexte réseau
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Résultat et sévérité
    status = Column(String(20), nullable=False, default="SUCCESS")    # SUCCESS | FAILURE
    severity = Column(String(20), nullable=False, default="LOW", index=True)  # LOW | MEDIUM | HIGH | CRITICAL

    # Horodatage
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.user_email}, severity={self.severity})>"
