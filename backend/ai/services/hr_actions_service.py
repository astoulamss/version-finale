import json
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.user import User, RoleEnum
from models.employees import Employee, EmployeeStatusEnum, Department, Position
from models.features import (
    Leave, LeaveStatusEnum, LeaveBalance, LeaveType,
    Alert, AlertStatusEnum,
    HrTicket, TicketStatusEnum,
    Contract, Formation, FormationEnrollment,
    Survey, SurveyQuestion, SurveyResponse, SurveyAnswer,
    QuestionTypeEnum,
    OnboardingPlan, OnboardingTask, OnboardingTaskStatusEnum, OnboardingStatusEnum,
    OffboardingPlan, OffboardingTask, OffboardingTaskStatusEnum, OffboardingStatusEnum,
    DocumentStatusEnum,
)
from models.absences import (
    Absence, AbsenceStatusEnum, AbsenceTypeEnum,
)
from models.notification import Notification


def _get_employee_by_name(db: Session, name: str) -> tuple:
    employees = db.query(Employee).all()
    name_lower = name.lower().strip()
    for emp in employees:
        try:
            full = f"{emp.user.prenom} {emp.user.nom}".lower()
            if name_lower == full or full == name_lower:
                return emp, emp.user
        except Exception:
            continue
    for emp in employees:
        try:
            parts = name_lower.split()
            emp_parts = {emp.user.prenom.lower(), emp.user.nom.lower()}
            if len(parts) >= 2 and set(p.lower() for p in parts[-2:]) == emp_parts:
                return emp, emp.user
        except Exception:
            continue
    return None, None


def create_leave(
    db: Session,
    employee_name: str,
    leave_type_name: str,
    start_date: str,
    end_date: str,
    reason: str = "",
) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}

    type_map = {
        "vacation": "Congé Payé", "annual": "Congé Payé", "congé annuel": "Congé Payé", "conge annuel": "Congé Payé",
        "congé payé": "Congé Payé", "conge paye": "Congé Payé", "paid": "Congé Payé",
        "sick": "Arrêt Maladie", "maladie": "Arrêt Maladie", "congé maladie": "Arrêt Maladie", "conge maladie": "Arrêt Maladie",
        "arrêt maladie": "Arrêt Maladie", "arret maladie": "Arrêt Maladie",
        "maternity": "Maternité / Paternité", "maternité": "Maternité / Paternité", "maternite": "Maternité / Paternité", "congé maternité": "Maternité / Paternité",
        "maternité/paternité": "Maternité / Paternité", "maternite/paternite": "Maternité / Paternité",
        "personal": "Congé Personnel", "personnel": "Congé Personnel", "congé personnel": "Congé Personnel", "conge personnel": "Congé Personnel",
        "unpaid": "Congé Sans Solde", "sans solde": "Congé Sans Solde", "congé sans solde": "Congé Sans Solde", "conge sans solde": "Congé Sans Solde",
    }
    mapped_name = type_map.get(leave_type_name.lower().strip(), leave_type_name)

    from models.features import LeaveType, Leave, LeaveStatusEnum
    from sqlalchemy import func
    leave_type = db.query(LeaveType).filter(func.lower(LeaveType.name) == mapped_name.lower()).first()

    if not leave_type:
        valid_types = db.query(LeaveType.name).all()
        valid_types_str = ", ".join([t[0] for t in valid_types])
        return {"status": "error", "message": f"Le système ne reconnaît pas le type de congé '{leave_type_name}' dans sa configuration actuelle. Voici les types de congés valides que vous pouvez utiliser :\n{valid_types_str}"}

    try:
        sd = datetime.strptime(start_date, "%Y-%m-%d").date() if "-" in start_date else datetime.strptime(start_date, "%d/%m/%Y").date()
        ed = datetime.strptime(end_date, "%Y-%m-%d").date() if "-" in end_date else datetime.strptime(end_date, "%d/%m/%Y").date()
    except Exception:
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY."}

    leave = Leave(
        employee_id=target_user.id,
        leave_type_id=leave_type.id,
        start_date=sd,
        end_date=ed,
        status=LeaveStatusEnum.PENDING,
        reason=reason or None
    )
    db.add(leave)
    db.commit()

    return {
        "status": "success",
        "message": f"Leave request created for {employee_name}: {leave_type.name} from {start_date} to {end_date} (PENDING).",
    }


def approve_leave(
    db: Session,
    leave_id: int,
    action: str,
    approver_name: str = "",
    reason: str = "",
) -> dict:
    from sqlalchemy import text
    row = db.execute(text("SELECT id, employee_id FROM leaves WHERE id = :lid"), {"lid": leave_id}).first()
    if not row:
        return {"status": "error", "message": f"Leave #{leave_id} not found."}

    if action == "approve":
        new_status = "APPROVED"
        notif_msg = f"Your leave request #{leave_id} has been APPROVED."
    elif action == "reject":
        new_status = "REJECTED"
        notif_msg = f"Your leave request #{leave_id} has been REJECTED."
        if reason:
            notif_msg += f" Reason: {reason}"
    else:
        return {"status": "error", "message": "Action must be 'approve' or 'reject'."}

    approver_id = None
    if approver_name:
        _, approver_user = _get_employee_by_name(db, approver_name)
        if approver_user:
            approver_id = approver_user.id

    db.execute(
        text("UPDATE leaves SET status = :st, approved_by = :ab, updated_at = NOW() WHERE id = :lid"),
        {"st": new_status, "ab": approver_id, "lid": leave_id},
    )
    db.execute(
        text("INSERT INTO notifications (user_id, message, created_at) VALUES (:uid, :msg, NOW())"),
        {"uid": row[1], "msg": notif_msg},
    )
    db.commit()

    return {
        "status": "success",
        "message": f"Leave #{leave_id} {action}d successfully.",
    }


