from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.db import get_db
from models.user import User, RoleEnum
from models.employees import Employee, Department, Position
from schemas.employees import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentManagerAssign,
    PositionCreate, PositionUpdate, PositionResponse,
    ManagerResponse
)
from core.security import get_current_user, require_role

router = APIRouter(prefix="/api/employees", tags=["Employees"])


# ────────────────────────────────────────────────────────────────────
# DÉPARTEMENTS
# ────────────────────────────────────────────────────────────────────

@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste tous les départements disponibles avec le manager affecté"""
    depts = db.query(Department).all()
    result = []
    for dept in depts:
        d = DepartmentResponse(
            id=dept.id,
            name=dept.name,
            description=dept.description,
            manager_id=dept.manager_id,
            manager_nom=dept.manager.nom if dept.manager else None,
            manager_prenom=dept.manager.prenom if dept.manager else None,
        )
        result.append(d)
    return result


@router.put("/departments/{dept_id}/manager", response_model=DepartmentResponse)
def assign_manager_to_department(
    dept_id: int,
    payload: DepartmentManagerAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Affecter ou désaffecter un manager à un département (RH et Admin uniquement)"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Département introuvable.")

    if payload.manager_id is not None:
        if payload.manager_id != dept.manager_id:
            manager = db.query(User).join(Employee, Employee.user_id == User.id).filter(
                User.id == payload.manager_id,
                User.role == RoleEnum.MANAGER,
                User.is_active == True
            ).first()
            if not manager:
                raise HTTPException(
                    status_code=400,
                    detail="L'utilisateur sélectionné n'est pas un manager actif ou n'a pas encore de profil employé."
                )
        dept.manager_id = payload.manager_id
    else:
        dept.manager_id = None

    db.commit()
    db.refresh(dept)
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        manager_id=dept.manager_id,
        manager_nom=dept.manager.nom if dept.manager else None,
        manager_prenom=dept.manager.prenom if dept.manager else None,
    )


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    dept_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Créer un nouveau département (Admin et RH uniquement)"""
    existing = db.query(Department).filter(Department.name == dept_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un département avec ce nom existe déjà"
        )
    
    dept = Department(name=dept_data.name, description=dept_data.description)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.patch("/departments/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: int,
    dept_data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Modifier un département (Admin et RH uniquement)"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Département introuvable"
        )
    
    update_data = dept_data.model_dump(exclude_unset=True)
    
    if "name" in update_data and update_data["name"] != dept.name:
        # Vérifier l'unicité du nom
        existing = db.query(Department).filter(Department.name == update_data["name"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un département avec ce nom existe déjà"
            )
            
    for field, value in update_data.items():
        setattr(dept, field, value)
        
    db.add(dept)
    db.commit()
    db.refresh(dept)
    
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        manager_id=dept.manager_id,
        manager_nom=dept.manager.nom if dept.manager else None,
        manager_prenom=dept.manager.prenom if dept.manager else None,
    )


@router.delete("/departments/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Supprimer un département (Admin et RH uniquement)"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Département introuvable"
        )
        
    # Détacher ce département de tous les employés concernés
    db.query(Employee).filter(Employee.department_id == dept_id).update({Employee.department_id: None})
    
    db.delete(dept)
    db.commit()
    return None


# ────────────────────────────────────────────────────────────────────
# POSTES
# ────────────────────────────────────────────────────────────────────

@router.get("/positions", response_model=List[PositionResponse])
def list_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste tous les postes disponibles"""
    return db.query(Position).all()


@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(
    pos_data: PositionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Créer un nouveau poste (Admin et RH uniquement)"""
    existing = db.query(Position).filter(Position.title == pos_data.title).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un poste avec ce titre existe déjà"
        )
    
    pos = Position(title=pos_data.title, description=pos_data.description)
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos


@router.patch("/positions/{pos_id}", response_model=PositionResponse)
def update_position(
    pos_id: int,
    pos_data: PositionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Modifier un poste (Admin et RH uniquement)"""
    pos = db.query(Position).filter(Position.id == pos_id).first()
    if not pos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poste introuvable"
        )
    
    update_data = pos_data.model_dump(exclude_unset=True)
    
    if "title" in update_data and update_data["title"] != pos.title:
        # Vérifier l'unicité du titre
        existing = db.query(Position).filter(Position.title == update_data["title"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un poste avec ce titre existe déjà"
            )
            
    for field, value in update_data.items():
        setattr(pos, field, value)
        
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos


@router.delete("/positions/{pos_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    pos_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Supprimer un poste (Admin et RH uniquement)"""
    pos = db.query(Position).filter(Position.id == pos_id).first()
    if not pos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poste introuvable"
        )
        
    # Détacher ce poste de tous les employés concernés
    db.query(Employee).filter(Employee.position_id == pos_id).update({Employee.position_id: None})
    
    db.delete(pos)
    db.commit()
    return None


# ────────────────────────────────────────────────────────────────────
# MANAGERS (pour le sélecteur lors de la création d'un employé)
# ────────────────────────────────────────────────────────────────────

@router.get("/managers", response_model=List[ManagerResponse])
def list_managers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """
    Retourne la liste des utilisateurs ayant le rôle manager.
    Utilisé lors de la création d'un employé pour choisir son manager.
    """
    managers = db.query(User).filter(
        User.role == RoleEnum.MANAGER,
        User.is_active == True
    ).all()
    return managers


# ────────────────────────────────────────────────────────────────────
# EMPLOYÉS
# ────────────────────────────────────────────────────────────────────

@router.post("/register-self", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def register_self_as_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH]))
):
    """
    Permet à l'utilisateur RH de créer son propre profil employé.
    """
    # Forcer le user_id à soi-même (sécurité)
    if employee_data.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez créer un profil employé que pour vous-même via cet endpoint."
        )

    # Vérifier qu'il n'a pas déjà un profil
    existing = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous avez déjà un profil employé."
        )

    # Vérifier le département
    if employee_data.department_id:
        dept = db.query(Department).filter(Department.id == employee_data.department_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail=f"Département id={employee_data.department_id} introuvable")

    # Vérifier le poste
    if employee_data.position_id:
        pos = db.query(Position).filter(Position.id == employee_data.position_id).first()
        if not pos:
            raise HTTPException(status_code=404, detail=f"Poste id={employee_data.position_id} introuvable")

    employee = Employee(
        user_id=current_user.id,
        department_id=employee_data.department_id,
        position_id=employee_data.position_id,
        manager_id=employee_data.manager_id,
        salary=employee_data.salary,
        hire_date=employee_data.hire_date,
        departure_date=employee_data.departure_date,
        status=employee_data.status,
        date_naissance=employee_data.date_naissance,
        nationalite=employee_data.nationalite,
        adresse=employee_data.adresse,
        numero_telephone=employee_data.numero_telephone,
        sexe=employee_data.sexe
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """
    Créer un nouvel employé (Admin et RH seulement).
    L'utilisateur référencé par user_id doit exister.
    Le manager_id doit correspondre à un utilisateur avec le rôle manager.
    """
    # Vérifier que l'utilisateur existe
    user = db.query(User).filter(User.id == employee_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur avec l'id {employee_data.user_id} introuvable"
        )

    # Vérifier qu'il n'a pas déjà un profil employé
    existing = db.query(Employee).filter(Employee.user_id == employee_data.user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet utilisateur a déjà un profil employé"
        )

    # Vérifier le département
    if employee_data.department_id:
        dept = db.query(Department).filter(Department.id == employee_data.department_id).first()
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Département avec l'id {employee_data.department_id} introuvable"
            )

    # Vérifier le poste
    if employee_data.position_id:
        pos = db.query(Position).filter(Position.id == employee_data.position_id).first()
        if not pos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Poste avec l'id {employee_data.position_id} introuvable"
            )

    if employee_data.manager_id:
        manager = db.query(User).filter(
            User.id == employee_data.manager_id,
            User.role == RoleEnum.MANAGER,
            User.is_active == True
        ).first()
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'utilisateur id={employee_data.manager_id} n'est pas un manager actif"
            )

    employee = Employee(
        user_id=employee_data.user_id,
        department_id=employee_data.department_id,
        position_id=employee_data.position_id,
        manager_id=employee_data.manager_id,
        salary=employee_data.salary,
        hire_date=employee_data.hire_date,
        departure_date=employee_data.departure_date,
        status=employee_data.status,
        date_naissance=employee_data.date_naissance,
        nationalite=employee_data.nationalite,
        adresse=employee_data.adresse,
        numero_telephone=employee_data.numero_telephone,
        sexe=employee_data.sexe
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER, RoleEnum.MEDECINE_TRAVAIL, RoleEnum.DIRECTION]))
):
    """
    Lister tous les employés avec leurs informations de département et poste.
    - Admin et RH : tous les employés (avec salaires), filtré pour RH
    - Manager : seulement les employés de son équipe (sans salaires)
    """
    if current_user.role == RoleEnum.MANAGER:
        manager_profile = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        
        query = db.query(Employee).filter(Employee.manager_id == current_user.id)
        if manager_profile and manager_profile.department_id:
            query = query.filter(Employee.department_id == manager_profile.department_id)
            
        employees = query.all()
        result = []
        for emp in employees:
            emp_data = EmployeeResponse.model_validate(emp)
            emp_data.salary = None
            result.append(emp_data)
        return result

    return db.query(Employee).all()


