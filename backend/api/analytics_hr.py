from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from database.db import get_db
from core.security import get_current_user, require_role
from models.user import User, RoleEnum
from models.employees import Employee, EmployeeStatusEnum, Department
from models.features import Contract, SurveyAnswer, SurveyQuestion, Survey, SurveyResponse
from models.absences import Absence
from fastapi_cache.decorator import cache
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/analytics-hr", tags=["HR Analytics"])

class SnapshotResponse(BaseModel):
    total_employees: int
    active_employees: int
    average_age: Optional[float]
    gender_distribution: dict
    turnover_rate: float
    turnover_by_department: dict = {}

class PayrollResponse(BaseModel):
    total_payroll: float
    avg_salary: float
    by_department: dict
    evolution_6_months: dict

class AbsenteeismResponse(BaseModel):
    total_hours: float
    by_type: dict
    by_month: dict
    by_department: dict = {}
    rate: Optional[float] = None

class EngagementResponse(BaseModel):
    average_score: Optional[float]
    total_responses: int
    by_department: dict = {}

def calculate_age(born: date) -> int:
    today = date.today()
    if not born:
        return 0
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

@router.get("/snapshot", response_model=SnapshotResponse)
@cache(expire=60)
def get_hr_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION]))
):
    employees = db.query(Employee).all()
    
    total = len(employees)
    active = [e for e in employees if e.status == EmployeeStatusEnum.ACTIVE]
    
    # Calculate Average Age
    ages = [calculate_age(e.date_naissance) for e in active if e.date_naissance]
    avg_age = sum(ages) / len(ages) if ages else None
    
    # Gender Distribution
    genders = {"Homme": 0, "Femme": 0, "Autre/Non renseigné": 0}
    for e in active:
        if e.sexe and "hom" in e.sexe.lower():
            genders["Homme"] += 1
        elif e.sexe and "fem" in e.sexe.lower():
            genders["Femme"] += 1
        else:
            genders["Autre/Non renseigné"] += 1
            
    # Turnover (Inactive / Total historical or specific timeframe, here simple ratio of inactive)
    turnover_rate = ((total - len(active)) / total * 100) if total > 0 else 0.0

    # Turnover par département
    dept_stats = {}
    for e in employees:
        dept_name = e.department.name if e.department else "Sans département"
        if dept_name not in dept_stats:
            dept_stats[dept_name] = {"total": 0, "active": 0}
        dept_stats[dept_name]["total"] += 1
        if e.status == EmployeeStatusEnum.ACTIVE:
            dept_stats[dept_name]["active"] += 1

    turnover_by_dept = {}
    for dept, stats in dept_stats.items():
        if stats["total"] > 0:
            rate = ((stats["total"] - stats["active"]) / stats["total"]) * 100
            turnover_by_dept[dept] = round(rate, 2)

    return SnapshotResponse(
        total_employees=len(active),
        active_employees=len(active),
        average_age=round(avg_age, 1) if avg_age else None,
        gender_distribution=genders,
        turnover_rate=round(turnover_rate, 2),
        turnover_by_department=turnover_by_dept
    )

class TurnoverEvolutionResponse(BaseModel):
    by_month: dict  # { "2026-01": 2.5, "2026-02": 3.1, ... }

@router.get("/turnover-evolution", response_model=TurnoverEvolutionResponse)
@cache(expire=60)
def get_turnover_evolution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION]))
):
    from dateutil.relativedelta import relativedelta
    import calendar

    today = date.today()
    all_employees = db.query(Employee).all()

    evolution = {}
    for i in range(5, -1, -1):
        target_month = today - relativedelta(months=i)
        _, last_day = calendar.monthrange(target_month.year, target_month.month)
        start_of_month = target_month.replace(day=1)
        end_of_month = target_month.replace(day=last_day)
        month_label = target_month.strftime("%Y-%m")

        # Count employees who left (departure_date) during this month
        departed_this_month = sum(
            1 for e in all_employees
            if e.departure_date and start_of_month <= e.departure_date <= end_of_month
        )

        # Headcount at start of month
        headcount = sum(
            1 for e in all_employees
            if e.hire_date and e.hire_date <= end_of_month
        )

        rate = round((departed_this_month / headcount * 100), 2) if headcount > 0 else 0.0
        evolution[month_label] = rate

    return TurnoverEvolutionResponse(by_month=evolution)

@router.get("/payroll", response_model=PayrollResponse)
@cache(expire=60)
def get_payroll_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION]))
):
    from dateutil.relativedelta import relativedelta
    import calendar
    
    all_employees = db.query(Employee).all()
    active_employees = [e for e in all_employees if e.status == EmployeeStatusEnum.ACTIVE]
    
    total_payroll = 0.0
    by_dept = {}
    
    for emp in active_employees:
        salary = float(emp.salary) if emp.salary else 0.0
        total_payroll += salary
        
        dept_name = emp.department.name if emp.department else "Sans département"
        by_dept[dept_name] = by_dept.get(dept_name, 0.0) + salary
        
    avg_salary = total_payroll / len(active_employees) if active_employees else 0.0
    
    # Calculate evolution over last 6 months
    evolution = {}
    today = date.today()
    
    for i in range(5, -1, -1):
        target_month = today - relativedelta(months=i)
        start_of_month = target_month.replace(day=1)
        _, last_day = calendar.monthrange(target_month.year, target_month.month)
        end_of_month = target_month.replace(day=last_day)
        
        month_label = target_month.strftime("%Y-%m")
        month_total = 0.0
        
        for emp in all_employees:
            if not emp.salary:
                continue
                
            hire_date = emp.hire_date or date.min
            departure_date = emp.departure_date or date.max
            
            # An employee was active during this month if they were hired before the end of the month
            # and left after the start of the month
            if hire_date <= end_of_month and departure_date >= start_of_month:
                month_total += float(emp.salary)
                
        evolution[month_label] = round(month_total, 2)
    
    return PayrollResponse(
        total_payroll=round(total_payroll, 2),
        avg_salary=round(avg_salary, 2),
        by_department={k: round(v, 2) for k, v in by_dept.items()},
        evolution_6_months=evolution
    )

