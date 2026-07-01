import os
os.environ['PYTHONUTF8'] = '1'
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from models.user import User
from models.features import Alert, AlertStatusEnum, Recommendation, RiskScore
from models.employees import Employee

def seed():
    db = SessionLocal()
    try:
        # Get a real employee
        emp = db.query(Employee).first()
        if not emp:
            print("Aucun employé trouvé.")
            return

        # Add Risk Score
        risk = RiskScore(
            employee_id=emp.user_id,
            turnover_risk=75.5,
            burnout_risk=85.0,
            engagement_risk=60.0
        )
        db.add(risk)
        db.flush()
        
        # Add Recommendations
        rec1 = Recommendation(
            employee_id=emp.user_id,
            risk_score_id=risk.id,
            recommendation="Planifier un entretien de suivi d'urgence (1:1)."
        )
        rec2 = Recommendation(
            employee_id=emp.user_id,
            risk_score_id=risk.id,
            recommendation="Proposer quelques jours de congés ou d'allègement de charge."
        )
        db.add_all([rec1, rec2])

        # Add Alerts
        alert1 = Alert(
            employee_id=emp.user_id,
            alert_type="Risque de Burnout",
            severity="High",
            description="Le collaborateur a accumulé beaucoup d'heures supplémentaires et son score d'engagement est en chute libre sur la dernière enquête.",
            status=AlertStatusEnum.NEW
        )
        alert2 = Alert(
            employee_id=emp.user_id,
            alert_type="Baisse de motivation",
            severity="Medium",
            description="L'employé est dans la même position depuis plus de 3 ans sans évolution salariale.",
            status=AlertStatusEnum.IN_PROGRESS
        )
        db.add_all([alert1, alert2])
        
        db.commit()
        print("Fausses alertes ajoutées avec succès dans la base de données !")
    except Exception as e:
        print(f"Erreur: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
