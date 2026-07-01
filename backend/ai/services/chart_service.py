import io
import base64
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams["figure.dpi"] = 120
plt.rcParams["figure.figsize"] = (10, 5.5)
plt.rcParams["font.size"] = 11
COLORS = ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]

def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def chart_leave_by_status(db: Session) -> dict:
    rows = db.execute(
        text("SELECT status, COUNT(*) AS cnt FROM leaves GROUP BY status ORDER BY cnt DESC")
    ).fetchall()
    labels = [r.status for r in rows]
    values = [r.cnt for r in rows]
    if not labels:
        return {"status": "error", "message": "No leave data found."}
    fig, ax = plt.subplots()
    ax.bar(labels, values, color=COLORS[:len(labels)])
    for i, v in enumerate(values):
        ax.text(i, v + 0.1, str(v), ha="center", fontweight="bold")
    ax.set_title("Leave Requests by Status")
    ax.set_ylabel("Count")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    return {
        "status": "success",
        "chart": _fig_to_b64(fig),
        "title": "Leave Requests by Status",
        "message": f"Leave breakdown: {', '.join(f'{l}={v}' for l, v in zip(labels, values))}",
    }


def chart_leave_by_type(db: Session) -> dict:
    rows = db.execute(
        text("SELECT leave_type, COUNT(*) AS cnt FROM leaves GROUP BY leave_type ORDER BY cnt DESC")
    ).fetchall()
    labels = [r.leave_type for r in rows]
    values = [r.cnt for r in rows]
    if not labels:
        return {"status": "error", "message": "No leave data found."}
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct="%1.1f%%", startangle=90,
        colors=COLORS[:len(labels)], wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    ax.legend(wedges, labels, loc="lower left", bbox_to_anchor=(0, -0.15), ncol=3, fontsize=9)
    ax.set_title("Leave Distribution by Type")
    return {
        "status": "success",
        "chart": _fig_to_b64(fig),
        "title": "Leave Distribution by Type",
        "message": f"Leave types: {', '.join(f'{l}={v}' for l, v in zip(labels, values))}",
    }


def chart_headcount_by_dept(db: Session) -> dict:
    rows = db.execute(
        text("SELECT COALESCE(d.name, 'No Dept') AS dept, COUNT(*) AS cnt "
             "FROM employees e LEFT JOIN departments d ON d.id = e.department_id "
             "GROUP BY d.name ORDER BY cnt DESC")
    ).fetchall()
    labels = [r.dept for r in rows]
    values = [r.cnt for r in rows]
    if not labels:
        return {"status": "error", "message": "No employee data found."}
    fig, ax = plt.subplots(figsize=(10, max(5, len(labels) * 0.4)))
    ax.barh(labels, values, color=COLORS[:len(labels)])
    for i, v in enumerate(values):
        ax.text(v + 0.1, i, str(v), va="center", fontweight="bold")
    ax.set_title("Headcount by Department")
    ax.set_xlabel("Employees")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.tight_layout()
    return {
        "status": "success",
        "chart": _fig_to_b64(fig),
        "title": "Headcount by Department",
        "message": f"Departments: {', '.join(f'{l}={v}' for l, v in zip(labels, values))}",
    }


def chart_contract_distribution(db: Session) -> dict:
    rows = db.execute(
        text("SELECT contract_type, COUNT(*) AS cnt FROM contracts GROUP BY contract_type ORDER BY cnt DESC")
    ).fetchall()
    labels = [r.contract_type for r in rows]
    values = [r.cnt for r in rows]
    if not labels:
        return {"status": "error", "message": "No contract data found."}
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct="%1.1f%%", startangle=90,
        colors=COLORS[:len(labels)], wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    ax.legend(wedges, labels, loc="lower left", bbox_to_anchor=(0, -0.15), ncol=3, fontsize=9)
    ax.set_title("Contract Distribution")
    return {
        "status": "success",
        "chart": _fig_to_b64(fig),
        "title": "Contract Distribution",
        "message": f"Contracts: {', '.join(f'{l}={v}' for l, v in zip(labels, values))}",
    }


def chart_employee_risk_scores(db: Session, employee_name: str = "", limit: int = 10) -> dict:
    rows = db.execute(
        text("SELECT u.nom || ' ' || u.prenom AS en, r.turnover_risk, r.burnout_risk, r.engagement_risk, r.generated_at "
             "FROM risk_scores r JOIN users u ON u.id = r.employee_id "
             "WHERE (:en = '' OR LOWER(u.nom || ' ' || u.prenom) LIKE LOWER('%' || :en || '%')) "
             "ORDER BY r.generated_at DESC LIMIT :lim"),
        {"en": employee_name, "lim": limit},
    ).fetchall()
    if not rows:
        return {"status": "error", "message": "No risk score data found."}
    labels = [r.en for r in rows]
    fig, ax = plt.subplots(figsize=(10, max(5, len(labels) * 0.35)))
    x = range(len(labels))
    w = 0.25
    ax.barh([i + w for i in x], [r.turnover_risk for r in rows], w, label="Turnover", color=COLORS[0])
    ax.barh([i for i in x], [r.burnout_risk for r in rows], w, label="Burnout", color=COLORS[1])
    ax.barh([i - w for i in x], [r.engagement_risk for r in rows], w, label="Engagement", color=COLORS[2])
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Risk Score")
    ax.set_title("Employee Risk Scores")
    ax.legend(fontsize=9)
    fig.tight_layout()
    return {
        "status": "success",
        "chart": _fig_to_b64(fig),
        "title": "Employee Risk Scores",
        "message": f"Risk scores for {len(rows)} employee(s).",
    }


CHART_FUNCTIONS = {
    "leave_by_status": chart_leave_by_status,
    "leave_by_type": chart_leave_by_type,
    "headcount_by_dept": chart_headcount_by_dept,
    "contract_distribution": chart_contract_distribution,
    "employee_risk_scores": chart_employee_risk_scores,
}


def generate_chart(
    db: Session,
    chart_type: str,
    employee_name: str = "",
    limit: int = 10,
) -> dict:
    func = CHART_FUNCTIONS.get(chart_type)
    if not func:
        return {
            "status": "error",
            "message": f"Unknown chart type '{chart_type}'. Available: {', '.join(CHART_FUNCTIONS.keys())}",
        }
    if chart_type == "employee_risk_scores":
        return func(db, employee_name=employee_name, limit=limit)
    return func(db)