def log_absence(
    db: Session,
    employee_name: str,
    absence_type: str,
    start_date: str,
    end_date: str,
    reason: str = "",
) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}

    type_map = {
        "maladie": AbsenceTypeEnum.MALADIE,
        "sick": AbsenceTypeEnum.MALADIE,
        "retard": AbsenceTypeEnum.RETARD,
        "late": AbsenceTypeEnum.RETARD,
        "injustifie": AbsenceTypeEnum.INJUSTIFIE,
        "unjustified": AbsenceTypeEnum.INJUSTIFIE,
        "autre": AbsenceTypeEnum.AUTRE,
        "other": AbsenceTypeEnum.AUTRE,
    }
    at = type_map.get(absence_type.lower(), AbsenceTypeEnum.AUTRE)

    try:
        sd = datetime.strptime(start_date, "%Y-%m-%d") if "-" in start_date else datetime.strptime(start_date, "%d/%m/%Y")
        ed = datetime.strptime(end_date, "%Y-%m-%d") if "-" in end_date else datetime.strptime(end_date, "%d/%m/%Y")
    except Exception:
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY."}

    absence = Absence(
        employee_id=target_user.id,
        absence_type=at,
        start_date=sd,
        end_date=ed,
        reason=reason or None,
    )
    db.execute(text("INSERT INTO absences (employee_id, absence_type, start_date, end_date, reason) VALUES (:eid, :at, :sd, :ed, :r)"), {
        "eid": target_user.id, "at": at.name, "sd": sd, "ed": ed, "r": reason or None,
    })
    db.commit()

    return {
        "status": "success",
        "message": f"Absence logged for {employee_name}: {absence_type} from {start_date} to {end_date}.",
    }


def send_notification(
    db: Session,
    employee_name: str,
    message: str,
    sender_name: str = "",
) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}

    notification = Notification(
        user_id=target_user.id,
        message=message,
    )
    db.add(notification)
    db.flush()
    db.commit()

    return {
        "status": "success",
        "message": f"Notification sent to {employee_name}: '{message[:80]}'",
    }


def create_hr_ticket(
    db: Session,
    employee_name: str,
    subject: str,
    description: str = "",
) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}

    ticket = HrTicket(
        employee_id=target_user.id,
        subject=subject,
        description=description or None,
        status=TicketStatusEnum.OPEN,
    )
    db.add(ticket)
    db.flush()
    db.commit()

    return {
        "status": "success",
        "message": f"HR ticket created for {employee_name}: '{subject}' (OPEN).",
        "ticket_id": ticket.id,
    }


def resolve_hr_ticket(
    db: Session,
    ticket_id: int,
    resolution: str = "resolved",
) -> dict:
    ticket = db.query(HrTicket).filter(HrTicket.id == ticket_id).first()
    if not ticket:
        return {"status": "error", "message": f"Ticket #{ticket_id} not found."}

    status_map = {
        "resolved": TicketStatusEnum.RESOLVED,
        "closed": TicketStatusEnum.CLOSED,
        "in_progress": TicketStatusEnum.IN_PROGRESS,
        "open": TicketStatusEnum.OPEN,
    }
    ticket.status = status_map.get(resolution, TicketStatusEnum.RESOLVED)
    db.flush()
    db.commit()

    return {
        "status": "success",
        "message": f"Ticket #{ticket_id} updated to {resolution.upper()}.",
    }


def update_employee_status(
    db: Session,
    employee_name: str,
    new_status: str,
) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}

    status_map = {
        "active": EmployeeStatusEnum.ACTIVE,
        "inactive": EmployeeStatusEnum.INACTIVE,
        "suspended": EmployeeStatusEnum.SUSPENDED,
        "on_leave": EmployeeStatusEnum.ON_LEAVE,
    }
    s = status_map.get(new_status.lower())
    if not s:
        return {"status": "error", "message": f"Invalid status '{new_status}'. Use: active, inactive, suspended, on_leave."}

    emp.status = s
    db.flush()
    db.commit()

    return {
        "status": "success",
        "message": f"{employee_name} status updated to {new_status.upper()}.",
    }


