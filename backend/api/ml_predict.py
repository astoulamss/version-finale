"""
api/ml_predict.py — Endpoint de prédiction IA (Option A : Déclenchement manuel)

Route : POST /api/ml/predict/{employee_id}
Accès : RH, Direction, Admin uniquement

Logique :
  1. Récupère les données réelles de l'employé depuis la DB
  2. Calcule des features (jours de maladie, heures sup, ancienneté...)
  3. Passe les données aux 3 modèles .pkl
  4. Sauvegarde les scores dans la table risk_scores
  5. Retourne les 3 probabilités + niveaux de risque RH
"""

import os
import joblib
import pandas as pd
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.db import get_db
from models.user import User, RoleEnum
from models.employees import Employee, Department, Position
from models.ml_features import PerformanceReview, Timesheet, SalaryHistory
from models.features import RiskScore, SurveyResponse, SurveyAnswer, SurveyQuestion
from models.absences import Absence
from core.security import get_current_user, require_role
from core.ai_recommender import generate_recommendations
from core.alert_trigger import check_and_trigger_alerts

router = APIRouter(prefix="/api/ml", tags=["ML Predictions"])

# ─── Chargement des modèles au démarrage (une seule fois en mémoire) ───────────
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "")
MODELS = {}

def load_models():
    """Charge les 3 modèles .pkl depuis le disque."""
    global MODELS
    model_files = {
        "turnover":     "/app/model_turnover.pkl",
        "burnout":      "/app/model_burnout.pkl",
        "disengagement":"/app/model_disengagement.pkl",
    }
    for name, path in model_files.items():
        if os.path.exists(path):
            MODELS[name] = joblib.load(path)
        else:
            raise FileNotFoundError(f"Modele introuvable : {path}")

# Charger les modeles au démarrage du module
try:
    load_models()
    print("[ML] Les 3 modeles IA charges avec succes.")
except FileNotFoundError as e:
    print(f"[ML] ATTENTION : {e}")


# ─── Seuils métier RH ──────────────────────────────────────────────────────────
def classify_risk(probability: float) -> str:
    if probability >= 0.75:
        return "HIGH"
    elif probability >= 0.55:
        return "MEDIUM"
    else:
        return "LOW"


