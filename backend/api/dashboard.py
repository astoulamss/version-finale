from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.user import User, RoleEnum
from models.features import Leave, LeaveStatusEnum, Document, Contract, Formation
from models.absences import Absence
from models.employees import Employee
from models.audit_log import AuditLog
from models.system_alerts import SystemAlert, SystemAlertStatusEnum
from models.chatbot import ChatbotLog
from api.workflows import get_blocked_workflows
from sqlalchemy import desc, or_
from schemas.user import DashboardResponse, StatsResponse
from database.db import get_db
from core.security import get_current_user, require_role
from typing import List
from pydantic import BaseModel
from datetime import datetime
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/admin/cockpit")
def get_admin_cockpit(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN]))
):
    """
    Retourne les données pour le Cockpit Admin (page d'accueil).
    """
    # 1. Dernières actions sensibles
    sensitive_logs = db.query(AuditLog).filter(
        or_(
            AuditLog.severity.in_(["HIGH", "CRITICAL"]),
            AuditLog.status == "FAILURE"
        )
    ).order_by(desc(AuditLog.created_at)).limit(4).all()
    
    sensitive_actions = [{
        "action": log.action,
        "user_email": log.user_email or "Inconnu",
        "created_at": log.created_at.isoformat(),
        "severity": log.severity
    } for log in sensitive_logs]

    # 2. Alertes non traitées
    unresolved_alerts = db.query(SystemAlert).filter(
        SystemAlert.status != SystemAlertStatusEnum.RESOLVED
    ).order_by(desc(SystemAlert.created_at)).limit(3).all()
    
    alerts_list = [{
        "category": "Système",
        "message": alert.title,
        "severity": alert.severity.value if hasattr(alert.severity, 'value') else alert.severity,
        "created_at": alert.created_at.isoformat()
    } for alert in unresolved_alerts]

    # 3. Workflows bloqués
    all_blocked = get_blocked_workflows(db=db, current_user=current_user)
    blocked_workflows = all_blocked[:3]

    # 4. Requêtes Chatbot risquées
    # Handle both string and enum if applicable
    risky_chatbot_logs = db.query(ChatbotLog).filter(
        or_(
            ChatbotLog.risk_level == "Signalé",
            ChatbotLog.risk_level == "Dangereux"
        )
    ).order_by(desc(ChatbotLog.created_at)).limit(2).all()
    
    risky_queries = [{
        "user_email": log.user.email if log.user else "anon_user",
        "query": log.query,
        "risk_level": log.risk_level
    } for log in risky_chatbot_logs]

    # 5. Counts globaux pour le Cockpit
    total_unresolved_alerts = db.query(SystemAlert).filter(
        SystemAlert.status != SystemAlertStatusEnum.RESOLVED
    ).count()

    from datetime import timedelta, timezone
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)
    total_chatbot_24h = db.query(ChatbotLog).filter(
        ChatbotLog.created_at >= last_24h
    ).count()

    total_blocked_workflows = len(all_blocked)

    active_users = db.query(User).filter(User.is_active == True).count()
    critical_alerts = db.query(SystemAlert).filter(
        SystemAlert.status != SystemAlertStatusEnum.RESOLVED,
        SystemAlert.severity.in_(["HIGH", "CRITICAL"])
    ).count()

    return {
        "user_name": f"{current_user.prenom} {current_user.nom}",
        "message": "Bienvenue sur le dashboard administrateur. Vous avez accès à la gestion complète du système.",
        "kpis": {
            "active_users": active_users,
            "critical_alerts": critical_alerts,
            "ai_conversations_24h": total_chatbot_24h,
            "blocked_workflows": total_blocked_workflows
        },
        "unresolved_alerts": [
            {
                "id": alert.id,
                "title": alert.title,
                "severity": alert.severity.value if hasattr(alert.severity, 'value') else alert.severity,
                "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M") if alert.created_at else ""
            } for alert in unresolved_alerts
        ],
        "flagged_queries": [
            {
                "id": log.id,
                "user_email": log.user.email if log.user else "anonyme",
                "query": log.query,
                "risk_level": log.risk_level
            } for log in risky_chatbot_logs
        ]
    }

