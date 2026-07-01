from sqlalchemy.orm import Session
from models.features import Alert, AlertStatusEnum
from models.user import RoleEnum
from core.ai_recommender import generate_recommendations
from utils.notifications import notify_role, notify_manager

def check_and_trigger_alerts(employee_id: int, turnover_risk: float, burnout_risk: float, disengagement_risk: float, features: dict, db: Session):
    """
    Vérifie si les risques dépassent le seuil critique (70%).
    turnover_risk, burnout_risk, disengagement_risk sont attendus entre 0.0 et 1.0
    Si oui, crée une alerte automatique (si elle n'existe pas déjà)
    et notifie les RH et le Manager.
    """
    THRESHOLD = 0.70
    
    high_risks = []
    if turnover_risk >= THRESHOLD:
        high_risks.append(("Risque de Démission (Turnover)", "turnover", turnover_risk * 100))
    if burnout_risk >= THRESHOLD:
        high_risks.append(("Risque de Burnout", "burnout", burnout_risk * 100))
    if disengagement_risk >= THRESHOLD:
        high_risks.append(("Risque de Désengagement", "disengagement", disengagement_risk * 100))
        
    if not high_risks:
        return
        
    # generate recommendations (attend des probabilités entre 0 et 1)
    recs = generate_recommendations(features, turnover_risk, burnout_risk, disengagement_risk)
    
    for risk_title, risk_type, risk_value in high_risks:
        # Check if an unresolved alert already exists for this employee and risk type
        existing = db.query(Alert).filter(
            Alert.employee_id == employee_id,
            Alert.alert_type == risk_title,
            Alert.status.in_([AlertStatusEnum.NEW, AlertStatusEnum.IN_PROGRESS])
        ).first()
        
        if not existing:
            # Build description from AI recommender
            type_recs = [r for r in recs if r["type"] == risk_type or r["type"] == "general"]
            desc = f"L'IA a détecté un risque estimé à {risk_value:.1f}%. "
            if type_recs:
                desc += "Analyse : " + " ".join([r["description"] for r in type_recs])
                
            new_alert = Alert(
                employee_id=employee_id,
                alert_type=risk_title,
                severity="high",
                description=desc,
                status=AlertStatusEnum.NEW
            )
            db.add(new_alert)
            db.commit()
            
            # Notifier RH, Direction et Manager
            msg = f"Alerte IA critique ({risk_title} à {risk_value:.1f}%) déclenchée pour un employé."
            notify_role(db, RoleEnum.RH, msg)
            notify_role(db, RoleEnum.DIRECTION, msg)
            notify_manager(db, employee_id, msg)
            
            # Notifier Médecine du Travail uniquement pour le Burnout
            if risk_type == "burnout":
                notify_role(db, RoleEnum.MEDECINE_TRAVAIL, msg)
