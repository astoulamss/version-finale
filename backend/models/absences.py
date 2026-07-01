from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, func, Boolean
from sqlalchemy.orm import relationship
from database.db import Base
import enum


class AbsenceTypeEnum(str, enum.Enum):
    MALADIE = "maladie"
    RETARD = "retard"
    INJUSTIFIE = "injustifie"
    AUTRE = "autre"


class AbsenceStatusEnum(str, enum.Enum):
    PENDING = "pending"
    RECEIVED = "received"
    APPROVED = "approved"
    REJECTED = "rejected"


from sqlalchemy import UniqueConstraint

class Absence(Base):
    __tablename__ = "absences"
    __table_args__ = (
        UniqueConstraint('employee_id', 'start_date', 'end_date', name='uq_absence_employee_dates'),
    )

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    absence_type = Column(Enum(AbsenceTypeEnum), default=AbsenceTypeEnum.MALADIE, nullable=False)
    status = Column(Enum(AbsenceStatusEnum), default=AbsenceStatusEnum.PENDING, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # Relations
    user = relationship("User", foreign_keys=[employee_id])

    def __repr__(self):
        return f"<Absence(id={self.id}, employee_id={self.employee_id}, type={self.absence_type}, status={self.status})>"
