from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

from database.db import get_db
from models.user import User, RoleEnum
from models.features import OffboardingPlan, OffboardingTask, OffboardingFeedback
from schemas.offboarding import (
    OffboardingPlanCreate, OffboardingPlanUpdate, OffboardingPlanResponse,
    OffboardingTaskCreate, OffboardingTaskUpdate, OffboardingTaskResponse,
    OffboardingFeedbackCreate, OffboardingFeedbackResponse
)
from core.security import require_role
from utils.history import log_action

router = APIRouter(prefix="/api/offboarding", tags=["Offboarding"])

def _build_plan_response(plan: OffboardingPlan, db: Session, current_user: User = None) -> OffboardingPlanResponse:
    tasks = db.query(OffboardingTask).filter(OffboardingTask.plan_id == plan.id).all()
    task_resps = []
    for t in tasks:
        tr = OffboardingTaskResponse.model_validate(t)
        if t.assigned_to:
            assignee = db.query(User).filter(User.id == t.assigned_to).first()
            if assignee:
                tr.assigned_nom = assignee.nom
                tr.assigned_prenom = assignee.prenom
        task_resps.append(tr)
    
    feedbacks = db.query(OffboardingFeedback).filter(OffboardingFeedback.plan_id == plan.id).order_by(OffboardingFeedback.created_at.asc()).all()
    feedback_resps = []
    
    hide_feedbacks = current_user and current_user.id == plan.employee_id
    
    if not hide_feedbacks:
        for f in feedbacks:
            fr = OffboardingFeedbackResponse.model_validate(f)
            if f.author:
                fr.author_nom = f.author.nom
                fr.author_prenom = f.author.prenom
            feedback_resps.append(fr)
    
    resp = OffboardingPlanResponse.model_validate(plan)
    if plan.employee:
        resp.employee_nom = plan.employee.nom
        resp.employee_prenom = plan.employee.prenom
        resp.employee_email = plan.employee.email
        resp.employee_role = plan.employee.role.value if hasattr(plan.employee.role, 'value') else plan.employee.role
    resp.tasks = task_resps
    resp.feedbacks = feedback_resps
    return resp

# ── PLANS ───────────────────────────────────────────────────────────

@router.get("/me", response_model=List[OffboardingPlanResponse])
def get_my_offboarding_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(None))
):
    """Récupérer les plans de sortie de l'utilisateur connecté"""
    plans = db.query(OffboardingPlan).filter(OffboardingPlan.employee_id == current_user.id).all()
    return [_build_plan_response(p, db, current_user) for p in plans]


@router.get("/", response_model=List[OffboardingPlanResponse])
def list_offboarding_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER, RoleEnum.DIRECTION]))
):
    """Lister les plans de sortie"""
    if current_user.role in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION]:
        plans = db.query(OffboardingPlan).all()
    else:
        from models.employees import Employee
        subordinates = db.query(Employee).filter(Employee.manager_id == current_user.id).all()
        sub_user_ids = [sub.user_id for sub in subordinates]
        task_plans_ids = [t.plan_id for t in db.query(OffboardingTask).filter(OffboardingTask.assigned_to == current_user.id).all()]
        plans = db.query(OffboardingPlan).filter(
            or_(
                OffboardingPlan.employee_id.in_(sub_user_ids),
                OffboardingPlan.id.in_(task_plans_ids)
            )
        ).all()
    return [_build_plan_response(p, db, current_user) for p in plans]

