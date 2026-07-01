import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.db import get_db
from models.ml_features import Timesheet, TimesheetStatusEnum
from models.user import User, RoleEnum
from models.employees import Employee
from schemas.ml_features import TimesheetCreate, TimesheetResponse
from core.security import get_current_user
from datetime import date, datetime, timedelta, time
from typing import List

router = APIRouter(
    prefix="/api/timesheets",
    tags=["Timesheets"],
)

def check_ip_address(request: Request):
    client_ip = request.headers.get("X-Ydays-Client-IP")
    if not client_ip:
        client_ip = request.headers.get("X-Forwarded-For")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.headers.get("X-Real-IP", request.client.host)

    allowed_ips_env = os.getenv("ALLOWED_OFFICE_IPS", "")
    if not allowed_ips_env:
        return client_ip
    
    allowed_ips = [ip.strip() for ip in allowed_ips_env.split(",") if ip.strip()]
    if client_ip not in allowed_ips:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Pointage refusé. Votre adresse IP ({client_ip}) n'appartient pas au réseau de l'entreprise."
        )
    return client_ip

@router.get("/today", response_model=TimesheetResponse)
def get_today_timesheet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Profil employé non trouvé.")
        
    today = date.today()
    ts = db.query(Timesheet).filter(Timesheet.employee_id == employee.id, Timesheet.date == today).first()
    if not ts:
        raise HTTPException(status_code=404, detail="Aucun pointage aujourd'hui.")
    return ts

@router.post("/clock-in", response_model=TimesheetResponse)
def clock_in(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enregistre l'arrivée de l'employé pour aujourd'hui.
    """
    client_ip = check_ip_address(request)
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Profil employé non trouvé.")
        
    today = date.today()
    existing = db.query(Timesheet).filter(Timesheet.employee_id == employee.id, Timesheet.date == today).first()
    
    if existing:
        if existing.clock_in and not existing.clock_out:
            raise HTTPException(status_code=400, detail="Vous avez déjà pointé votre arrivée aujourd'hui.")
        raise HTTPException(status_code=400, detail="Vous avez déjà pointé pour cette date.")
        
    new_timesheet = Timesheet(
        employee_id=employee.id,
        date=today,
        clock_in=datetime.now(),
        ip_address=client_ip,
        status=TimesheetStatusEnum.PENDING
    )
    db.add(new_timesheet)
    db.commit()
    db.refresh(new_timesheet)
    return new_timesheet

@router.post("/clock-out", response_model=TimesheetResponse)
def clock_out(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enregistre le départ de l'employé et calcule automatiquement les heures travaillées.
    """
    client_ip = check_ip_address(request)
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Profil employé non trouvé.")
        
    today = date.today()
    ts = db.query(Timesheet).filter(Timesheet.employee_id == employee.id, Timesheet.date == today).first()
    
    if not ts:
        raise HTTPException(status_code=400, detail="Vous n'avez pas pointé d'arrivée aujourd'hui.")
    if ts.clock_out:
        raise HTTPException(status_code=400, detail="Vous avez déjà pointé votre départ aujourd'hui.")
        
    if ts.clock_in.tzinfo:
        from datetime import timezone
        ts.clock_out = datetime.now(ts.clock_in.tzinfo)
    else:
        ts.clock_out = datetime.now()
    
    # Calcul de la déduction de la pause (12:00 à 13:00)
    pause_start = datetime.combine(today, time(12, 0))
    pause_end = datetime.combine(today, time(13, 0))
    
    if ts.clock_in.tzinfo:
        pause_start = pause_start.replace(tzinfo=ts.clock_in.tzinfo)
        pause_end = pause_end.replace(tzinfo=ts.clock_in.tzinfo)
        
    overlap_start = max(ts.clock_in, pause_start)
    overlap_end = min(ts.clock_out, pause_end)
    
    break_duration = 0
    if overlap_start < overlap_end:
        break_duration = (overlap_end - overlap_start).total_seconds() / 3600.0
        
    # Calcul du décompte total moins la pause
    diff = ts.clock_out - ts.clock_in
    hours = (diff.total_seconds() / 3600.0) - break_duration
        
    ts.hours_worked = max(round(hours, 2), 0)
    
    # Décompte : on compense les retards. S'il a travaillé plus de 8h au total, c'est de l'heure supplémentaire.
    if ts.hours_worked > 8:
        ts.is_overtime = True
        
    db.commit()
    db.refresh(ts)
    return ts

@router.get("/mine", response_model=List[TimesheetResponse])
def get_my_timesheets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        return []
    return db.query(Timesheet).filter(Timesheet.employee_id == employee.id).order_by(Timesheet.date.desc()).limit(100).all()

@router.get("/", response_model=List[TimesheetResponse])
def get_all_timesheets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [RoleEnum.RH, RoleEnum.MANAGER, RoleEnum.DIRECTION]:
        raise HTTPException(status_code=403, detail="Non autorisé.")
        
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    
    query = db.query(Timesheet)
    if current_user.role == RoleEnum.MANAGER:
        managed_employees = db.query(Employee).filter(Employee.manager_id == current_user.id).all()
        managed_emp_ids = [e.id for e in managed_employees]
        query = query.filter(Timesheet.employee_id.in_(managed_emp_ids))
    elif employee:
        # Exclure les pointages de l'utilisateur connecté (car il a son propre onglet)
        query = query.filter(Timesheet.employee_id != employee.id)
        
    return query.order_by(Timesheet.date.desc()).limit(100).all()
