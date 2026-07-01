from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from database.db import Base
import enum
from datetime import datetime


class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    COLLABORATEUR = "collaborateur"
    DIRECTION = "direction"
    MANAGER = "manager"
    RH = "rh"
    MEDECINE_TRAVAIL = "medecine_travail"



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mots_de_passe = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.COLLABORATEUR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    first_login = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, nom={self.nom}, prenom={self.prenom}, role={self.role})>"

    @property
    def departement(self) -> str | None:
        from sqlalchemy.orm import object_session
        from models.employees import Employee
        session = object_session(self)
        if session:
            emp = session.query(Employee).filter(Employee.user_id == self.id).first()
            if emp and emp.department:
                return emp.department.name
        return None