def reassign_employee(
    db: Session,
    employee_name: str,
    new_department: str = "",
    new_position: str = "",
    new_manager: str = "",
) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}

    changes = []
    if new_department:
        from models.employees import Department
        dept = db.query(Department).filter(Department.name.ilike(f"%{new_department}%")).first()
        if dept:
            emp.department_id = dept.id
            changes.append(f"department={dept.name}")
        else:
            return {"status": "error", "message": f"Department '{new_department}' not found."}

    if new_position:
        from models.employees import Position
        pos = db.query(Position).filter(Position.title.ilike(f"%{new_position}%")).first()
        if pos:
            emp.position_id = pos.id
            changes.append(f"position={pos.title}")
        else:
            return {"status": "error", "message": f"Position '{new_position}' not found."}

    if new_manager:
        _, mgr_user = _get_employee_by_name(db, new_manager)
        if mgr_user:
            emp.manager_id = mgr_user.id
            changes.append(f"manager={new_manager}")
        else:
            return {"status": "error", "message": f"Manager '{new_manager}' not found."}

    db.flush()
    db.commit()

    if not changes:
        return {"status": "error", "message": "No changes specified."}

    return {
        "status": "success",
        "message": f"{employee_name} updated: {', '.join(changes)}.",
    }


def create_alert(
    db: Session,
    employee_name: str,
    alert_type: str,
    severity: str,
    description: str = "",
) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}

    severity = severity.lower()
    if severity not in ("low", "medium", "high"):
        severity = "medium"

    alert = Alert(
        employee_id=target_user.id,
        alert_type=alert_type,
        severity=severity,
        description=description or None,
        status=AlertStatusEnum.NEW,
    )
    db.add(alert)
    db.flush()
    db.commit()

    return {
        "status": "success",
        "message": f"Alert created for {employee_name}: [{severity.upper()}] {alert_type}.",
        "alert_id": alert.id,
    }


# ── USER / EMPLOYEE MANAGEMENT ──

def create_user(
    db: Session,
    nom: str,
    prenom: str,
    email: str,
    role: str = "collaborateur",
    mots_de_passe: str = "default123",
) -> dict:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return {"status": "error", "message": f"User with email '{email}' already exists."}
    role_map = {
        "admin": "admin", "collaborateur": "collaborateur",
        "direction": "direction", "manager": "manager",
        "rh": "rh", "medecine_travail": "medecine_travail",
        "responsable_qvt": "responsable_qvt",
    }
    r = role_map.get(role.lower())
    if not r:
        return {"status": "error", "message": f"Invalid role '{role}'."}
    from core.security import hash_password
    user = User(
        nom=nom, prenom=prenom, email=email,
        mots_de_passe=hash_password(mots_de_passe),
        role=r, is_active=True, first_login=True,
    )
    db.add(user)
    db.flush()
    db.commit()
    return {"status": "success", "message": f"User '{prenom} {nom}' created (role: {role}).", "user_id": user.id}


def update_employee_salary(db: Session, employee_name: str, salary: float) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}

    # Update employee table
    emp.salary = salary
    
    # Also update the contract table if a contract exists
    from models.features import Contract
    contract = db.query(Contract).filter(Contract.user_id == target_user.id).order_by(Contract.id.desc()).first()
    if contract:
        contract.salary = str(salary)

    db.flush()
    db.commit()

    return {
        "status": "success",
        "message": f"{employee_name} salary updated to {salary:.2f} EUR.",
    }


def assign_employee_role(db: Session, employee_name: str, new_role: str) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    role_map = {
        "admin": "admin", "collaborateur": "collaborateur",
        "direction": "direction", "manager": "manager",
        "rh": "rh", "medecine_travail": "medecine_travail",
        "responsable_qvt": "responsable_qvt",
    }
    r = role_map.get(new_role.lower())
    if not r:
        return {"status": "error", "message": f"Invalid role '{new_role}'."}
    target_user.role = r
    db.flush()
    db.commit()
    return {"status": "success", "message": f"{employee_name} role changed to {new_role}."}


# ── CONTRACT MANAGEMENT ──

def create_contract(
    db: Session,
    employee_name: str,
    contract_type: str,
    position: str,
    start_date: str,
    end_date: str = "",
    salary: str = "",
) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    try:
        sd = datetime.strptime(start_date, "%Y-%m-%d").date()
        ed = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    except Exception:
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."}
    contract = Contract(
        user_id=target_user.id, contract_type=contract_type,
        position=position, start_date=sd, end_date=ed,
        salary=salary or None,
    )
    db.add(contract)
    db.flush()
    db.commit()
    return {"status": "success", "message": f"Contract created for {employee_name}: {contract_type} - {position}."}


# ── DEPARTMENT / POSITION MANAGEMENT ──

def create_department(db: Session, name: str, description: str = "") -> dict:
    existing = db.query(Department).filter(Department.name == name).first()
    if existing:
        return {"status": "error", "message": f"Department '{name}' already exists."}
    dept = Department(name=name, description=description or None)
    db.add(dept)
    db.flush()
    db.commit()
    return {"status": "success", "message": f"Department '{name}' created.", "department_id": dept.id}


def create_position(db: Session, title: str, description: str = "") -> dict:
    existing = db.query(Position).filter(Position.title == title).first()
    if existing:
        return {"status": "error", "message": f"Position '{title}' already exists."}
    pos = Position(title=title, description=description or None)
    db.add(pos)
    db.flush()
    db.commit()
    return {"status": "success", "message": f"Position '{title}' created.", "position_id": pos.id}


