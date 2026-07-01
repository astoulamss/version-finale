from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User, RoleEnum
from models.features import Leave, LeaveType, LeaveStatusEnum, LeaveTypeEnum, LeaveBalance
from schemas.features import LeaveCreate, LeaveResponse, LeaveUpdate, LeaveEdit, LeaveTypeCreate, LeaveTypeResponse, LeaveBalanceResponse
from core.security import get_current_user, require_role
from utils.history import log_action
from utils.notifications import notify_role, notify_manager
from utils.notifications import create_notification
from typing import List


router = APIRouter(prefix="/api/leaves", tags=["leaves"])


# Create a leave request (for employees)
@router.post("/", response_model=LeaveResponse)
def create_leave(
    leave_data: LeaveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.COLLABORATEUR, RoleEnum.MANAGER, RoleEnum.RH, RoleEnum.MEDECINE_TRAVAIL]))
):
    """
    Create a leave request
    - Only employees and managers can create leave requests
    """
    # Validate dates
    if leave_data.start_date > leave_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )

    # Map leave_type Enum or leave_type_id to leave_type_id
    if leave_data.leave_type_id is not None:
        leave_type_obj = db.query(LeaveType).filter(LeaveType.id == leave_data.leave_type_id).first()
        if not leave_type_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Leave type id {leave_data.leave_type_id} not found."
            )
    elif leave_data.leave_type is not None:
        enum_to_name = {
            LeaveTypeEnum.VACATION: "Congé Payé",
            LeaveTypeEnum.SICK: "Arrêt Maladie",
            LeaveTypeEnum.MATERNITY: "Maternité / Paternité",
            LeaveTypeEnum.PERSONAL: "Congé Personnel",
            LeaveTypeEnum.UNPAID: "Congé Sans Solde"
        }
        target_name = enum_to_name.get(leave_data.leave_type)
        leave_type_obj = db.query(LeaveType).filter(LeaveType.name == target_name).first()
        if not leave_type_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Leave type '{target_name}' not found in database."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either leave_type_id or leave_type must be provided."
        )

    leave = Leave(
        employee_id=current_user.id,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        leave_type_id=leave_type_obj.id,
        reason=leave_data.reason
    )

    db.add(leave)
    from sqlalchemy.exc import IntegrityError
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une demande de congé existe déjà pour cet employé sur cette même période."
        )

    from utils.workflow_service import init_workflow
    is_auto = init_workflow(db, 'leave', leave, current_user)

    if not is_auto:
        log_action(
            db=db,
            record_type="leave",
            record_id=leave.id,
            action="created",
            performed_by=current_user.id,
            details=f"Demande de congé de type {leave.leave_type} créée (en attente de validation) pour la période du {leave.start_date} au {leave.end_date}."
        )

    return leave


def _auto_archive_leaves(db: Session):
    from datetime import date
    today = date.today()
    db.query(Leave).filter(
        Leave.is_archived == False,
        Leave.end_date < today
    ).update({"is_archived": True})
    db.commit()


# Get my leave requests
@router.get("/my-leaves", response_model=List[LeaveResponse])
def get_my_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.COLLABORATEUR, RoleEnum.MANAGER, RoleEnum.RH, RoleEnum.MEDECINE_TRAVAIL])),
    is_archived: bool = False
):
    """Get all leave requests for the current user"""
    _auto_archive_leaves(db)
    leaves = db.query(Leave).filter(
        Leave.employee_id == current_user.id,
        Leave.is_archived == is_archived
    ).all()
    return leaves


# Get all leave requests (RH and Admin only)
@router.get("/", response_model=List[LeaveResponse])
def get_all_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN])),
    is_archived: bool = False
):
    """
    Get all leave requests in the system.
    Only RH and Admin can view all leaves.
    """
    _auto_archive_leaves(db)
    leaves = db.query(Leave).filter(Leave.is_archived == is_archived).all()
    return leaves


# Get all leave requests for team (managers only)
@router.get("/team", response_model=List[LeaveResponse])
def get_team_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER])),
    is_archived: bool = False
):
    """Get all leave requests for the manager's team"""
    _auto_archive_leaves(db)
    from models.employees import Employee
    # Récupérer les IDs des employés de l'équipe du manager
    team_ids = [
        e.user_id for e in
        db.query(Employee).filter(Employee.manager_id == current_user.id).all()
    ]
    if not team_ids:
        return []
    leaves = db.query(Leave).filter(
        Leave.employee_id.in_(team_ids),
        Leave.is_archived == is_archived
    ).all()
    return leaves