@router.post("/", response_model=OffboardingPlanResponse, status_code=status.HTTP_201_CREATED)
def create_offboarding_plan(
    plan_data: OffboardingPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Créer un nouveau plan de sortie (RH et Admin uniquement)"""
    # Vérifier que l'employé existe
    employee = db.query(User).filter(User.id == plan_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employé id={plan_data.employee_id} introuvable."
        )

    # Vérifier s'il a déjà un plan de sortie
    existing = db.query(OffboardingPlan).filter(OffboardingPlan.employee_id == plan_data.employee_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet employé a déjà un plan de sortie enregistré."
        )

    plan = OffboardingPlan(
        employee_id=plan_data.employee_id,
        departure_date=plan_data.departure_date,
        departure_reason=plan_data.departure_reason,
        status=plan_data.status,
        equipment_returned=plan_data.equipment_returned,
        administrative_closed=plan_data.administrative_closed
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    log_action(
        db=db,
        record_type="offboarding_plan",
        record_id=plan.id,
        action="created",
        performed_by=current_user.id,
        details=f"Plan de sortie créé pour l'employé id={plan.employee_id}"
    )

    return _build_plan_response(plan, db, current_user)

@router.get("/{plan_id}", response_model=OffboardingPlanResponse)
def get_offboarding_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER]))
):
    """Obtenir le détail d'un plan de sortie"""
    plan = db.query(OffboardingPlan).filter(OffboardingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de sortie introuvable.")

    if current_user.role == RoleEnum.MANAGER:
        from models.employees import Employee
        is_subordinate = db.query(Employee).filter(Employee.manager_id == current_user.id, Employee.user_id == plan.employee_id).first() is not None
        has_task = db.query(OffboardingTask).filter(OffboardingTask.plan_id == plan.id, OffboardingTask.assigned_to == current_user.id).first() is not None
        if not is_subordinate and not has_task:
            raise HTTPException(status_code=403, detail="Non autorisé à consulter ce plan.")

    return _build_plan_response(plan, db, current_user)

@router.put("/{plan_id}", response_model=OffboardingPlanResponse)
def update_offboarding_plan(
    plan_id: int,
    update_data: OffboardingPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER, RoleEnum.DIRECTION]))
):
    """Modifier un plan de sortie (avec règles de validation de statut)"""
    plan = db.query(OffboardingPlan).filter(OffboardingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de sortie introuvable.")

    target_employee = db.query(User).filter(User.id == plan.employee_id).first()

    # Vérification des droits d'accès basique
    if current_user.role == RoleEnum.MANAGER:
        from models.employees import Employee
        is_subordinate = db.query(Employee).filter(Employee.manager_id == current_user.id, Employee.user_id == plan.employee_id).first() is not None
        if not is_subordinate:
            raise HTTPException(status_code=403, detail="Non autorisé à modifier ce plan.")
    elif current_user.role == RoleEnum.DIRECTION:
        if target_employee.role != RoleEnum.RH:
            raise HTTPException(status_code=403, detail="La direction ne peut valider que les plans des RH.")

    u_dict = update_data.model_dump(exclude_unset=True)

    # Logique de validation du statut
    if "status" in u_dict and (u_dict["status"] == "completed" or getattr(u_dict["status"], "value", u_dict["status"]) == "completed"):
        if target_employee.role == RoleEnum.RH and current_user.role not in [RoleEnum.ADMIN, RoleEnum.DIRECTION]:
            raise HTTPException(status_code=403, detail="Seule la Direction peut valider le plan d'un RH.")
        elif target_employee.role == RoleEnum.MANAGER and current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH]:
            raise HTTPException(status_code=403, detail="Seul un RH peut valider le plan d'un Manager.")
        elif target_employee.role == RoleEnum.COLLABORATEUR and current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER]:
            raise HTTPException(status_code=403, detail="Non autorisé à valider ce plan.")

    for k, v in u_dict.items():
        setattr(plan, k, v)

    db.commit()
    db.refresh(plan)

    log_action(
        db=db,
        record_type="offboarding_plan",
        record_id=plan.id,
        action="updated",
        performed_by=current_user.id,
        details=f"Plan de sortie id={plan.id} mis à jour."
    )

    return _build_plan_response(plan, db, current_user)

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offboarding_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Supprimer un plan de sortie (RH et Admin uniquement)"""
    plan = db.query(OffboardingPlan).filter(OffboardingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de sortie introuvable.")

    # Supprimer tâches et feedbacks associés en cascade
    db.query(OffboardingTask).filter(OffboardingTask.plan_id == plan_id).delete()
    db.query(OffboardingFeedback).filter(OffboardingFeedback.plan_id == plan_id).delete()
    db.delete(plan)
    db.commit()

    log_action(
        db=db,
        record_type="offboarding_plan",
        record_id=plan_id,
        action="deleted",
        performed_by=current_user.id,
        details=f"Plan de sortie id={plan_id} supprimé."
    )
    return None

# ── TASKS ───────────────────────────────────────────────────────────

@router.post("/{plan_id}/tasks", response_model=OffboardingTaskResponse, status_code=status.HTTP_201_CREATED)
def create_offboarding_task(
    plan_id: int,
    task_data: OffboardingTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Ajouter une tâche à un plan de sortie (RH et Admin uniquement)"""
    plan = db.query(OffboardingPlan).filter(OffboardingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de sortie introuvable.")

    if task_data.assigned_to:
        assignee = db.query(User).filter(User.id == task_data.assigned_to).first()
        if not assignee:
            raise HTTPException(status_code=404, detail=f"Responsable id={task_data.assigned_to} introuvable.")

    task = OffboardingTask(
        plan_id=plan_id,
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        status=task_data.status,
        assigned_to=task_data.assigned_to
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    log_action(
        db=db,
        record_type="offboarding_task",
        record_id=task.id,
        action="created",
        performed_by=current_user.id,
        details=f"Tâche de sortie '{task.title}' ajoutée au plan id={plan_id}."
    )

    tr = OffboardingTaskResponse.model_validate(task)
    if task.assigned_to:
        assignee = db.query(User).filter(User.id == task.assigned_to).first()
        if assignee:
            tr.assigned_nom = assignee.nom
            tr.assigned_prenom = assignee.prenom
    return tr

@router.put("/tasks/{task_id}", response_model=OffboardingTaskResponse)
def update_offboarding_task(
    task_id: int,
    update_data: OffboardingTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER]))
):
    """Modifier une tâche de sortie"""
    task = db.query(OffboardingTask).filter(OffboardingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche de sortie introuvable.")

    u_dict = update_data.model_dump(exclude_unset=True)

    is_assigned = task.assigned_to == current_user.id
    is_status_update = "status" in u_dict
    
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH]:
        if is_status_update and not is_assigned:
            raise HTTPException(status_code=403, detail="Vous ne pouvez valider uniquement les tâches qui vous sont assignées.")
        
        if current_user.role == RoleEnum.MANAGER:
            from models.employees import Employee
            plan = db.query(OffboardingPlan).filter(OffboardingPlan.id == task.plan_id).first()
            is_subordinate = db.query(Employee).filter(Employee.manager_id == current_user.id, Employee.user_id == plan.employee_id).first() is not None
            if not is_subordinate and not is_assigned:
                raise HTTPException(status_code=403, detail="Non autorisé à modifier cette tâche.")
    if "assigned_to" in u_dict and u_dict["assigned_to"] is not None:
        assignee = db.query(User).filter(User.id == u_dict["assigned_to"]).first()
        if not assignee:
            raise HTTPException(status_code=404, detail=f"Responsable id={u_dict['assigned_to']} introuvable.")

    for k, v in u_dict.items():
        setattr(task, k, v)

    db.commit()
    db.refresh(task)

    log_action(
        db=db,
        record_type="offboarding_task",
        record_id=task.id,
        action="updated",
        performed_by=current_user.id,
        details=f"Tâche de sortie id={task.id} mise à jour."
    )

    tr = OffboardingTaskResponse.model_validate(task)
    if task.assigned_to:
        assignee = db.query(User).filter(User.id == task.assigned_to).first()
        if assignee:
            tr.assigned_nom = assignee.nom
            tr.assigned_prenom = assignee.prenom
    return tr

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offboarding_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Supprimer une tâche de sortie (RH et Admin uniquement)"""
    task = db.query(OffboardingTask).filter(OffboardingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche de sortie introuvable.")

    db.delete(task)
    db.commit()

    log_action(
        db=db,
        record_type="offboarding_task",
        record_id=task_id,
        action="deleted",
        performed_by=current_user.id,
        details=f"Tâche de sortie id={task_id} supprimée."
    )
    return None

# ── FEEDBACKS ───────────────────────────────────────────────────────

@router.post("/{plan_id}/feedback", response_model=OffboardingFeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_offboarding_feedback(
    plan_id: int,
    feedback_data: OffboardingFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.COLLABORATEUR, RoleEnum.MANAGER]))
):
    """Laisser un commentaire/feedback sur un plan de sortie (RH, Admin, Employé concerné, Manager)"""
    plan = db.query(OffboardingPlan).filter(OffboardingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de sortie introuvable.")

    is_authorized = False
    if current_user.role in [RoleEnum.ADMIN, RoleEnum.RH]:
        is_authorized = True
    else:
        # Vérifier si le user courant est le manager de l'employé
        from models.employees import Employee
        emp_profile = db.query(Employee).filter(Employee.user_id == plan.employee_id).first()
        if emp_profile and emp_profile.manager_id == current_user.id:
            is_authorized = True

    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à laisser un feedback sur ce plan de sortie."
        )

    feedback = OffboardingFeedback(
        plan_id=plan_id,
        author_id=current_user.id,
        comment=feedback_data.comment
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    log_action(
        db=db,
        record_type="offboarding_feedback",
        record_id=feedback.id,
        action="created",
        performed_by=current_user.id,
        details=f"Feedback ajouté par user_id={current_user.id} sur le plan de sortie id={plan_id}."
    )

    fr = OffboardingFeedbackResponse.model_validate(feedback)
    fr.author_nom = current_user.nom
    fr.author_prenom = current_user.prenom
    return fr
