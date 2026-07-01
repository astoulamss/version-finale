from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base
import enum

class SystemAlertStatusEnum(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

class SystemAlert(Base):
    __tablename__ = "system_alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), nullable=False, index=True) # e.g., INFO, WARNING, CRITICAL
    status = Column(Enum(SystemAlertStatusEnum), default=SystemAlertStatusEnum.NEW, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    history = relationship("SystemAlertHistory", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SystemAlert(id={self.id}, title={self.title}, status={self.status}, severity={self.severity})>"


class SystemAlertHistory(Base):
    __tablename__ = "system_alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("system_alerts.id"), nullable=False)
    action = Column(Text, nullable=False)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    alert = relationship("SystemAlert", back_populates="history")
    performer = relationship("User", foreign_keys=[performed_by])

    def __repr__(self):
        return f"<SystemAlertHistory(id={self.id}, alert_id={self.alert_id}, action={self.action})>"