@router.get("/absenteeism", response_model=AbsenteeismResponse)
@cache(expire=60)
def get_absenteeism_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION]))
):
    absences = db.query(Absence).all()
    
    total_hours = 0.0
    by_type = {}
    by_month = {}
    by_dept = {}

    employees = db.query(Employee).all()
    user_dept_map = {e.user_id: (e.department.name if e.department else "Sans département") for e in employees}
    
    for abs in absences:
        if abs.start_date and abs.end_date:
            hours = (abs.end_date - abs.start_date).total_seconds() / 3600
            if hours > 0:
                total_hours += hours
                abs_type = abs.absence_type.value if hasattr(abs.absence_type, 'value') else str(abs.absence_type)
                by_type[abs_type] = by_type.get(abs_type, 0.0) + hours
                
                month = abs.start_date.strftime("%Y-%m")
                by_month[month] = by_month.get(month, 0.0) + hours
                
                dept_name = user_dept_map.get(abs.employee_id, "Sans département")
                by_dept[dept_name] = by_dept.get(dept_name, 0.0) + hours

    current_month = date.today().strftime("%Y-%m")
    current_month_hours = by_month.get(current_month, 0.0)
    active_employees = sum(1 for e in employees if e.status == EmployeeStatusEnum.ACTIVE)
    
    rate = 0.0
    if active_employees > 0:
        rate = (current_month_hours / (active_employees * 151.67)) * 100

    return AbsenteeismResponse(
        total_hours=round(total_hours, 2),
        by_type={k: round(v, 2) for k, v in by_type.items()},
        by_month={k: round(v, 2) for k, v in sorted(by_month.items())[-6:]}, # Last 6 months
        by_department={k: round(v, 2) for k, v in by_dept.items()},
        rate=round(rate, 2)
    )

@router.get("/engagement", response_model=EngagementResponse)
@cache(expire=60)
def get_engagement_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION]))
):
    # Filter only rating questions
    answers = db.query(SurveyAnswer, SurveyResponse.employee_id).join(SurveyQuestion, SurveyAnswer.question_id == SurveyQuestion.id).join(SurveyResponse, SurveyAnswer.response_id == SurveyResponse.id).filter(SurveyQuestion.question_type == 'rating').all()
    
    valid_scores = []
    dept_scores = {}
    unique_participants = set()

    employees = db.query(Employee).all()
    emp_dept_map = {e.id: (e.department.name if e.department else "Sans département") for e in employees}

    for answer, emp_id in answers:
        if answer.score is not None:
            score = float(answer.score)
            valid_scores.append(score)
            unique_participants.add(emp_id)
            dept_name = emp_dept_map.get(emp_id, "Sans département")
            if dept_name not in dept_scores:
                dept_scores[dept_name] = []
            dept_scores[dept_name].append(score)

    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else None
    
    by_department = {}
    for dept, scores in dept_scores.items():
        if scores:
            by_department[dept] = round(sum(scores) / len(scores), 2)

    return EngagementResponse(
        average_score=round(avg_score, 2) if avg_score else None,
        total_responses=len(unique_participants),
        by_department=by_department
    )

class SatisfactionResponse(BaseModel):
    average_score: Optional[float]
    total_responses: int
    by_department: dict = {}

@router.get("/satisfaction", response_model=SatisfactionResponse)
@cache(expire=60)
def get_satisfaction_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.DIRECTION]))
):
    # Questions notées uniquement dans les sondages dont le titre contient "satisfaction"
    answers = db.query(SurveyAnswer, SurveyResponse.employee_id)\
        .join(SurveyQuestion, SurveyAnswer.question_id == SurveyQuestion.id)\
        .join(SurveyResponse, SurveyAnswer.response_id == SurveyResponse.id)\
        .join(Survey, SurveyQuestion.survey_id == Survey.id)\
        .filter(SurveyQuestion.question_type == 'rating')\
        .filter(func.lower(Survey.title).like('%satisfaction%'))\
        .all()
    
    valid_scores = []
    dept_scores = {}
    unique_participants = set()

    employees = db.query(Employee).all()
    emp_dept_map = {e.id: (e.department.name if e.department else "Sans département") for e in employees}

    for answer, emp_id in answers:
        if answer.score is not None:
            score = float(answer.score)
            valid_scores.append(score)
            unique_participants.add(emp_id)
            dept_name = emp_dept_map.get(emp_id, "Sans département")
            if dept_name not in dept_scores:
                dept_scores[dept_name] = []
            dept_scores[dept_name].append(score)

    # Conversion en pourcentage. Si la note maximale est inconnue, on suppose sur 5 par défaut pour ces calculs.
    # Dans SurveyAnswer, score_percentage = (score / 5) * 100
    percentage_scores = [(s / 5.0) * 100 for s in valid_scores]
    avg_percentage = sum(percentage_scores) / len(percentage_scores) if percentage_scores else None
    
    by_department = {}
    for dept, scores in dept_scores.items():
        if scores:
            dept_percentages = [(s / 5.0) * 100 for s in scores]
            by_department[dept] = round(sum(dept_percentages) / len(dept_percentages), 2)

    return SatisfactionResponse(
        average_score=round(avg_percentage, 2) if avg_percentage else None,
        total_responses=len(unique_participants),
        by_department=by_department
    )

