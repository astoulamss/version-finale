from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User
from schemas.user import LoginRequest, TokenResponse, UserResponse
from core.security import verify_password, create_access_token, get_current_user
from utils.audit_service import log_action, get_client_info, AuditAction, AuditSeverity, AuditStatus

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(login_request: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authentifier un utilisateur et retourner un JWT token
    """
    client = get_client_info(request)

    # Rechercher l'utilisateur
    user = db.query(User).filter(User.email == login_request.email).first()

    # Vérifier l'utilisateur et le mot de passe
    if not user or not verify_password(login_request.mots_de_passe, user.mots_de_passe):
        # Audit : connexion échouée
        log_action(
            db=db,
            action=AuditAction.USER_LOGIN_FAILED,
            severity=AuditSeverity.MEDIUM,
            status=AuditStatus.FAILURE,
            user_email=login_request.email,
            resource=f"Auth",
            details={"reason": "Identifiants incorrects", "email_attempted": login_request.email},
            **client,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    # Vérifier si l'utilisateur est actif
    if not user.is_active:
        log_action(
            db=db,
            action=AuditAction.USER_LOGIN_FAILED,
            severity=AuditSeverity.MEDIUM,
            status=AuditStatus.FAILURE,
            user_id=user.id,
            user_email=user.email,
            resource=f"User#{user.id}",
            details={"reason": "Compte désactivé"},
            **client,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cet utilisateur est désactivé"
        )

    # Créer le JWT token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id, "role": user.role.value})

    # Audit : connexion réussie
    log_action(
        db=db,
        action=AuditAction.USER_LOGIN_SUCCESS,
        severity=AuditSeverity.LOW,
        status=AuditStatus.SUCCESS,
        user_id=user.id,
        user_email=user.email,
        resource=f"User#{user.id}",
        details={"role": user.role.value},
        **client,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Rafraîchir le JWT token pour un utilisateur actif
    """
    access_token = create_access_token(data={"sub": current_user.email, "user_id": current_user.id, "role": current_user.role.value})

    log_action(
        db=db,
        action=AuditAction.TOKEN_REFRESH,
        severity=AuditSeverity.LOW,
        status=AuditStatus.SUCCESS,
        user_id=current_user.id,
        user_email=current_user.email,
        resource=f"User#{current_user.id}",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": current_user
    }

from fastapi.security import HTTPAuthorizationCredentials
from core.security import security, ACCESS_TOKEN_EXPIRE_MINUTES
from core.cache import add_token_to_blocklist

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Déconnecter un utilisateur en ajoutant son token à la blocklist Redis.
    """
    token = credentials.credentials
    # Convertir les minutes en secondes pour Redis
    expire_in_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    await add_token_to_blocklist(token, expire_in_seconds)

    log_action(
        db=db,
        action=AuditAction.USER_LOGOUT,
        severity=AuditSeverity.LOW,
        status=AuditStatus.SUCCESS,
        user_id=current_user.id,
        user_email=current_user.email,
        resource=f"User#{current_user.id}",
    )

    return {"message": "Déconnexion réussie"}
