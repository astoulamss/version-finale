from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User, RoleEnum
from models.history import HistoryLog
from models.features import Leave, Document
from models.absences import Absence
from models.employees import Employee
from schemas.history import HistoryLogResponse
from core.security import get_current_user, require_role
from typing import List, Optional
from datetime import date

router = APIRouter(prefix="/api/history", tags=["History & Audit"])


@router.get("/leaves/{leave_id}", response_model=List[HistoryLogResponse])
def get_leave_history(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtenir l'historique des actions sur un congé spécifique.
    - L'employé concerné, son manager, le RH et l'Admin peuvent le voir.
    """
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Congé introuvable."
        )

    # Vérification des permissions
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH]:
        if leave.employee_id != current_user.id:
            if current_user.role == RoleEnum.MANAGER:
                # Vérifier si l'employé fait partie de l'équipe du manager
                emp = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
                if not emp or emp.manager_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Accès refusé. Ce congé appartient à un employé hors de votre équipe."
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accès refusé. Ce congé ne vous appartient pas."
                )

    logs = db.query(HistoryLog).filter(
        HistoryLog.record_type == "leave",
        HistoryLog.record_id == leave_id
    ).order_by(HistoryLog.created_at.asc()).all()

    # Formater avec le nom de la personne qui a effectué l'action
    result = []
    for log in logs:
        resp = HistoryLogResponse.model_validate(log)
        if log.user:
            resp.performer_nom = log.user.nom
            resp.performer_prenom = log.user.prenom
        result.append(resp)

    return result


@router.get("/absences/{absence_id}", response_model=List[HistoryLogResponse])
def get_absence_history(
    absence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtenir l'historique des actions sur une absence spécifique.
    - L'employé concerné, son manager, le RH et l'Admin peuvent le voir.
    """
    absence = db.query(Absence).filter(Absence.id == absence_id).first()
    if not absence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Absence introuvable."
        )

    # Vérification des permissions
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH]:
        if absence.employee_id != current_user.id:
            if current_user.role == RoleEnum.MANAGER:
                # Vérifier si l'employé fait partie de l'équipe du manager
                emp = db.query(Employee).filter(Employee.user_id == absence.employee_id).first()
                if not emp or emp.manager_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Accès refusé. Cette absence appartient à un employé hors de votre équipe."
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accès refusé. Cette absence ne vous appartient pas."
                )

    logs = db.query(HistoryLog).filter(
        HistoryLog.record_type == "absence",
        HistoryLog.record_id == absence_id
    ).order_by(HistoryLog.created_at.asc()).all()

    result = []
    for log in logs:
        resp = HistoryLogResponse.model_validate(log)
        if log.user:
            resp.performer_nom = log.user.nom
            resp.performer_prenom = log.user.prenom
        result.append(resp)

    return result


@router.get("/", response_model=List[HistoryLogResponse])
def list_my_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    record_type: Optional[str] = Query(
        None,
        description="Filtrer par type d'enregistrement : leave, absence, document"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Date de début (incluse) au format YYYY-MM-DD"
    ),
    end_date: Optional[date] = Query(
        None,
        description="Date de fin (incluse) au format YYYY-MM-DD"
    ),
):
    """
    Liste globale d'historique avec filtres optionnels :
    - **record_type** : `leave`, `absence`, `document`
    - **start_date** / **end_date** : plage de dates (YYYY-MM-DD)

    Permissions :
    - RH / Admin : toutes les actions de l'entreprise.
    - Manager : actions le concernant ou concernant son équipe.
    - Collaborateur : uniquement les actions le concernant.
    """
    query = db.query(HistoryLog).join(User, HistoryLog.performed_by == User.id, isouter=True)

    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH]:
        if current_user.role == RoleEnum.MANAGER:
            team_ids = [e.user_id for e in db.query(Employee).filter(Employee.manager_id == current_user.id).all()]
            all_target_ids = team_ids + [current_user.id]

            leave_ids = [l.id for l in db.query(Leave).filter(Leave.employee_id.in_(all_target_ids)).all()]
            absence_ids = [a.id for a in db.query(Absence).filter(Absence.employee_id.in_(all_target_ids)).all()]
            doc_ids = [d.id for d in db.query(Document).filter(Document.employee_id.in_(all_target_ids)).all()]

            query = query.filter(
                (HistoryLog.performed_by == current_user.id) |
                ((HistoryLog.record_type == "leave") & (HistoryLog.record_id.in_(leave_ids))) |
                ((HistoryLog.record_type == "absence") & (HistoryLog.record_id.in_(absence_ids))) |
                ((HistoryLog.record_type == "document") & (HistoryLog.record_id.in_(doc_ids)))
            )
        else:
            query = query.filter(HistoryLog.performed_by == current_user.id)

    # ── Filtres optionnels ─────────────────────────────────────────────
    if record_type:
        query = query.filter(HistoryLog.record_type == record_type)

    if start_date:
        query = query.filter(HistoryLog.created_at >= start_date)

    if end_date:
        # inclure toute la journée de end_date
        from datetime import datetime, timedelta
        end_dt = datetime.combine(end_date, datetime.max.time())
        query = query.filter(HistoryLog.created_at <= end_dt)

    logs = query.order_by(HistoryLog.created_at.desc()).all()

    result = []
    for log in logs:
        resp = HistoryLogResponse.model_validate(log)
        if log.user:
            resp.performer_nom = log.user.nom
            resp.performer_prenom = log.user.prenom
        result.append(resp)

    return result


@router.get("/documents/{document_id}", response_model=List[HistoryLogResponse])
def get_document_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtenir l'historique des actions sur un document spécifique (téléchargements, etc.).
    - L'employé concerné, son manager, le RH et l'Admin peuvent le voir.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document introuvable."
        )

    # Vérification des permissions
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH]:
        if document.employee_id != current_user.id:
            if current_user.role == RoleEnum.MANAGER:
                # Vérifier si l'employé fait partie de l'équipe du manager
                emp = db.query(Employee).filter(Employee.user_id == document.employee_id).first()
                if not emp or emp.manager_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Accès refusé. Ce document appartient à un employé hors de votre équipe."
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accès refusé. Ce document ne vous appartient pas."
                )

    logs = db.query(HistoryLog).filter(
        HistoryLog.record_type == "document",
        HistoryLog.record_id == document_id
    ).order_by(HistoryLog.created_at.asc()).all()

    result = []
    for log in logs:
        resp = HistoryLogResponse.model_validate(log)
        if log.user:
            resp.performer_nom = log.user.nom
            resp.performer_prenom = log.user.prenom
        result.append(resp)

    return result
