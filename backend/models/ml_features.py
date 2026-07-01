from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database.db import Base

class TimesheetStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class SalaryHistory(Base):
    __tablename__ = "salary_history"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    old_salary = Column(Numeric(10, 2), nullable=True)
    new_salary = Column(Numeric(10, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    employee = relationship("Employee", foreign_keys=[employee_id])

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_date = Column(Date, nullable=False)
    performance_rating = Column(Integer, nullable=False) # 1 to 5
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    employee = relationship("Employee", foreign_keys=[employee_id])
    evaluator = relationship("User", foreign_keys=[evaluator_id])

class Timesheet(Base):
    __tablename__ = "timesheets"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    clock_in = Column(DateTime(timezone=True), nullable=True)
    clock_out = Column(DateTime(timezone=True), nullable=True)
    hours_worked = Column(Numeric(5, 2), nullable=True)
    is_overtime = Column(Boolean, default=False)
    ip_address = Column(String(50), nullable=True)
    status = Column(Enum(TimesheetStatusEnum), default=TimesheetStatusEnum.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    employee = relationship("Employee", foreign_keys=[employee_id])

    @property
    def employee_name(self) -> str:
        if self.employee and self.employee.user:
            return f"{self.employee.user.prenom} {self.employee.user.nom}"
        return f"Employé #{self.employee_id}"
