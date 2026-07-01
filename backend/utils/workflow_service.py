from sqlalchemy.orm import Session
from models.user import User, RoleEnum
from models.employees import Employee
from models.features import Leave, LeaveStatusEnum, LeaveBalance, WorkflowConfig, ApprovalWorkflow, ApprovalWorkflowStatusEnum
from models.absences import Absence, AbsenceStatusEnum
from utils.notifications import create_notification
from utils.history import log_action
from datetime import datetime

def init_workflow(db: Session, entity_type: str, entity, requester_user: User):
    """
    Applique la règle de workflow configurée pour une nouvelle demande (Leave ou Absence).
    """
    # 1. Récupérer la config
    config = db.query(WorkflowConfig).filter(WorkflowConfig.entity_type == entity_type).first()
    logic_type = config.logic_type if config else 'single_manager'

    if logic_type == 'auto':
        # Validation automatique
        if entity_type == 'leave':
            entity.status = LeaveStatusEnum.APPROVED
            # Mise à jour du solde
            duration = (entity.end_date - entity.start_date).days + 1
            balance = db.query(LeaveBalance).filter(
                LeaveBalance.employee_id == entity.employee_id,
                LeaveBalance.leave_type_id == entity.leave_type_id
            ).first()
            if balance:
                balance.remaining_days = float(balance.remaining_days) - float(duration)
                db.add(balance)
            log_action(
                db=db,
                record_type="leave",
                record_id=entity.id,
                action="approved",
                performed_by=requester_user.id,
                details="Validation automatique du congé (règle auto)."
            )
            create_notification(db, entity.employee_id, f"Votre demande de congé du {entity.start_date.strftime('%d/%m/%Y')} au {entity.end_date.strftime('%d/%m/%Y')} a été validée automatiquement.")
        elif entity_type == 'absence':
            entity.status = AbsenceStatusEnum.APPROVED
            log_action(
                db=db,
                record_type="absence",
                record_id=entity.id,
                action="approved",
                performed_by=requester_user.id,
                details="Validation automatique de l'absence (règle auto)."
            )
            create_notification(db, entity.employee_id, f"Votre absence du {entity.start_date.strftime('%d/%m/%Y')} au {entity.end_date.strftime('%d/%m/%Y')} a été validée automatiquement.")
        
        db.add(entity)
        db.commit()
        return True

    # Pour toutes les autres logiques, le statut initial est PENDING
    if entity_type == 'leave':
        entity.status = LeaveStatusEnum.PENDING
    elif entity_type == 'absence':
        entity.status = AbsenceStatusEnum.PENDING
    db.add(entity)
    db.flush()

    approver_id = None
    if logic_type in ('single_manager', 'sequential'):
        # Étape 1 : le manager direct
        emp = db.query(Employee).filter(Employee.user_id == requester_user.id).first()
        if emp and emp.manager_id:
            approver_id = emp.manager_id
        else:
            # Fallback : premier utilisateur RH ou admin active
            fallback_user = db.query(User).filter(User.role == RoleEnum.RH, User.is_active == True).first()
            if not fallback_user:
                fallback_user = db.query(User).filter(User.role == RoleEnum.ADMIN, User.is_active == True).first()
            approver_id = fallback_user.id if fallback_user else requester_user.id

    elif logic_type == 'single_rh':
        # Étape 1 : le validateur RH configuré ou fallback
        if config and config.validator_user_id:
            approver_id = config.validator_user_id
        else:
            fallback_user = db.query(User).filter(User.role == RoleEnum.RH, User.is_active == True).first()
            if not fallback_user:
                fallback_user = db.query(User).filter(User.role == RoleEnum.ADMIN, User.is_active == True).first()
            approver_id = fallback_user.id if fallback_user else requester_user.id

    # Création de l'étape de validation en attente
    wf_step = ApprovalWorkflow(
        entity_type=entity_type,
        entity_id=entity.id,
        approver_id=approver_id,
        status=ApprovalWorkflowStatusEnum.PENDING,
        created_at=datetime.utcnow()
    )
    db.add(wf_step)
    db.commit()

    # Envoyer notification au validateur
    approver = db.query(User).filter(User.id == approver_id).first()
    if approver:
        entity_label = "congé" if entity_type == "leave" else "absence"
        msg = f"Nouvelle demande de {entity_label} par {requester_user.prenom} {requester_user.nom} en attente de votre validation."
        create_notification(db, approver_id, msg)

    return False

