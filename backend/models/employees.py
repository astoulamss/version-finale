from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey, Enum, func
from sqlalchemy.orm import relationship
from database.db import Base
import enum


class EmployeeStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ON_LEAVE = "on_leave"


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    employees = relationship("Employee", back_populates="department")
    manager = relationship("User", foreign_keys=[manager_id])

    def __repr__(self):
        return f"<Department(id={self.id}, name={self.name})>"


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    employees = relationship("Employee", back_populates="position")

    def __repr__(self):
        return f"<Position(id={self.id}, title={self.title})>"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    # manager_id pointe vers un autre user ayant le rôle manager
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    salary = Column(Numeric(10, 2), nullable=True)
    hire_date = Column(Date, nullable=True)
    departure_date = Column(Date, nullable=True)
    status = Column(Enum(EmployeeStatusEnum, name='employeestatusenum'), default=EmployeeStatusEnum.ACTIVE, nullable=False)
    date_naissance = Column(Date, nullable=True)
    nationalite = Column(String(100), nullable=True)
    adresse = Column(String(255), nullable=True)
    distance_from_home_km = Column(Integer, nullable=True)
    numero_telephone = Column(String(50), nullable=True)
    sexe = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    user = relationship("User", foreign_keys=[user_id])
    manager = relationship("User", foreign_keys=[manager_id])
    department = relationship("Department", back_populates="employees")
    position = relationship("Position", back_populates="employees")

    @property
    def contract_type(self):
        from sqlalchemy.orm import object_session
        from models.features import Contract
        session = object_session(self)
        if session:
            contract = session.query(Contract).filter(
                Contract.user_id == self.user_id,
            ).order_by(Contract.id.desc()).first()
            if contract:
                return contract.contract_type
        return None

    def __repr__(self):
        return f"<Employee(id={self.id}, user_id={self.user_id}, status={self.status})>"
