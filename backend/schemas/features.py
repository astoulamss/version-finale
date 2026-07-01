from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, Dict, Any
from models.features import LeaveStatusEnum, LeaveTypeEnum, DocumentStatusEnum


# Leave Schemas
class LeaveCreate(BaseModel):
    start_date: date
    end_date: date
    leave_type: Optional[LeaveTypeEnum] = None
    leave_type_id: Optional[int] = None
    reason: Optional[str] = None


class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    start_date: date
    end_date: date
    leave_type_id: int
    leave_type: LeaveTypeEnum
    status: LeaveStatusEnum
    reason: Optional[str]
    created_at: datetime
    is_archived: bool

    class Config:
        from_attributes = True


class LeaveUpdate(BaseModel):
    status: LeaveStatusEnum
    reason: Optional[str] = None
    is_archived: Optional[bool] = None


class LeaveEdit(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    leave_type: Optional[LeaveTypeEnum] = None
    leave_type_id: Optional[int] = None
    reason: Optional[str] = None


# Leave Type Schemas
class LeaveTypeCreate(BaseModel):
    name: str
    max_days: int
    description: Optional[str] = None


class LeaveTypeResponse(BaseModel):
    id: int
    name: str
    max_days: int
    description: Optional[str]

    class Config:
        from_attributes = True


# Leave Balance Schemas
class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: int
    leave_type_id: int
    remaining_days: float
    updated_at: datetime
    leave_type_name: Optional[str] = None

    class Config:
        from_attributes = True


# Document Type Schemas
class DocumentTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DocumentTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


# Document Template Schemas
class DocumentTemplateCreate(BaseModel):
    name: str
    content: str
    description: Optional[str] = None


class DocumentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None


class DocumentTemplateResponse(BaseModel):
    id: int
    name: str
    content: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Document Schemas

class DocumentManualCreate(BaseModel):
    """Création manuelle d'un document pour un employé (RH/Admin)"""
    employee_id: int
    title: str
    document_type: Optional[str] = None  # ex: attestation, contrat, congé, absence
    content: str
    status: DocumentStatusEnum = DocumentStatusEnum.DRAFT


class DocumentGenerateRequest(BaseModel):
    """Génération d'un document à partir d'un template (RH/Admin)"""
    employee_id: int
    template_id: int
    document_type: Optional[str] = None
    extra_vars: Optional[Dict[str, Any]] = None  # ex: {"start_date": "01/06/2026", "end_date": "05/06/2026"}
    status: DocumentStatusEnum = DocumentStatusEnum.DRAFT


class DocumentStatusUpdate(BaseModel):
    """Mise à jour du statut d'un document"""
    status: DocumentStatusEnum


class DocumentResponse(BaseModel):
    id: int
    employee_id: int
    template_id: Optional[int]
    document_type: Optional[str]
    title: str
    content: str
    generated_by_ai: bool
    status: DocumentStatusEnum
    created_by: int
    created_at: datetime
    file_url: Optional[str] = None
    is_sent: bool = False

    class Config:
        from_attributes = True



# Formation Schemas
class FormationCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    target_department_id: Optional[int] = None


class FormationResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_date: date
    end_date: date
    target_department_id: Optional[int] = None
    target_department_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Contract Schemas
class ContractCreate(BaseModel):
    contract_type: str
    start_date: date
    end_date: Optional[date] = None
    position: str
    salary: Optional[str] = None


class ContractResponse(BaseModel):
    id: int
    user_id: int
    contract_type: str
    start_date: date
    end_date: Optional[date]
    position: str
    salary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Formation Enrollment Schemas
class FormationEnrollmentCreate(BaseModel):
    employee_id: Optional[int] = None


class FormationEnrollmentResponse(BaseModel):
    id: int
    employee_id: int
    formation_id: int
    enrolled_at: datetime
    nom: Optional[str] = None
    prenom: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    formation_title: Optional[str] = None
    formation_description: Optional[str] = None
    formation_start_date: Optional[date] = None
    formation_end_date: Optional[date] = None

    class Config:
        from_attributes = True
