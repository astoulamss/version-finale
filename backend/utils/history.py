from sqlalchemy.orm import Session
from models.history import HistoryLog


def log_action(db: Session, record_type: str, record_id: int, action: str, performed_by: int, details: str):
    """
    Ajouter une entrée dans l'historique (audit logs).
    """
    log = HistoryLog(
        record_type=record_type,
        record_id=record_id,
        action=action,
        performed_by=performed_by,
        details=details
    )
    db.add(log)
    db.commit()
