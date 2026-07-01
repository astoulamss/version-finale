"""
Script de configuration de la base de données
Lance les migrations et crée les tables
"""

from database.db import engine, Base
from models.user import User
from models.features import Leave, LeaveType, Document, Formation, Contract, DocumentType, FormationEnrollment, LeaveBalance, OnboardingPlan, OnboardingTask, OnboardingStep, OffboardingPlan, OffboardingTask, OffboardingFeedback, Survey, SurveyQuestion, SurveyResponse, SurveyAnswer, KpiSnapshot, RiskScore, WorkflowConfig
import os

from models.employees import Employee, Department, Position
from models.absences import Absence
from models.history import HistoryLog
from models.notification import Notification




def init_db():
    """Créer toutes les tables"""
    print("Création des tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables créées avec succès")

    # Initialiser les données de base
    from seed_data import run_seed
    run_seed()


def drop_db():
    """Supprimer toutes les tables (utiliser avec précaution)"""
    print("Suppression des tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ Tables supprimées avec succès")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            init_db()
        elif sys.argv[1] == "drop":
            if os.getenv("FORCE_DROP") == "1" or input("Êtes-vous sûr? (yes/no): ").lower() == "yes":
                drop_db()
            else:
                print("Opération annulée")
        else:
            print("Usage: python init_db.py [init|drop]")
    else:
        init_db()

