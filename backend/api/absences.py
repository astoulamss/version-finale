from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from database.db import get_db
from models.user import User, RoleEnum
from models.employees import Employee
from models.absences import Absence, AbsenceTypeEnum, AbsenceStatusEnum
from schemas.absences import (
    AbsenceCreate, AbsenceUpdate, AbsenceResponse,
    AbsencesListResponse, AbsenceStats, AbsenceStatsByType
)
from core.security import get_current_user, require_role
from utils.history import log_action
from utils.notifications import create_notification, notify_role, notify_manager

router = APIRouter(prefix="/api/absences", tags=["Absences"])


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _check_dates(start: datetime, end: datetime):
    if start >= end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La date de début doit être strictement antérieure à la date de fin."
        )


def _get_employee_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur id={user_id} introuvable."
        )
    return user


def _check_write_access(db: Session, current_user: User, target_user_id: int):
    """Vérifie que current_user peut créer/modifier une absence pour target_user_id."""
    if current_user.role in [RoleEnum.ADMIN, RoleEnum.RH]:
        return
    if target_user_id == current_user.id:
        return
    if current_user.role == RoleEnum.MANAGER:
        emp = db.query(Employee).filter(Employee.user_id == target_user_id).first()
        if emp and emp.manager_id == current_user.id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Vous ne pouvez déclarer d'absence que pour vous-même ou les membres de votre équipe."
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès refusé. Vous ne pouvez déclarer d'absence que pour vous-même."
    )


def _check_read_access(db: Session, current_user: User, absence: Absence):
    """Vérifie que current_user peut lire cette absence."""
    if current_user.role in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MEDECINE_TRAVAIL, RoleEnum.DIRECTION]:
        return
    if absence.employee_id == current_user.id:
        return
    if current_user.role == RoleEnum.MANAGER:
        emp = db.query(Employee).filter(Employee.user_id == absence.employee_id).first()
        if emp and emp.manager_id == current_user.id:
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès refusé. Cette absence ne fait pas partie de votre périmètre."
    )


def _build_response(absence: Absence, target_user: User) -> AbsenceResponse:
    resp = AbsenceResponse.model_validate(absence)
    resp.nom = target_user.nom
    resp.prenom = target_user.prenom
    return resp


# ─────────────────────────────────────────────
# POST /api/absences/   — Déclarer une absence
# ─────────────────────────────────────────────