# ── FORMATION MANAGEMENT ──

def create_formation(
    db: Session,
    title: str,
    start_date: str,
    end_date: str,
    description: str = "",
) -> dict:
    try:
        sd = datetime.strptime(start_date, "%Y-%m-%d").date()
        ed = datetime.strptime(end_date, "%Y-%m-%d").date()
    except Exception:
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."}
    formation = Formation(title=title, description=description or None, start_date=sd, end_date=ed)
    db.add(formation)
    db.flush()
    db.commit()
    return {"status": "success", "message": f"Formation '{title}' created.", "formation_id": formation.id}


def enroll_in_formation(db: Session, employee_name: str, formation_title: str) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    formation = db.query(Formation).filter(Formation.title.ilike(f"%{formation_title}%")).first()
    if not formation:
        return {"status": "error", "message": f"Formation '{formation_title}' not found."}
    existing = db.query(FormationEnrollment).filter(
        FormationEnrollment.employee_id == target_user.id,
        FormationEnrollment.formation_id == formation.id,
    ).first()
    if existing:
        return {"status": "error", "message": f"{employee_name} is already enrolled in '{formation_title}'."}
    enrollment = FormationEnrollment(employee_id=target_user.id, formation_id=formation.id)
    db.add(enrollment)
    db.flush()
    db.commit()
    return {"status": "success", "message": f"{employee_name} enrolled in '{formation.title}'."}


# ── ONBOARDING / OFFBOARDING TASK PROGRESS ──

def update_onboarding_task_status(db: Session, task_id: int, new_status: str) -> dict:
    task = db.query(OnboardingTask).filter(OnboardingTask.id == task_id).first()
    if not task:
        return {"status": "error", "message": f"Onboarding task #{task_id} not found."}
    status_map = {"todo": OnboardingTaskStatusEnum.TODO, "in_progress": OnboardingTaskStatusEnum.IN_PROGRESS, "done": OnboardingTaskStatusEnum.DONE}
    s = status_map.get(new_status.lower())
    if not s:
        return {"status": "error", "message": "Status must be: todo, in_progress, or done."}
    task.status = s
    db.flush()
    db.commit()
    # Update plan status if all tasks done
    remaining = db.query(OnboardingTask).filter(OnboardingTask.plan_id == task.plan_id, OnboardingTask.status != OnboardingTaskStatusEnum.DONE).count()
    if remaining == 0:
        plan = db.query(OnboardingPlan).filter(OnboardingPlan.id == task.plan_id).first()
        if plan and plan.status.value == "pending":
            from models.features import OnboardingStatusEnum
            plan.status = OnboardingStatusEnum.COMPLETED
            db.flush()
            db.commit()
    return {"status": "success", "message": f"Onboarding task #{task_id} set to {new_status}."}


def update_offboarding_task_status(db: Session, task_id: int, new_status: str) -> dict:
    task = db.query(OffboardingTask).filter(OffboardingTask.id == task_id).first()
    if not task:
        return {"status": "error", "message": f"Offboarding task #{task_id} not found."}
    status_map = {"todo": OffboardingTaskStatusEnum.TODO, "in_progress": OffboardingTaskStatusEnum.IN_PROGRESS, "done": OffboardingTaskStatusEnum.DONE}
    s = status_map.get(new_status.lower())
    if not s:
        return {"status": "error", "message": "Status must be: todo, in_progress, or done."}
    task.status = s
    db.flush()
    db.commit()
    if remaining == 0:
        plan = db.query(OffboardingPlan).filter(OffboardingPlan.id == task.plan_id).first()
        if plan and (plan.status.value == "pending" or plan.status.value == "in_progress"):
            from models.features import OffboardingStatusEnum
            plan.status = OffboardingStatusEnum.COMPLETED
            db.flush()
            db.commit()
    return {"status": "success", "message": f"Offboarding task #{task_id} set to {new_status}."}

def update_onboarding_plan_status(db: Session, employee_name: str, new_status: str) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not target_user:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    plan = db.query(OnboardingPlan).filter(OnboardingPlan.employee_id == target_user.id).first()
    if not plan:
        return {"status": "error", "message": f"No onboarding plan found for '{employee_name}'."}
    
    status_map = {
        "pending": OnboardingStatusEnum.PENDING,
        "in_progress": OnboardingStatusEnum.IN_PROGRESS,
        "completed": OnboardingStatusEnum.COMPLETED,
        "cancelled": OnboardingStatusEnum.CANCELLED
    }
    s = status_map.get(new_status.lower())
    if not s:
        return {"status": "error", "message": "Status must be: pending, in_progress, completed, or cancelled."}
    
    plan.status = s
    db.flush()
    db.commit()
    return {"status": "success", "message": f"Onboarding plan for '{employee_name}' set to {new_status}."}

