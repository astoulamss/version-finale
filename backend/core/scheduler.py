from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database.db import SessionLocal
from api.ml_predict import run_global_predictions
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def nightly_ml_predictions():
    """Tâche nocturne exécutant les prédictions IA sur tous les employés actifs."""
    logger.info("Début de l'analyse globale IA nocturne...")
    db = SessionLocal()
    try:
        count = run_global_predictions(db)
        logger.info(f"Analyse globale IA terminée. {count} employés mis à jour.")
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse globale IA: {e}")
    finally:
        db.close()

def start_scheduler():
    """Démarre le scheduler et enregistre les tâches."""
    # Exécuter tous les jours à minuit
    scheduler.add_job(
        nightly_ml_predictions,
        CronTrigger(hour=0, minute=0),
        id="nightly_ml_predictions",
        name="Mise à jour nocturne des scores IA",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler APScheduler démarré avec succès.")

def stop_scheduler():
    """Arrête le scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler APScheduler arrêté.")
