from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "admin"
    COLLABORATEUR = "collaborateur"
    DIRECTION = "direction"
    MANAGER = "manager"
    RH = "rh"
    MEDECINE_TRAVAIL = "medecine_travail"



class UserBase(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    role: RoleEnum = RoleEnum.COLLABORATEUR


class UserCreate(UserBase):
    mots_de_passe: str


class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    first_login: bool
    created_at: datetime
    departement: Optional[str] = None

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    mots_de_passe: str


class LoginRequest(BaseModel):
    email: EmailStr
    mots_de_passe: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class DashboardResponse(BaseModel):
    role: str
    user_name: str
    first_login: bool
    message: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class AdminPasswordReset(BaseModel):
    """Réinitialisation du mot de passe d'un utilisateur par l'Admin."""
    new_password: str


class StatsResponse(BaseModel):
    """Statistiques globales pour le tableau de bord Admin/RH."""
    total_users: int
    total_employees: int
    leaves_pending: int
    leaves_approved: int
    total_absences: int
    total_documents: int
    total_contracts: int