# Dashboard Admin
@router.get("/admin", response_model=DashboardResponse)
def admin_dashboard(current_user: User = Depends(require_role([RoleEnum.ADMIN]))):
    """
    Dashboard pour les administrateurs
    
    Accès:
    - Gestion complète du système
    - Création et modification des utilisateurs
    - Gestion des rôles et permissions
    - Rapports et audits
    """
    return {
        "role": "admin",
        "user_name": f"{current_user.prenom} {current_user.nom}",
        "first_login": current_user.first_login,
        "message": "Bienvenue sur le dashboard administrateur. Vous avez accès à la gestion complète du système."
    }


@router.get("/manager/cockpit")
def get_manager_cockpit(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.DIRECTION]))
):
    """
    Retourne les données agrégées pour le Cockpit Manager.
    """
    # Find team members
    from models.employees import Employee
    from models.features import Leave, LeaveStatusEnum, Alert, AlertStatusEnum, RiskScore, Recommendation, HrTicket, OnboardingPlan, OnboardingTask
    from models.absences import Absence
    from sqlalchemy import desc, func
    from datetime import date, datetime, timedelta
    
    # 1. Équipe
    team_employees = db.query(Employee).filter(Employee.manager_id == current_user.id).all()
    
    # Fallback seulement s'il n'a pas d'équipe ET n'est pas un simple manager
    if not team_employees and current_user.role != RoleEnum.MANAGER:
        team_employees = db.query(Employee).limit(10).all()
        
    # Restrict to the same department as the manager to avoid cross-department bleeding
    manager_emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if manager_emp and manager_emp.department_id:
        team_employees = [emp for emp in team_employees if emp.department_id == manager_emp.department_id]
        
    team_user_ids = [e.user_id for e in team_employees]
    
    # KPIs
    effectif = len(team_employees)
    actifs = len([e for e in team_employees if e.status == 'active'])
    
    # On détermine "en congé" basiquement
    today = date.today()
    leaves_today = db.query(Leave).filter(
        Leave.employee_id.in_(team_user_ids),
        Leave.status == 'approved',
        Leave.start_date <= today,
        Leave.end_date >= today
    ).count()
    en_conge = leaves_today
    
    # 2. Demandes en attente (Congés et Absences) qui ne sont pas dépassées
    pending_leaves = db.query(Leave).filter(
        Leave.employee_id.in_(team_user_ids), 
        Leave.status == 'pending',
        Leave.end_date >= today
    ).all()
    
    pending_absences = db.query(Absence).filter(
        Absence.employee_id.in_(team_user_ids),
        Absence.status == 'pending',
        Absence.end_date >= today
    ).all()
    
    leaves_data = []
    for l in pending_leaves:
        leaves_data.append({
            "id": l.id,
            "req_type": "leave",
            "employee_id": l.employee_id,
            "employee_initials": "".join([part[0] for part in (l.employee.prenom + " " + l.employee.nom).split() if part]).upper() if l.employee else "??",
            "employee_name": f"{l.employee.prenom} {l.employee.nom}" if l.employee else "Inconnu",
            "start_date": l.start_date.isoformat() if l.start_date else None,
            "end_date": l.end_date.isoformat() if l.end_date else None,
            "duration": (l.end_date - l.start_date).days + 1 if l.end_date and l.start_date else 0,
            "leave_type": l.leave_type
        })
        
    absences_data = []
    for a in pending_absences:
        duration = 0
        if a.start_date and a.end_date:
            delta = a.end_date - a.start_date
            duration = max(1, int(delta.total_seconds() / 86400)) # approximate days
            
        absences_data.append({
            "id": a.id,
            "req_type": "absence",
            "employee_id": a.employee_id,
            "employee_initials": "".join([part[0] for part in (a.user.prenom + " " + a.user.nom).split() if part]).upper() if hasattr(a, 'user') and a.user else "??",
            "employee_name": f"{a.user.prenom} {a.user.nom}" if hasattr(a, 'user') and a.user else "Inconnu",
            "start_date": a.start_date.isoformat() if a.start_date else None,
            "end_date": a.end_date.isoformat() if a.end_date else None,
            "duration": duration,
            "leave_type": "Absence: " + (a.absence_type.value if hasattr(a.absence_type, 'value') else str(a.absence_type))
        })
        
    leaves_data.sort(key=lambda x: x["start_date"] if x["start_date"] else "")
    absences_data.sort(key=lambda x: x["start_date"] if x["start_date"] else "")
    
    # 3. Absences (mois en cours)
    start_of_month = datetime(today.year, today.month, 1)
    absences = db.query(Absence).filter(
        Absence.employee_id.in_(team_user_ids),
        Absence.start_date >= start_of_month
    ).all()
    
    absences_by_emp = {}
    for a in absences:
        if a.employee_id not in absences_by_emp:
            absences_by_emp[a.employee_id] = {"hours": 0.0, "name": f"{a.user.prenom} {a.user.nom}" if hasattr(a, 'user') and a.user else "Inconnu"}
        if a.start_date and a.end_date:
            delta = a.end_date - a.start_date
            hours = max(0.0, delta.total_seconds() / 3600.0)
            absences_by_emp[a.employee_id]["hours"] += hours
            
    absences_list = [{"employee_id": k, "name": v["name"], "hours": v["hours"]} for k, v in absences_by_emp.items()]
    absences_list.sort(key=lambda x: x["hours"], reverse=True)
    
    # 4. Alertes équipe
    active_alerts = db.query(Alert).filter(
        Alert.employee_id.in_(team_user_ids),
        Alert.status.in_(['NEW', 'IN_PROGRESS']),
        Alert.alert_type.ilike('%Désengagement%')
    ).order_by(desc(Alert.created_at)).all()
    
    urgent_alerts = len([a for a in active_alerts if a.severity in ['HIGH', 'CRITICAL']])
    
    alerts_data = [{
        "id": a.id,
        "employee_name": f"{a.employee.prenom} {a.employee.nom}" if a.employee else "Inconnu",
        "alert_type": a.alert_type,
        "severity": a.severity,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "description": a.description
    } for a in active_alerts[:5]]
    
    # 5. Engagement & Risques
    engagement_sum = 0
    past_engagement_sum = 0
    valid_scores_count = 0
    valid_past_scores_count = 0
    risk_scores_data = []
    
    thirty_days_ago_dt = datetime.combine(today - timedelta(days=30), datetime.min.time())
    
    for emp in team_employees:
        latest_risk = db.query(RiskScore).filter(RiskScore.employee_id == emp.user_id).order_by(desc(RiskScore.generated_at)).first()
        if latest_risk:
            eng_score = 100 - float(latest_risk.engagement_risk or 0)
            engagement_sum += eng_score
            valid_scores_count += 1
            
            risk_scores_data.append({
                "employee_id": emp.user_id,
                "employee_name": "Collaborateur anonymisé" if current_user.role == RoleEnum.MANAGER else (f"{emp.user.prenom} {emp.user.nom}" if emp.user else "Inconnu"),
                "risk_level": "Élevé" if latest_risk.engagement_risk and latest_risk.engagement_risk >= 75 else ("Moyen" if latest_risk.engagement_risk and latest_risk.engagement_risk >= 55 else "Faible"),
                "score": float(latest_risk.engagement_risk or 0)
            })
            
        past_risk = db.query(RiskScore).filter(
            RiskScore.employee_id == emp.user_id,
            RiskScore.generated_at < thirty_days_ago_dt
        ).order_by(desc(RiskScore.generated_at)).first()
        
        if past_risk:
            past_eng_score = 100 - float(past_risk.engagement_risk or 0)
            past_engagement_sum += past_eng_score
            valid_past_scores_count += 1
            
    avg_engagement = round(engagement_sum / valid_scores_count) if valid_scores_count > 0 else 0
    past_avg_engagement = round(past_engagement_sum / valid_past_scores_count) if valid_past_scores_count > 0 else avg_engagement
    
    diff = avg_engagement - past_avg_engagement
    trend_sign = "+" if diff > 0 else ""
    engagement_trend = f"{trend_sign}{diff}% ce mois" if valid_scores_count > 0 else "N/A"
    risk_scores_data.sort(key=lambda x: x["score"], reverse=True)
    
    # 6. Mon équipe
    active_team_employees = [e for e in team_employees if e.status == 'active' and (not hasattr(e, 'user') or not e.user or getattr(e.user, 'is_active', True) is not False)]
    team_data = [{
        "id": e.user_id,
        "initials": "".join([part[0] for part in (e.user.prenom + " " + e.user.nom).split() if part]).upper() if e.user else "??",
        "name": f"{e.user.prenom} {e.user.nom}" if e.user else "Inconnu",
        "position": e.position.title if e.position else "Membre"
    } for e in active_team_employees]
    
    # 7. Tickets RH
    tickets = db.query(HrTicket).filter(
        HrTicket.employee_id.in_(team_user_ids),
        HrTicket.status != 'closed'
    ).order_by(desc(HrTicket.created_at)).all()
    
    tickets_data = [{
        "id": t.id,
        "subject": t.subject,
        "status": t.status.value if hasattr(t.status, 'value') else t.status,
        "employee_initials": "".join([part[0] for part in (t.employee.prenom + " " + t.employee.nom).split() if part]).upper() if t.employee else "??"
    } for t in tickets[:5]]

    # 8. Onboarding
    onboarding_data = []
    for emp in team_employees:
        plan = db.query(OnboardingPlan).filter(
            OnboardingPlan.employee_id == emp.user_id,
            OnboardingPlan.status != 'completed'
        ).order_by(desc(OnboardingPlan.created_at)).first()
        
        if plan:
            tasks = db.query(OnboardingTask).filter(OnboardingTask.plan_id == plan.id).all()
            days_since = (today - emp.hire_date).days if emp.hire_date else (today - plan.start_date).days if plan.start_date else 0
            onboarding_data.append({
                "employee_name": f"{emp.user.prenom} {emp.user.nom}" if emp.user else "Inconnu",
                "days": max(0, days_since),
                "tasks": [
                    {
                        "name": t.title,
                        "done": t.status == 'done'
                    } for t in tasks
                ]
            })

    total_absence_hours = sum(v["hours"] for v in absences_by_emp.values())
    total_expected_hours = effectif * 168 # Approx 21 days * 8h
    absence_rate_val = round((total_absence_hours / total_expected_hours) * 100) if total_expected_hours > 0 else 0
    
    return {
        "kpis": {
            "effectif_total": effectif,
            "actifs": actifs,
            "en_conge": en_conge,
            "pending_requests": len(leaves_data),
            "avg_delay_days": 1.2,
            "active_alerts_total": len(active_alerts),
            "urgent_alerts": urgent_alerts,
            "avg_engagement": avg_engagement,
            "engagement_trend": engagement_trend,
            "absence_rate": f"{absence_rate_val}%"
        },
        "pending_leaves": leaves_data,
        "pending_absences_reqs": absences_data,
        "absences": absences_list,
        "alerts": alerts_data,
        "team_members": team_data,
        "onboarding": onboarding_data,
        "risk_scores": risk_scores_data[:3],
        "tickets": tickets_data
    }


# Dashboard Collaborateur (Employé)
@router.get("/collaborateur", response_model=DashboardResponse)
def collaborateur_dashboard(current_user: User = Depends(require_role([RoleEnum.COLLABORATEUR]))):
    """
    Dashboard pour les collaborateurs (employés)
    
    Accès:
    - Profil personnel
    - Congés
    - Documents personnels
    - Formations
    - Chatbot RH
    """
    return {
        "role": "collaborateur",
        "user_name": f"{current_user.prenom} {current_user.nom}",
        "first_login": current_user.first_login,
        "message": "Bienvenue sur votre dashboard employé. Vous pouvez consulter vos congés, documents, formations et accéder au chatbot RH."
    }


# Dashboard Direction
@router.get("/direction", response_model=DashboardResponse)
def direction_dashboard(current_user: User = Depends(require_role([RoleEnum.DIRECTION]))):
    """
    Dashboard pour la direction
    
    Accès:
    - Tableaux de bord stratégiques
    - Prévisions RH
    - KPI globaux
    - Analyses prédictives
    """
    return {
        "role": "direction",
        "user_name": f"{current_user.prenom} {current_user.nom}",
        "first_login": current_user.first_login,
        "message": "Bienvenue sur le dashboard direction. Vous avez une vue stratégique avec les KPI globaux, prévisions RH et analyses prédictives."
    }


# Dashboard Manager
@router.get("/manager", response_model=DashboardResponse)
def manager_dashboard(current_user: User = Depends(require_role([RoleEnum.MANAGER]))):
    """
    Dashboard pour les managers
    
    Accès:
    - Tout ce que peut faire un employé (profil, congés, documents, formations, chatbot RH)
    - Validation des congés de l'équipe
    - Suivi de son équipe
    - Évaluations
    - Indicateurs de son équipe
    """
    return {
        "role": "manager",
        "user_name": f"{current_user.prenom} {current_user.nom}",
        "first_login": current_user.first_login,
        "message": "Bienvenue sur votre dashboard manager. Vous pouvez gérer votre équipe, valider les congés et suivre les indicateurs."
    }


# Dashboard RH
@router.get("/rh", response_model=DashboardResponse)
def rh_dashboard(current_user: User = Depends(require_role([RoleEnum.RH]))):
    """
    Dashboard pour les RH
    
    Accès:
    - Gestion des employés (consultation et modification des profils)
    - Contrats
    - Onboarding
    - Offboarding
    - Génération de documents
    - Reporting RH
    """
    return {
        "role": "rh",
        "user_name": f"{current_user.prenom} {current_user.nom}",
        "first_login": current_user.first_login,
        "message": "Bienvenue sur le dashboard RH. Vous pouvez gérer les employés, contrats, onboarding/offboarding et générer des documents."
    }


# Dashboard Médecine du Travail
@router.get("/medecine-travail", response_model=DashboardResponse)
def medecine_travail_dashboard(current_user: User = Depends(require_role([RoleEnum.MEDECINE_TRAVAIL]))):
    """
    Dashboard pour la médecine du travail
    
    Accès:
    - Statistiques d'absentéisme
    - Alertes sur les risques psychosociaux
    - Indicateurs de surcharge de travail
    - Données agrégées sur la santé au travail
    - Tableaux de bord de prévention
    - Gestion des salaires
    - Gestion des contrats
    - Données financières RH
    """
    return {
        "role": "medecine_travail",
        "user_name": f"{current_user.prenom} {current_user.nom}",
        "first_login": current_user.first_login,
        "message": "Bienvenue sur le dashboard médecine du travail. Vous pouvez consulter l'absentéisme, les risques psychosociaux, la surcharge de travail et les données de santé au travail."
    }



# Route générique pour rediriger vers le dashboard selon le rôle
@router.get("/home", response_model=DashboardResponse)
def get_dashboard(current_user: User = Depends(get_current_user)):
    """
    Rediriger l'utilisateur vers son dashboard selon son rôle
    """
    role_messages = {
        RoleEnum.ADMIN: "Bienvenue sur le dashboard administrateur. Vous avez accès à la gestion complète du système.",
        RoleEnum.COLLABORATEUR: "Bienvenue sur votre dashboard. Vous pouvez consulter vos congés, documents, formations et accéder au chatbot RH.",
        RoleEnum.DIRECTION: "Bienvenue sur le dashboard direction. Vous avez une vue stratégique avec les KPI globaux et analyses prédictives.",
        RoleEnum.MANAGER: "Bienvenue sur votre dashboard manager. Vous pouvez gérer votre équipe, valider les congés et suivre les indicateurs.",
        RoleEnum.RH: "Bienvenue sur le dashboard RH. Vous pouvez gérer les employés, contrats, onboarding/offboarding et générer des documents.",
        RoleEnum.MEDECINE_TRAVAIL: "Bienvenue sur le dashboard médecine du travail. Vous pouvez consulter l'absentéisme, les risques psychosociaux et les données de santé.",
    }

    return {
        "role": current_user.role.value,
        "user_name": f"{current_user.prenom} {current_user.nom}",
        "first_login": current_user.first_login,
        "message": role_messages.get(current_user.role, "Bienvenue!")
    }