@router.post("/", response_model=AbsenceResponse, status_code=status.HTTP_201_CREATED)
def create_absence(
    absence_data: AbsenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Déclarer une absence.
    - Collaborateur : uniquement pour soi-même.
    - Manager : pour soi-même ou les membres de son équipe.
    - RH / Admin : pour n'importe quel employé.
    """
    _check_dates(absence_data.start_date, absence_data.end_date)
    target_user = _get_employee_or_404(db, absence_data.employee_id)
    _check_write_access(db, current_user, absence_data.employee_id)

    new_absence = Absence(
        employee_id=absence_data.employee_id,
        absence_type=absence_data.absence_type,
        start_date=absence_data.start_date,
        end_date=absence_data.end_date,
        reason=absence_data.reason
    )
    db.add(new_absence)
    from sqlalchemy.exc import IntegrityError
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une absence existe déjà pour cet employé sur cette même période."
        )

    from utils.workflow_service import init_workflow
    is_auto = init_workflow(db, 'absence', new_absence, target_user)

    if not is_auto:
        log_action(
            db=db,
            record_type="absence",
            record_id=new_absence.id,
            action="created",
            performed_by=current_user.id,
            details=(
                f"Absence déclarée ({new_absence.absence_type.value}) "
                f"pour l'employé id={new_absence.employee_id} "
                f"du {new_absence.start_date} au {new_absence.end_date} (en attente de validation)."
            )
        )

    return _build_response(new_absence, target_user)


# ─────────────────────────────────────────────
# GET /api/absences/   — Lister avec filtres
# ─────────────────────────────────────────────

@router.get("/", response_model=AbsencesListResponse)
def list_absences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    absence_type: Optional[AbsenceTypeEnum] = Query(None, description="Filtrer par type d'absence"),
    employee_id: Optional[int] = Query(None, description="Filtrer par employé (Admin/RH/Manager)"),
    start_from: Optional[datetime] = Query(None, description="Absences commençant après cette date"),
    start_to: Optional[datetime] = Query(None, description="Absences commençant avant cette date"),
    is_archived: bool = Query(False, description="Afficher les archives ou les actives")
):
    """
    Lister les absences avec filtres optionnels.
    - RH / Admin / Direction / Médecine du travail : toutes les absences.
    - Manager : ses propres absences + celles de son équipe.
    - Collaborateur : uniquement ses propres absences.
    """
    query = db.query(Absence).join(User, Absence.employee_id == User.id)

    # Auto-archivage des absences dès que leur date de fin est dépassée
    from datetime import datetime
    cutoff = datetime.utcnow()
    db.query(Absence).filter(
        Absence.is_archived == False,
        Absence.end_date < cutoff
    ).update({"is_archived": True})
    db.commit()

    # Filtre de périmètre par rôle
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL]:
        if current_user.role == RoleEnum.MANAGER:
            team_ids = [e.user_id for e in db.query(Employee).filter(Employee.manager_id == current_user.id).all()]
            allowed_ids = team_ids + [current_user.id]
            query = query.filter(Absence.employee_id.in_(allowed_ids))
        else:
            query = query.filter(Absence.employee_id == current_user.id)

    # Filtres optionnels
    if absence_type:
        query = query.filter(Absence.absence_type == absence_type)
    if employee_id:
        # Vérifier que l'utilisateur a le droit de voir cet employé
        if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL]:
            if employee_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")
        query = query.filter(Absence.employee_id == employee_id)
    if start_from:
        query = query.filter(Absence.start_date >= start_from)
    if start_to:
        query = query.filter(Absence.start_date <= start_to)

    query = query.filter(Absence.is_archived == is_archived)

    query = query.order_by(Absence.start_date.desc())
    absences_list = query.all()

    responses = []
    total_hours = 0.0
    for abs_obj in absences_list:
        resp = AbsenceResponse.model_validate(abs_obj)
        resp.nom    = abs_obj.user.nom
        resp.prenom = abs_obj.user.prenom
        responses.append(resp)
        total_hours += resp.duration_hours

    return AbsencesListResponse(
        absences=responses,
        total_hours=total_hours
    )


# ─────────────────────────────────────────────
# GET /api/absences/stats   — Statistiques
# ─────────────────────────────────────────────

@router.get("/stats", response_model=AbsenceStats)
def get_absence_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_from: Optional[datetime] = Query(None),
    start_to: Optional[datetime] = Query(None),
):
    """
    Statistiques sur les absences (RH, Admin, Direction, Médecine du travail).
    Retourne : total, heures, répartition par type, employés les plus absents.
    """
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès réservé aux RH, Admin, Direction et Médecine du travail.")

    query = db.query(Absence)
    if start_from:
        query = query.filter(Absence.start_date >= start_from)
    if start_to:
        query = query.filter(Absence.start_date <= start_to)

    all_absences = query.all()

    # Répartition par type
    by_type_map: dict[str, dict] = {}
    total_hours = 0.0
    for a in all_absences:
        t = a.absence_type.value
        hours = max(0.0, (a.end_date - a.start_date).total_seconds() / 3600.0)
        total_hours += hours
        if t not in by_type_map:
            by_type_map[t] = {"count": 0, "total_hours": 0.0}
        by_type_map[t]["count"] += 1
        by_type_map[t]["total_hours"] = by_type_map[t]["total_hours"] + hours

    by_type = [
        AbsenceStatsByType(absence_type=t, count=v["count"], total_hours=v["total_hours"])
        for t, v in sorted(by_type_map.items(), key=lambda x: -x[1]["count"])
    ]

    # Employés les plus absents (top 5)
    emp_map: dict[int, dict] = {}
    for a in all_absences:
        eid = a.employee_id
        hours = max(0.0, (a.end_date - a.start_date).total_seconds() / 3600.0)
        if eid not in emp_map:
            u = db.query(User).filter(User.id == eid).first()
            emp_map[eid] = {
                "employee_id": eid,
                "nom": u.nom if u else "?",
                "prenom": u.prenom if u else "?",
                "absence_count": 0,
                "total_hours": 0.0,
            }
        emp_map[eid]["absence_count"] += 1
        emp_map[eid]["total_hours"] = emp_map[eid]["total_hours"] + hours

    most_affected = sorted(emp_map.values(), key=lambda x: -x["total_hours"])[:5]
    
    total_employees = db.query(User).count()
    rate = (total_hours / (total_employees * 1607)) * 100 if total_employees > 0 else 0

    return AbsenceStats(
        total_absences=len(all_absences),
        total_hours=total_hours,
        by_type=by_type,
        most_affected_employees=most_affected,
        rate=rate
    )


# ─────────────────────────────────────────────
# GET /api/absences/{id}   — Détail
# ─────────────────────────────────────────────

@router.get("/{absence_id}", response_model=AbsenceResponse)
def get_absence(
    absence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir le détail d'une absence par son ID."""
    absence = db.query(Absence).filter(Absence.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Absence introuvable.")

    _check_read_access(db, current_user, absence)
    target_user = _get_employee_or_404(db, absence.employee_id)
    return _build_response(absence, target_user)


# ─────────────────────────────────────────────
# PUT /api/absences/{id}   — Modifier
# ─────────────────────────────────────────────

@router.put("/{absence_id}", response_model=AbsenceResponse)
def update_absence(
    absence_id: int,
    update_data: AbsenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Modifier une absence existante.
    - Admin / RH : toutes les absences.
    - Manager / Collaborateur : uniquement les leurs (ou leur équipe pour le manager).
    """
    absence = db.query(Absence).filter(Absence.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Absence introuvable.")

    _check_write_access(db, current_user, absence.employee_id)

    # Intercept workflow rules
    from models.features import ApprovalWorkflow, ApprovalWorkflowStatusEnum
    active_step = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.entity_type == 'absence',
        ApprovalWorkflow.entity_id == absence_id,
        ApprovalWorkflow.status == ApprovalWorkflowStatusEnum.PENDING
    ).first()

    if active_step and update_data.status is not None:
        if current_user.role != RoleEnum.ADMIN and active_step.approver_id != current_user.id:
            assigned_user = db.query(User).filter(User.id == active_step.approver_id).first()
            is_assigned_rh = assigned_user and assigned_user.role == RoleEnum.RH
            if not (current_user.role == RoleEnum.RH and is_assigned_rh):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accès refusé. Vous n'êtes pas le validateur désigné pour cette étape."
                )
        from utils.workflow_service import process_workflow_step
        action = 'approve' if update_data.status in [AbsenceStatusEnum.APPROVED, AbsenceStatusEnum.RECEIVED] else 'reject'
        final_status = update_data.status if update_data.status == AbsenceStatusEnum.RECEIVED else None
        res = process_workflow_step(db, active_step.id, action, current_user.id, final_status=final_status)
        if res.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res.get("message")
            )
        db.refresh(absence)
        target_user = _get_employee_or_404(db, absence.employee_id)
        return _build_response(absence, target_user)

    # Appliquer les modifications
    update_dict = update_data.model_dump(exclude_unset=True)
    
    status_changed = False
    old_status = absence.status
    if "status" in update_dict:
        if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à modifier le statut de cette absence."
            )
        if current_user.role == RoleEnum.MANAGER and absence.employee_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Un manager ne peut pas valider ses propres absences."
            )
        if update_dict["status"] != old_status:
            status_changed = True

    if "is_archived" in update_dict and update_dict["is_archived"] is True:
        if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER]:
            if not (current_user.id == absence.employee_id and absence.status == AbsenceStatusEnum.PENDING):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Seuls les Managers et RH peuvent archiver des absences, sauf si votre absence est encore en attente."
                )

    for field, value in update_dict.items():
        setattr(absence, field, value)

    # Re-valider les dates après modification
    _check_dates(absence.start_date, absence.end_date)

    db.commit()
    db.refresh(absence)

    log_action(
        db=db,
        record_type="absence",
        record_id=absence.id,
        action="updated",
        performed_by=current_user.id,
        details=f"Absence id={absence.id} modifiée. Champs: {list(update_dict.keys())}"
    )

    # Notifier l'employé si modification par quelqu'un d'autre
    if absence.employee_id != current_user.id:
        if status_changed:
            status_labels = {
                "approved": "validée",
                "rejected": "refusée",
                "pending": "mise en attente"
            }
            status_str = status_labels.get(absence.status, absence.status)
            msg = f"Votre absence du {absence.start_date.strftime('%d/%m/%Y')} au {absence.end_date.strftime('%d/%m/%Y')} a été {status_str} par {current_user.prenom} {current_user.nom}."
        else:
            msg = f"Votre absence du {absence.start_date.strftime('%d/%m/%Y')} au {absence.end_date.strftime('%d/%m/%Y')} a été modifiée par {current_user.prenom} {current_user.nom}."
        
        create_notification(db, absence.employee_id, msg)

    target_user = _get_employee_or_404(db, absence.employee_id)
    return _build_response(absence, target_user)


# ─────────────────────────────────────────────
# DELETE /api/absences/{id}   — Supprimer
# ─────────────────────────────────────────────

@router.delete("/{absence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_absence(
    absence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprimer une absence. (DÉSACTIVÉ)
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="La suppression des déclarations d'absence est interdite. Veuillez archiver l'absence à la place."
    )
