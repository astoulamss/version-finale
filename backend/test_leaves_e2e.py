import sys
import os
import requests
from database.db import SessionLocal
from models.user import User
from models.features import LeaveType, LeaveBalance, Leave
import models.employees

def run():
    db = SessionLocal()
    sarah = db.query(User).filter(User.email == 'sarah.benali@ydays.company').first()
    rh = db.query(User).filter(User.email == 'amina.rachidi@ydays.company').first()
    
    print('--- ETAPE 1 : ETAT INITIAL (DB) ---')
    bals = db.query(LeaveBalance).filter(LeaveBalance.employee_id == sarah.id).all()
    for b in bals:
        print(f'{b.leave_type.name}: {b.remaining_days}')
    
    print('\n--- ETAPE 2 : LOGIN API ---')
    r = requests.post('http://127.0.0.1:8000/api/auth/login', json={'email': 'sarah.benali@ydays.company', 'mots_de_passe': 'YDAYS2026!'})
    sarah_token = r.json().get('access_token')
    if not sarah_token: print("LOGIN FAILED FOR SARAH", r.text)
    
    r_rh = requests.post('http://127.0.0.1:8000/api/auth/login', json={'email': 'amina.rachidi@ydays.company', 'mots_de_passe': 'RH2026!'})
    rh_token = r_rh.json().get('access_token')
    if not rh_token: print("LOGIN FAILED FOR RH", r_rh.text)
    
    print('\n--- ETAPE 3 : GET BALANCES VIA API (SARAH) ---')
    r_bals = requests.get('http://127.0.0.1:8000/api/leaves/balances/me', headers={'Authorization': f'Bearer {sarah_token}'})
    print(r_bals.json())
    
    print('\n--- ETAPE 4 : CREER DEMANDE MALADIE (SARAH) ---')
    sick_type = db.query(LeaveType).filter(LeaveType.name == 'Arrêt Maladie').first()
    if not sick_type:
        sick_type = LeaveType(name="Arrêt Maladie", description="", max_days=10)
        db.add(sick_type)
        db.commit()
    
    payload = {
        'start_date': '2026-07-01',
        'end_date': '2026-07-05',
        'leave_type': 'sick',
        'reason': 'Grippe'
    }
    r_create = requests.post('http://127.0.0.1:8000/api/leaves/', json=payload, headers={'Authorization': f'Bearer {sarah_token}'})
    leave_data = r_create.json()
    if r_create.status_code >= 400: print("LEAVE CREATE ERROR", r_create.text)
    leave_id = leave_data.get('id')
    print(f'Leave created: ID {leave_id}, Status: {leave_data.get("status")}')
    
    print('\n--- ETAPE 5 : VALIDATION RH ---')
    if leave_id:
        r_validate = requests.put(f'http://127.0.0.1:8000/api/leaves/{leave_id}', json={'status': 'approved', 'comments': 'Ok bon retablissement'}, headers={'Authorization': f'Bearer {rh_token}'})
        print(f'Validation response: {r_validate.json().get("status")}')
    else:
        print("Skipping validation, no leave_id")
    
    print('\n--- ETAPE 6 : VERIFICATION NOUVEAUX SOLDES (DB) ---')
    db.expire_all()
    bals_after = db.query(LeaveBalance).filter(LeaveBalance.employee_id == sarah.id, LeaveBalance.leave_type_id == sick_type.id).first()
    print(f'{bals_after.leave_type.name}: {bals_after.remaining_days}')
    
    print('\n--- ETAPE 7 : VERIFICATION NOUVEAUX SOLDES (API) ---')
    r_bals_after = requests.get('http://127.0.0.1:8000/api/leaves/balances/me', headers={'Authorization': f'Bearer {sarah_token}'})
    print(r_bals_after.json())
    
    db.close()

run()