@router.get("/stats-debug")
def get_stats_debug(db: Session = Depends(get_db)):
    return {
        "total_contracts": db.query(Contract).count(),
        "total_documents": db.query(Document).count()
    }

@router.get("/stats", response_model=StatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION]))
):
    """
    Statistiques globales du système pour le tableau de bord.
    Accessible à l'Admin et au RH uniquement.

    Retourne :
    - **total_users** : nombre total d'utilisateurs actifs
    - **total_employees** : nombre de profils employés
    - **leaves_pending** : congés en attente de validation
    - **leaves_approved** : congés approuvés
    - **total_absences** : nombre total d'absences enregistrées
    - **total_documents** : nombre total de documents générés
    - **total_contracts** : nombre total de contrats
    """
    user_query = db.query(User).filter(User.is_active == True)
    employee_query = db.query(Employee).filter(Employee.status == 'active')
    leave_pending_query = db.query(Leave).filter(Leave.status == LeaveStatusEnum.PENDING)
    leave_approved_query = db.query(Leave).filter(Leave.status == LeaveStatusEnum.APPROVED)
    absence_query = db.query(Absence)
    document_query = db.query(Document)
    contract_query = db.query(Contract)



    total_users = user_query.count()
    total_employees = employee_query.count()
    leaves_pending = leave_pending_query.count()
    leaves_approved = leave_approved_query.count()
    total_absences = absence_query.count()
    total_documents = document_query.count()
    total_contracts = contract_query.count()

    return StatsResponse(
        total_users=total_users,
        total_employees=total_employees,
        leaves_pending=leaves_pending,
        leaves_approved=leaves_approved,
        total_absences=total_absences,
        total_documents=total_documents,
        total_contracts=total_contracts
    )


# ---------------------------------------------------------------
# Analytics endpoint — Direction, Médecine du Travail, QVT
# ---------------------------------------------------------------

class LeaveAnalyticsItem(BaseModel):
    id: int
    employee_id: int
    start_date: str
    end_date: str
    leave_type: str
    status: str
    reason: str | None = None
    created_at: str

    class Config:
        from_attributes = True


@router.get("/analytics/leaves", response_model=List[LeaveAnalyticsItem])
def get_analytics_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([
        RoleEnum.DIRECTION,
        RoleEnum.MEDECINE_TRAVAIL,
        RoleEnum.ADMIN,
        RoleEnum.RH,
    ]))
):
    """
    Retourne toutes les demandes de congé pour les rôles stratégiques.
    Accessible à : Direction, Médecine du Travail, Responsable QVT, Admin, RH.
    """
    leaves = db.query(Leave).all()
    return [
        LeaveAnalyticsItem(
            id=l.id,
            employee_id=l.employee_id,
            start_date=str(l.start_date),
            end_date=str(l.end_date),
            leave_type=l.leave_type.value if hasattr(l.leave_type, 'value') else str(l.leave_type),
            status=l.status.value if hasattr(l.status, 'value') else str(l.status),
            reason=l.reason,
            created_at=l.created_at.isoformat() if isinstance(l.created_at, datetime) else str(l.created_at),
        )
        for l in leaves
    ]

@router.get("/workload-stats")
def get_workload_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION, RoleEnum.MEDECINE_TRAVAIL]))
):
    """
    Retourne le total des tâches actives (Manager, Onboarding, Offboarding)
    pour calculer la surcharge de travail.
    """
    from models.features import ManagerTask, OnboardingTask, OffboardingTask, TaskStatusEnum
    
    manager_tasks = db.query(ManagerTask).filter(ManagerTask.status != TaskStatusEnum.DONE, ManagerTask.status != TaskStatusEnum.CANCELLED).count()
    onboarding_tasks = db.query(OnboardingTask).filter(OnboardingTask.status != 'done').count()
    offboarding_tasks = db.query(OffboardingTask).filter(OffboardingTask.status != 'done').count()
    
    total_active_tasks = manager_tasks + onboarding_tasks + offboarding_tasks
    
    return {
        "active_tasks": total_active_tasks,
        "manager_tasks": manager_tasks,
        "onboarding_tasks": onboarding_tasks,
        "offboarding_tasks": offboarding_tasks
    }

