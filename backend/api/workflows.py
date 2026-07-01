from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User, RoleEnum
from models.features import WorkflowConfig, ApprovalWorkflow, ApprovalWorkflowStatusEnum, Leave
from models.absences import Absence
from core.security import require_role
from pydantic import BaseModel
from typing import Optional, List
from utils.workflow_service import process_workflow_step
from utils.history import log_action
from utils.notifications import create_notification
from datetime import datetime

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

# ── Schemas ──
class WorkflowConfigUpdate(BaseModel):
    logic_type: str
    validator_user_id: Optional[int] = None
    validator_role: Optional[str] = None

class WorkflowOverride(BaseModel):
    workflow_step_id: int
    action: str  # 'approve', 'reject', 'reassign'
    new_approver_id: Optional[int] = None

class UserInfoResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    role: str

class WorkflowConfigResponse(BaseModel):
    id: int
    entity_type: str
    logic_type: str
    validator_role: Optional[str] = None
    validator_user_id: Optional[int] = None
    validator_user: Optional[UserInfoResponse] = None

    class Config:
        from_attributes = True

# ── Routes ──

@router.get("/configs", response_model=List[WorkflowConfigResponse])
def get_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION]))
):
    """
    Récupérer toutes les configurations de workflow. S'assurer que celles par défaut existent.
    """
    configs = db.query(WorkflowConfig).all()
    expected_entities = ["leave", "absence"]
    existing_entities = [c.entity_type for c in configs]
    
    added_new = False
    for entity in expected_entities:
        if entity not in existing_entities:
            new_config = WorkflowConfig(entity_type=entity, logic_type="single_manager")
            db.add(new_config)
            configs.append(new_config)
            added_new = True
            
    if added_new:
        db.commit()
        for c in configs:
            if not c.id: # Refresh only newly added configs to get their IDs
                db.refresh(c)
                
    return configs

@router.put("/configs/{entity_type}", response_model=WorkflowConfigResponse)
def update_config(
    entity_type: str,
    payload: WorkflowConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.DIRECTION]))
):
    """
    Modifier la configuration d'un workflow (Admin uniquement).
    """
    if entity_type not in ('leave', 'absence'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type d'entité invalide. Doit être 'leave' ou 'absence'."
        )

    config = db.query(WorkflowConfig).filter(WorkflowConfig.entity_type == entity_type).first()
    if not config:
        config = WorkflowConfig(entity_type=entity_type)
        db.add(config)

    config.logic_type = payload.logic_type
    config.validator_user_id = payload.validator_user_id
    config.validator_role = payload.validator_role

    db.commit()
    db.refresh(config)

    log_action(
        db=db,
        record_type="workflow_config",
        record_id=config.id,
        action="updated",
        performed_by=current_user.id,
        details=f"Workflow pour '{entity_type}' mis à jour : {payload.logic_type}."
    )

    return config

@router.get("/validators", response_model=List[UserInfoResponse])
def get_validators(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION]))
):
    """
    Lister tous les utilisateurs pouvant être désignés comme validateurs.
    (Managers, RH, Direction, Admins actifs).
    """
    roles_allowed = [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER, RoleEnum.DIRECTION]
    validators = db.query(User).filter(
        User.role.in_(roles_allowed),
        User.is_active == True
    ).order_by(User.prenom, User.nom).all()
    return validators

@router.get("/blocked")
def get_blocked_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION]))
):
    """
    Lister toutes les étapes de validation bloquées (pending) dans le système.
    """
    pending_steps = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.status == ApprovalWorkflowStatusEnum.PENDING
    ).order_by(ApprovalWorkflow.created_at.desc()).all()

    results = []
    for step in pending_steps:
        # Détails de la demande
        requester_name = "Inconnu"
        details_str = ""
        created_at_request = None

        if step.entity_type == 'leave':
            leave = db.query(Leave).filter(Leave.id == step.entity_id).first()
            if leave:
                req_user = db.query(User).filter(User.id == leave.employee_id).first()
                if req_user:
                    requester_name = f"{req_user.prenom} {req_user.nom}"
                start_str = leave.start_date.strftime("%d/%m/%Y")
                end_str = leave.end_date.strftime("%d/%m/%Y")
                type_name = leave.leave_type_relation.name if leave.leave_type_relation else "Congé"
                details_str = f"{type_name} du {start_str} au {end_str}"
                created_at_request = leave.created_at

        elif step.entity_type == 'absence':
            abs_obj = db.query(Absence).filter(Absence.id == step.entity_id).first()
            if abs_obj:
                req_user = db.query(User).filter(User.id == abs_obj.employee_id).first()
                if req_user:
                    requester_name = f"{req_user.prenom} {req_user.nom}"
                start_str = abs_obj.start_date.strftime("%d/%m/%Y %H:%M")
                end_str = abs_obj.end_date.strftime("%d/%m/%Y %H:%M")
                details_str = f"Absence ({abs_obj.absence_type.value}) du {start_str} au {end_str}"
                created_at_request = abs_obj.created_at

        approver = db.query(User).filter(User.id == step.approver_id).first()
        approver_name = f"{approver.prenom} {approver.nom}" if approver else f"User #{step.approver_id}"

        results.append({
            "workflow_step_id": step.id,
            "entity_type": step.entity_type,
            "entity_id": step.entity_id,
            "requester_name": requester_name,
            "details": details_str,
            "created_at": step.created_at.isoformat() if step.created_at else None,
            "approver_id": step.approver_id,
            "approver_name": approver_name
        })

    return results

@router.post("/override")
def override_workflow(
    payload: WorkflowOverride,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.DIRECTION]))
):
    """
    Action forcée par l'administrateur (Approuver, Rejeter ou Réassigner).
    """
    step = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.id == payload.workflow_step_id).first()
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Étape de workflow introuvable."
        )

    if step.status != ApprovalWorkflowStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette étape a déjà été traitée."
        )

    if payload.action == 'reassign':
        if not payload.new_approver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="new_approver_id requis pour réassignation."
            )
        
        old_approver = db.query(User).filter(User.id == step.approver_id).first()
        old_name = f"{old_approver.prenom} {old_approver.nom}" if old_approver else f"User #{step.approver_id}"
        
        new_approver = db.query(User).filter(User.id == payload.new_approver_id).first()
        if not new_approver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nouvel approbateur introuvable."
            )
        new_name = f"{new_approver.prenom} {new_approver.nom}"

        step.approver_id = payload.new_approver_id
        db.add(step)
        db.commit()

        log_action(
            db=db,
            record_type="workflow_override",
            record_id=step.id,
            action="reassigned",
            performed_by=current_user.id,
            details=f"Réassignation forcée de {old_name} vers {new_name} par l'admin."
        )

        create_notification(
            db, 
            payload.new_approver_id, 
            f"Une demande de {step.entity_type} vous a été réassignée par l'administrateur."
        )

        return {"status": "success", "message": f"Workflow réassigné à {new_name}."}

    elif payload.action in ('approve', 'reject'):
        # Action forcée d'approbation ou de rejet
        res = process_workflow_step(
            db=db,
            step_id=step.id,
            action=payload.action,
            performer_id=current_user.id
        )
        if res.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res.get("message")
            )
        
        # Enregistrer une note d'action forcée dans les logs d'audit
        log_action(
            db=db,
            record_type="workflow_override",
            record_id=step.id,
            action="override_" + payload.action,
            performed_by=current_user.id,
            details=f"Action forcée '{payload.action}' par l'administrateur."
        )

        return res

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action invalide. Choix possibles: approve, reject, reassign."
        )
