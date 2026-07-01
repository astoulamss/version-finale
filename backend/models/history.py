from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from database.db import Base


class HistoryLog(Base):
    __tablename__ = "history_logs"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(50), nullable=False)  # "leave" ou "absence"
    record_id = Column(Integer, nullable=False)       # ID du congé ou de l'absence
    action = Column(String(100), nullable=False)       # "created", "approved", "rejected", "cancelled", etc.
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True) # Qui a fait l'action
    details = Column(Text, nullable=True)             # Description textuelle
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relation
    user = relationship("User", foreign_keys=[performed_by])

    def __repr__(self):
        return f"<HistoryLog(id={self.id}, type={self.record_type}, action={self.action})>"