def update_offboarding_plan_status(db: Session, employee_name: str, new_status: str) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not target_user:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    plan = db.query(OffboardingPlan).filter(OffboardingPlan.employee_id == target_user.id).first()
    if not plan:
        return {"status": "error", "message": f"No offboarding plan found for '{employee_name}'."}
    
    from models.features import OffboardingStatusEnum
    status_map = {
        "pending": OffboardingStatusEnum.PENDING,
        "in_progress": OffboardingStatusEnum.IN_PROGRESS,
        "completed": OffboardingStatusEnum.COMPLETED,
        "cancelled": OffboardingStatusEnum.CANCELLED
    }
    s = status_map.get(new_status.lower())
    if not s:
        return {"status": "error", "message": "Status must be: pending, in_progress, completed, or cancelled."}
    
    plan.status = s
    db.flush()
    db.commit()
    return {"status": "success", "message": f"Offboarding plan for '{employee_name}' set to {new_status}."}


# ── LEAVE BALANCE MANAGEMENT ──

def update_leave_balance(db: Session, employee_name: str, leave_type_name: str, remaining_days: float) -> dict:
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    lt = db.query(LeaveType).filter(LeaveType.name.ilike(f"%{leave_type_name}%")).first()
    if not lt:
        return {"status": "error", "message": f"Leave type '{leave_type_name}' not found."}
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == target_user.id,
        LeaveBalance.leave_type_id == lt.id,
    ).first()
    if balance:
        balance.remaining_days = remaining_days
    else:
        balance = LeaveBalance(employee_id=target_user.id, leave_type_id=lt.id, remaining_days=remaining_days)
        db.add(balance)
    db.flush()
    db.commit()
    return {"status": "success", "message": f"{employee_name} {lt.name} balance set to {remaining_days} days."}


# ── SURVEY MANAGEMENT ──

def create_survey(db: Session, title: str, description: str = "") -> dict:
    survey = Survey(title=title, description=description or None)
    db.add(survey)
    db.flush()
    db.commit()
    return {"status": "success", "message": f"Survey '{title}' created.", "survey_id": survey.id}


def add_survey_question(db: Session, survey_title: str, question: str, question_type: str = "free_text") -> dict:
    survey = db.query(Survey).filter(Survey.title.ilike(f"%{survey_title}%")).first()
    if not survey:
        return {"status": "error", "message": f"Survey '{survey_title}' not found."}
    type_map = {
        "free_text": QuestionTypeEnum.FREE_TEXT, "single_choice": QuestionTypeEnum.SINGLE_CHOICE,
        "multiple_choice": QuestionTypeEnum.MULTIPLE_CHOICE, "rating": QuestionTypeEnum.RATING,
        "yes_no": QuestionTypeEnum.YES_NO,
    }
    qt = type_map.get(question_type.lower(), QuestionTypeEnum.FREE_TEXT)
    q = SurveyQuestion(survey_id=survey.id, question=question, question_type=qt)
    db.add(q)
    db.flush()
    db.commit()
    return {"status": "success", "message": f"Question added to survey '{survey_title}'."}


def submit_survey_response(db: Session, employee_name: str, survey_title: str, answers: list) -> dict:
    """answers is a list of {'question': str, 'answer': str}"""
    emp, target_user = _get_employee_by_name(db, employee_name)
    if not emp:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    survey = db.query(Survey).filter(Survey.title.ilike(f"%{survey_title}%")).first()
    if not survey:
        return {"status": "error", "message": f"Survey '{survey_title}' not found."}
    response = SurveyResponse(survey_id=survey.id, employee_id=target_user.id)
    db.add(response)
    db.flush()
    count = 0
    for a in answers:
        q_text = a.get("question", "")
        a_text = a.get("answer", "")
        question = db.query(SurveyQuestion).filter(
            SurveyQuestion.survey_id == survey.id,
            SurveyQuestion.question.ilike(f"%{q_text}%"),
        ).first()
        if question:
            answer = SurveyAnswer(response_id=response.id, question_id=question.id, answer=a_text)
            db.add(answer)
            count += 1
    db.flush()
    db.commit()
    return {"status": "success", "message": f"Survey response submitted for {employee_name} ({count} answers)."}


# ── EMPLOYEE CREATION (user already exists) ──

def create_employee(
    db: Session,
    user_id: int,
    department_name: str = "",
    position_title: str = "",
    manager_name: str = "",
    salary: float = None,
) -> dict:
    existing = db.query(Employee).filter(Employee.user_id == user_id).first()
    if existing:
        return {"status": "error", "message": f"Employee #{user_id} already has a record."}
    dept_id = None
    if department_name:
        dept = db.query(Department).filter(Department.name.ilike(f"%{department_name}%")).first()
        if dept:
            dept_id = dept.id
    pos_id = None
    if position_title:
        pos = db.query(Position).filter(Position.title.ilike(f"%{position_title}%")).first()
        if pos:
            pos_id = pos.id
    mgr_id = None
    if manager_name:
        _, mgr_user = _get_employee_by_name(db, manager_name)
        if mgr_user:
            mgr_id = mgr_user.id
    emp = Employee(
        user_id=user_id, department_id=dept_id, position_id=pos_id,
        manager_id=mgr_id, salary=salary, status=EmployeeStatusEnum.ACTIVE,
        hire_date=date.today(),
    )
    db.add(emp)
    db.flush()
    db.commit()
    return {"status": "success", "message": f"Employee record created for user #{user_id}.", "employee_id": emp.id}


# ── USER UPDATE ──