# ─── Préparation des features depuis la DB ────────────────────────────────────
def build_employee_features(employee: Employee, db: Session) -> dict:
    """
    Construit un dictionnaire de features à partir des données réelles de la DB.
    Correspond exactement aux colonnes utilisées lors de l'entraînement.
    """
    today = date.today()

    # Ancienneté en années
    tenure_years = 0
    if employee.hire_date:
        tenure_years = (today - employee.hire_date).days // 365

    # Salaire mensuel
    monthly_salary = float(employee.salary) if employee.salary else 3000.0

    # Département et poste
    dept_name = employee.department.name if employee.department else "Autre"
    pos_title = employee.position.title if employee.position else "Agent"
    distance_km = employee.distance_from_home_km or 15

    # Dernière note d'entretien
    last_review = (
        db.query(PerformanceReview)
        .filter(PerformanceReview.employee_id == employee.id)
        .order_by(PerformanceReview.review_date.desc())
        .first()
    )
    performance_rating = last_review.performance_rating if last_review else 3

    # Jours d'absence maladie (12 derniers mois)
    from datetime import datetime
    one_year_ago_dt = datetime(today.year - 1, today.month, today.day)
    absences = db.query(Absence).filter(
        Absence.employee_id == employee.user_id,
        Absence.start_date >= one_year_ago_dt
    ).all()
    sick_days = 0
    for a in absences:
        if a.end_date and a.start_date:
            delta = a.end_date - a.start_date
            sick_days += max(1, delta.days)

    # Heures supplémentaires et moyenne mensuelle (12 derniers mois)
    timesheets = db.query(Timesheet).filter(
        Timesheet.employee_id == employee.id,
        Timesheet.date >= one_year_ago_dt.date()
    ).all()
    
    overtime_count = sum(1 for t in timesheets if t.is_overtime)
    overtime = "Yes" if overtime_count > 5 else "No"
    
    total_hours = sum(float(t.hours_worked) for t in timesheets if t.hours_worked)
    months_worked = max(1, (today - (employee.hire_date or today)).days // 30)
    months_worked = min(12, months_worked) # max 12 months
    avg_monthly_hours = int(total_hours / months_worked) if timesheets else 151

    # Augmentation de salaire (SalaryHistory)
    salary_history = db.query(SalaryHistory).filter(SalaryHistory.employee_id == employee.id).order_by(SalaryHistory.effective_date.desc()).all()
    percent_salary_hike = 12
    if len(salary_history) > 0 and salary_history[0].old_salary and salary_history[0].new_salary:
        if salary_history[0].old_salary > 0:
            percent_salary_hike = int(((salary_history[0].new_salary - salary_history[0].old_salary) / salary_history[0].old_salary) * 100)

    # Scores de satisfaction (neutres si pas de données)
    work_life_balance_score = 3
    environment_satisfaction = 3
    job_satisfaction = 3
    relationship_satisfaction = 3
    
    # Remplacement par les vraies données d'enquête
    latest_responses = db.query(SurveyResponse).filter(SurveyResponse.employee_id == employee.user_id).order_by(SurveyResponse.submitted_at.desc()).limit(10).all()
    if latest_responses:
        for resp in latest_responses:
            answers = db.query(SurveyAnswer).filter(SurveyAnswer.response_id == resp.id).all()
            for ans in answers:
                q = db.query(SurveyQuestion).filter(SurveyQuestion.id == ans.question_id).first()
                if q and q.question_type == "rating" and ans.score is not None:
                    q_text = q.question.lower()
                    if "équilibre" in q_text or "work-life" in q_text:
                        work_life_balance_score = float(ans.score)
                    elif "environnement" in q_text or "environment" in q_text:
                        environment_satisfaction = float(ans.score)
                    elif "job" in q_text or "travail" in q_text or "satisfait" in q_text or "satisfaction" in q_text:
                        job_satisfaction = float(ans.score)
                    elif "relation" in q_text or "collègue" in q_text or "manager" in q_text:
                        relationship_satisfaction = float(ans.score)

    # Formations dans les 12 derniers mois (utilisation directe si disponible)
    training_times = 2  # valeur neutre par défaut

    # --- NOUVEAU: Comptage des tâches assignées non terminées ---
    from models.features import ManagerTask, OnboardingTask, OffboardingTask
    
    assigned_tasks_count = 0
    assigned_tasks_count += db.query(ManagerTask).filter(ManagerTask.assigned_to == employee.user_id, ManagerTask.status != "done").count()
    assigned_tasks_count += db.query(OnboardingTask).filter(OnboardingTask.assigned_to == employee.user_id, OnboardingTask.status != "done").count()
    assigned_tasks_count += db.query(OffboardingTask).filter(OffboardingTask.assigned_to == employee.user_id, OffboardingTask.status != "done").count()

    return {
        "distance_from_home_km":   distance_km,
        "department":              dept_name,
        "job_role":                pos_title,
        "monthly_salary":          monthly_salary,
        "percent_salary_hike":     percent_salary_hike,
        "tenure_in_years":         tenure_years,
        "training_times_last_year":training_times,
        "work_life_balance_score": work_life_balance_score,
        "environment_satisfaction":environment_satisfaction,
        "job_satisfaction":        job_satisfaction,
        "relationship_satisfaction":relationship_satisfaction,
        "overtime":                overtime,
        "avg_monthly_hours":       avg_monthly_hours,
        "sick_leave_days_last_year":sick_days,
        "performance_rating":      performance_rating,
        "assigned_tasks_count":    assigned_tasks_count,
    }


# ─── Endpoint principal ────────────────────────────────────────────────────────
@router.post("/predict/{employee_id}")
def predict_employee_risk(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL]))
):
    """
    Déclenche une prédiction IA manuelle pour un employé donné.
    Retourne les 3 scores de risque : Turnover, Burnout, Désengagement.
    Accessible uniquement aux RH, Admins et Direction.
    """
    if not MODELS:
        raise HTTPException(
            status_code=503,
            detail="Les modeles IA ne sont pas charges sur le serveur. Verifiez les fichiers .pkl."
        )

    # Récupérer l'employé
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employe introuvable.")

    # Construire les features
    features = build_employee_features(employee, db)
    df = pd.DataFrame([features])

    # Obtenir les probabilités de chaque modèle
    turnover_proba     = float(MODELS["turnover"].predict_proba(df)[0][1])
    burnout_proba      = float(MODELS["burnout"].predict_proba(df)[0][1])
    disengagement_proba = float(MODELS["disengagement"].predict_proba(df)[0][1])

    # Sauvegarder dans la table risk_scores
    risk_entry = RiskScore(
        employee_id=employee.user_id,
        turnover_risk=round(turnover_proba * 100, 2),
        burnout_risk=round(burnout_proba * 100, 2),
        engagement_risk=round(disengagement_proba * 100, 2),
    )
    db.add(risk_entry)
    db.commit()
    db.refresh(risk_entry)

    check_and_trigger_alerts(
        employee_id=employee.user_id,
        turnover_risk=turnover_proba,
        burnout_risk=burnout_proba,
        disengagement_risk=disengagement_proba,
        features=features,
        db=db
    )

    # Génération des recommandations expertes
    recommendations = generate_recommendations(features, turnover_proba, burnout_proba, disengagement_proba)

    # Réponse complète avec niveaux de risque RH et recommandations
    response_data = {
        "employee_id": employee_id,
        "generated_at": risk_entry.generated_at,
        "features_used": features,
        "predictions": {
            "turnover": {
                "probability": round(turnover_proba * 100, 1),
                "risk_level":  classify_risk(turnover_proba),
                "label":       "Risque de Demission"
            },
            "burnout": {
                "probability": round(burnout_proba * 100, 1),
                "risk_level":  classify_risk(burnout_proba),
                "label":       "Risque de Burnout"
            },
            "disengagement": {
                "probability": round(disengagement_proba * 100, 1),
                "risk_level":  classify_risk(disengagement_proba),
                "label":       "Risque de Desengagement"
            }
        },
        "recommendations": recommendations
    }

    if current_user.role in [RoleEnum.DIRECTION]:
        response_data["predictions"].pop("burnout", None)
        response_data["recommendations"] = [
            r for r in recommendations 
            if "burnout" not in r.get("title", "").lower() and "burnout" not in r.get("description", "").lower()
        ]

    return response_data


