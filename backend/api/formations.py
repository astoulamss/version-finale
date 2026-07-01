from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User, RoleEnum
from models.employees import Employee
from models.features import Formation, FormationEnrollment
from schemas.features import FormationCreate, FormationResponse, FormationEnrollmentCreate, FormationEnrollmentResponse
from core.security import get_current_user, require_role
from typing import List, Optional
from utils.history import log_action
from utils.notifications import create_notification


router = APIRouter(prefix="/api/formations", tags=["formations"])





# Get all formations
@router.get("/", response_model=List[FormationResponse])
def get_all_formations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available formations (tous les rôles authentifiés) - only active ones"""
    from datetime import date
    from sqlalchemy import or_
    from models.employees import Employee

    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    dept_id = employee.department_id if employee else None

    formations = db.query(Formation).filter(
        Formation.end_date >= date.today(),
        or_(Formation.target_department_id == None, Formation.target_department_id == dept_id)
    ).all()
    return formations



# Get all formations (RH can access all)
@router.get("/rh/all", response_model=List[FormationResponse])
def get_all_formations_rh(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    """Get all formations (RH and Admin)"""
    formations = db.query(Formation).all()
    return formations


# Get my enrollments
@router.get("/my-enrollments", response_model=List[FormationEnrollmentResponse])
def get_my_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir les formations auxquelles l'utilisateur connecté est inscrit"""
    enrollments = db.query(FormationEnrollment).filter(FormationEnrollment.employee_id == current_user.id).all()
    
    # Formater la réponse
    responses = []
    for enrollment in enrollments:
        resp = FormationEnrollmentResponse.model_validate(enrollment)
        resp.nom = current_user.nom
        resp.prenom = current_user.prenom
        resp.formation_title = enrollment.formation.title
        resp.formation_description = enrollment.formation.description
        resp.formation_start_date = enrollment.formation.start_date
        resp.formation_end_date = enrollment.formation.end_date
        responses.append(resp)
        
    return responses


# Get my team's enrollments (Manager only)
@router.get("/my-team-enrollments", response_model=List[FormationEnrollmentResponse])
def get_my_team_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER]))
):
    """Obtenir les formations auxquelles les membres de l'équipe du manager sont inscrits"""
    from models.employees import Employee
    manager_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    
    if not manager_employee or not manager_employee.department_id:
        return []

    # Get all employees in the manager's department (excluding the manager)
    team_employees = db.query(Employee).filter(
        Employee.department_id == manager_employee.department_id,
        Employee.user_id != current_user.id
    ).all()
    
    team_user_ids = [emp.user_id for emp in team_employees]
    if not team_user_ids:
        return []
        
    enrollments = db.query(FormationEnrollment).filter(FormationEnrollment.employee_id.in_(team_user_ids)).all()
    
    responses = []
    # Fetch team user objects for quick lookup
    team_users = db.query(User).filter(User.id.in_(team_user_ids)).all()
    user_map = {u.id: u for u in team_users}
    
    for enrollment in enrollments:
        resp = FormationEnrollmentResponse.model_validate(enrollment)
        user = user_map.get(enrollment.employee_id)
        if user:
            resp.nom = user.nom
            resp.prenom = user.prenom
        resp.formation_title = enrollment.formation.title
        resp.formation_description = enrollment.formation.description
        resp.formation_start_date = enrollment.formation.start_date
        resp.formation_end_date = enrollment.formation.end_date
        responses.append(resp)
        
    return responses


# Create a formation (RH and Admin)
@router.post("/", response_model=FormationResponse)
def create_formation(
    formation_data: FormationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    """
    Create a new formation
    - Only RH and Admin can create formations
    """
    # Validate dates
    if formation_data.start_date > formation_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )

    formation = Formation(
        title=formation_data.title,
        description=formation_data.description,
        start_date=formation_data.start_date,
        end_date=formation_data.end_date,
        target_department_id=formation_data.target_department_id
    )

    db.add(formation)
    db.commit()
    db.refresh(formation)

    return formation


# Get formation by ID
@router.get("/{formation_id}", response_model=FormationResponse)
def get_formation(
    formation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific formation (tous les rôles authentifiés)"""
    formation = db.query(Formation).filter(Formation.id == formation_id).first()

    if not formation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formation not found"
        )

    return formation



# Update formation (RH and Admin)
@router.put("/{formation_id}", response_model=FormationResponse)
def update_formation(
    formation_id: int,
    formation_data: FormationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    """Update a formation (RH and Admin)"""
    formation = db.query(Formation).filter(Formation.id == formation_id).first()

    if not formation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formation not found"
        )

    # Validate dates
    if formation_data.start_date > formation_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )

    formation.title = formation_data.title
    formation.description = formation_data.description
    formation.start_date = formation_data.start_date
    formation.end_date = formation_data.end_date
    formation.target_department_id = formation_data.target_department_id

    db.add(formation)
    db.commit()
    db.refresh(formation)

    return formation


# Delete formation (Admin and RH)
@router.delete("/{formation_id}")
def delete_formation(
    formation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Delete a formation (Admin and RH)"""
    formation = db.query(Formation).filter(Formation.id == formation_id).first()

    if not formation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formation not found"
        )

    db.delete(formation)
    db.commit()

    return {"message": "Formation deleted successfully"}