def update_user(
    db: Session,
    employee_name: str,
    nom: str = "",
    prenom: str = "",
    email: str = "",
    is_active: bool = None,
) -> dict:
    _, target_user = _get_employee_by_name(db, employee_name)
    if not target_user:
        return {"status": "error", "message": f"User '{employee_name}' not found."}
    updates = []
    if nom:
        target_user.nom = nom
        updates.append("nom")
    if prenom:
        target_user.prenom = prenom
        updates.append("prenom")
    if email:
        target_user.email = email
        updates.append("email")
    if is_active is not None:
        target_user.is_active = is_active
        updates.append("is_active")
    if not updates:
        return {"status": "error", "message": "No fields to update."}
    db.flush()
    db.commit()
    return {"status": "success", "message": f"User {employee_name} updated: {', '.join(updates)}."}


# ── RISK SCORE ──

def create_risk_score(
    db: Session,
    employee_name: str,
    turnover_risk: float = 0,
    burnout_risk: float = 0,
    engagement_risk: float = 0,
) -> dict:
    _, target_user = _get_employee_by_name(db, employee_name)
    if not target_user:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    db.execute(
        text("INSERT INTO risk_scores (employee_id, turnover_risk, burnout_risk, engagement_risk, generated_at) "
             "VALUES (:eid, :tr, :br, :er, NOW())"),
        {"eid": target_user.id, "tr": turnover_risk, "br": burnout_risk, "er": engagement_risk},
    )
    db.commit()
    return {"status": "success", "message": f"Risk score created for {employee_name} (turnover={turnover_risk}, burnout={burnout_risk}, engagement={engagement_risk})."}


# ── RECOMMENDATION ──

def create_recommendation(
    db: Session,
    employee_name: str,
    risk_score_id: int,
    recommendation: str,
) -> dict:
    _, target_user = _get_employee_by_name(db, employee_name)
    if not target_user:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    db.execute(
        text("INSERT INTO recommendations (employee_id, risk_score_id, recommendation, status, created_at) "
             "VALUES (:eid, :rsid, :rec, 'PENDING', NOW())"),
        {"eid": target_user.id, "rsid": risk_score_id, "rec": recommendation},
    )
    db.commit()
    return {"status": "success", "message": f"Recommendation created for {employee_name}."}


# ── APPROVAL WORKFLOW ──

def process_approval(
    db: Session,
    entity_type: str,
    entity_id: int,
    approver_name: str,
    action: str,
) -> dict:
    _, approver_user = _get_employee_by_name(db, approver_name)
    if not approver_user:
        return {"status": "error", "message": f"Approver '{approver_name}' not found."}
    new_status = "APPROVED" if action == "approve" else "REJECTED"
    db.execute(
        text("INSERT INTO approval_workflows (entity_type, entity_id, approver_id, status, created_at) "
             "VALUES (:et, :eid, :aid, :st, NOW())"),
        {"et": entity_type, "eid": entity_id, "aid": approver_user.id, "st": new_status},
    )
    if entity_type == "leave":
        db.execute(
            text("UPDATE leaves SET status = :st, approved_by = :aid, updated_at = NOW() WHERE id = :eid"),
            {"st": new_status, "aid": approver_user.id, "eid": entity_id},
        )
    db.commit()
    return {"status": "success", "message": f"Approval workflow {new_status} for {entity_type}#{entity_id} by {approver_name}.{' Leave status also updated.' if entity_type == 'leave' else ''}"}


# ── UPDATE ALERT STATUS ──

def update_alert_status(
    db: Session,
    alert_id: int,
    status: str,
    performed_by_name: str = "",
) -> dict:
    status = status.upper()
    if status not in ("NEW", "IN_PROGRESS", "RESOLVED"):
        return {"status": "error", "message": f"Invalid status '{status}'. Use NEW, IN_PROGRESS, or RESOLVED."}
    _, performer = _get_employee_by_name(db, performed_by_name) if performed_by_name else (None, None)
    performer_id = performer.id if performer else None
    row = db.execute(text("SELECT id FROM alerts WHERE id = :aid"), {"aid": alert_id}).first()
    if not row:
        return {"status": "error", "message": f"Alert #{alert_id} not found."}
    db.execute(
        text("UPDATE alerts SET status = :st WHERE id = :aid"),
        {"st": status, "aid": alert_id},
    )
    if performer_id:
        db.execute(
            text("INSERT INTO alert_history (alert_id, action, performed_by, created_at) VALUES (:aid, :act, :pb, NOW())"),
            {"aid": alert_id, "act": f"Status changed to {status}", "pb": performer_id},
        )
    db.commit()
    return {"status": "success", "message": f"Alert #{alert_id} status updated to '{status}'."}


# ── READ TOOLS ──

