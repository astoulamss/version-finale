import os
import json
import re
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func as safunc, exc
from models.user import User, RoleEnum
from models.features import Document, DocumentTemplate, DocumentType, DocumentStatusEnum
from models.employees import Employee, Department, Position
from ai.utils.llm_client import call_llm
from ai.utils.pdf_generator import generate_pdf as make_pdf
from ai.utils.minio_client import upload_pdf
from ai.services.chart_service import generate_chart
from ai.services.hr_actions_service import (
    create_leave, approve_leave, log_absence,
    send_notification, create_hr_ticket, resolve_hr_ticket,
    update_employee_status, reassign_employee, create_alert,
    create_user, update_employee_salary, assign_employee_role,
    create_contract, create_department, create_position,
    create_formation, enroll_in_formation,
    update_onboarding_task_status, update_offboarding_task_status,
    update_onboarding_plan_status, update_offboarding_plan_status,
    update_leave_balance, create_survey, add_survey_question, submit_survey_response,
    create_employee, update_user, create_risk_score, create_recommendation,
    process_approval, update_alert_status,
    get_alerts, get_approval_workflows, get_risk_scores, get_recommendations,
    update_leave, update_absence, update_contract,
    create_onboarding_plan, create_offboarding_plan,
)
from ai.services.onboarding_service import generate_onboarding, generate_offboarding, get_onboarding_plans, get_offboarding_plans
from datetime import datetime, date

GENERATED_DIR = Path(__file__).parent.parent / "generated"


def get_employee_count(db: Session) -> dict:
    total = db.query(Employee).count()
    return {"status": "success", "total_employees": total}


def get_current_user(user: User) -> dict:
    return {
        "status": "success",
        "user": {
            "id": user.id,
            "nom": user.nom,
            "prenom": user.prenom,
            "email": user.email,
            "role": user.role.value,
        },
    }


TOOLS = [
]