# Enroll in a formation
@router.post("/{formation_id}/enroll", response_model=FormationEnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_in_formation(
    formation_id: int,
    enroll_data: Optional[FormationEnrollmentCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    S'inscrire ou inscrire un collaborateur à une formation.
    - Collaborateur/Manager : s'inscrire soi-même uniquement (employee_id ignoré ou doit correspondre à son propre ID).
    - Admin/RH : inscrire n'importe quel employé via employee_id.
    """
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formation non trouvée"
        )

    target_user_id = current_user.id
    if enroll_data and enroll_data.employee_id is not None:
        if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH]:
            if enroll_data.employee_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accès refusé. Seuls Admin et RH peuvent inscrire d'autres collaborateurs."
                )
        # Vérifier que l'utilisateur ciblé existe
        target_user = db.query(User).filter(User.id == enroll_data.employee_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employé ciblé non trouvé."
            )
        target_user_id = enroll_data.employee_id
    else:
        target_user = current_user

    # Vérifier s'il est déjà inscrit
    existing = db.query(FormationEnrollment).filter(
        FormationEnrollment.employee_id == target_user_id,
        FormationEnrollment.formation_id == formation_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet employé est déjà inscrit à cette formation."
        )

    # Créer l'inscription
    enrollment = FormationEnrollment(
        employee_id=target_user_id,
        formation_id=formation_id
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    # Récupérer l'utilisateur ciblé pour le nom/prénom s'il est différent de current_user
    if target_user_id != current_user.id:
        target_user = db.query(User).filter(User.id == target_user_id).first()

    # Historique d'action
    log_action(
        db=db,
        record_type="formation_enrollment",
        record_id=enrollment.id,
        action="enrolled",
        performed_by=current_user.id,
        details=f"Utilisateur id={target_user_id} inscrit à la formation '{formation.title}' par l'utilisateur id={current_user.id}."
    )

    # Notification si l'inscription est faite pour un tiers
    if target_user_id != current_user.id:
        create_notification(
            db=db,
            user_id=target_user_id,
            message=f"Vous avez été inscrit à la formation '{formation.title}' (début le {formation.start_date}) par {current_user.prenom} {current_user.nom}."
        )

    resp = FormationEnrollmentResponse.model_validate(enrollment)
    resp.nom = target_user.nom if target_user else None
    resp.prenom = target_user.prenom if target_user else None
    resp.formation_title = formation.title
    return resp


# Get participants of a formation
@router.get("/{formation_id}/participants", response_model=List[FormationEnrollmentResponse])
def get_formation_participants(
    formation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir la liste des participants inscrits à une formation"""
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formation non trouvée"
        )
        
    enrollments = db.query(FormationEnrollment).filter(FormationEnrollment.formation_id == formation_id).all()
    
    responses = []
    for enrollment in enrollments:
        user = enrollment.employee
        if not user:
            continue
            
        # Fetch employee profile for position, department, and manager_id
        employee_profile = db.query(Employee).filter(Employee.user_id == user.id).first()
        
        # If current user is manager, only show participants managed by them
        if current_user.role == RoleEnum.MANAGER:
            if not employee_profile or employee_profile.manager_id != current_user.id:
                continue

        resp = FormationEnrollmentResponse.model_validate(enrollment)
        resp.nom = user.nom
        resp.prenom = user.prenom
        
        if employee_profile:
            if employee_profile.position:
                resp.position = employee_profile.position.title
            if employee_profile.department:
                resp.department = employee_profile.department.name
                
        resp.formation_title = formation.title
        responses.append(resp)
        
    return responses


# Unenroll self
@router.delete("/{formation_id}/enroll", status_code=status.HTTP_204_NO_CONTENT)
def unenroll_from_formation(
    formation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Se désinscrire soi-même d'une formation"""
    enrollment = db.query(FormationEnrollment).filter(
        FormationEnrollment.employee_id == current_user.id,
        FormationEnrollment.formation_id == formation_id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inscription non trouvée pour cet utilisateur."
        )

    formation_title = enrollment.formation.title
    
    log_action(
        db=db,
        record_type="formation_enrollment",
        record_id=enrollment.id,
        action="unenrolled",
        performed_by=current_user.id,
        details=f"Désinscription personnelle de la formation '{formation_title}'."
    )

    db.delete(enrollment)
    db.commit()
    return None


# Unenroll specific employee (Admin/RH or self)
@router.delete("/{formation_id}/enroll/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def force_unenroll_from_formation(
    formation_id: int,
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Désinscrire un employé spécifique d'une formation (Admin/RH ou l'employé concerné)."""
    if current_user.id != employee_id and current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Vous ne pouvez désinscrire que vous-même."
        )

    enrollment = db.query(FormationEnrollment).filter(
        FormationEnrollment.employee_id == employee_id,
        FormationEnrollment.formation_id == formation_id
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inscription introuvable."
        )

    formation_title = enrollment.formation.title

    log_action(
        db=db,
        record_type="formation_enrollment",
        record_id=enrollment.id,
        action="unenrolled",
        performed_by=current_user.id,
        details=f"Désinscription de l'utilisateur id={employee_id} de la formation '{formation_title}' par l'utilisateur id={current_user.id}."
    )

    if employee_id != current_user.id:
        create_notification(
            db=db,
            user_id=employee_id,
            message=f"Vous avez été désinscrit de la formation '{formation_title}' par {current_user.prenom} {current_user.nom}."
        )

    db.delete(enrollment)
    db.commit()
    return None
