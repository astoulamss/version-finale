from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
from models.employees import EmployeeStatusEnum
from schemas.user import UserResponse


# ── Département ──────────────────────────────────────────────
class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    manager_id: Optional[int] = None
    manager_nom: Optional[str] = None
    manager_prenom: Optional[str] = None

    class Config:
        from_attributes = True


class DepartmentManagerAssign(BaseModel):
    manager_id: Optional[int] = None  # None = désaffecter le manager


# ── Poste ────────────────────────────────────────────────────
class PositionCreate(BaseModel):
    title: str
    description: Optional[str] = None


class PositionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class PositionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ── Manager (utilisateur avec rôle manager) ──────────────────
class ManagerResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str

    class Config:
        from_attributes = True


# ── Employé ──────────────────────────────────────────────────
class EmployeeCreate(BaseModel):
    user_id: int
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    manager_id: Optional[int] = None   # ID de l'utilisateur manager
    salary: Optional[float] = None
    hire_date: Optional[date] = None
    departure_date: Optional[date] = None
    status: EmployeeStatusEnum = EmployeeStatusEnum.ACTIVE
    date_naissance: Optional[date] = None
    nationalite: Optional[str] = None
    adresse: Optional[str] = None
    numero_telephone: Optional[str] = None
    sexe: Optional[str] = None


class EmployeeUpdate(BaseModel):
    """Mise à jour partielle d'un profil employé (Admin et RH seulement)"""
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    manager_id: Optional[int] = None
    salary: Optional[float] = None
    hire_date: Optional[date] = None
    departure_date: Optional[date] = None
    status: Optional[EmployeeStatusEnum] = None
    date_naissance: Optional[date] = None
    nationalite: Optional[str] = None
    adresse: Optional[str] = None
    numero_telephone: Optional[str] = None
    sexe: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: int
    user_id: int
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    manager_id: Optional[int] = None
    salary: Optional[float] = None
    hire_date: Optional[date] = None
    departure_date: Optional[date] = None
    status: EmployeeStatusEnum
    date_naissance: Optional[date] = None
    nationalite: Optional[str] = None
    adresse: Optional[str] = None
    numero_telephone: Optional[str] = None
    sexe: Optional[str] = None
    created_at: datetime
    contract_type: Optional[str] = None

    # Objets imbriqués pour le front-end
    user: Optional[UserResponse] = None
    department: Optional[DepartmentResponse] = None
    position: Optional[PositionResponse] = None
    manager: Optional[UserResponse] = None

    class Config:
        from_attributes = True
