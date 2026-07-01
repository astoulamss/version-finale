from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.db import get_db
from core.cache import is_token_blocklisted
import os

load_dotenv()

# Configuration du hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Schéma de sécurité Bearer (partagé par tous les routers)
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hacher un mot de passe"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifier un mot de passe"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Créer un JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """Décoder un JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"DEBUG: JWTError - {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Dépendance pour obtenir l'utilisateur courant à partir du JWT token.
    Centralisée ici pour éviter les imports croisés entre les routers.
    """
    from models.user import User  # Import local pour éviter les cycles potentiels

    token = credentials.credentials
    
    # Vérifier si le token est révoqué (logout)
    if await is_token_blocklisted(token):
        print("DEBUG: Token blocklisted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée ou déconnectée",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")
    user_id = payload.get("user_id")

    if not email or not user_id:
        print("DEBUG: missing email or user_id in payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        print("DEBUG: User not found in DB")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé",
        )

    return user


def require_role(required_roles: list | None = None):
    """
    Dépendance factory pour vérifier le rôle de l'utilisateur.
    Usage : Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
    """
    def check_role(
        request: Request,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if required_roles is not None and current_user.role not in required_roles:
            # Notify ADMIN and RH of the unauthorized access attempt
            from utils.notifications import notify_role
            from models.user import RoleEnum
            
            path = request.url.path
            msg = f"⚠️ Alerte de sécurité : {current_user.prenom} {current_user.nom} (Rôle: {current_user.role.value}) a tenté d'accéder sans autorisation à la ressource {path}."
            try:
                notify_role(db, RoleEnum.ADMIN, msg)
                notify_role(db, RoleEnum.RH, msg)
            except Exception as e:
                print("Erreur notification accès refusé:", e)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Rôles requis : {', '.join([r.value for r in required_roles])}",
            )
        return current_user

    return check_role