@router.get("/me", response_model=EmployeeResponse)
def get_my_employee_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtenir sa propre fiche employé (département, poste, manager, statut).
    Accessible à tous les utilisateurs authentifiés.
    Le salaire est masqué sauf pour Admin et RH.
    """
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vous n'avez pas encore de profil employé associé à votre compte."
        )

    emp_data = EmployeeResponse.model_validate(employee)

    # Masquer le salaire si non-admin et non-RH
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH]:
        emp_data.salary = None

    return emp_data


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER, RoleEnum.DIRECTION]))
):
    """Obtenir le détail d'un employé (Admin, RH et Manager de l'employé)"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employé introuvable"
        )

    if current_user.role == RoleEnum.MANAGER:
        if employee.manager_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé. Cet employé ne fait pas partie de votre équipe."
            )
        emp_data = EmployeeResponse.model_validate(employee)
        emp_data.salary = None
        return emp_data

    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Supprimer un profil employé (Admin et RH seulement)"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employé introuvable"
        )



    db.delete(employee)
    db.commit()
    return None


@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """
    Mettre à jour le profil d'un employé (Admin et RH seulement).
    Seuls les champs fournis sont modifiés (PATCH partiel).
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employé introuvable"
        )



    update_data = employee_data.model_dump(exclude_unset=True)

    if "department_id" in update_data:
        dept_id = update_data["department_id"]
        if dept_id is not None:
            dept = db.query(Department).filter(Department.id == dept_id).first()
            if not dept:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Département id={dept_id} introuvable"
                )
        employee.department_id = dept_id

    if "position_id" in update_data:
        pos_id = update_data["position_id"]
        if pos_id is not None:
            pos = db.query(Position).filter(Position.id == pos_id).first()
            if not pos:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Poste id={pos_id} introuvable"
                )
        employee.position_id = pos_id

    if "manager_id" in update_data:
        mgr_id = update_data["manager_id"]
        if mgr_id is not None and mgr_id != employee.manager_id:
            manager = db.query(User).filter(
                User.id == mgr_id,
                User.role == RoleEnum.MANAGER,
                User.is_active == True
            ).first()
            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"L'utilisateur id={mgr_id} n'est pas un manager actif"
                )
        employee.manager_id = mgr_id

    # Appliquer le reste des champs
    simple_fields = ["salary", "hire_date", "departure_date", "status", "date_naissance", "nationalite", "adresse", "numero_telephone", "sexe"]
    for field in simple_fields:
        if field in update_data:
            setattr(employee, field, update_data[field])

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee
