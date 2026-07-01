from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database.db import get_db
from core.security import get_current_user, require_role
from models.user import User, RoleEnum
from models.employees import Employee, Department
from models.announcement import Announcement, RecipientTypeEnum, AnnouncementStatusEnum
from models.notification import Notification

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])

# --- Schemas ---

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    recipient_type: RecipientTypeEnum
    recipient_id: Optional[int] = None

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    sender_name: str
    recipient_type: RecipientTypeEnum
    recipient_id: Optional[int]
    recipient_name: str
    status: AnnouncementStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True

class RecipientOption(BaseModel):
    id: int
    name: str
    type: str # 'DEPARTMENT' or 'EMPLOYEE'

class RecipientsListResponse(BaseModel):
    departments: List[RecipientOption]
    employees: List[RecipientOption]

# --- Endpoints ---

@router.get("/recipients", response_model=RecipientsListResponse)
def get_recipients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION]))
):
    """Récupérer la liste des destinataires possibles (Départements et Employés actifs)"""
    departments = db.query(Department).all()
    employees = db.query(Employee).join(User, Employee.user_id == User.id).filter(User.is_active == True).all()

    dept_options = [RecipientOption(id=d.id, name=d.name, type="DEPARTMENT") for d in departments]
    
    emp_options = []
    for e in employees:
        if e.user:
            dept_name = e.department.name if e.department else "Sans département"
            emp_options.append(RecipientOption(
                id=e.user_id, 
                name=f"{e.user.prenom} {e.user.nom} - {dept_name}", 
                type="EMPLOYEE"
            ))

    return RecipientsListResponse(departments=dept_options, employees=emp_options)


@router.post("", response_model=AnnouncementResponse)
def create_announcement(
    data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION]))
):
    """Envoyer une nouvelle annonce/communication"""
    # 1. Validation de base
    if data.recipient_type in [RecipientTypeEnum.DEPARTMENT, RecipientTypeEnum.EMPLOYEE] and not data.recipient_id:
        raise HTTPException(status_code=400, detail="recipient_id est requis pour ce type de destinataire.")

    # 2. Résoudre le nom du destinataire
    recipient_name = "Tous les collaborateurs (Global)"
    target_users: List[User] = []

    if data.recipient_type == RecipientTypeEnum.GLOBAL:
        target_users = db.query(User).filter(User.is_active == True).all()
    
    elif data.recipient_type == RecipientTypeEnum.DEPARTMENT:
        dept = db.query(Department).filter(Department.id == data.recipient_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Département non trouvé.")
        recipient_name = f"Département: {dept.name}"
        employees_in_dept = db.query(Employee).filter(Employee.department_id == dept.id).all()
        user_ids = [e.user_id for e in employees_in_dept]
        target_users = db.query(User).filter(User.id.in_(user_ids), User.is_active == True).all()
    
    elif data.recipient_type == RecipientTypeEnum.EMPLOYEE:
        emp_user = db.query(User).filter(User.id == data.recipient_id).first()
        if not emp_user:
            raise HTTPException(status_code=404, detail="Employé non trouvé.")
        recipient_name = f"Employé: {emp_user.prenom} {emp_user.nom}"
        target_users = [emp_user]

    # 3. Créer l'enregistrement de l'annonce
    announcement = Announcement(
        title=data.title,
        content=data.content,
        sender_id=current_user.id,
        recipient_type=data.recipient_type,
        recipient_id=data.recipient_id,
        status=AnnouncementStatusEnum.SENT
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    # 4. Générer les notifications pour chaque utilisateur cible
    notifications_to_create = []
    for user in target_users:
        msg = f"📣 Annonce RH: {announcement.title}"
        if len(msg) > 250:
            msg = msg[:247] + "..."
        notif = Notification(
            user_id=user.id,
            message=msg
        )
        notifications_to_create.append(notif)
    
    if notifications_to_create:
        db.add_all(notifications_to_create)
        announcement.status = AnnouncementStatusEnum.DELIVERED
        db.commit()

    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        sender_name=f"{current_user.prenom} {current_user.nom}",
        recipient_type=announcement.recipient_type,
        recipient_id=announcement.recipient_id,
        recipient_name=recipient_name,
        status=announcement.status,
        created_at=announcement.created_at
    )


@router.get("", response_model=List[AnnouncementResponse])
def get_announcements_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION]))
):
    """Historique de toutes les annonces envoyées"""
    announcements = db.query(Announcement).order_by(desc(Announcement.created_at)).all()
    
    result = []
    for ann in announcements:
        # Re-construire le recipient_name (on pourrait aussi le stocker en BDD pour optimiser)
        recipient_name = "Tous les collaborateurs (Global)"
        if ann.recipient_type == RecipientTypeEnum.DEPARTMENT and ann.recipient_id:
            dept = db.query(Department).filter(Department.id == ann.recipient_id).first()
            if dept:
                recipient_name = f"Département: {dept.name}"
        elif ann.recipient_type == RecipientTypeEnum.EMPLOYEE and ann.recipient_id:
            emp = db.query(User).filter(User.id == ann.recipient_id).first()
            if emp:
                recipient_name = f"Employé: {emp.prenom} {emp.nom}"

        result.append(AnnouncementResponse(
            id=ann.id,
            title=ann.title,
            content=ann.content,
            sender_name=f"{ann.sender.prenom} {ann.sender.nom}" if ann.sender else "Inconnu",
            recipient_type=ann.recipient_type,
            recipient_id=ann.recipient_id,
            recipient_name=recipient_name,
            status=ann.status,
            created_at=ann.created_at
        ))

    return result
