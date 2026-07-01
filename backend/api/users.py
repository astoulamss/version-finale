from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from database.db import get_db
from models.user import User, RoleEnum
from schemas.user import UserResponse, UserUpdate, UserCreate, PasswordChangeRequest, AdminPasswordReset
from core.security import hash_password, verify_password
from api.dashboard import get_current_user
from utils.email_service import send_welcome_email, send_reset_password_email
from utils.audit_service import log_action, AuditAction, AuditSeverity, AuditStatus

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer un nouvel utilisateur (Admin seulement).
    Un email contenant les identifiants est automatiquement envoyé au nouvel utilisateur.
    """
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seul l'Admin peut créer des utilisateurs."
        )

    # Vérifier si l'utilisateur existe déjà
    db_user = db.query(User).filter(User.email == user_create.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà enregistré"
        )

    # Garder le mot de passe en clair pour l'email AVANT de le hasher
    plain_password = user_create.mots_de_passe

    # Créer le nouvel utilisateur
    new_user = User(
        nom=user_create.nom,
        prenom=user_create.prenom,
        email=user_create.email,
        mots_de_passe=hash_password(plain_password),
        role=user_create.role,
        is_active=True,
        first_login=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Audit : création d'utilisateur
    log_action(
        db=db,
        action=AuditAction.USER_CREATED,
        severity=AuditSeverity.HIGH,
        status=AuditStatus.SUCCESS,
        user_id=current_user.id,
        user_email=current_user.email,
        resource=f"User#{new_user.id}",
        details={"created_email": new_user.email, "created_role": new_user.role.value, "created_name": f"{new_user.prenom} {new_user.nom}"},
    )

    # Envoyer l'email de bienvenue en arrière-plan (ne bloque pas la réponse)
    background_tasks.add_task(
        send_welcome_email,
        prenom=new_user.prenom,
        nom=new_user.nom,
        email=new_user.email,
        password=plain_password,
        role=new_user.role.value
    )

    return new_user


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Obtenir le profil de l'utilisateur courant
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour le profil de l'utilisateur courant (Admin seulement)
    """
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seul l'Admin peut modifier son profil."
        )
    
    # Mettre à jour les champs fournis
    update_data = user_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user