@router.get("/predict/{employee_id}/history")
def get_prediction_history(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL]))
):
    """
    Retourne l'historique de toutes les prédictions IA pour un employé.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employe introuvable.")

    scores = (
        db.query(RiskScore)
        .filter(RiskScore.employee_id == employee.user_id)
        .order_by(RiskScore.generated_at.desc())
        .limit(10)
        .all()
    )

    return [
        {
            "id": s.id,
            "generated_at": s.generated_at,
            "turnover_risk": float(s.turnover_risk) if s.turnover_risk else None,
            "burnout_risk": float(s.burnout_risk) if s.burnout_risk else None,
            "engagement_risk": float(s.engagement_risk) if s.engagement_risk else None,
        }
        for s in scores
    ]


# ─── Fonctions Globales et Automatisation ─────────────────────────────────────

def run_global_predictions(db: Session):
    """
    Parcourt tous les employés actifs et met à jour leurs scores de risque IA.
    Utilisé par le endpoint manuel ET par la tâche cron nocturne.
    """
    if not MODELS:
        print("[ML] Erreur : Modèles non chargés pour la prédiction globale.")
        return 0

    # On récupère tous les employés actifs
    employees = db.query(Employee).filter(Employee.status == "active").all()
    count = 0
    
    for emp in employees:
        try:
            features = build_employee_features(emp, db)
            df = pd.DataFrame([features])
            
            turnover_proba     = float(MODELS["turnover"].predict_proba(df)[0][1])
            burnout_proba      = float(MODELS["burnout"].predict_proba(df)[0][1])
            disengagement_proba = float(MODELS["disengagement"].predict_proba(df)[0][1])
            
            risk_entry = RiskScore(
                employee_id=emp.user_id,
                turnover_risk=round(turnover_proba * 100, 2),
                burnout_risk=round(burnout_proba * 100, 2),
                engagement_risk=round(disengagement_proba * 100, 2),
            )
            db.add(risk_entry)
            
            check_and_trigger_alerts(
                employee_id=emp.user_id,
                turnover_risk=turnover_proba,
                burnout_risk=burnout_proba,
                disengagement_risk=disengagement_proba,
                features=features,
                db=db
            )
            
            count += 1
        except Exception as e:
            print(f"[ML] Erreur sur employé {emp.id}: {e}")
            
    db.commit()
    return count

@router.post("/predict-all")
def trigger_global_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL, RoleEnum.MANAGER]))
):
    """
    Déclenche manuellement l'analyse IA de tous les employés.
    """
    if not MODELS:
        raise HTTPException(status_code=503, detail="Modèles IA non chargés.")
        
    count = run_global_predictions(db)
    return {"message": f"Prédictions générées pour {count} employés."}


@router.post("/predict-nlp")
def trigger_nlp_pipeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.DIRECTION]))
):
    """
    Déclenche manuellement l'analyse NLP des logs Chatbot pour tous les employés.
    """
    from ai.services.nlp_analyzer import run_nightly_nlp_pipeline
    try:
        count = run_nightly_nlp_pipeline(db)
        return {"message": f"Analyse NLP terminée. Profils mis à jour : {count}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/global-stats")
def get_global_ai_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL, RoleEnum.MANAGER]))
):
    """
    Retourne les statistiques IA globales pour le dashboard analytique.
    Si l'utilisateur est un manager, filtre uniquement sur son département.
    """
    manager_emp = None
    if current_user.role == RoleEnum.MANAGER:
        manager_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()

    # Sous-requête pour avoir le DERNIER score de chaque employé
    subquery = (
        db.query(
            RiskScore.employee_id,
            func.max(RiskScore.generated_at).label("latest_date")
        )
        .group_by(RiskScore.employee_id)
        .subquery()
    )
    
    query = (
        db.query(RiskScore, Employee)
        .join(subquery, (RiskScore.employee_id == subquery.c.employee_id) & (RiskScore.generated_at == subquery.c.latest_date))
        .join(Employee, Employee.user_id == RiskScore.employee_id)
        .filter(Employee.status == "active")
    )

    if current_user.role == RoleEnum.MANAGER:
        query = query.filter(Employee.manager_id == current_user.id)
        if manager_emp and manager_emp.department_id:
            query = query.filter(Employee.department_id == manager_emp.department_id)

    latest_scores = query.all()
    
    if not latest_scores:
        return {"message": "Aucune donnée"}
        
    # Aggrégations pour les graphiques
    turnover_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    burnout_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    disengagement_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    
    dept_stats = {}
    
    risk_list = []

    for score, emp in latest_scores:
        if emp.user and emp.user.role in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION]:
            continue
            
        t_risk = float(score.turnover_risk) if score.turnover_risk else 0
        b_risk = float(score.burnout_risk) if score.burnout_risk else 0
        d_risk = float(score.engagement_risk) if score.engagement_risk else 0
        
        turnover_levels[classify_risk(t_risk/100)] += 1
        burnout_levels[classify_risk(b_risk/100)] += 1
        disengagement_levels[classify_risk(d_risk/100)] += 1
        
        dept_name = emp.department.name if emp.department else "Sans département"
        if dept_name not in dept_stats:
            dept_stats[dept_name] = {"turnover": [], "burnout": [], "disengagement": []}
            
        dept_stats[dept_name]["turnover"].append(t_risk)
        dept_stats[dept_name]["burnout"].append(b_risk)
        dept_stats[dept_name]["disengagement"].append(d_risk)
        
        composite_risk = (t_risk + b_risk + d_risk) / 3
        risk_list.append({
            "employee_id": emp.id,
            "user_id": emp.user_id,
            "prenom": "Collaborateur" if current_user.role == RoleEnum.MANAGER else (emp.user.prenom if emp.user else "Inconnu"),
            "nom": "anonymisé" if current_user.role == RoleEnum.MANAGER else (emp.user.nom if emp.user else "Inconnu"),
            "department": dept_name,
            "composite_risk": round(composite_risk, 1),
            "turnover_risk": t_risk,
            "burnout_risk": b_risk,
            "disengagement_risk": d_risk
        })
        
    dept_averages = []
    for d_name, lists in dept_stats.items():
        dept_averages.append({
            "department": d_name,
            "turnover": round(sum(lists["turnover"])/len(lists["turnover"]), 1) if lists["turnover"] else 0,
            "burnout": round(sum(lists["burnout"])/len(lists["burnout"]), 1) if lists["burnout"] else 0,
            "disengagement": round(sum(lists["disengagement"])/len(lists["disengagement"]), 1) if lists["disengagement"] else 0,
            "count": len(lists["turnover"])
        })
        
    top_risk = sorted(risk_list, key=lambda x: x["composite_risk"], reverse=True)[:10]

    for tr in top_risk:
        emp = db.query(Employee).filter(Employee.id == tr["employee_id"]).first()
        if emp:
            features = build_employee_features(emp, db)
            recs = generate_recommendations(
                features, 
                tr["turnover_risk"] / 100, 
                tr["burnout_risk"] / 100, 
                tr["disengagement_risk"] / 100
            )
            if current_user.role in [RoleEnum.DIRECTION]:
                tr["recommendations"] = [
                    r for r in recs 
                    if "burnout" not in r.get("title", "").lower() and "burnout" not in r.get("description", "").lower()
                ]
            elif current_user.role == RoleEnum.MEDECINE_TRAVAIL:
                tr["recommendations"] = [
                    r for r in recs 
                    if "burnout" in r.get("title", "").lower() or "burnout" in r.get("description", "").lower() or "santé" in r.get("description", "").lower()
                ]
            else:
                tr["recommendations"] = recs
        else:
            tr["recommendations"] = []

    return {
        "total_analyzed": len(latest_scores),
        "distribution": {
            "turnover": turnover_levels,
            "burnout": burnout_levels,
            "disengagement": disengagement_levels
        },
        "departments": dept_averages,
        "top_risk_employees": top_risk
    }
