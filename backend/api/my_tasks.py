from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date

from database.db import get_db
from models.user import User
from models.features import ManagerTask, TaskStatusEnum
from schemas.task import ManagerTaskResponse, ManagerTaskUpdate
from core.security import get_current_user

router = APIRouter(prefix="/api/my/tasks", tags=["My Tasks"], redirect_slashes=False)


def _build_task_response(task: ManagerTask) -> ManagerTaskResponse:
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
    if task.creator:
        resp.creator_nom = task.creator.nom
        resp.creator_prenom = task.creator.prenom
    return resp


@router.get("/", response_model=List[ManagerTaskResponse])
def get_my_tasks(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    overdue: Optional[bool] = Query(None, description="Seulement les tâches en retard"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lister les tâches assignées à l'utilisateur connecté."""
    query = db.query(ManagerTask).filter(ManagerTask.assigned_to == current_user.id)

    if status:
        try:
            status_enum = TaskStatusEnum(status)
            query = query.filter(ManagerTask.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Statut invalide: {status}")

    if overdue is True:
        today = date.today()
        query = query.filter(
            and_(
                ManagerTask.due_date < today,
                ManagerTask.status.not_in([TaskStatusEnum.DONE, TaskStatusEnum.CANCELLED])
            )
        )

    tasks = query.order_by(ManagerTask.created_at.desc()).all()
    return [_build_task_response(t) for t in tasks]


@router.get("/stats", )
def get_my_tasks_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Statistiques des tâches de l'utilisateur connecté."""
    today = date.today()
    base = db.query(ManagerTask).filter(ManagerTask.assigned_to == current_user.id)

    total = base.count()
    todo = base.filter(ManagerTask.status == TaskStatusEnum.TODO).count()
    in_progress = base.filter(ManagerTask.status == TaskStatusEnum.IN_PROGRESS).count()
    done = base.filter(ManagerTask.status == TaskStatusEnum.DONE).count()
    overdue = base.filter(
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


@router.patch("/{task_id}/status", response_model=ManagerTaskResponse)
def update_my_task_status(
    task_id: int,
    update_data: ManagerTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mettre à jour le statut d'une tâche assignée à l'utilisateur connecté (seulement le statut)."""
    task = db.query(ManagerTask).filter(
        ManagerTask.id == task_id,
        ManagerTask.assigned_to == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable ou non autorisée.")

    # Le collaborateur ne peut modifier que le statut
    if update_data.status:
        try:
            task.status = TaskStatusEnum(update_data.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Statut invalide: {update_data.status}")

    db.commit()
    db.refresh(task)
    task = db.query(ManagerTask).filter(ManagerTask.id == task_id).first()
    return _build_task_response(task)
