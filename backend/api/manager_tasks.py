from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date

from database.db import get_db
from models.user import User, RoleEnum
from models.features import ManagerTask, TaskStatusEnum, TaskPriorityEnum
from models.employees import Employee, Department
from schemas.task import ManagerTaskCreate, ManagerTaskUpdate, ManagerTaskResponse
from core.security import require_role

router = APIRouter(prefix="/api/manager/tasks", tags=["Manager Tasks"], redirect_slashes=False)


def _build_task_response(task: ManagerTask, db: Session = None) -> ManagerTaskResponse:
    resp = ManagerTaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        assigned_to=task.assigned_to,
        created_by=task.created_by,
        due_date=task.due_date,
        priority=task.priority.value if hasattr(task.priority, "value") else task.priority,
        status=task.status.value if hasattr(task.status, "value") else task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
    if task.assignee:
        resp.assignee_nom = task.assignee.nom
        resp.assignee_prenom = task.assignee.prenom
        
        # Récupérer le département si db est fourni
        if db:
            employee = db.query(Employee).filter(Employee.user_id == task.assignee.id).first()
            if employee and employee.department:
                resp.assignee_department = employee.department.name

    if task.creator:
        resp.creator_nom = task.creator.nom
        resp.creator_prenom = task.creator.prenom
    return resp


def _get_team_user_ids(db: Session, manager_id: int) -> List[int]:
    """Retourne les user_ids des membres directs de l'équipe du manager."""
    subordinates = db.query(Employee).filter(Employee.manager_id == manager_id).all()
    return [emp.user_id for emp in subordinates]