@router.put("/me/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Changer le mot de passe de l'utilisateur connecté
    """
    # Vérifier l'ancien mot de passe
    if not verify_password(password_data.old_password, current_user.mots_de_passe):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'ancien mot de passe est incorrect"
        )
    
    # Hacher et sauvegarder le nouveau mot de passe
    current_user.mots_de_passe = hash_password(password_data.new_password)
    current_user.first_login = False   # ← plus jamais redirigé vers la page de changement
    db.add(current_user)
    db.commit()

    # Audit : changement de mot de passe
    log_action(
        db=db,
        action=AuditAction.PASSWORD_CHANGED,
        severity=AuditSeverity.MEDIUM,
        status=AuditStatus.SUCCESS,
        user_id=current_user.id,
        user_email=current_user.email,
        resource=f"User#{current_user.id}",
    )

    return {"message": "Mot de passe modifié avec succès"}


@router.get("/", response_model=list[UserResponse])
def list_users(
    search: Optional[str] = None,
    role: Optional[RoleEnum] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lister les utilisateurs selon le rôle :
    - Admin : tous les utilisateurs (filtrable par recherche/rôle)
    - RH : uniquement les collaborateurs et managers (filtrable par recherche/rôle)
    """
    if current_user.role not in [
        RoleEnum.ADMIN,
        RoleEnum.RH,
        RoleEnum.DIRECTION,
        RoleEnum.MEDECINE_TRAVAIL
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seuls Admin, RH et les rôles stratégiques peuvent voir la liste des utilisateurs."
        )

    query = db.query(User)

    # Appliquer le filtre par rôle
    if role is not None:
        query = query.filter(User.role == role)

    # Appliquer le filtre de recherche (nom, prenom, email)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                User.nom.ilike(search_filter),
                User.prenom.ilike(search_filter),
                User.email.ilike(search_filter)
            )
        )

    return query.all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtenir les détails d'un utilisateur
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Un utilisateur ne peut voir ses détails que s'il est admin, RH, un rôle stratégique ou si c'est lui-même
    if current_user.id != user_id and current_user.role not in [
        RoleEnum.ADMIN,
        RoleEnum.RH,
        RoleEnum.DIRECTION,
        RoleEnum.MEDECINE_TRAVAIL
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour un utilisateur (Admin seulement)
    """
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seul l'Admin peut modifier les profils des utilisateurs."
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    update_data = user_update.model_dump(exclude_unset=True)

    old_values = {field: getattr(user, field, None) for field in update_data}
    for field, value in update_data.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit : modification d'utilisateur
    log_action(
        db=db,
        action=AuditAction.USER_UPDATED,
        severity=AuditSeverity.MEDIUM,
        status=AuditStatus.SUCCESS,
        user_id=current_user.id,
        user_email=current_user.email,
        resource=f"User#{user_id}",
        details={"updated_fields": list(update_data.keys()), "target_email": user.email},
    )

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Désactiver un utilisateur (Admin seulement)
    """
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seul l'Admin peut supprimer des utilisateurs."
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Au lieu de supprimer, désactiver
    user.is_active = False
    db.add(user)
    db.commit()

    # Audit : désactivation de compte
    log_action(
        db=db,
        action=AuditAction.USER_DEACTIVATED,
        severity=AuditSeverity.HIGH,
        status=AuditStatus.SUCCESS,
        user_id=current_user.id,
        user_email=current_user.email,
        resource=f"User#{user_id}",
        details={"target_email": user.email, "target_name": f"{user.prenom} {user.nom}"},
    )

    return None


@router.delete("/{user_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer DÉFINITIVEMENT un utilisateur (Admin seulement)
    Supprime toutes ses données liées pour respecter les contraintes de clés étrangères.
    """
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seul l'Admin peut supprimer définitivement des utilisateurs."
        )
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    from sqlalchemy import text

    # Les tables où une référence à l'utilisateur peut être mise à NULL
    tables_to_nullify = [
        ("departments", "manager_id"),
        ("hr_tickets", "assigned_to"),
        ("leaves", "approved_by"),
        ("offboarding_tasks", "assigned_to"),
        ("onboarding_tasks", "assigned_to"),
        ("history_logs", "performed_by"),
        ("chatbot_logs", "user_id"),
        ("chatbot_messages", "user_id"),
        ("employees", "manager_id"),
        ("workflow_configs", "validator_user_id"),
    ]

    # Les tables où la ligne doit être supprimée car elle dépend de l'utilisateur
    tables_to_delete = [
        ("absences", "employee_id"),
        ("alerts", "employee_id"),
        ("approval_workflows", "approver_id"),
        ("chatbot_conversations", "user_id"),
        ("contracts", "user_id"),
        ("documents", "employee_id"),
        ("documents", "created_by"),
        ("hr_tickets", "employee_id"),
        ("leave_balances", "employee_id"),
        ("leaves", "employee_id"),
        ("manager_tasks", "created_by"),
        ("manager_tasks", "assigned_to"),
        ("notifications", "user_id"),
        ("offboarding_plans", "employee_id"),
        ("onboarding_plans", "employee_id"),
        ("risk_scores", "employee_id"),
        ("survey_responses", "employee_id"),
        ("alert_history", "performed_by"),
        ("offboarding_feedbacks", "author_id"),
        ("onboarding_feedbacks", "author_id"),
        ("recommendations", "employee_id"),
        ("formation_enrollments", "employee_id"),
        ("offboarding_tasks", "assigned_to"), # Parfois null, mais si c'est assigné, supprimons ? Non, nullable=True ! On a mis dans nullify.
        # Enlevons offboarding_tasks ici.
        ("employees", "user_id"),
        ("performance_reviews", "evaluator_id"),
    ]

    try:
        # Récupérer l'ID de l'employé associé s'il existe et nettoyer ses tables enfants
        emp_res = db.execute(text("SELECT id FROM employees WHERE user_id = :uid"), {"uid": user_id}).fetchone()
        if emp_res:
            emp_id = emp_res[0]
            db.execute(text("DELETE FROM performance_reviews WHERE employee_id = :eid"), {"eid": emp_id})
            db.execute(text("DELETE FROM salary_history WHERE employee_id = :eid"), {"eid": emp_id})
            db.execute(text("DELETE FROM timesheets WHERE employee_id = :eid"), {"eid": emp_id})

        # Nullifier les références (les relations non bloquantes)
        for table, col in tables_to_nullify:
            db.execute(text(f"UPDATE {table} SET {col} = NULL WHERE {col} = :uid"), {"uid": user_id})
        
        # Supprimer les dépendances fortes
        for table, col in tables_to_delete:
            db.execute(text(f"DELETE FROM {table} WHERE {col} = :uid"), {"uid": user_id})

        # Enfin, supprimer l'utilisateur
        deleted_email = user.email
        deleted_name = f"{user.prenom} {user.nom}"
        db.delete(user)
        db.commit()

        # Audit : suppression définitive (CRITICAL)
        log_action(
            db=db,
            action=AuditAction.USER_DELETED,
            severity=AuditSeverity.CRITICAL,
            status=AuditStatus.SUCCESS,
            user_id=current_user.id,
            user_email=current_user.email,
            resource=f"User#{user_id}",
            details={"deleted_email": deleted_email, "deleted_name": deleted_name, "permanent": True},
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression : {str(e)}"
        )

    return None



@router.post("/{user_id}/reset-password", status_code=status.HTTP_200_OK)
def admin_reset_password(
    user_id: int,
    data: AdminPasswordReset,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Réinitialiser le mot de passe d'un utilisateur (Admin seulement).
    Utile lors de l'onboarding ou si l'utilisateur a oublié son mot de passe.
    L'utilisateur devra changer son mot de passe à sa prochaine connexion (first_login = True).
    """
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Seul l'Admin peut réinitialiser les mots de passe."
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe doit contenir au moins 8 caractères."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    from core.security import hash_password as _hash
    user.mots_de_passe = _hash(data.new_password)
    user.first_login = True  # Forcer le changement de mot de passe à la reconnexion
    db.add(user)
    db.commit()

    # Audit : réinitialisation de mot de passe par admin
    log_action(
        db=db,
        action=AuditAction.PASSWORD_RESET_ADMIN,
        severity=AuditSeverity.HIGH,
        status=AuditStatus.SUCCESS,
        user_id=current_user.id,
        user_email=current_user.email,
        resource=f"User#{user_id}",
        details={"target_email": user.email, "target_name": f"{user.prenom} {user.nom}"},
    )

    # Planifier l'envoi de l'email avec le nouveau mot de passe temporaire
    background_tasks.add_task(
        send_reset_password_email,
        prenom=user.prenom,
        nom=user.nom,
        email=user.email,
        password=data.new_password
    )

    return {
        "message": f"Mot de passe réinitialisé avec succès pour {user.prenom} {user.nom}. L'utilisateur devra le changer à sa prochaine connexion."
    }
