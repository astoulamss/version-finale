import httpx
from sqlalchemy.orm import Session
from models.notification import Notification, UserDevice


# ── Titre intelligent à partir du message ────────────────────────────────────

def _infer_title(message: str) -> str:
    msg = message.lower()
    if any(k in msg for k in ["congé", "conge", "leave", "absence"]):
        return "Congés & Absences"
    if any(k in msg for k in ["document", "contrat", "contract", "attestation", "pdf"]):
        return "Documents"
    if any(k in msg for k in ["formation", "training"]):
        return "Formations"
    if any(k in msg for k in ["onboarding", "intégration"]):
        return "Onboarding"
    if any(k in msg for k in ["offboarding", "départ"]):
        return "Offboarding"
    if any(k in msg for k in ["tâche", "task", "todo"]):
        return "Tâches"
    if any(k in msg for k in ["alerte", "alert", "risque", "burnout", "sécurité"]):
        return "Alerte"
    if any(k in msg for k in ["sondage", "survey"]):
        return "Sondage"
    if any(k in msg for k in ["paie", "salaire", "salary"]):
        return "Paie"
    return "Notification RH"


# ── Envoi push via Expo Push API ─────────────────────────────────────────────

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_expo_push(tokens: list, title: str, body: str, data: dict | None = None):
    """Envoie une notification push Expo à une liste de tokens."""
    if not tokens:
        return

    messages = [
        {
            "to": token,
            "title": title,
            "body": body[:255],
            "data": data or {},
            "sound": "default",
            "priority": "high",
        }
        for token in tokens
        if token and token.startswith("ExponentPushToken")
    ]

    if not messages:
        return

    try:
        with httpx.Client(timeout=10.0) as client:
            client.post(
                EXPO_PUSH_URL,
                json=messages,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
    except Exception as e:
        print(f"[Push] Erreur envoi Expo: {e}")


def _get_user_tokens(db: Session, user_id: int) -> list:
    devices = db.query(UserDevice).filter(UserDevice.user_id == user_id).all()
    return [d.expo_push_token for d in devices]


# ── API publique ─────────────────────────────────────────────────────────────

def create_notification(db: Session, user_id: int, message: str):
    """Crée une notification in-app ET envoie un push si l'utilisateur a un appareil enregistré."""
    notification = Notification(user_id=user_id, message=message, is_read=False)
    db.add(notification)
    db.commit()
    db.refresh(notification)

    tokens = _get_user_tokens(db, user_id)
    if tokens:
        send_expo_push(tokens, title=_infer_title(message), body=message)

    return notification


def notify_role(db: Session, role: str, message: str):
    """Notifie tous les utilisateurs d'un rôle (in-app + push)."""
    from models.user import User
    users = db.query(User).filter(User.role == role, User.is_active == True).all()
    for user in users:
        create_notification(db, user.id, message)


def notify_manager(db: Session, employee_user_id: int, message: str):
    """Notifie le manager direct d'un collaborateur (in-app + push)."""
    from models.employees import Employee
    employee = db.query(Employee).filter(Employee.user_id == employee_user_id).first()
    if employee and employee.manager_id:
        create_notification(db, employee.manager_id, message)