# Leave types routes
@router.get("/types", response_model=List[LeaveTypeResponse])
def get_leave_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all leave types. Anyone authenticated can call this."""
    return db.query(LeaveType).all()


@router.post("/types", response_model=LeaveTypeResponse)
def create_leave_type(
    leave_type_data: LeaveTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH]))
):
    """
    Create a new leave type.
    Strictly restricted to RH.
    """
    # Check if a leave type with the same name already exists
    existing = db.query(LeaveType).filter(LeaveType.name == leave_type_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A leave type with this name already exists"
        )
    
    leave_type = LeaveType(
        name=leave_type_data.name,
        max_days=leave_type_data.max_days,
        description=leave_type_data.description
    )
    db.add(leave_type)
    db.commit()
    db.refresh(leave_type)
    
    # Log action to history
    log_action(
        db=db,
        record_type="leave_type",
        record_id=leave_type.id,
        action="created",
        performed_by=current_user.id,
        details=f"Type de congé '{leave_type.name}' (max {leave_type.max_days} jours) créé."
    )
    
    return leave_type


@router.put("/types/{type_id}", response_model=LeaveTypeResponse)
def update_leave_type(
    type_id: int,
    leave_type_data: LeaveTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH]))
):
    """
    Update an existing leave type.
    Strictly restricted to RH.
    """
    leave_type = db.query(LeaveType).filter(LeaveType.id == type_id).first()
    if not leave_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave type not found"
        )
    
    # Check name uniqueness if changed
    if leave_type_data.name != leave_type.name:
        existing = db.query(LeaveType).filter(LeaveType.name == leave_type_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A leave type with this name already exists"
            )
            
    old_max_days = leave_type.max_days
    
    leave_type.name = leave_type_data.name
    leave_type.max_days = leave_type_data.max_days
    leave_type.description = leave_type_data.description
    
    # Adjust existing balances if max_days changed
    if old_max_days != leave_type_data.max_days:
        diff = leave_type_data.max_days - old_max_days
        from models.features import LeaveBalance
        db.query(LeaveBalance).filter(LeaveBalance.leave_type_id == type_id).update(
            {"remaining_days": LeaveBalance.remaining_days + diff}, synchronize_session=False
        )
    
    db.add(leave_type)
    db.commit()
    db.refresh(leave_type)
    
    # Log action to history
    log_action(
        db=db,
        record_type="leave_type",
        record_id=leave_type.id,
        action="modified",
        performed_by=current_user.id,
        details=f"Type de congé '{leave_type.name}' modifié (max {leave_type.max_days} jours)."
    )
    
    return leave_type


@router.delete("/types/{type_id}")
def delete_leave_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH]))
):
    """
    Delete a leave type.
    Strictly restricted to RH.
    """
    leave_type = db.query(LeaveType).filter(LeaveType.id == type_id).first()
    if not leave_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave type not found"
        )
        
    # Check if there are existing leave requests using this type to avoid foreign key errors
    has_leaves = db.query(Leave).filter(Leave.leave_type_id == type_id).first()
    if has_leaves:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete this leave type because there are leave requests associated with it."
        )
        
    # Delete associated balances first
    db.query(LeaveBalance).filter(LeaveBalance.leave_type_id == type_id).delete()
    
    db.delete(leave_type)
    db.commit()
    
    # Log action to history
    log_action(
        db=db,
        record_type="leave_type",
        record_id=type_id,
        action="deleted",
        performed_by=current_user.id,
        details=f"Type de congé id={type_id} supprimé."
    )
    
    return {"message": "Leave type deleted successfully"}


# Leave balance routes
@router.get("/balances/me", response_model=List[LeaveBalanceResponse])
def get_my_leave_balances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get leave balances for the currently logged-in user.
    Auto-initializes balances if any leave types don't have them yet.
    """
    leave_types = db.query(LeaveType).all()
    existing_balances = db.query(LeaveBalance).filter(LeaveBalance.employee_id == current_user.id).all()
    
    existing_type_ids = {b.leave_type_id for b in existing_balances}
    
    initialized_any = False
    for lt in leave_types:
        if lt.id not in existing_type_ids:
            new_balance = LeaveBalance(
                employee_id=current_user.id,
                leave_type_id=lt.id,
                remaining_days=float(lt.max_days)
            )
            db.add(new_balance)
            initialized_any = True
            
    if initialized_any:
        db.commit()
        # Refetch to get updated list with newly created balances
        existing_balances = db.query(LeaveBalance).filter(LeaveBalance.employee_id == current_user.id).all()
        
    return existing_balances