@router.get("/", response_model=List[ManagerTaskResponse])
def list_team_tasks(
    status: Optional[str] = Query(None, description="Filtrer par statut (todo, in_progress, done, cancelled)"),
    assigned_to: Optional[int] = Query(None, description="Filtrer par membre de l'équipe"),
    overdue: Optional[bool] = Query(None, description="Uniquement les tâches dont la deadline est dépassée"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Lister toutes les tâches de l'équipe du manager connecté."""
    if current_user.role == RoleEnum.MANAGER:
        team_user_ids = _get_team_user_ids(db, current_user.id)
        if not team_user_ids:
            return []
        query = db.query(ManagerTask).filter(
            ManagerTask.assigned_to.in_(team_user_ids)
        )
    else:
        query = db.query(ManagerTask)

    if status:
        try:
            status_enum = TaskStatusEnum(status)
            query = query.filter(ManagerTask.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Statut invalide: {status}")

    if assigned_to is not None:
        # Vérifier que cet employé appartient bien à l'équipe du manager
        if current_user.role == RoleEnum.MANAGER:
            team_user_ids = _get_team_user_ids(db, current_user.id)
            if assigned_to not in team_user_ids:
                raise HTTPException(status_code=403, detail="Cet employé n'est pas dans votre équipe.")
        query = query.filter(ManagerTask.assigned_to == assigned_to)

    if overdue is True:
        today = date.today()
        query = query.filter(
            and_(
                ManagerTask.due_date < today,
                ManagerTask.status.not_in([TaskStatusEnum.DONE, TaskStatusEnum.CANCELLED])
            )
        )

    tasks = query.order_by(ManagerTask.created_at.desc()).all()
    return [_build_task_response(t, db) for t in tasks]


@router.post("/", response_model=ManagerTaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: ManagerTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Créer une tâche et l'assigner à un membre de l'équipe."""
    # Vérifier que l'assigné existe
    assignee = db.query(User).filter(User.id == task_data.assigned_to).first()
    if not assignee:
        raise HTTPException(status_code=404, detail=f"Utilisateur id={task_data.assigned_to} introuvable.")

    # Vérifier que l'assigné appartient bien à l'équipe du manager
    if current_user.role == RoleEnum.MANAGER:
        team_user_ids = _get_team_user_ids(db, current_user.id)
        if task_data.assigned_to not in team_user_ids:
            raise HTTPException(status_code=403, detail="Cet employé n'est pas dans votre équipe.")

    # Valider priority et status
    try:
        priority_enum = TaskPriorityEnum(task_data.priority)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Priorité invalide: {task_data.priority}")

    try:
        status_enum = TaskStatusEnum(task_data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Statut invalide: {task_data.status}")

    task = ManagerTask(
        title=task_data.title,
        description=task_data.description,
        assigned_to=task_data.assigned_to,
        created_by=current_user.id,
        due_date=task_data.due_date,
        priority=priority_enum,
        status=status_enum,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Reload relations
    db.refresh(task)
    task = db.query(ManagerTask).filter(ManagerTask.id == task.id).first()
    return _build_task_response(task, db)


@router.put("/{task_id}", response_model=ManagerTaskResponse)
def update_task(
    task_id: int,
    update_data: ManagerTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Modifier une tâche (statut, deadline, priorité, description...)."""
    task = db.query(ManagerTask).filter(ManagerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable.")

    # Vérifier les droits
    if current_user.role == RoleEnum.MANAGER:
        team_user_ids = _get_team_user_ids(db, current_user.id)
        if task.assigned_to not in team_user_ids and task.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Non autorisé à modifier cette tâche.")

    u_dict = update_data.model_dump(exclude_unset=True)

    if "priority" in u_dict and u_dict["priority"] is not None:
        try:
            u_dict["priority"] = TaskPriorityEnum(u_dict["priority"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Priorité invalide: {u_dict['priority']}")

    if "status" in u_dict and u_dict["status"] is not None:
        try:
            u_dict["status"] = TaskStatusEnum(u_dict["status"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Statut invalide: {u_dict['status']}")

    if "assigned_to" in u_dict and u_dict["assigned_to"] is not None:
        if current_user.role == RoleEnum.MANAGER:
            team_user_ids = _get_team_user_ids(db, current_user.id)
            if u_dict["assigned_to"] not in team_user_ids:
                raise HTTPException(status_code=403, detail="Cet employé n'est pas dans votre équipe.")
        assignee = db.query(User).filter(User.id == u_dict["assigned_to"]).first()
        if not assignee:
            raise HTTPException(status_code=404, detail=f"Utilisateur id={u_dict['assigned_to']} introuvable.")

    for k, v in u_dict.items():
        setattr(task, k, v)

    db.commit()
    db.refresh(task)
    task = db.query(ManagerTask).filter(ManagerTask.id == task_id).first()
    return _build_task_response(task, db)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Supprimer une tâche."""
    task = db.query(ManagerTask).filter(ManagerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable.")

    if current_user.role == RoleEnum.MANAGER:
        team_user_ids = _get_team_user_ids(db, current_user.id)
        if task.assigned_to not in team_user_ids and task.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Non autorisé à supprimer cette tâche.")

    db.delete(task)
    db.commit()
    return None


@router.get("/stats/summary")
def get_tasks_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MEDECINE_TRAVAIL]))
):
    """Statistiques des tâches de l'équipe du manager."""
    today = date.today()

    if current_user.role == RoleEnum.MANAGER:
        team_user_ids = _get_team_user_ids(db, current_user.id)
        base_query = db.query(ManagerTask).filter(ManagerTask.assigned_to.in_(team_user_ids))
    else:
        base_query = db.query(ManagerTask)

    total = base_query.count()
    todo = base_query.filter(ManagerTask.status == TaskStatusEnum.TODO).count()
    in_progress = base_query.filter(ManagerTask.status == TaskStatusEnum.IN_PROGRESS).count()
    done = base_query.filter(ManagerTask.status == TaskStatusEnum.DONE).count()
    overdue = base_query.filter(
        and_(
            ManagerTask.due_date < today,
            ManagerTask.status.not_in([TaskStatusEnum.DONE, TaskStatusEnum.CANCELLED])
        )
    ).count()

    return {
        "total": total,
        "todo": todo,
        "in_progress": in_progress,
        "done": done,
        "overdue": overdue,
        "not_done": todo + in_progress,
    }