def get_alerts(db: Session, employee_name: str = "", status: str = "", limit: int = 20, user = None) -> dict:
    st = status.upper() if status else ""
    rows = db.execute(
        text("SELECT a.id, a.employee_id, u.nom || ' ' || u.prenom AS employee_name, "
             "a.alert_type, a.severity, a.description, a.status, a.created_at "
             "FROM alerts a JOIN users u ON u.id = a.employee_id "
             "WHERE (:en = '' OR LOWER(u.nom || ' ' || u.prenom) LIKE LOWER('%' || :en || '%')) "
             "AND (:st = '' OR a.status::text = :st) ORDER BY a.created_at DESC LIMIT :lim"),
        {"en": employee_name, "st": st, "lim": limit},
    ).fetchall()
    
    # Anonymize or filter based on role
    sanitized_alerts = []
    for r in rows:
        d = dict(r._mapping)
        # Convert datetime to string
        if "created_at" in d and d["created_at"]:
            d["created_at"] = str(d["created_at"])
            
        if user and user.role.value != "medecine_travail":
            # HR/Admin cannot see names for Burnout or health alerts
            if "burnout" in str(d.get("alert_type")).lower() or "santé" in str(d.get("alert_type")).lower():
                d["employee_name"] = "ANONYMIZED"
                d["employee_id"] = "ANONYMIZED"
        sanitized_alerts.append(d)
    return {
        "status": "success",
        "message": f"Found {len(rows)} alert(s).",
        "alerts": sanitized_alerts,
        "count": len(sanitized_alerts),
    }


def get_approval_workflows(db: Session, entity_type: str = "", status: str = "", limit: int = 20) -> dict:
    st = status.upper() if status else ""
    rows = db.execute(
        text("SELECT w.id, w.entity_type, w.entity_id, w.approver_id, "
             "u.nom || ' ' || u.prenom AS approver_name, w.status, w.created_at "
             "FROM approval_workflows w JOIN users u ON u.id = w.approver_id "
             "WHERE (:et = '' OR w.entity_type = :et) "
             "AND (:st = '' OR w.status::text = :st) ORDER BY w.created_at DESC LIMIT :lim"),
        {"et": entity_type, "st": st, "lim": limit},
    ).fetchall()
    return {
        "status": "success",
        "message": f"Found {len(rows)} approval workflow(s).",
        "approval_workflows": [dict(r._mapping) for r in rows],
        "count": len(rows),
    }


def get_risk_scores(db: Session, employee_name: str = "", limit: int = 20, user = None) -> dict:
    rows = db.execute(
        text("SELECT r.id, r.employee_id, u.nom || ' ' || u.prenom AS employee_name, "
             "r.turnover_risk, r.burnout_risk, r.engagement_risk, r.generated_at "
             "FROM risk_scores r JOIN users u ON u.id = r.employee_id "
             "WHERE (:en = '' OR LOWER(u.nom || ' ' || u.prenom) LIKE LOWER('%' || :en || '%')) "
             "ORDER BY r.generated_at DESC LIMIT :lim"),
        {"en": employee_name, "lim": limit},
    ).fetchall()

    sanitized_scores = []
    for r in rows:
        d = dict(r._mapping)
        
        # Convert Decimals to float and datetime to string
        for k in ["turnover_risk", "burnout_risk", "engagement_risk"]:
            if k in d and d[k] is not None:
                d[k] = float(d[k])
        if "generated_at" in d and d["generated_at"]:
            d["generated_at"] = str(d["generated_at"])
            
        if user:
            if user.role.value != "medecine_travail":
                # HR cannot see burnout risk names
                d["burnout_risk"] = "HIDDEN (Medical Confidentiality)"
                # To be absolutely safe, we enforce the rule that no names are shown for general queries
                if employee_name == "":
                    d["employee_name"] = "ANONYMIZED"
            else:
                # Medecine travail cannot see turnover and engagement risk
                d["turnover_risk"] = "HIDDEN (HR Confidentiality)"
                d["engagement_risk"] = "HIDDEN (HR Confidentiality)"
                
        sanitized_scores.append(d)
    return {
        "status": "success",
        "message": f"Found {len(rows)} risk score(s).",
        "risk_scores": sanitized_scores,
        "count": len(sanitized_scores),
    }


def get_recommendations(db: Session, employee_name: str = "", status: str = "", limit: int = 20, user = None) -> dict:
    st = status.upper() if status else ""
    rows = db.execute(
        text("SELECT rec.id, rec.employee_id, u.nom || ' ' || u.prenom AS employee_name, "
             "rec.risk_score_id, rec.recommendation, rec.status, rec.created_at "
             "FROM recommendations rec JOIN users u ON u.id = rec.employee_id "
             "WHERE (:en = '' OR LOWER(u.nom || ' ' || u.prenom) LIKE LOWER('%' || :en || '%')) "
             "AND (:st = '' OR rec.status::text = :st) ORDER BY rec.created_at DESC LIMIT :lim"),
        {"en": employee_name, "st": st, "lim": limit},
    ).fetchall()
    
    sanitized_recs = []
    for r in rows:
        d = dict(r._mapping)
        
        # Convert datetime to string
        if "created_at" in d and d["created_at"]:
            d["created_at"] = str(d["created_at"])
            
        if user and user.role.value != "medecine_travail":
            # For general recommendations, hide names unless specifically queried
            if employee_name == "":
                d["employee_name"] = "ANONYMIZED"
                d["employee_id"] = "ANONYMIZED"
        sanitized_recs.append(d)
        
    return {
        "status": "success",
        "message": f"Found {len(sanitized_recs)} recommendation(s).",
        "recommendations": sanitized_recs,
        "count": len(sanitized_recs),
    }