# Get all leave balances (RH and Admin only)
@router.get("/balances", response_model=List[LeaveBalanceResponse])
def get_all_leave_balances(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    """
    Get all leave balances for all users in the system.
    Strictly restricted to RH and Admin.
    """
    from models.user import User as UserModel
    users = db.query(UserModel).filter(UserModel.role.in_([RoleEnum.COLLABORATEUR, RoleEnum.MANAGER])).all()
    leave_types = db.query(LeaveType).all()
    
    all_balances = db.query(LeaveBalance).all()
    existing_map = {(b.employee_id, b.leave_type_id) for b in all_balances}
    
    initialized_any = False
    for u in users:
        for lt in leave_types:
            if (u.id, lt.id) not in existing_map:
                new_balance = LeaveBalance(
                    employee_id=u.id,
                    leave_type_id=lt.id,
                    remaining_days=float(lt.max_days)
                )
                db.add(new_balance)
                initialized_any = True
                
    if initialized_any:
        db.commit()
        all_balances = db.query(LeaveBalance).all()
        
    return all_balances


# Approve/Reject leave request (managers, RH and admins)
@router.put("/{leave_id}", response_model=LeaveResponse)
def update_leave_status(
    leave_id: int,
    leave_update: LeaveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.RH, RoleEnum.ADMIN]))
):
    """
    Approve or reject a leave request
    - Managers can only validate simple leaves (<= 5 days) of non-manager employees
    - RH and Admin can validate any leaves, including long leaves (> 5 days), special leaves, and manager leaves
    """
    leave = db.query(Leave).filter(Leave.id == leave_id).first()

    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )

    # Intercept workflow rules
    from models.features import ApprovalWorkflow, ApprovalWorkflowStatusEnum
    active_step = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.entity_type == 'leave',
        ApprovalWorkflow.entity_id == leave_id,
        ApprovalWorkflow.status == ApprovalWorkflowStatusEnum.PENDING
    ).first()

    if active_step:
        if current_user.role != RoleEnum.ADMIN and active_step.approver_id != current_user.id:
            assigned_user = db.query(User).filter(User.id == active_step.approver_id).first()
            is_assigned_rh = assigned_user and assigned_user.role == RoleEnum.RH
            if not (current_user.role == RoleEnum.RH and is_assigned_rh):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accès refusé. Vous n'êtes pas le validateur désigné pour cette étape."
                )
        from utils.workflow_service import process_workflow_step
        action = 'approve' if leave_update.status == LeaveStatusEnum.APPROVED else 'reject'
        res = process_workflow_step(db, active_step.id, action, current_user.id)
        if res.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res.get("message")
            )
        db.refresh(leave)
        return leave

    # Fetch requester to check their role
    requester = db.query(User).filter(User.id == leave.employee_id).first()
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requester user not found"
        )

    # For MANAGER role, verify that they are the manager of this employee
    if current_user.role == RoleEnum.MANAGER:
        from models.employees import Employee
        emp_profile = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
        if not emp_profile or emp_profile.manager_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé. Vous pouvez uniquement valider les congés des membres de votre équipe."
            )
            
        # Un manager ne peut pas valider ses propres congés
        if requester.role == RoleEnum.MANAGER and requester.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé. Un manager ne peut pas valider ses propres congés."
            )

    # Calculate leave duration
    duration = (leave.end_date - leave.start_date).days + 1

    old_status = leave.status
    leave.status = leave_update.status
    leave.approved_by = current_user.id

    # Handle leave balance updates
    if leave_update.status == LeaveStatusEnum.APPROVED and old_status != LeaveStatusEnum.APPROVED:
        # Subtract from balance
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == leave.employee_id,
            LeaveBalance.leave_type_id == leave.leave_type_id
        ).first()
        if not balance:
            # Auto-initialize balance using max_days of the leave type
            balance = LeaveBalance(
                employee_id=leave.employee_id,
                leave_type_id=leave.leave_type_id,
                remaining_days=float(leave.leave_type_relation.max_days) if leave.leave_type_relation else 25.0
            )
            db.add(balance)
            db.flush()
        
        balance.remaining_days = float(balance.remaining_days) - float(duration)
        db.add(balance)

    elif old_status == LeaveStatusEnum.APPROVED and leave_update.status in [LeaveStatusEnum.REJECTED, LeaveStatusEnum.CANCELLED]:
        # Restore to balance
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == leave.employee_id,
            LeaveBalance.leave_type_id == leave.leave_type_id
        ).first()
        if balance:
            balance.remaining_days = float(balance.remaining_days) + float(duration)
            db.add(balance)

    db.add(leave)
    db.commit()
    db.refresh(leave)

    # Log action to history
    log_action(
        db=db,
        record_type="leave",
        record_id=leave.id,
        action=leave.status.value,
        performed_by=current_user.id,
        details=f"Demande de congé validée avec le statut '{leave.status.value}' par l'utilisateur id={current_user.id}."
    )

    # Envoyer une notification in-app à l'employé
    type_label = {
        "vacation": "congé payé",
        "sick": "congé maladie",
        "maternity": "congé maternité",
        "personal": "congé personnel",
        "unpaid": "congé sans solde"
    }.get(leave.leave_type, "congé")
    
    status_label = {
        "approved": "acceptée",
        "rejected": "refusée",
        "cancelled": "annulée"
    }.get(leave.status.value, leave.status.value)

    message = f"Votre demande de {type_label} du {leave.start_date} au {leave.end_date} a été {status_label}."
    create_notification(db, leave.employee_id, message)

    return leave