def _safe(text: str) -> str:
    if not text:
        return ""
    text = text.replace('\u2014', '--').replace('\u2013', '-')
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u00ab', '"').replace('\u00bb', '"')
    text = text.replace('\u0153', 'oe').replace('\u0152', 'OE')
    text = text.replace('\u20ac', ' EUR')
    text = text.replace('\u202f', ' ').replace('\u00a0', ' ')
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,2}(.+?)_{1,2}', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'`+', '', text)
    return text.encode('latin-1', errors='replace').decode('latin-1')


def format_date_fr(date_val) -> str:
    if not date_val:
        return ""
    if isinstance(date_val, str):
        date_str = date_val.strip()
        try:
            if "-" in date_str:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            elif "/" in date_str:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
            else:
                return date_str
        except Exception:
            return date_str
    elif isinstance(date_val, (date, datetime)):
        dt = date_val
    else:
        return str(date_val)

    months = {
        1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
        7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
    }
    day_str = "1er" if dt.day == 1 else str(dt.day)
    return f"{day_str} {months[dt.month]} {dt.year}"






def _upload_pdf_bytes(pdf_bytes: bytes, base_name: str) -> str:
    from ai.utils.minio_client import upload_pdf as _up
    return _up(pdf_bytes, base_name)


def generate_work_certificate_pdf(
    employee_name: str,
    job_title: str,
    department: str,
    contract_type: str,
    start_date: str,
    city: str,
) -> str:
    from ai.utils.pdf_generator import generate_work_certificate_html, html_to_pdf
    title = f"attestation-travail-{employee_name}"
    html = generate_work_certificate_html(
        employee_name, job_title, department,
        contract_type, start_date, city
    )
    pdf_bytes = html_to_pdf(html)
    file_url = _upload_pdf_bytes(pdf_bytes, title)
    return file_url


def generate_report_pdf(title: str, content: str) -> str:
    from ai.utils.pdf_generator import generate_report_html, html_to_pdf
    html = generate_report_html(title, content)
    pdf_bytes = html_to_pdf(html)
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().lower()[:80] or "rapport"
    file_url = _upload_pdf_bytes(pdf_bytes, safe_title)
    return file_url


def generate_leave_certificate_pdf(
    employee_name: str,
    employee_id: str,
    job_title: str,
    department: str,
    contract_type: str,
    contract_start_date: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    num_days: str,
    status: str,
    city: str,
    hr_manager_name: str,
) -> str:
    from ai.utils.pdf_generator import generate_leave_certificate_html, html_to_pdf
    title = f"certificat-conge-{employee_name}"
    html = generate_leave_certificate_html(
        employee_name, employee_id, job_title, department,
        contract_type, contract_start_date, leave_type,
        start_date, end_date, num_days, status,
        city, hr_manager_name
    )
    pdf_bytes = html_to_pdf(html)
    file_url = _upload_pdf_bytes(pdf_bytes, title)
    return file_url


# ── HR ACTION TOOLS ──
HR_ACTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_leave",
            "description": "Create a leave (congé) request for an employee. The leave will be PENDING until approved.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "leave_type_name": {"type": "string", "description": "Leave type name (e.g. Congé Payé, Arret Maladie, Maternité/Paternité, Congé Personnel, Congé Sans Solde)"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "reason": {"type": "string", "description": "Reason for the leave"},
                },
                "required": ["employee_name", "leave_type_name", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "approve_leave",
            "description": "Approve or reject a pending leave request by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "leave_id": {"type": "integer", "description": "ID of the leave request"},
                    "action": {"type": "string", "enum": ["approve", "reject"], "description": "Action to take"},
                    "approver_name": {"type": "string", "description": "Name of the person approving/rejecting"},
                    "reason": {"type": "string", "description": "Reason for rejection (only for reject)"},
                },
                "required": ["leave_id", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_absence",
            "description": "Log an absence (retard/maladie/injustifié) for an employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "absence_type": {"type": "string", "enum": ["maladie", "retard", "injustifie", "autre"], "description": "Type of absence"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "reason": {"type": "string", "description": "Reason for the absence"},
                },
                "required": ["employee_name", "absence_type", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_notification",
            "description": "Send a notification/message to an employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "message": {"type": "string", "description": "Notification message content"},
                    "sender_name": {"type": "string", "description": "Name of the sender (optional)"},
                },
                "required": ["employee_name", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_hr_ticket",
            "description": "Create a new HR support ticket for an employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "subject": {"type": "string", "description": "Ticket subject/title"},
                    "description": {"type": "string", "description": "Detailed description of the issue"},
                },
                "required": ["employee_name", "subject"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resolve_hr_ticket",
            "description": "Update the status of an HR ticket (resolve, close, mark in progress).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer", "description": "ID of the ticket"},
                    "resolution": {"type": "string", "enum": ["resolved", "closed", "in_progress", "open"], "description": "New status"},
                },
                "required": ["ticket_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_employee_status",
            "description": "Update an employee's status (active/inactive/suspended/on_leave).",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "new_status": {"type": "string", "enum": ["active", "inactive", "suspended", "on_leave"], "description": "New status"},
                },
                "required": ["employee_name", "new_status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reassign_employee",
            "description": "Reassign an employee to a different department, position, or manager.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "new_department": {"type": "string", "description": "New department name (optional)"},
                    "new_position": {"type": "string", "description": "New position title (optional)"},
                    "new_manager": {"type": "string", "description": "Full name of new manager (optional)"},
                },
                "required": ["employee_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_alert",
            "description": "Create an HR alert for monitoring (e.g., high absenteeism, risk detected).",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "alert_type": {"type": "string", "description": "Type of alert (e.g. absence, performance, risk, burnout)"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"], "description": "Alert severity"},
                    "description": {"type": "string", "description": "Detailed description of the alert"},
                },
                "required": ["employee_name", "alert_type", "severity"],
            },
        },
    },
]

# ── USER / EMPLOYEE TOOLS ──
USER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_user",
            "description": "Create a new user account in the system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom": {"type": "string", "description": "Last name"},
                    "prenom": {"type": "string", "description": "First name"},
                    "email": {"type": "string", "description": "Email address"},
                    "role": {"type": "string", "enum": ["admin", "collaborateur", "direction", "manager", "rh", "medecine_travail", "responsable_qvt"], "description": "User role"},
                    "mots_de_passe": {"type": "string", "description": "Password (optional, default: default123)"},
                },
                "required": ["nom", "prenom", "email", "role"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_employee_salary",
            "description": "Update an employee's salary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "salary": {"type": "number", "description": "New salary amount"},
                },
                "required": ["employee_name", "salary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "assign_employee_role",
            "description": "Change an employee's role/permissions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "new_role": {"type": "string", "enum": ["admin", "collaborateur", "direction", "manager", "rh", "medecine_travail", "responsable_qvt"], "description": "New role"},
                },
                "required": ["employee_name", "new_role"],
            },
        },
    },
]

# ── CONTRACT TOOLS ──
CONTRACT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_contract",
            "description": "Create a new contract for an employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "contract_type": {"type": "string", "description": "Type (CDI, CDD, Stage, Alternance, Freelance)"},
                    "position": {"type": "string", "description": "Job title / position"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD (optional)"},
                    "salary": {"type": "string", "description": "Salary (optional)"},
                },
                "required": ["employee_name", "contract_type", "position", "start_date"],
            },
        },
    },
]

# ── DEPARTMENT / POSITION TOOLS ──
DEPT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_department",
            "description": "Create a new department.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Department name"},
                    "description": {"type": "string", "description": "Description (optional)"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_position",
            "description": "Create a new job position/title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Position title"},
                    "description": {"type": "string", "description": "Description (optional)"},
                },
                "required": ["title"],
            },
        },
    },
]

# ── FORMATION TOOLS ──
FORMATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_formation",
            "description": "Create a new training/formation program.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Formation title"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "description": {"type": "string", "description": "Description (optional)"},
                },
                "required": ["title", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enroll_in_formation",
            "description": "Enroll an employee in a formation/training.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "formation_title": {"type": "string", "description": "Title of the formation"},
                },
                "required": ["employee_name", "formation_title"],
            },
        },
    },
]

# ── TASK PROGRESS TOOLS ──
TASK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_onboarding_task_status",
            "description": "Update the status of an onboarding task (todo/in_progress/done).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID of the onboarding task"},
                    "new_status": {"type": "string", "enum": ["todo", "in_progress", "done"], "description": "New status"},
                },
                "required": ["task_id", "new_status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_offboarding_task_status",
            "description": "Update the status of an offboarding task (todo/in_progress/done).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID of the offboarding task"},
                    "new_status": {"type": "string", "enum": ["todo", "in_progress", "done"], "description": "New status"},
                },
                "required": ["task_id", "new_status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_onboarding_plan_status",
            "description": "Update the status of an onboarding plan (pending/in_progress/completed/cancelled).",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "new_status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"], "description": "New status"},
                },
                "required": ["employee_name", "new_status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_offboarding_plan_status",
            "description": "Update the status of an offboarding plan (pending/in_progress/completed/cancelled).",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "new_status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"], "description": "New status"},
                },
                "required": ["employee_name", "new_status"],
            },
        },
    },
]

# ── LEAVE BALANCE TOOLS ──
LEAVE_BALANCE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_leave_balance",
            "description": "Update remaining leave days for an employee's leave type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "leave_type_name": {"type": "string", "description": "Leave type name (e.g. Congé Payé, Arret Maladie)"},
                    "remaining_days": {"type": "number", "description": "Number of remaining days"},
                },
                "required": ["employee_name", "leave_type_name", "remaining_days"],
            },
        },
    },
]

# ── SURVEY TOOLS ──
SURVEY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_survey",
            "description": "Create a new survey.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Survey title"},
                    "description": {"type": "string", "description": "Description (optional)"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_survey_question",
            "description": "Add a question to an existing survey.",
            "parameters": {
                "type": "object",
                "properties": {
                    "survey_title": {"type": "string", "description": "Title of the survey"},
                    "question": {"type": "string", "description": "Question text"},
                    "question_type": {"type": "string", "enum": ["free_text", "single_choice", "multiple_choice", "rating", "yes_no"], "description": "Type of question"},
                },
                "required": ["survey_title", "question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_survey_response",
            "description": "Submit a survey response for an employee. Provide answers as a list of {question, answer}.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "survey_title": {"type": "string", "description": "Title of the survey"},
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {"type": "string"},
                                "answer": {"type": "string"},
                            },
                            "required": ["question", "answer"],
                        },
                        "description": "List of question/answer pairs",
                    },
                },
                "required": ["employee_name", "survey_title", "answers"],
            },
        },
    },
]

ONBOARDING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_onboarding_plan",
            "description": (
                "Generate and save an onboarding plan for a new employee. "
                "Creates the plan with steps and tasks in the database. "
                "Use when user asks to generate or create an onboarding plan for an employee."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {
                        "type": "string",
                        "description": "Full name of the employee",
                    },
                    "plan_type": {
                        "type": "string",
                        "enum": ["7_days", "30_days", "90_days"],
                        "description": "Duration of the onboarding plan",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date YYYY-MM-DD (optional, defaults to today)",
                    },
                },
                "required": ["employee_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_onboarding_plans",
            "description": (
                "Retrieve onboarding plans for an employee. "
                "Returns all onboarding plans, steps, and tasks. "
                "Use when user asks about onboarding plans, tasks, or integration status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {
                        "type": "string",
                        "description": "Full name of the employee (optional, returns all plans if omitted)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_offboarding_plan",
            "description": (
                "Generate and save an offboarding plan for a departing employee. "
                "Creates the plan with steps and tasks in the database. "
                "Use when user asks to generate or create an offboarding plan."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {
                        "type": "string",
                        "description": "Full name of the employee",
                    },
                    "departure_date": {
                        "type": "string",
                        "description": "Departure date YYYY-MM-DD (optional, defaults to today)",
                    },
                    "departure_reason": {
                        "type": "string",
                        "description": "Reason for departure (optional)",
                    },
                },
                "required": ["employee_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_offboarding_plans",
            "description": (
                "Retrieve offboarding plans for an employee. "
                "Returns all offboarding plans, steps, and tasks. "
                "Use when user asks about offboarding plans or departure status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {
                        "type": "string",
                        "description": "Full name of the employee (optional, returns all plans if omitted)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_employee",
            "description": "Create an employee record linked to an existing user. Required: user_id. Optional: department, position, manager, salary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID of the employee"},
                    "department_name": {"type": "string", "description": "Department name (optional)"},
                    "position_title": {"type": "string", "description": "Job position title (optional)"},
                    "manager_name": {"type": "string", "description": "Manager full name (optional)"},
                    "salary": {"type": "number", "description": "Salary amount (optional)"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_user",
            "description": "Update a user's profile fields: nom, prenom, email, is_active. Use when user asks to edit profile, change name, or deactivate/activate account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "nom": {"type": "string", "description": "New last name (optional)"},
                    "prenom": {"type": "string", "description": "New first name (optional)"},
                    "email": {"type": "string", "description": "New email (optional)"},
                    "is_active": {"type": "boolean", "description": "Set true to activate, false to deactivate (optional)"},
                },
                "required": ["employee_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_risk_score",
            "description": "Create a risk assessment score for an employee. Scores are 0-100 for turnover_risk, burnout_risk, and engagement_risk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "turnover_risk": {"type": "number", "description": "Turnover risk score 0-100 (default 0)"},
                    "burnout_risk": {"type": "number", "description": "Burnout risk score 0-100 (default 0)"},
                    "engagement_risk": {"type": "number", "description": "Engagement risk score 0-100 (default 0)"},
                },
                "required": ["employee_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_recommendation",
            "description": "Create a recommendation linked to a risk score for an employee. Provide the risk_score_id and recommendation text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "risk_score_id": {"type": "integer", "description": "ID of the related risk score"},
                    "recommendation": {"type": "string", "description": "Recommendation text"},
                },
                "required": ["employee_name", "risk_score_id", "recommendation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_approval",
            "description": "Create or process an approval workflow for any entity (leave, document, etc.). Approve or reject by providing the entity type, entity ID, approver name, and action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "description": "Entity type e.g. 'leave', 'document', 'absence'"},
                    "entity_id": {"type": "integer", "description": "ID of the entity to approve/reject"},
                    "approver_name": {"type": "string", "description": "Full name of the approver"},
                    "action": {"type": "string", "enum": ["approve", "reject"], "description": "approve or reject"},
                },
                "required": ["entity_type", "entity_id", "approver_name", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_alert_status",
            "description": "Update the status of an HR alert (new, in_progress, resolved). Optionally record who performed the action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "alert_id": {"type": "integer", "description": "ID of the alert"},
                    "status": {"type": "string", "enum": ["NEW", "IN_PROGRESS", "RESOLVED"], "description": "New status (NEW, IN_PROGRESS, RESOLVED)"},
                    "performed_by_name": {"type": "string", "description": "Name of person performing the action (optional)"},
                },
                "required": ["alert_id", "status"],
            },
        },
    },
    # ── READ TOOLS ──
    {
        "type": "function",
        "function": {
            "name": "get_alerts",
            "description": "Get HR alerts with optional filters by employee name or status (NEW, IN_PROGRESS, RESOLVED).",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Filter by employee name (optional)"},
                    "status": {"type": "string", "description": "Filter by status: NEW, IN_PROGRESS, RESOLVED (optional)"},
                    "limit": {"type": "integer", "description": "Max results (default 20)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_approval_workflows",
            "description": "Get approval workflows with optional filters by entity_type or status (PENDING, APPROVED, REJECTED).",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "description": "Filter by entity type e.g. 'leave' (optional)"},
                    "status": {"type": "string", "description": "Filter by status: PENDING, APPROVED, REJECTED (optional)"},
                    "limit": {"type": "integer", "description": "Max results (default 20)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_risk_scores",
            "description": "Get risk scores for employees, optionally filtered by employee name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Filter by employee name (optional)"},
                    "limit": {"type": "integer", "description": "Max results (default 20)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommendations",
            "description": "Get recommendations with optional filters by employee name or status (PENDING, IN_PROGRESS, DONE).",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Filter by employee name (optional)"},
                    "status": {"type": "string", "description": "Filter by status: PENDING, IN_PROGRESS, DONE (optional)"},
                    "limit": {"type": "integer", "description": "Max results (default 20)"},
                },
            },
        },
    },
    # ── UPDATE TOOLS ──
    {
        "type": "function",
        "function": {
            "name": "update_leave",
            "description": "Update a leave request's status, dates, or reason. Status values: PENDING, APPROVED, REJECTED, CANCELLED.",
            "parameters": {
                "type": "object",
                "properties": {
                    "leave_id": {"type": "integer", "description": "ID of the leave request"},
                    "status": {"type": "string", "description": "New status: PENDING, APPROVED, REJECTED, CANCELLED (optional)"},
                    "start_date": {"type": "string", "description": "New start date YYYY-MM-DD (optional)"},
                    "end_date": {"type": "string", "description": "New end date YYYY-MM-DD (optional)"},
                    "reason": {"type": "string", "description": "New reason text (optional)"},
                },
                "required": ["leave_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_absence",
            "description": "Update an absence record's type, dates, or reason. Type values: MALADIE, RETARD, INJUSTIFIE, AUTRE.",
            "parameters": {
                "type": "object",
                "properties": {
                    "absence_id": {"type": "integer", "description": "ID of the absence record"},
                    "absence_type": {"type": "string", "description": "New type: MALADIE, RETARD, INJUSTIFIE, AUTRE (optional)"},
                    "start_date": {"type": "string", "description": "New start date (optional)"},
                    "end_date": {"type": "string", "description": "New end date (optional)"},
                    "reason": {"type": "string", "description": "New reason text (optional)"},
                },
                "required": ["absence_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_contract",
            "description": "Update a contract's type, dates, position, or salary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_id": {"type": "integer", "description": "ID of the contract"},
                    "contract_type": {"type": "string", "description": "New contract type (optional)"},
                    "start_date": {"type": "string", "description": "New start date YYYY-MM-DD (optional)"},
                    "end_date": {"type": "string", "description": "New end date YYYY-MM-DD (optional)"},
                    "position": {"type": "string", "description": "New position title (optional)"},
                    "salary": {"type": "string", "description": "New salary amount as string (optional)"},
                },
                "required": ["contract_id"],
            },
        },
    },
    # ── CREATE ONBOARDING / OFFBOARDING PLANS ──
    {
        "type": "function",
        "function": {
            "name": "create_onboarding_plan",
            "description": "Create an onboarding plan for a new employee. Plan types: SEVEN_DAYS, THIRTY_DAYS, NINETY_DAYS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "plan_type": {"type": "string", "description": "SEVEN_DAYS, THIRTY_DAYS, or NINETY_DAYS (default THIRTY_DAYS)"},
                },
                "required": ["employee_name", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_offboarding_plan",
            "description": "Create an offboarding plan for a departing employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "departure_date": {"type": "string", "description": "Departure date YYYY-MM-DD"},
                    "departure_reason": {"type": "string", "description": "Reason for departure (optional)"},
                },
                "required": ["employee_name", "departure_date"],
            },
        },
    },
    # ── CHART GENERATION ──
    {
        "type": "function",
        "function": {
            "name": "generate_chart",
            "description": "Generate a chart for HR analytics. Use when user asks for visual analysis, statistics, or wants to 'see' data. Types: leave_by_status (bar), leave_by_type (pie), headcount_by_dept (horizontal bar), contract_distribution (pie), employee_risk_scores (grouped bar). Returns a base64 PNG image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_type": {
                        "type": "string",
                        "enum": ["leave_by_status", "leave_by_type", "headcount_by_dept", "contract_distribution", "employee_risk_scores"],
                        "description": "Type of chart to generate"
                    },
                    "employee_name": {"type": "string", "description": "Filter by employee name (only for employee_risk_scores, optional)"},
                    "limit": {"type": "integer", "description": "Max results (only for employee_risk_scores, default 10)"},
                },
                "required": ["chart_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_count",
            "description": (
                "Get the total number of employees in the company. "
                "Call this when the user asks 'how many employees', 'employee count', "
                "'nombre d employes', 'combien d employes', or similar questions. "
                "Returns the total employee count directly."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_user",
            "description": (
                "Get the current user's identity and role. "
                "Call this when the user asks 'who am I', 'what is my role', "
                "'what can I do', 'qui suis je', 'quel est mon role'. "
                "Returns the user's name, email, and role."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

TOOLS.extend(HR_ACTION_TOOLS)
TOOLS.extend(USER_TOOLS)
TOOLS.extend(CONTRACT_TOOLS)
TOOLS.extend(DEPT_TOOLS)
TOOLS.extend(FORMATION_TOOLS)
TOOLS.extend(TASK_TOOLS)
TOOLS.extend(LEAVE_BALANCE_TOOLS)
TOOLS.extend(SURVEY_TOOLS)
TOOLS.extend(ONBOARDING_TOOLS)

GENERATE_HR_DOC_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "generate_hr_document",
            "description": (
                "Generate a rich text/PDF document (e.g. contract, certificate, warning) for an employee. "
                "Use this when the user asks to generate a document or contract. "
                "This will create a PDF and return the URL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {
                        "type": "string",
                        "description": "Full name of the employee",
                    },
                    "document_type": {
                        "type": "string",
                        "description": "Type of document (e.g. contrat, attestation)",
                    },
                    "user_prompt": {
                        "type": "string",
                        "description": "The exact instruction or details for the document to be generated",
                    },
                },
                "required": ["employee_name", "document_type", "user_prompt"],
            },
        },
    },
]
TOOLS.extend(GENERATE_HR_DOC_TOOL)

# ── PDF DOCUMENT GENERATION TOOLS (exposed to LLM) ──
PDF_DOC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_work_certificate_pdf",
            "description": (
                "Generate a work certificate (attestation de travail) PDF for an employee. "
                "Use when the user asks for 'attestation de travail', 'attestation d emploi', "
                "'work certificate' or 'employment certificate' for a specific person. "
                "Only provide employee_name and city; other fields are auto-filled from the database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "job_title": {"type": "string", "description": "Employee job title (auto-filled if omitted)"},
                    "department": {"type": "string", "description": "Employee department (auto-filled if omitted)"},
                    "contract_type": {"type": "string", "description": "Contract type CDI/CDD/etc. (auto-filled if omitted)"},
                    "start_date": {"type": "string", "description": "Contract start date (auto-filled if omitted)"},
                    "city": {"type": "string", "description": "City of issuance (e.g. Abidjan)"},
                },
                "required": ["employee_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_leave_certificate_pdf",
            "description": (
                "Generate a leave certificate (certificat de congé) PDF for an employee. "
                "Use when the user asks for a leave/holiday certificate."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee"},
                    "leave_type": {"type": "string", "description": "Type of leave (e.g. Congé annuel)"},
                    "start_date": {"type": "string", "description": "Leave start date DD/MM/YYYY"},
                    "end_date": {"type": "string", "description": "Leave end date DD/MM/YYYY"},
                    "num_days": {"type": "string", "description": "Number of leave days"},
                    "status": {"type": "string", "description": "Leave status (Approuvé, En attente, etc.)"},
                    "city": {"type": "string", "description": "City of issuance"},
                },
                "required": ["employee_name", "leave_type", "start_date", "end_date", "num_days", "status"],
            },
        },
    },
]
TOOLS.extend(PDF_DOC_TOOLS)









def build_company_context(db: Session) -> str:
    parts = []
    parts.append("Company Name: Nexcore rh")
    parts.append("Legal Representative: AKMEL JEAN")
    parts.append("Address: paris sur-seine 9280")
    total_employees = db.query(Employee).count()
    parts.append(f"Total employees: {total_employees}")

    depts = db.query(Department).all()
    if depts:
        parts.append("Departments:")
        for d in depts:
            count = db.query(Employee).filter(Employee.department_id == d.id).count()
            parts.append(f"  - {d.name}: {count} employees")

    employees = db.query(Employee).all()
    if employees:
        parts.append("Employee details:")
        for emp in employees:
            user = emp.user
            dept_name = emp.department.name if emp.department else "N/A"
            pos_title = emp.position.title if emp.position else "N/A"
            salary = f"{emp.salary} EUR" if emp.salary else "N/A"
            parts.append(f"  - {user.prenom} {user.nom} | {pos_title} | {dept_name} | {salary} | Status: {emp.status.value}")

    return "\n".join(parts)


def _ensure_document_type(db: Session, type_name: str = "ai_generated_report") -> DocumentType:
    existing = db.query(DocumentType).filter(DocumentType.name == type_name).first()
    if existing:
        return existing
    try:
        with db.begin_nested():
            dt = DocumentType(name=type_name, description="Documents generes automatiquement par l'IA")
            db.add(dt)
            db.flush()
            return dt
    except exc.IntegrityError:
        return db.query(DocumentType).filter(DocumentType.name == type_name).first()


def _ensure_document_template(db: Session, name: str, content: str) -> DocumentTemplate:
    existing = db.query(DocumentTemplate).filter(DocumentTemplate.name == name).first()
    if existing:
        return existing
    try:
        with db.begin_nested():
            template = DocumentTemplate(
                name=name,
                content=content,
                description="Template cree automatiquement depuis la generation IA",
            )
            db.add(template)
            db.flush()
            return template
    except exc.IntegrityError:
        return db.query(DocumentTemplate).filter(DocumentTemplate.name == name).first()


def save_generated_document(
    title: str,
    content: str,
    requesting_user: User,
    db: Session,
    doc_type_name: str = "ai_generated_report",
    employee_id: int = None,
) -> dict:
    content = content.strip()

    # Ensure DocumentType exists
    dt = _ensure_document_type(db, doc_type_name)

    # Ensure DocumentTemplate exists (find-or-create)
    tmpl = _ensure_document_template(
        db,
        name=f"AI: {title[:90]}",
        content=content,
    )

    target_id = employee_id if employee_id else requesting_user.id

    doc_record = Document(
        employee_id=target_id,
        template_id=tmpl.id,
        document_type=doc_type_name,
        title=title,
        content=content,
        generated_by_ai=True,
        status=DocumentStatusEnum.FINAL,
        created_by=requesting_user.id,
    )
    db.add(doc_record)
    db.flush()
    doc_id = doc_record.id

    pdf_bytes = make_pdf(title, content, doc_type_name)
    file_url = upload_pdf(pdf_bytes, title)

    doc_record.file_url = file_url
    db.commit()

    return {
        "id": doc_id,
        "title": title,
        "content": content,
        "document_type": doc_type_name,
        "generated_by_ai": True,
        "pdf_url": f"/api/ai/documents/minio/{file_url.split('/', 1)[-1]}",
        "status": DocumentStatusEnum.FINAL.value,
    }


def generate_document_from_prompt(
    user_prompt: str,
    requesting_user: User,
    db: Session,
    title: str | None = None,
    employee_id: int = None,
) -> dict:
    company_data = build_company_context(db)

    system = (
        "You are SmartRH Document Generator by NexcoreRH. Generate a professional HR document in French based on the user's request. "
        "Format the document properly with a title, date, subject, body paragraphs, and signature block. "
        "NEVER use markdown symbols like **, *, _, #, or backticks. Write plain text only. "
        "Use ALL CAPS for section headers (e.g., INFORMATIONS DE L'EMPLOYE). "
        "Use simple dashes for lists (- item). "
        "Use the company data provided to make the document accurate and detailed. "
        "For working hours, use the standard company hours: Monday to Friday, 10h00 to 18h00, unless specified otherwise.\n\n"
        f"Company Data:\n{company_data}\n\n"
    )

    if employee_id:
        emp = db.query(Employee).filter(Employee.user_id == employee_id).first()
        if emp:
            emp_details = (
                f"Target Employee Full Details:\n"
                f"- Nom complet: {emp.user.prenom} {emp.user.nom}\n"
                f"- Adresse: {emp.adresse or 'Non renseignée'}\n"
                f"- Nationalité: {emp.nationalite or 'Non renseignée'}\n"
                f"- Date de naissance: {emp.date_naissance or 'Non renseignée'}\n"
                f"- Sexe: {emp.sexe or 'Non renseigné'}\n"
                f"- Téléphone: {emp.numero_telephone or 'Non renseigné'}\n"
                f"- Poste: {emp.position.title if emp.position else 'Non renseigné'}\n"
                f"- Département: {emp.department.name if emp.department else 'Non renseigné'}\n"
                f"- Salaire: {emp.salary} EUR\n"
                f"- Date d'embauche: {emp.hire_date or 'Non renseignée'}\n"
                f"USE THESE EXACT DETAILS to fill in the document (address, name, etc.). DO NOT use placeholders like [adresse à compléter] if the information is provided above."
            )
            system += emp_details

    doc_content = call_llm(system, user_prompt, temperature=0.3, max_tokens=2048)
    if not doc_content:
        doc_content = "Document could not be generated. Please try again."

    doc_title = title or f"Document genere - {user_prompt[:50]}"

    return save_generated_document(
        title=doc_title,
        content=doc_content,
        requesting_user=requesting_user,
        db=db,
        employee_id=employee_id,
    )

def generate_hr_document(db: Session, user: User, employee_id: int, document_type: str, user_prompt: str) -> dict:
    return generate_document_from_prompt(
        user_prompt=user_prompt,
        requesting_user=user,
        db=db,
        title=document_type.capitalize(),
        employee_id=employee_id,
    )


TOOL_REGISTRY = {


    "create_leave": create_leave,
    "approve_leave": approve_leave,
    "log_absence": log_absence,
    "send_notification": send_notification,
    "create_hr_ticket": create_hr_ticket,
    "resolve_hr_ticket": resolve_hr_ticket,
    "update_employee_status": update_employee_status,
    "reassign_employee": reassign_employee,
    "create_alert": create_alert,
    "create_user": create_user,
    "update_employee_salary": update_employee_salary,
    "assign_employee_role": assign_employee_role,
    "create_contract": create_contract,
    "create_department": create_department,
    "create_position": create_position,
    "create_formation": create_formation,
    "enroll_in_formation": enroll_in_formation,
    "update_onboarding_task_status": update_onboarding_task_status,
    "update_offboarding_task_status": update_offboarding_task_status,
    "update_onboarding_plan_status": update_onboarding_plan_status,
    "update_offboarding_plan_status": update_offboarding_plan_status,
    "update_leave_balance": update_leave_balance,
    "create_survey": create_survey,
    "add_survey_question": add_survey_question,
    "submit_survey_response": submit_survey_response,
    "generate_onboarding_plan": generate_onboarding,
    "generate_offboarding_plan": generate_offboarding,
    "get_onboarding_plans": get_onboarding_plans,
    "get_offboarding_plans": get_offboarding_plans,
    "get_employee_count": get_employee_count,
    "get_current_user": get_current_user,
    "create_employee": create_employee,
    "update_user": update_user,
    "create_risk_score": create_risk_score,
    "create_recommendation": create_recommendation,
    "process_approval": process_approval,
    "update_alert_status": update_alert_status,
    "get_alerts": get_alerts,
    "get_approval_workflows": get_approval_workflows,
    "get_risk_scores": get_risk_scores,
    "get_recommendations": get_recommendations,
    "update_leave": update_leave,
    "update_absence": update_absence,
    "update_contract": update_contract,
    "create_onboarding_plan": create_onboarding_plan,
    "create_offboarding_plan": create_offboarding_plan,
    "generate_chart": generate_chart,
    "generate_hr_document": generate_hr_document,
    "generate_work_certificate_pdf": generate_work_certificate_pdf,
    "generate_report_pdf": generate_report_pdf,
    "generate_leave_certificate_pdf": generate_leave_certificate_pdf,
}

_DB_TOOLS = {
    "create_leave", "approve_leave", "log_absence", "send_notification",
    "create_hr_ticket", "resolve_hr_ticket", "update_employee_status",
    "reassign_employee", "create_alert",
    "create_user", "update_employee_salary", "assign_employee_role",
    "create_contract", "create_department", "create_position",
    "create_formation", "enroll_in_formation",
    "update_onboarding_task_status", "update_offboarding_task_status",
    "update_onboarding_plan_status", "update_offboarding_plan_status",
    "update_leave_balance",
    "create_survey", "add_survey_question", "submit_survey_response",
    "generate_onboarding_plan", "generate_offboarding_plan", "generate_hr_document",
    "get_onboarding_plans", "get_offboarding_plans",
    "get_employee_count", "get_current_user",
    "update_leave", "update_absence", "update_contract",
    "create_onboarding_plan", "create_offboarding_plan",
    "generate_chart",
    "create_employee", "update_user", "create_risk_score",
    "create_recommendation", "process_approval", "update_alert_status",
    "get_alerts", "get_approval_workflows", "get_risk_scores",
    "get_recommendations",
}

def execute_tool(tool_call: dict, db: Session = None, user: User = None) -> dict:
    func_name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"])

    func = TOOL_REGISTRY.get(func_name)
    if not func:
        return {"status": "error", "message": f"Tool '{func_name}' not found."}

    try:
        # ── Role-gated PDF generation tools — auto-fill from DB ──
        _PDF_GEN_TOOLS = {"generate_work_certificate_pdf", "generate_report_pdf", "generate_leave_certificate_pdf"}
        if func_name in _PDF_GEN_TOOLS:
            if user is None:
                return {"status": "error", "message": "Authenticated user required."}
            if user.role.value not in ["admin", "rh"]:
                return {"status": "error", "message": "Accès refusé : seuls les rôles Admin et RH peuvent générer des documents."}

            # Auto-enrich arguments from DB for work/leave certificate
            emp_rec = None
            if func_name in ("generate_work_certificate_pdf", "generate_leave_certificate_pdf") and db is not None:
                emp_name = arguments.get("employee_name", "")
                emp_rec = db.query(Employee).join(User, Employee.user_id == User.id).filter(
                    safunc.concat(User.prenom, ' ', User.nom).ilike(f"%{emp_name}%")
                ).first() if emp_name else None

                if emp_rec:
                    from models.features import Contract
                    contract = db.query(Contract).filter(Contract.user_id == emp_rec.user_id).first()
                    if not arguments.get("job_title"):
                        arguments["job_title"] = emp_rec.position.title if emp_rec.position else "Employé"
                    if not arguments.get("department"):
                        arguments["department"] = emp_rec.department.name if emp_rec.department else "Général"
                    if not arguments.get("contract_type"):
                        arguments["contract_type"] = contract.contract_type if contract else "CDI"
                    if not arguments.get("start_date"):
                        arguments["start_date"] = str(contract.start_date) if contract and contract.start_date else "01/01/2024"
                    if not arguments.get("city"):
                        arguments["city"] = "Abidjan"
                    if func_name == "generate_leave_certificate_pdf":
                        if not arguments.get("employee_id"):
                            arguments["employee_id"] = str(emp_rec.user_id)
                        if not arguments.get("contract_start_date"):
                            arguments["contract_start_date"] = str(contract.start_date) if contract and contract.start_date else "N/A"
                        if not arguments.get("hr_manager_name"):
                            arguments["hr_manager_name"] = f"{user.prenom} {user.nom}"

            result = func(**arguments)

            # ── Save generated document to DB so it appears in document management ──
            if db is not None and isinstance(result, str) and emp_rec is not None:
                try:
                    _emp_name = arguments.get("employee_name", "")
                    _doc_type_map = {
                        "generate_work_certificate_pdf": "attestation_travail",
                        "generate_leave_certificate_pdf": "certificat_conge",
                        "generate_report_pdf": "rapport",
                    }
                    _doc_type = _doc_type_map.get(func_name, "ai_generated")
                    _doc_title_map = {
                        "generate_work_certificate_pdf": f"Attestation de travail - {_emp_name}",
                        "generate_leave_certificate_pdf": f"Certificat de congé - {_emp_name}",
                        "generate_report_pdf": arguments.get("title", "Rapport IA"),
                    }
                    _doc_title = _doc_title_map.get(func_name, f"Document IA - {_emp_name}")

                    from models.features import DocumentType, DocumentTemplate, DocumentStatusEnum
                    _type_rec = db.query(DocumentType).filter(DocumentType.name == _doc_type).first()
                    if not _type_rec:
                        _type_rec = DocumentType(name=_doc_type, description=f"Généré par IA : {_doc_type}")
                        db.add(_type_rec)
                        db.flush()

                    _tmpl_name = f"Template IA {_doc_type}"
                    _tmpl_rec = db.query(DocumentTemplate).filter(DocumentTemplate.name == _tmpl_name).first()
                    if not _tmpl_rec:
                        _tmpl_rec = DocumentTemplate(
                            name=_tmpl_name,
                            content=_doc_title,
                            description=f"Modèle automatique IA pour {_doc_type}"
                        )
                        db.add(_tmpl_rec)
                        db.flush()

                    _doc_rec = Document(
                        employee_id=emp_rec.user_id,
                        template_id=_tmpl_rec.id,
                        document_type=_doc_type,
                        title=_doc_title,
                        content=_doc_title,
                        generated_by_ai=True,
                        status=DocumentStatusEnum.FINAL,
                        created_by=user.id,
                        file_url=result,
                        is_sent=False,  # L'employé ne voit le document que si le RH le valide et l'envoie

                    )
                    db.add(_doc_rec)
                    db.commit()
                except Exception as _save_err:
                    print(f"[execute_tool] Failed to save document record: {_save_err}")
                    try:
                        db.rollback()
                    except Exception:
                        pass

        elif func_name in _DB_TOOLS:
            if db is None:
                return {"status": "error", "message": "Database connection required."}

            if func_name in ("generate_onboarding_plan", "generate_offboarding_plan", "generate_hr_document"):
                if user is None:
                    return {"status": "error", "message": "Authenticated user required."}
                if user.role.value not in ["admin", "rh"]:
                    return {"status": "error", "message": "Access denied: Only Admin and RH roles can generate plans/documents."}
                employee_name = arguments.pop("employee_name", "")
                emp_rec = db.query(Employee).join(User, Employee.user_id == User.id).filter(
                    safunc.concat(User.prenom, ' ', User.nom).ilike(f"%{employee_name}%")
                ).first()
                if not emp_rec:
                    return {"status": "error", "message": f"Employee '{employee_name}' not found."}
                arguments["employee_id"] = emp_rec.user_id
                result = func(db=db, user=user, **arguments)
            elif func_name in ("get_onboarding_plans", "get_offboarding_plans"):
                employee_name = arguments.pop("employee_name", "")
                result = func(db=db, employee_name=employee_name)
            elif func_name == "get_current_user":
                if user is None:
                    return {"status": "error", "message": "Authenticated user required."}
                result = func(user=user)
            elif func_name in ("get_alerts", "get_risk_scores", "get_recommendations"):
                result = func(db=db, user=user, **arguments)
            else:
                result = func(db=db, **arguments)

        else:
            result = func(**arguments)

        if isinstance(result, dict):
            return result
        if isinstance(result, list):
            return {"status": "success", "data": result}
        if isinstance(result, str):
            key = result.split("/", 1)[-1] if "/" in result else result
            return {
                "status": "success",
                "pdf_url": f"/api/ai/documents/minio/{key}",
                "file_name": key,
                "message": "Document généré avec succès.",
            }
        return {
            "status": "success",
            "file_name": Path(result).name if result else "",
            "file_path": str(result),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