def process_workflow_step(db: Session, step_id: int, action: str, performer_id: int, final_status=None):
    """
    Traite la validation d'une étape par un approbateur.
    action: 'approve' ou 'reject'
    final_status: optionnel, pour forcer le statut final (ex: 'received')
    """
    step = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.id == step_id).first()
    if not step:
        return {"status": "error", "message": "Étape de workflow introuvable."}

    if step.status != ApprovalWorkflowStatusEnum.PENDING:
        return {"status": "error", "message": "Cette étape a déjà été traitée."}

    # Récupérer l'entité
    entity = None
    requester_user = None
    if step.entity_type == 'leave':
        entity = db.query(Leave).filter(Leave.id == step.entity_id).first()
        if entity:
            requester_user = db.query(User).filter(User.id == entity.employee_id).first()
    elif step.entity_type == 'absence':
        entity = db.query(Absence).filter(Absence.id == step.entity_id).first()
        if entity:
            requester_user = db.query(User).filter(User.id == entity.employee_id).first()

    if not entity:
        return {"status": "error", "message": "Demande associée introuvable."}

    config = db.query(WorkflowConfig).filter(WorkflowConfig.entity_type == step.entity_type).first()
    logic_type = config.logic_type if config else 'single_manager'

    performer = db.query(User).filter(User.id == performer_id).first()
    performer_name = f"{performer.prenom} {performer.nom}" if performer else f"User #{performer_id}"

    if action == 'reject':
        step.status = ApprovalWorkflowStatusEnum.REJECTED
        if step.entity_type == 'leave':
            entity.status = LeaveStatusEnum.REJECTED
        elif step.entity_type == 'absence':
            entity.status = AbsenceStatusEnum.REJECTED
        db.add(step)
        db.add(entity)
        db.commit()

        log_action(
            db=db,
            record_type=step.entity_type,
            record_id=entity.id,
            action="rejected",
            performed_by=performer_id,
            details=f"Demande rejetée via le workflow par {performer_name}."
        )
        create_notification(db, entity.employee_id, f"Votre demande de {step.entity_type} a été refusée.")
        return {"status": "success", "message": "Étape de rejet traitée."}

    # Cas action == 'approve'
    step.status = ApprovalWorkflowStatusEnum.APPROVED
    db.add(step)
    db.flush()

    # Si logique séquentielle, et qu'on vient d'approuver l'étape du manager :
    steps_count = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.entity_type == step.entity_type,
        ApprovalWorkflow.entity_id == step.entity_id
    ).count()

    if logic_type == 'sequential' and steps_count == 1:
        # Étape 1 validée, on crée l'étape 2 (RH désigné)
        next_approver_id = None
        if config and config.validator_user_id:
            next_approver_id = config.validator_user_id
        else:
            fallback_user = db.query(User).filter(User.role == RoleEnum.RH, User.is_active == True).first()
            if not fallback_user:
                fallback_user = db.query(User).filter(User.role == RoleEnum.ADMIN, User.is_active == True).first()
            next_approver_id = fallback_user.id if fallback_user else performer_id

        next_step = ApprovalWorkflow(
            entity_type=step.entity_type,
            entity_id=step.entity_id,
            approver_id=next_approver_id,
            status=ApprovalWorkflowStatusEnum.PENDING,
            created_at=datetime.utcnow()
        )
        db.add(next_step)
        db.commit()

        log_action(
            db=db,
            record_type=step.entity_type,
            record_id=entity.id,
            action="approved_step1",
            performed_by=performer_id,
            details=f"Étape 1 (Manager) approuvée par {performer_name}. En attente du validateur RH."
        )

        # Notification au nouveau validateur
        next_approver = db.query(User).filter(User.id == next_approver_id).first()
        if next_approver:
            msg = f"Validation Étape 2 requise pour la demande de {step.entity_type} de {requester_user.prenom} {requester_user.nom}."
            create_notification(db, next_approver_id, msg)

        return {"status": "success", "message": "Étape 1 approuvée. Étape 2 créée."}

    else:
        # Validation finale
        if step.entity_type == 'leave':
            old_status = entity.status
            entity.status = final_status if final_status else LeaveStatusEnum.APPROVED
            entity.approved_by = performer_id
            
            # Déduire du solde si ce n'était pas déjà approuvé
            if old_status != LeaveStatusEnum.APPROVED:
                duration = (entity.end_date - entity.start_date).days + 1
                balance = db.query(LeaveBalance).filter(
                    LeaveBalance.employee_id == entity.employee_id,
                    LeaveBalance.leave_type_id == entity.leave_type_id
                ).first()
                if balance:
                    balance.remaining_days = float(balance.remaining_days) - float(duration)
                    db.add(balance)

        elif step.entity_type == 'absence':
            entity.status = final_status if final_status else AbsenceStatusEnum.APPROVED

        db.add(entity)
        db.commit()

        log_action(
            db=db,
            record_type=step.entity_type,
            record_id=entity.id,
            action="approved",
            performed_by=performer_id,
            details=f"Demande entièrement approuvée par {performer_name}."
        )

        create_notification(db, entity.employee_id, f"Votre demande de {step.entity_type} a été approuvée.")
        return {"status": "success", "message": "Demande entièrement approuvée."}