# Get leave by ID
@router.get("/{leave_id}", response_model=LeaveResponse)
def get_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific leave request"""
    leave = db.query(Leave).filter(Leave.id == leave_id).first()

    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )

    # Check if user can view this leave
    if leave.employee_id != current_user.id and current_user.role not in [RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.RH]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this leave request"
        )

    return leave


# Delete leave request (only own and pending)
@router.delete("/{leave_id}")
def delete_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.COLLABORATEUR, RoleEnum.MANAGER, RoleEnum.RH, RoleEnum.MEDECINE_TRAVAIL]))
):
    """Delete a leave request (only if it's pending and belongs to the user)"""
    leave = db.query(Leave).filter(Leave.id == leave_id).first()

    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )

    # Only the employee who created it can delete
    if leave.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own leave requests"
        )

    # Can only delete pending requests
    if leave.status != LeaveStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete pending leave requests"
        )

    # Log action to history before deleting
    log_action(
        db=db,
        record_type="leave",
        record_id=leave.id,
        action="deleted",
        performed_by=current_user.id,
        details="Demande de congé annulée et supprimée par le demandeur."
    )

    db.delete(leave)
    db.commit()

    return {"message": "Leave request deleted successfully"}


# Edit leave request (only own and pending)
@router.patch("/{leave_id}", response_model=LeaveResponse)
def edit_leave(
    leave_id: int,
    leave_data: LeaveEdit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.COLLABORATEUR, RoleEnum.MANAGER, RoleEnum.RH, RoleEnum.MEDECINE_TRAVAIL]))
):
    """
    Modify an existing leave request.
    - Only the employee who created the request can modify it.
    - The request must be in 'pending' status to be modified.
    """
    leave = db.query(Leave).filter(Leave.id == leave_id).first()

    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )

    # Only the employee who created it can modify
    if leave.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own leave requests"
        )

    # Can only modify pending requests
    if leave.status != LeaveStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only modify pending leave requests"
        )

    # Update fields if provided
    if leave_data.start_date is not None:
        leave.start_date = leave_data.start_date
    if leave_data.end_date is not None:
        leave.end_date = leave_data.end_date
    if leave_data.leave_type_id is not None:
        leave_type_obj = db.query(LeaveType).filter(LeaveType.id == leave_data.leave_type_id).first()
        if not leave_type_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Leave type id {leave_data.leave_type_id} not found."
            )
        leave.leave_type_id = leave_type_obj.id
    elif leave_data.leave_type is not None:
        enum_to_name = {
            LeaveTypeEnum.VACATION: "Congé Payé",
            LeaveTypeEnum.SICK: "Arrêt Maladie",
            LeaveTypeEnum.MATERNITY: "Maternité / Paternité",
            LeaveTypeEnum.PERSONAL: "Congé Personnel",
            LeaveTypeEnum.UNPAID: "Congé Sans Solde"
        }
        target_name = enum_to_name.get(leave_data.leave_type)
        leave_type_obj = db.query(LeaveType).filter(LeaveType.name == target_name).first()
        if not leave_type_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Leave type '{target_name}' not found in database."
            )
        leave.leave_type_id = leave_type_obj.id
    if leave_data.reason is not None:
        leave.reason = leave_data.reason

    # Validate dates after updates
    if leave.start_date > leave.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )

    db.add(leave)
    db.commit()
    db.refresh(leave)

    # Log action to history
    log_action(
        db=db,
        record_type="leave",
        record_id=leave.id,
        action="modified",
        performed_by=current_user.id,
        details=f"Demande de congé modifiée par le demandeur. Nouvelle période: du {leave.start_date} au {leave.end_date}."
    )

    return leave
