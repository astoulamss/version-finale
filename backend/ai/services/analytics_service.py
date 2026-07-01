from sqlalchemy.orm import Session
from models.user import User, RoleEnum
from models.features import Leave, Contract
from models.employees import Employee
from datetime import date, timedelta


def analyze_risk(
    analysis_type: str,
    user: User,
    db: Session,
    department_id: int | None = None,
    period_start: date | None = None,
    period_end: date | None = None,
) -> dict:
    if user.role not in (RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION):
        return {
            "analysis_type": analysis_type,
            "risk_level": "unknown",
            "risk_score": 0.0,
            "factors": ["Access denied"],
            "recommendations": [],
            "disclaimer": "You are not authorized to access this analysis.",
        }
    if analysis_type == "turnover":
        return _analyze_turnover(user, db, department_id)
    elif analysis_type == "absenteeism":
        return _analyze_absenteeism(user, db, department_id, period_start, period_end)
    elif analysis_type == "engagement":
        return _analyze_engagement(user, db, department_id)
    else:
        return {
            "analysis_type": analysis_type,
            "risk_level": "unknown",
            "risk_score": 0.0,
            "factors": ["Unknown analysis type"],
            "recommendations": ["Please specify: turnover, absenteeism, or engagement"],
            "disclaimer": "This is a statistical placeholder analysis. ML model not yet deployed.",
        }


def _analyze_turnover(user: User, db: Session, department_id: int | None = None) -> dict:
    query = db.query(Employee)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    total = query.count()

    recent = query.filter(
        Employee.status == "inactive",
        Employee.updated_at >= date.today() - timedelta(days=180),
    ).count()

    turnover_rate = (recent / total * 100) if total > 0 else 0

    risk_level = "low"
    risk_score = turnover_rate / 20
    if turnover_rate > 15:
        risk_level = "high"
    elif turnover_rate > 8:
        risk_level = "medium"

    return {
        "analysis_type": "turnover",
        "risk_level": risk_level,
        "risk_score": min(risk_score, 1.0),
        "factors": [
            f"Turnover rate: {turnover_rate:.1f}% in last 6 months",
            f"Total employees: {total}",
            f"Recent departures: {recent}",
        ],
        "recommendations": _get_turnover_recommendations(turnover_rate),
        "disclaimer": "This is a statistical placeholder analysis. ML model not yet deployed.",
    }


def _analyze_absenteeism(
    user: User, db: Session,
    department_id: int | None = None,
    period_start: date | None = None,
    period_end: date | None = None,
) -> dict:
    from models.features import LeaveStatusEnum, LeaveTypeEnum

    query = db.query(Leave).filter(Leave.status == LeaveStatusEnum.APPROVED)
    if department_id:
        query = query.join(Employee, Employee.user_id == Leave.employee_id).filter(
            Employee.department_id == department_id
        )
    if period_start:
        query = query.filter(Leave.start_date >= period_start)
    if period_end:
        query = query.filter(Leave.end_date <= period_end)

    total_leaves = query.count()
    sick_leaves = query.filter(Leave.leave_type == LeaveTypeEnum.SICK).count()

    risk_level = "low"
    risk_score = 0.0
    if sick_leaves > 20:
        risk_level = "high"
        risk_score = 0.8
    elif sick_leaves > 10:
        risk_level = "medium"
        risk_score = 0.5

    return {
        "analysis_type": "absenteeism",
        "risk_level": risk_level,
        "risk_score": risk_score,
        "factors": [
            f"Total approved leaves: {total_leaves}",
            f"Sick leaves: {sick_leaves}",
        ],
        "recommendations": [
            "Consider wellness programs if sick leave is high",
            "Review department workload distribution",
        ],
        "disclaimer": "This is a statistical placeholder analysis. ML model not yet deployed.",
    }


def _analyze_engagement(user: User, db: Session, department_id: int | None = None) -> dict:
    return {
        "analysis_type": "engagement",
        "risk_level": "medium",
        "risk_score": 0.4,
        "factors": [
            "Engagement analysis requires survey data (not yet implemented)",
            "Proxy metrics: leave frequency, contract renewals",
        ],
        "recommendations": [
            "Deploy employee engagement surveys",
            "Monitor leave patterns as early indicators",
        ],
        "disclaimer": "This is a statistical placeholder analysis. ML model not yet deployed. Survey data integration required for accurate engagement prediction.",
    }


def _get_turnover_recommendations(rate: float) -> list[str]:
    if rate > 15:
        return [
            "Urgent: Conduct exit interviews for recent departures",
            "Review compensation and benefits packages",
            "Implement retention bonuses for key roles",
            "Schedule skip-level meetings to surface concerns",
        ]
    elif rate > 8:
        return [
            "Monitor departure patterns by department",
            "Review career development opportunities",
            "Consider stay interviews with high-performing employees",
        ]
    return [
        "Continue regular check-ins and career development",
        "Maintain current retention strategies",
    ]
