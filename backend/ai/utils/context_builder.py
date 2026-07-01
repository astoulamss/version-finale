from sqlalchemy.orm import Session
from sqlalchemy import func, text
from models.user import User, RoleEnum
from models.features import (
    Document, DocumentStatusEnum, Contract, Formation, FormationEnrollment,
    OnboardingPlan, OnboardingTask, OnboardingStep, OnboardingFeedback,
    OffboardingPlan, OffboardingTask, OffboardingStep, OffboardingFeedback,
    RiskScore, Recommendation, Alert, AlertHistory,
    KpiSnapshot, Survey, SurveyQuestion, SurveyResponse, SurveyAnswer,
    HrTicket, ApprovalWorkflow,
    LeaveBalance, LeaveType,
)
from models.employees import Employee, Department, Position, EmployeeStatusEnum
from models.absences import Absence, AbsenceTypeEnum
from models.history import HistoryLog
from models.notification import Notification
from models.chatbot import ChatbotConversation, ChatbotLog
from datetime import date, datetime


def build_user_context(user: User, db: Session) -> dict:
    employee = db.query(Employee).filter(Employee.user_id == user.id).first()
    contract = db.query(Contract).filter(Contract.user_id == user.id).first()

    context = {
        "user": {
            "id": user.id,
            "nom": user.nom,
            "prenom": user.prenom,
            "email": user.email,
            "role": user.role.value if user.role else "unknown",
            "is_active": user.is_active,
        }
    }

    if employee:
        context["employee"] = {
            "id": employee.id,
            "status": employee.status.value if employee.status else "unknown",
            "salary": str(employee.salary) if employee.salary else None,
        }
        if employee.department:
            context["employee"]["department"] = employee.department.name
        if employee.position:
            context["employee"]["position"] = employee.position.title
        if employee.manager:
            context["employee"]["manager"] = f"{employee.manager.prenom} {employee.manager.nom}"

    if contract:
        context["contract"] = {
            "type": contract.contract_type,
            "position": contract.position,
            "start_date": str(contract.start_date) if contract.start_date else None,
            "end_date": str(contract.end_date) if contract.end_date else None,
            "salary": contract.salary,
        }

    return context


def build_leave_context(user: User, db: Session) -> str:
    result = db.execute(
        text("SELECT l.id, lt.name as leave_type, l.start_date, l.end_date, l.status, l.reason, l.approved_by, l.created_at "
             "FROM leaves l JOIN leave_types lt ON l.leave_type_id = lt.id WHERE l.employee_id = :eid ORDER BY l.created_at DESC LIMIT 10"),
        {"eid": user.id}
    )
    leaves = result.fetchall()
    if not leaves:
        return "No leave records found."

    lines = ["Your Leave Requests:"]
    for l in leaves:
        lines.append(
            f"- {l.leave_type}: {l.start_date} to {l.end_date} "
            f"[{l.status}]"
        )
    return "\n".join(lines)


def build_department_context(user: User, db: Session) -> str:
    employee = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not employee:
        return ""

    if user.role == RoleEnum.MANAGER:
        direct_reports = (
            db.query(Employee)
            .filter(Employee.manager_id == user.id)
            .all()
        )
        if not direct_reports:
            return "No direct reports found."
        lines = ["Your Direct Reports:"]
        for emp in direct_reports:
            dept_name = emp.department.name if emp.department else "N/A"
            pos_title = emp.position.title if emp.position else "N/A"
            lines.append(f"- {emp.user.prenom} {emp.user.nom} | {pos_title} ({dept_name})")
        return "\n".join(lines)

    if not employee.department_id:
        return ""

    dept_employees = (
        db.query(Employee)
        .filter(Employee.department_id == employee.department_id)
        .all()
    )
    lines = [f"Department ({employee.department.name if employee.department else 'N/A'}):"]
    for emp in dept_employees:
        pos = emp.position.title if emp.position else "N/A"
        lines.append(f"- {emp.user.prenom} {emp.user.nom} | {pos} ({emp.user.role.value})")
    return "\n".join(lines)


def build_rh_context(user: User, db: Session) -> str:
    if user.role not in (RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.MEDECINE_TRAVAIL):
        return ""
    lines = []

    # ── COUNTS OVERVIEW ──
    total_employees = db.query(Employee).count()
    total_users = db.query(User).count()
    total_departments = db.query(Department).count()
    total_positions = db.query(Position).count()
    total_contracts = db.query(Contract).count()
    total_leaves = db.execute(text("SELECT count(*) FROM leaves")).scalar()
    total_absences = db.execute(text("SELECT count(*) FROM absences")).scalar()
    total_formations = db.query(Formation).count()
    total_docs = db.query(Document).count()
    ai_docs = db.query(Document).filter(Document.generated_by_ai == True).count()
    pending_leaves = db.execute(text("SELECT count(*) FROM leaves WHERE status::text = 'PENDING'")).scalar()
    total_onboardings = db.query(OnboardingPlan).count()
    total_offboardings = db.query(OffboardingPlan).count()
    total_alerts = db.query(Alert).filter(Alert.status != "resolved").count()
    total_open_tickets = db.query(HrTicket).filter(HrTicket.status.in_(["open", "in_progress"])).count()
    total_surveys = db.query(Survey).count()

    lines.append("=== COMPANY OVERVIEW ===")
    lines.append(f"Users: {total_users} | Employees: {total_employees} | Departments: {total_departments} | Positions: {total_positions}")
    lines.append(f"Contracts: {total_contracts} | Leaves: {total_leaves} | Absences: {total_absences} | Formations: {total_formations}")
    lines.append(f"Documents (total): {total_docs} | AI-generated: {ai_docs} | Pending leaves: {pending_leaves}")
    lines.append(f"Onboardings: {total_onboardings} | Offboardings: {total_offboardings} | Active Alerts: {total_alerts} | Open Tickets: {total_open_tickets} | Surveys: {total_surveys}")
    lines.append("")

    # ── USERS & ROLES ──
    roles_result = db.execute(text("SELECT role::text, count(*) FROM users GROUP BY role ORDER BY role")).fetchall()
    lines.append("=== USERS BY ROLE ===")
    for r, c in roles_result:
        lines.append(f"- {r}: {c}")
    lines.append("")

    # ── DEPARTMENTS ──
    lines.append("=== DEPARTMENTS ===")
    depts = db.query(Department).all()
    for d in depts:
        cnt = db.query(Employee).filter(Employee.department_id == d.id).count()
        lines.append(f"- {d.name} ({cnt} employees): {d.description or ''}")
    lines.append("")

    # ── POSITIONS ──
    lines.append("=== POSITIONS ===")
    positions = db.query(Position).all()
    for p in positions:
        cnt = db.query(Employee).filter(Employee.position_id == p.id).count()
        lines.append(f"- {p.title} ({cnt} employees): {p.description or ''}")
    lines.append("")

    # ── ALL EMPLOYEES (full details) ──
    lines.append("=== ALL EMPLOYEES ===")
    employees_result = db.execute(
        text("SELECT e.id, e.user_id, e.salary, e.status::text, e.department_id, e.position_id, e.manager_id, "
             "u.prenom, u.nom, u.role::text, u.email, u.is_active, "
             "d.name as dept_name, p.title as pos_title, "
             "mu.prenom as m_prenom, mu.nom as m_nom "
             "FROM employees e "
             "JOIN users u ON u.id = e.user_id "
             "LEFT JOIN departments d ON d.id = e.department_id "
             "LEFT JOIN positions p ON p.id = e.position_id "
             "LEFT JOIN users mu ON mu.id = e.manager_id "
             "ORDER BY e.id")
    ).fetchall()
    for e in employees_result:
        sal = f"{float(e.salary):.2f} EUR" if e.salary else "N/A"
        manager_name = f"{e.m_prenom} {e.m_nom}" if e.m_prenom else "N/A"
        lines.append(f"- #{e.id} {e.prenom} {e.nom} | Role: {e.role} | {e.pos_title or 'N/A'} ({e.dept_name or 'N/A'}) | Status: {e.status} | Salary: {sal} | Manager: {manager_name} | Email: {e.email} | Active: {e.is_active}")
    lines.append("")

    # ── ALL CONTRACTS ──
    lines.append("=== ALL CONTRACTS ===")
    contracts = db.query(Contract).order_by(Contract.id).all()
    for c in contracts:
        u = db.query(User).filter(User.id == c.user_id).first()
        name = f"{u.prenom} {u.nom}" if u else "N/A"
        lines.append(f"- #{c.id} {name} | Type: {c.contract_type} | Position: {c.position} | Salary: {c.salary or 'N/A'} | Start: {c.start_date} | End: {c.end_date or 'N/A'}")
    lines.append("")

    # ── ALL LEAVES (full details) ──
    lines.append("=== ALL LEAVES ===")
    leaves_result = db.execute(
        text("SELECT l.id, l.employee_id, lt.name as leave_type, l.start_date, l.end_date, l.status, l.reason, l.approved_by, l.created_at "
             "FROM leaves l JOIN leave_types lt ON l.leave_type_id = lt.id ORDER BY l.created_at DESC")
    ).fetchall()
    for l in leaves_result:
        u = db.query(User).filter(User.id == l.employee_id).first()
        name = f"{u.prenom} {u.nom}" if u else "N/A"
        approved_by_name = "N/A"
        if l.approved_by:
            au = db.query(User).filter(User.id == l.approved_by).first()
            approved_by_name = f"{au.prenom} {au.nom}" if au else "N/A"
        lines.append(f"- #{l.id} {name} | Type: {l.leave_type} | {l.start_date} to {l.end_date} | Status: {l.status} | Approved by: {approved_by_name} | Reason: {l.reason or 'N/A'}")
    lines.append("")

    # ── ALL ABSENCES ──
    lines.append("=== ALL ABSENCES ===")
    absences_result = db.execute(
        text("SELECT id, employee_id, absence_type, start_date, end_date, reason, created_at "
             "FROM absences ORDER BY created_at DESC")
    ).fetchall()
    for a in absences_result:
        u = db.query(User).filter(User.id == a.employee_id).first()
        name = f"{u.prenom} {u.nom}" if u else "N/A"
        reason = a.reason or 'N/A'
        
        if str(a.absence_type).lower() == "maladie" and user.role != RoleEnum.MEDECINE_TRAVAIL:
            reason = "[Confidentiel Médical]"
            
        lines.append(f"- #{a.id} {name} | Type: {a.absence_type} | {a.start_date} to {a.end_date} | Reason: {reason}")
    lines.append("")

    # ── ALL FORMATIONS ──
    lines.append("=== ALL FORMATIONS ===")
    formations = db.query(Formation).order_by(Formation.id).all()
    for f in formations:
        enrolled = db.query(FormationEnrollment).filter(FormationEnrollment.formation_id == f.id).count()
        lines.append(f"- #{f.id} {f.title} | {f.start_date} to {f.end_date} | Enrolled: {enrolled} | {f.description or ''}")
        enrollments = db.query(FormationEnrollment).filter(FormationEnrollment.formation_id == f.id).all()
        for en in enrollments:
            eu = db.query(User).filter(User.id == en.employee_id).first()
            ename = f"{eu.prenom} {eu.nom}" if eu else "N/A"
            lines.append(f"  * {ename} (enrolled: {en.enrolled_at})")
    lines.append("")

    # ── ALL DOCUMENTS ──
    lines.append("=== ALL DOCUMENTS ===")
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    for d in docs:
        emp_user = db.query(User).filter(User.id == d.employee_id).first()
        emp_name = f"{emp_user.prenom} {emp_user.nom}" if emp_user else "N/A"
        creator = db.query(User).filter(User.id == d.created_by).first()
        creator_name = f"{creator.prenom} {creator.nom}" if creator else "N/A"
        ai_tag = "AI" if d.generated_by_ai else "Manual"
        lines.append(f"- #{d.id} [{ai_tag}] | {d.title} | Type: {d.document_type or 'N/A'} | Employee: {emp_name} | Status: {d.status.value} | Created by: {creator_name} | {d.created_at}")
    lines.append("")

    # ── HISTORY LOGS (last 20) ──
    lines.append("=== RECENT HISTORY LOGS (last 20) ===")
    logs = db.query(HistoryLog).order_by(HistoryLog.created_at.desc()).limit(20).all()
    for h in logs:
        user_name = "N/A"
        if h.performed_by:
            hu = db.query(User).filter(User.id == h.performed_by).first()
            user_name = f"{hu.prenom} {hu.nom}" if hu else "N/A"
        lines.append(f"- #{h.id} {h.action} on {h.record_type} #{h.record_id} by {user_name} | {h.details or ''} | {h.created_at}")
    lines.append("")

    # ── NOTIFICATIONS ──
    total_notif = db.query(Notification).count()
    unread_notif = db.query(Notification).filter(Notification.is_read == False).count()
    lines.append(f"=== NOTIFICATIONS: {total_notif} total, {unread_notif} unread ===")
    notifs = db.query(Notification).order_by(Notification.created_at.desc()).limit(10).all()
    for n in notifs:
        nu = db.query(User).filter(User.id == n.user_id).first()
        nname = f"{nu.prenom} {nu.nom}" if nu else "N/A"
        lines.append(f"- #{n.id} {nname} | {n.message} | Read: {n.is_read} | {n.created_at}")
    lines.append("")

    # ── LEAVE BALANCES ──
    lines.append("=== LEAVE BALANCES ===")
    balances = db.query(LeaveBalance).order_by(LeaveBalance.employee_id).all()
    for b in balances:
        bu = db.query(User).filter(User.id == b.employee_id).first()
        bname = f"{bu.prenom} {bu.nom}" if bu else "N/A"
        lt = db.query(LeaveType).filter(LeaveType.id == b.leave_type_id).first()
        ltname = lt.name if lt else "N/A"
        lines.append(f"- {bname} | {ltname}: {b.remaining_days} days remaining")
    if not balances:
        lines.append("- No leave balances recorded")
    lines.append("")

    # ── ONBOARDING PLANS ──
    lines.append("=== ONBOARDING PLANS ===")
    onboardings = db.query(OnboardingPlan).order_by(OnboardingPlan.created_at.desc()).all()
    for o in onboardings:
        ou = db.query(User).filter(User.id == o.employee_id).first()
        oname = f"{ou.prenom} {ou.nom}" if ou else "N/A"
        lines.append(f"- #{o.id} {oname} | Plan: {o.plan_type.value} | Status: {o.status.value} | {o.start_date} to {o.end_date}")
        tasks = db.query(OnboardingTask).filter(OnboardingTask.plan_id == o.id).all()
        for t in tasks:
            au = db.query(User).filter(User.id == t.assigned_to).first()
            aname = f"{au.prenom} {au.nom}" if au else "N/A"
            lines.append(f"  * Task: {t.title} | Status: {t.status.value} | Due: {t.due_date or 'N/A'} | Assigned to: {aname}")
        feedbacks = db.query(OnboardingFeedback).filter(OnboardingFeedback.onboarding_id == o.id).all()
        for fb in feedbacks:
            fau = db.query(User).filter(User.id == fb.author_id).first()
            faname = f"{fau.prenom} {fau.nom}" if fau else "N/A"
            lines.append(f"  * Feedback by {faname}: {fb.comment or 'N/A'}")
    if not onboardings:
        lines.append("- No onboarding plans")
    lines.append("")

    # ── OFFBOARDING PLANS ──
    lines.append("=== OFFBOARDING PLANS ===")
    offboardings = db.query(OffboardingPlan).order_by(OffboardingPlan.created_at.desc()).all()
    for o in offboardings:
        ou = db.query(User).filter(User.id == o.employee_id).first()
        oname = f"{ou.prenom} {ou.nom}" if ou else "N/A"
        lines.append(f"- #{o.id} {oname} | Departure: {o.departure_date} | Reason: {o.departure_reason or 'N/A'} | Status: {o.status.value}")
        tasks = db.query(OffboardingTask).filter(OffboardingTask.plan_id == o.id).all()
        for t in tasks:
            au = db.query(User).filter(User.id == t.assigned_to).first()
            aname = f"{au.prenom} {au.nom}" if au else "N/A"
            lines.append(f"  * Task: {t.title} | Status: {t.status.value} | Due: {t.due_date or 'N/A'} | Assigned to: {aname}")
        feedbacks = db.query(OffboardingFeedback).filter(OffboardingFeedback.plan_id == o.id).all()
        for fb in feedbacks:
            fau = db.query(User).filter(User.id == fb.author_id).first()
            faname = f"{fau.prenom} {fau.nom}" if fau else "N/A"
            lines.append(f"  * Feedback by {faname}: {fb.comment or 'N/A'}")
    if not offboardings:
        lines.append("- No offboarding plans")
    lines.append("")

    # ── RISK SCORES ──
    lines.append("=== RISK SCORES ===")
    risks = db.query(RiskScore).order_by(RiskScore.generated_at.desc()).all()
    for r in risks:
        ru = db.query(User).filter(User.id == r.employee_id).first()
        if ru and ru.role in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION]:
            continue
        
        # Check employee status
        emp = db.query(Employee).filter(Employee.user_id == r.employee_id).first()
        if not emp or emp.status != "active":
            continue

        turnover_str = r.turnover_risk if user.role != RoleEnum.MANAGER else 'N/A'
        engagement_str = r.engagement_risk if user.role != RoleEnum.MANAGER else 'N/A'
        rname = f"{ru.prenom} {ru.nom}" if ru else "N/A"
        lines.append(f"- {rname} | Turnover risk: {turnover_str or 'N/A'} | Burnout risk: {r.burnout_risk or 'N/A'} | Engagement risk: {engagement_str or 'N/A'} | Generated: {r.generated_at}")
    if not risks:
        lines.append("- No risk scores recorded")
    lines.append("")

    # ── RECOMMENDATIONS ──
    lines.append("=== RECOMMENDATIONS ===")
    recs = db.query(Recommendation).order_by(Recommendation.created_at.desc()).all()
    for rec in recs:
        reu = db.query(User).filter(User.id == rec.employee_id).first()
        rename = f"{reu.prenom} {reu.nom}" if reu else "N/A"
        lines.append(f"- #{rec.id} {rename} | Status: {rec.status.value} | {rec.recommendation}")
    if not recs:
        lines.append("- No recommendations")
    lines.append("")

    # ── ALERTS ──
    lines.append("=== ALERTS ===")
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    for a in alerts:
        au = db.query(User).filter(User.id == a.employee_id).first()
        aname = f"{au.prenom} {au.nom}" if au else "N/A"
        lines.append(f"- #{a.id} {aname} | Type: {a.alert_type} | Severity: {a.severity} | Status: {a.status.value} | {a.description or ''}")
        history = db.query(AlertHistory).filter(AlertHistory.alert_id == a.id).order_by(AlertHistory.created_at.desc()).all()
        for ah in history:
            pu = db.query(User).filter(User.id == ah.performed_by).first()
            pname = f"{pu.prenom} {pu.nom}" if pu else "N/A"
            lines.append(f"  * {ah.action} by {pname} | {ah.created_at}")
    if not alerts:
        lines.append("- No alerts")
    lines.append("")

    # ── KPI SNAPSHOTS ──
    lines.append("=== KPI SNAPSHOTS ===")
    kpis = db.query(KpiSnapshot).order_by(KpiSnapshot.snapshot_date.desc()).limit(12).all()
    for k in kpis:
        lines.append(f"- {k.snapshot_date}: Headcount={k.headcount} | Turnover={k.turnover_rate or 'N/A'}% | Absenteeism={k.absenteeism_rate or 'N/A'}% | Engagement={k.engagement_score or 'N/A'} | Payroll={k.payroll_amount or 'N/A'} EUR")
    if not kpis:
        lines.append("- No KPI snapshots")
    lines.append("")

    # ── SURVEYS ──
    lines.append("=== SURVEYS ===")
    surveys = db.query(Survey).order_by(Survey.created_at.desc()).all()
    for s in surveys:
        qcount = db.query(SurveyQuestion).filter(SurveyQuestion.survey_id == s.id).count()
        rcount = db.query(SurveyResponse).filter(SurveyResponse.survey_id == s.id).count()
        lines.append(f"- #{s.id} {s.title} | Questions: {qcount} | Responses: {rcount} | {s.description or ''}")
    if not surveys:
        lines.append("- No surveys")
    lines.append("")

    # ── HR TICKETS ──
    lines.append("=== HR TICKETS ===")
    tickets = db.query(HrTicket).order_by(HrTicket.created_at.desc()).all()
    for t in tickets:
        tu = db.query(User).filter(User.id == t.employee_id).first()
        tname = f"{tu.prenom} {tu.nom}" if tu else "N/A"
        assignee = ""
        if t.assigned_to:
            au = db.query(User).filter(User.id == t.assigned_to).first()
            assignee = f" | Assigned to: {au.prenom} {au.nom}" if au else ""
        lines.append(f"- #{t.id} {tname} | Subject: {t.subject} | Status: {t.status.value}{assignee} | {t.created_at}")
    if not tickets:
        lines.append("- No HR tickets")
    lines.append("")

    # ── APPROVAL WORKFLOWS ──
    lines.append("=== APPROVAL WORKFLOWS ===")
    workflows = db.query(ApprovalWorkflow).order_by(ApprovalWorkflow.created_at.desc()).all()
    for w in workflows:
        wu = db.query(User).filter(User.id == w.approver_id).first()
        wname = f"{wu.prenom} {wu.nom}" if wu else "N/A"
        lines.append(f"- #{w.id} Entity: {w.entity_type} #{w.entity_id} | Approver: {wname} | Status: {w.status.value} | {w.created_at}")
    if not workflows:
        lines.append("- No approval workflows")
    lines.append("")

    # ── CHATBOT LOGS (last 20) ──
    lines.append("=== CHATBOT LOGS (last 20) ===")
    chatbot_logs = db.query(ChatbotLog).order_by(ChatbotLog.created_at.desc()).limit(20).all()
    for cl in chatbot_logs:
        clu = db.query(User).filter(User.id == cl.user_id).first()
        clname = f"{clu.prenom} {clu.nom}" if clu else "Anonymous"
        lines.append(f"- #{cl.id} {clname} | Risk: {cl.risk_level or 'N/A'} | Q: {cl.query[:80]}... | A: {cl.response[:80]}... | {cl.created_at}")
    if not chatbot_logs:
        lines.append("- No chatbot logs")
    lines.append("")

    # ── SALARY SUMMARY ──
    total_salary = db.query(func.sum(Employee.salary)).scalar() or 0
    avg_salary = db.query(func.avg(Employee.salary)).scalar() or 0
    max_salary = db.query(func.max(Employee.salary)).scalar() or 0
    min_salary = db.query(func.min(Employee.salary)).scalar() or 0
    lines.append("=== SALARY SUMMARY ===")
    lines.append(f"Total: {float(total_salary):.2f} EUR | Average: {float(avg_salary):.2f} EUR | Min: {float(min_salary):.2f} EUR | Max: {float(max_salary):.2f} EUR")
    lines.append("")

    return "\n".join(lines)


def build_full_context(user: User, db: Session) -> str:
    parts = []
    user_ctx = build_user_context(user, db)
    parts.append("--- USER PROFILE ---")
    u = user_ctx["user"]
    parts.append(f"Name: {u['prenom']} {u['nom']}")
    parts.append(f"Email: {u['email']}")
    parts.append(f"Role: {u['role']}")

    emp = user_ctx.get("employee")
    if emp:
        parts.append(f"Department: {emp.get('department', 'N/A')}")
        parts.append(f"Position: {emp.get('position', 'N/A')}")
        if emp.get("manager"):
            parts.append(f"Manager: {emp['manager']}")

    if emp and emp.get("salary"):
        parts.append(f"Salary: {emp['salary']} EUR/month")

    contract = user_ctx.get("contract")
    if contract:
        parts.append(f"Contract: {contract['type']} - {contract['position']}")
        if contract.get("salary"):
            parts.append(f"Contract salary: {contract['salary']}")

    parts.append("")
    parts.append("--- LEAVE DATA ---")
    parts.append(build_leave_context(user, db))

    if user.role == RoleEnum.MANAGER:
        parts.append("")
        parts.append("--- TEAM DATA ---")
        parts.append(build_department_context(user, db))
    elif user.role in (RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.MEDECINE_TRAVAIL):
        parts.append("")
        parts.append("--- DEPARTMENT DATA ---")
        parts.append(build_department_context(user, db))
        parts.append("")
        parts.append("--- COMPANY OVERVIEW ---")
        parts.append(build_rh_context(user, db))

    return "\n".join(parts)