# ── UPDATE TOOLS (raw SQL to bypass ORM mismatch) ──

def update_leave(
    db: Session,
    leave_id: int,
    status: str = "",
    start_date: str = "",
    end_date: str = "",
    reason: str = "",
) -> dict:
    row = db.execute(text("SELECT id FROM leaves WHERE id = :lid"), {"lid": leave_id}).first()
    if not row:
        return {"status": "error", "message": f"Leave #{leave_id} not found."}
    parts = []
    params = {"lid": leave_id}
    if status:
        parts.append("status = :st")
        params["st"] = status.upper()
    if start_date:
        parts.append("start_date = :sd")
        params["sd"] = start_date
    if end_date:
        parts.append("end_date = :ed")
        params["ed"] = end_date
    if reason:
        parts.append("reason = :re")
        params["re"] = reason
    if not parts:
        return {"status": "error", "message": "No fields to update."}
    parts.append("updated_at = NOW()")
    db.execute(text(f"UPDATE leaves SET {', '.join(parts)} WHERE id = :lid"), params)
    db.commit()
    return {"status": "success", "message": f"Leave #{leave_id} updated."}


def update_absence(
    db: Session,
    absence_id: int,
    absence_type: str = "",
    start_date: str = "",
    end_date: str = "",
    reason: str = "",
) -> dict:
    row = db.execute(text("SELECT id FROM absences WHERE id = :aid"), {"aid": absence_id}).first()
    if not row:
        return {"status": "error", "message": f"Absence #{absence_id} not found."}
    parts = []
    params = {"aid": absence_id}
    if absence_type:
        parts.append("absence_type = :at")
        params["at"] = absence_type.upper()
    if start_date:
        parts.append("start_date = :sd")
        params["sd"] = start_date
    if end_date:
        parts.append("end_date = :ed")
        params["ed"] = end_date
    if reason:
        parts.append("reason = :re")
        params["re"] = reason
    if not parts:
        return {"status": "error", "message": "No fields to update."}
    db.execute(text(f"UPDATE absences SET {', '.join(parts)} WHERE id = :aid"), params)
    db.commit()
    return {"status": "success", "message": f"Absence #{absence_id} updated."}


def update_contract(
    db: Session,
    contract_id: int,
    contract_type: str = "",
    start_date: str = "",
    end_date: str = "",
    position: str = "",
    salary: str = "",
) -> dict:
    row = db.execute(text("SELECT id FROM contracts WHERE id = :cid"), {"cid": contract_id}).first()
    if not row:
        return {"status": "error", "message": f"Contract #{contract_id} not found."}
    parts = []
    params = {"cid": contract_id}
    if contract_type:
        parts.append("contract_type = :ct")
        params["ct"] = contract_type
    if start_date:
        parts.append("start_date = :sd")
        params["sd"] = start_date
    if end_date:
        parts.append("end_date = :ed")
        params["ed"] = end_date
    if position:
        parts.append("position = :po")
        params["po"] = position
    if salary:
        parts.append("salary = :sa")
        params["sa"] = salary
    if not parts:
        return {"status": "error", "message": "No fields to update."}
    db.execute(text(f"UPDATE contracts SET {', '.join(parts)} WHERE id = :cid"), params)
    db.commit()
    return {"status": "success", "message": f"Contract #{contract_id} updated."}


# ── CREATE ONBOARDING / OFFBOARDING PLANS ──

def create_onboarding_plan(
    db: Session,
    employee_name: str,
    start_date: str,
    end_date: str,
    plan_type: str = "THIRTY_DAYS",
) -> dict:
    _, target_user = _get_employee_by_name(db, employee_name)
    if not target_user:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    pt = plan_type.upper()
    if pt not in ("SEVEN_DAYS", "THIRTY_DAYS", "NINETY_DAYS"):
        return {"status": "error", "message": f"Invalid plan_type '{plan_type}'. Use SEVEN_DAYS, THIRTY_DAYS, or NINETY_DAYS."}
    db.execute(
        text("INSERT INTO onboarding_plans (employee_id, start_date, end_date, status, plan_type, created_at) "
             "VALUES (:eid, :sd, :ed, 'PENDING', :pt, NOW())"),
        {"eid": target_user.id, "sd": start_date, "ed": end_date, "pt": pt},
    )
    db.commit()
    return {"status": "success", "message": f"Onboarding plan created for {employee_name} ({pt})."}


def create_offboarding_plan(
    db: Session,
    employee_name: str,
    departure_date: str,
    departure_reason: str = "",
) -> dict:
    _, target_user = _get_employee_by_name(db, employee_name)
    if not target_user:
        return {"status": "error", "message": f"Employee '{employee_name}' not found."}
    db.execute(
        text("INSERT INTO offboarding_plans (employee_id, departure_date, departure_reason, status, created_at) "
             "VALUES (:eid, :dd, :dr, 'PENDING', NOW())"),
        {"eid": target_user.id, "dd": departure_date, "dr": departure_reason},
    )
    db.commit()
    return {"status": "success", "message": f"Offboarding plan created for {employee_name}."}
