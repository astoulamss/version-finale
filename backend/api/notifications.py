from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User
from models.notification import Notification, BroadcastMessage, UserDevice
from schemas.notification import NotificationResponse, ExpoTokenRegister, UserDeviceResponse
from core.security import get_current_user, require_role
from models.user import RoleEnum
from pydantic import BaseModel
from typing import List, Optional

class BroadcastRequest(BaseModel):
    message: str
    user_id: Optional[int] = None
    target_role: Optional[str] = None

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationResponse])
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtenir toutes les notifications in-app de l'utilisateur connecté (triées par les plus récentes).
    """
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()
    return notifications


@router.put("/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marquer toutes les notifications non lues de l'utilisateur comme lues.
    Utile pour un bouton « Tout marquer comme lu » côté front-end.
    """
    updated = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).all()

    count = len(updated)
    for notif in updated:
        notif.is_read = True

    db.commit()
    return {"message": f"{count} notification(s) marquée(s) comme lue(s)."}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marquer une notification spécifique comme lue.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification introuvable."
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprimer une notification spécifique de son flux.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification introuvable."
        )

    db.delete(notification)
    db.commit()
    return None

@router.post("/broadcast", status_code=status.HTTP_201_CREATED)
def broadcast_notification(
    data: BroadcastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION, RoleEnum.ADMIN]))
):
    """
    Créer une notification. 
    Si user_id est fourni, envoie uniquement à cet utilisateur.
    Si target_role est fourni, envoie à tous les utilisateurs de ce rôle.
    Sinon, envoie à tous les utilisateurs actifs.
    """
    count = 0
    
    if data.user_id:
        # Envoi ciblé à un utilisateur
        target_user = db.query(User).filter(User.id == data.user_id, User.is_active == True).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Utilisateur cible introuvable ou inactif.")
        
        notification = Notification(
            user_id=target_user.id,
            message=data.message,
            is_read=False
        )
        db.add(notification)
        count = 1
    elif data.target_role:
        # Envoi ciblé à un rôle
        try:
            role_enum = RoleEnum(data.target_role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Rôle invalide.")
            
        users = db.query(User).filter(User.role == role_enum, User.is_active == True).all()
        for u in users:
            notification = Notification(
                user_id=u.id,
                message=data.message,
                is_read=False
            )
            db.add(notification)
            count += 1
    else:
        # Envoi global
        users = db.query(User).filter(User.is_active == True).all()
        for u in users:
            notification = Notification(
                user_id=u.id,
                message=data.message,
                is_read=False
            )
            db.add(notification)
            count += 1
        
    # Log the broadcast message
    broadcast_log = BroadcastMessage(
        message=data.message,
        target_role=data.target_role,
        target_user_id=data.user_id,
        sender_id=current_user.id,
        recipient_count=count
    )
    db.add(broadcast_log)
    db.commit()
    return {"message": f"Message envoyé à {count} utilisateur(s)."}

@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Nombre de notifications non lues — utilisé pour le badge push."""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    return {"unread_count": count}


@router.post("/register-device", response_model=UserDeviceResponse, status_code=status.HTTP_200_OK)
def register_device(
    payload: ExpoTokenRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enregistre ou met à jour le token Expo push de l'appareil de l'utilisateur.
    Appelé au démarrage de l'app après obtention de la permission.
    """
    device = db.query(UserDevice).filter(
        UserDevice.expo_push_token == payload.token
    ).first()

    if device:
        device.user_id = current_user.id
        device.platform = payload.platform
    else:
        device = UserDevice(
            user_id=current_user.id,
            expo_push_token=payload.token,
            platform=payload.platform,
        )
        db.add(device)

    db.commit()
    db.refresh(device)
    return device


@router.delete("/unregister-device", status_code=status.HTTP_204_NO_CONTENT)
def unregister_device(
    payload: ExpoTokenRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprime le token push au logout pour ne plus recevoir de notifications."""
    db.query(UserDevice).filter(
        UserDevice.expo_push_token == payload.token,
        UserDevice.user_id == current_user.id
    ).delete()
    db.commit()


@router.get("/broadcast-history")
def get_broadcast_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION, RoleEnum.ADMIN]))
):
    """
    Obtenir l'historique des messages diffusés.
    """
    history = db.query(BroadcastMessage).order_by(BroadcastMessage.created_at.desc()).all()
    result = []
    for h in history:
        sender = db.query(User).filter(User.id == h.sender_id).first()
        target_user = None
        if h.target_user_id:
            target_user = db.query(User).filter(User.id == h.target_user_id).first()
        
        result.append({
            "id": h.id,
            "message": h.message,
            "target_role": h.target_role,
            "target_user": f"{target_user.prenom} {target_user.nom}" if target_user else None,
            "sender": f"{sender.prenom} {sender.nom}" if sender else f"#{h.sender_id}",
            "created_at": h.created_at,
            "recipient_count": h.recipient_count
        })
    return result
