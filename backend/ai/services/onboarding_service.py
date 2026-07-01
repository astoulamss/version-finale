import re
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from models.user import User, RoleEnum
from models.features import (
    Contract, Formation,
    OnboardingPlan, OnboardingPlanTypeEnum, OnboardingStatusEnum,
    OnboardingStep, OnboardingTask, OnboardingTaskStatusEnum,
    OffboardingPlan, OffboardingStatusEnum,
    OffboardingTask, OffboardingTaskStatusEnum, OffboardingStep,
)
from models.employees import Employee
from ai.utils.llm_client import call_llm
import os


ONBOARDING_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "onboarding.txt")
OFFBOARDING_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "offboarding.txt")


def _load_prompt(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Generate a structured plan based on the employee data provided."


def _build_employee_data(employee_id: int, db: Session) -> str:
    target = db.query(User).filter(User.id == employee_id).first()
    if not target:
        return "Employee not found."

    employee = db.query(Employee).filter(Employee.user_id == employee_id).first()
    contract = db.query(Contract).filter(Contract.user_id == employee_id).first()
    formations = db.query(Formation).all()

    parts = [
        f"Name: {target.prenom} {target.nom}",
        f"Email: {target.email}",
        f"Role: {target.role.value}",
    ]
    if employee:
        parts.append(f"Department: {employee.department.name if employee.department else 'N/A'}")
        parts.append(f"Position: {employee.position.title if employee.position else 'N/A'}")
    if contract:
        parts.append(f"Contract type: {contract.contract_type}")
        parts.append(f"Position: {contract.position}")
        parts.append(f"Start date: {contract.start_date}")
        parts.append(f"End date: {contract.end_date or 'N/A'}")

    parts.append("")
    parts.append("Available formations:")
    for f in formations:
        parts.append(f"- {f.title} ({f.start_date} to {f.end_date})")

    return "\n".join(parts)


def _parse_sections(text: str) -> list[dict]:
    """Split markdown text into sections by ## headings. Returns list of {title, content}."""
    sections = []
    current_title = "Introduction"
    current_lines = []
    for line in text.split("\n"):
        if line.startswith("## "):
            if current_lines:
                sections.append({"title": current_title, "content": "\n".join(current_lines).strip()})
            current_title = line.strip("## #").strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append({"title": current_title, "content": "\n".join(current_lines).strip()})
    return sections


def _parse_tasks_from_section(content: str, step_order: int) -> list[str]:
    """Extract bullet-point tasks from a section's content."""
    tasks = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            tasks.append(line[2:].strip())
        elif re.match(r"^\d+[.)]", line):
            tasks.append(re.sub(r"^\d+[.)]\s*", "", line))
    return tasks


def _find_employee(db: Session, name: str):
    from models.employees import Employee as EmpModel
    employees = db.query(EmpModel).all()
    name_lower = name.lower().strip()
    for emp in employees:
        try:
            full = f"{emp.user.prenom} {emp.user.nom}".lower()
            if name_lower in full or full in name_lower:
                return emp
        except Exception:
            continue
    return None


def get_onboarding_plans(db: Session, employee_name: str = "") -> list[dict]:
    query = db.query(OnboardingPlan).order_by(OnboardingPlan.created_at.desc())
    if employee_name:
        emp_rec = _find_employee(db, employee_name)
        if emp_rec:
            query = query.filter(OnboardingPlan.employee_id == emp_rec.user_id)
        else:
            return [{"error": f"Employee '{employee_name}' not found."}]
    plans = query.all()
    if not plans:
        return [{"message": "No onboarding plans found."}]
    result = []
    for p in plans:
        u = db.query(User).filter(User.id == p.employee_id).first()
        name = f"{u.prenom} {u.nom}" if u else "N/A"
        steps = db.query(OnboardingStep).filter(OnboardingStep.onboarding_id == p.id).order_by(OnboardingStep.step_order).all()
        tasks = db.query(OnboardingTask).filter(OnboardingTask.plan_id == p.id).all()
        done = sum(1 for t in tasks if t.status == OnboardingTaskStatusEnum.DONE)
        result.append({
            "plan_id": p.id,
            "employee": name,
            "plan_type": p.plan_type.value,
            "start_date": str(p.start_date),
            "end_date": str(p.end_date),
            "status": p.status.value,
            "steps": [{"id": s.id, "title": s.title, "order": s.step_order} for s in steps],
            "tasks": [{"id": t.id, "title": t.title, "status": t.status.value} for t in tasks],
            "task_count": len(tasks),
            "done_count": done,
        })
    return result


def get_offboarding_plans(db: Session, employee_name: str = "") -> list[dict]:
    query = db.query(OffboardingPlan).order_by(OffboardingPlan.created_at.desc())
    if employee_name:
        emp_rec = _find_employee(db, employee_name)
        if emp_rec:
            query = query.filter(OffboardingPlan.employee_id == emp_rec.user_id)
        else:
            return [{"error": f"Employee '{employee_name}' not found."}]
    plans = query.all()
    if not plans:
        return [{"message": "No offboarding plans found."}]
    result = []
    for p in plans:
        u = db.query(User).filter(User.id == p.employee_id).first()
        name = f"{u.prenom} {u.nom}" if u else "N/A"
        steps = db.query(OffboardingStep).filter(OffboardingStep.plan_id == p.id).order_by(OffboardingStep.step_order).all()
        tasks = db.query(OffboardingTask).filter(OffboardingTask.plan_id == p.id).all()
        result.append({
            "plan_id": p.id,
            "employee": name,
            "departure_date": str(p.departure_date),
            "departure_reason": p.departure_reason,
            "status": p.status.value,
            "steps": [{"id": s.id, "title": s.title, "order": s.step_order} for s in steps],
            "tasks": [{"id": t.id, "title": t.title, "status": t.status.value} for t in tasks],
        })
    return result


def generate_onboarding(
    employee_id: int,
    user: User,
    db: Session,
    plan_type: str = "30_days",
    start_date: str | None = None,
) -> dict:
    if user.role not in (RoleEnum.ADMIN, RoleEnum.RH):
        return {"type": "onboarding", "checklist": "Access denied.", "employee_name": "Unknown", "plan_id": None}

    data = _build_employee_data(employee_id, db)
    if data == "Employee not found.":
        return {"type": "onboarding", "checklist": "Employee not found.", "employee_name": "Unknown", "plan_id": None}

    target = db.query(User).filter(User.id == employee_id).first()
    system = _load_prompt(ONBOARDING_PROMPT_PATH)
    llm_prompt = (
        f"Generate onboarding plan for employee (plan type: {plan_type}):\n\n{data}\n\n"
        f"Use ## headings for each section."
    )
    response = call_llm(system, llm_prompt)
    if not response:
        response = "Onboarding plan could not be generated."

    # Parse start date
    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            sd = date.today()
    else:
        sd = date.today()

    # Calculate end date from plan type
    days_map = {"7_days": 7, "30_days": 30, "90_days": 90}
    num_days = days_map.get(plan_type, 30)
    ed = sd + timedelta(days=num_days)

    # Map plan_type string to enum
    pt_map = {
        "7_days": OnboardingPlanTypeEnum.SEVEN_DAYS,
        "30_days": OnboardingPlanTypeEnum.THIRTY_DAYS,
        "90_days": OnboardingPlanTypeEnum.NINETY_DAYS,
    }
    pt_enum = pt_map.get(plan_type, OnboardingPlanTypeEnum.THIRTY_DAYS)

    # Create the plan in DB
    plan = OnboardingPlan(
        employee_id=employee_id,
        start_date=sd,
        end_date=ed,
        status=OnboardingStatusEnum.PENDING,
        plan_type=pt_enum,
    )
    db.add(plan)
    db.flush()

    # Parse sections and create steps + tasks
    sections = _parse_sections(response)
    for step_idx, section in enumerate(sections, 1):
        step = OnboardingStep(
            onboarding_id=plan.id,
            title=section["title"],
            description=section["content"][:500] if section["content"] else None,
            step_order=step_idx,
        )
        db.add(step)
        db.flush()

        task_titles = _parse_tasks_from_section(section["content"], step_idx)
        if not task_titles:
            task_titles = [section["title"]]

        for task_title in task_titles:
            task = OnboardingTask(
                plan_id=plan.id,
                step_id=step.id,
                title=task_title[:255],
                status=OnboardingTaskStatusEnum.TODO,
                due_date=ed,
            )
            db.add(task)

    db.commit()

    return {
        "type": "onboarding",
        "checklist": response,
        "employee_name": f"{target.prenom} {target.nom}",
        "plan_id": plan.id,
    }


def generate_offboarding(
    employee_id: int,
    user: User,
    db: Session,
    departure_date: str | None = None,
    departure_reason: str | None = None,
) -> dict:
    if user.role not in (RoleEnum.ADMIN, RoleEnum.RH):
        return {"type": "offboarding", "checklist": "Access denied.", "employee_name": "Unknown", "plan_id": None}

    data = _build_employee_data(employee_id, db)
    if data == "Employee not found.":
        return {"type": "offboarding", "checklist": "Employee not found.", "employee_name": "Unknown", "plan_id": None}

    target = db.query(User).filter(User.id == employee_id).first()

    # Parse departure date
    if departure_date:
        try:
            dd = datetime.strptime(departure_date, "%Y-%m-%d").date()
        except ValueError:
            dd = date.today()
    else:
        dd = date.today()

    system = _load_prompt(OFFBOARDING_PROMPT_PATH)
    llm_prompt = (
        f"Generate offboarding plan for employee:\n\n{data}\n\n"
        f"Departure date: {dd}\n"
        f"Departure reason: {departure_reason or 'Not specified'}\n\n"
        f"Use ## headings for each section."
    )
    response = call_llm(system, llm_prompt)
    if not response:
        response = "Offboarding plan could not be generated."

    # Create the plan in DB
    plan = OffboardingPlan(
        employee_id=employee_id,
        departure_date=dd,
        departure_reason=departure_reason,
        status=OffboardingStatusEnum.PENDING,
    )
    db.add(plan)
    db.flush()

    # Parse sections and create steps + tasks
    sections = _parse_sections(response)
    for step_idx, section in enumerate(sections, 1):
        step = OffboardingStep(
            plan_id=plan.id,
            title=section["title"],
            step_order=step_idx,
        )
        db.add(step)
        db.flush()

        task_titles = _parse_tasks_from_section(section["content"], step_idx)
        if not task_titles:
            task_titles = [section["title"]]

        for task_title in task_titles:
            task = OffboardingTask(
                plan_id=plan.id,
                step_id=step.id,
                title=task_title[:255],
                status=OffboardingTaskStatusEnum.TODO,
                due_date=dd,
            )
            db.add(task)

    db.commit()

    return {
        "type": "offboarding",
        "checklist": response,
        "employee_name": f"{target.prenom} {target.nom}",
        "plan_id": plan.id,
    }
