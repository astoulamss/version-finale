import requests
import json
from database.db import SessionLocal
from models.user import User, RoleEnum
from models.features import WorkflowConfig, Leave
from models.employees import Employee, Department, Position
from core.security import hash_password

BASE_URL = "http://localhost:8000"

def run_tests():
    print("--- WORKFLOWS BACKEND TESTING ---")
    
    # 1. Ensure test users exist in DB via direct DB access for test convenience
    db = SessionLocal()
    try:
        # Create department
        dept = db.query(Department).first()
        if not dept:
            dept = Department(name="R&D", description="Research and Development")
            db.add(dept)
            db.flush()
            
        # Create position
        pos = db.query(Position).first()
        if not pos:
            pos = Position(title="Software Engineer")
            db.add(pos)
            db.flush()

        # Manager user
        mgr = db.query(User).filter(User.email == "manager.test@example.com").first()
        if not mgr:
            mgr = User(
                nom="Test", prenom="Manager", email="manager.test@example.com",
                mots_de_passe=hash_password("password123"), role=RoleEnum.MANAGER, is_active=True
            )
            db.add(mgr)
            db.flush()
            
            # Create employee profile for manager
            emp_mgr = Employee(user_id=mgr.id, department_id=dept.id, position_id=pos.id, status="active")
            db.add(emp_mgr)

        # Collaborator user
        collab = db.query(User).filter(User.email == "collab.test@example.com").first()
        if not collab:
            collab = User(
                nom="Test", prenom="Collab", email="collab.test@example.com",
                mots_de_passe=hash_password("password123"), role=RoleEnum.COLLABORATEUR, is_active=True
            )
            db.add(collab)
            db.flush()
            
            # Create employee profile for collab, pointing to manager
            emp_collab = Employee(user_id=collab.id, department_id=dept.id, position_id=pos.id, manager_id=mgr.id, status="active")
            db.add(emp_collab)

        # RH validator user
        rh_user = db.query(User).filter(User.email == "rh.test@example.com").first()
        if not rh_user:
            rh_user = User(
                nom="Test", prenom="RH", email="rh.test@example.com",
                mots_de_passe=hash_password("password123"), role=RoleEnum.RH, is_active=True
            )
            db.add(rh_user)
            db.flush()

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error preparing database: {e}")
        return
    finally:
        db.close()

    # Get login tokens
    admin_token = get_token("admin@example.com", "admin123")
    collab_token = get_token("collab.test@example.com", "password123")
    mgr_token = get_token("manager.test@example.com", "password123")
    rh_token = get_token("rh.test@example.com", "password123")

    if not all([admin_token, collab_token, mgr_token, rh_token]):
        print("Failed to get all tokens.")
        return

    # Check validator user ID
    db = SessionLocal()
    rh_user_id = db.query(User).filter(User.email == "rh.test@example.com").first().id
    db.close()

    # --- Scenario 1: Auto Approval ---
    print("\n--- Test Scenario 1: Logic = 'auto' ---")
    set_workflow_config(admin_token, "leave", "auto", None)
    leave1 = create_leave(collab_token)
    print(f"Leave status under 'auto': {leave1.get('status')}")
    assert leave1.get('status') == 'approved', "Expected auto approval"

    # --- Scenario 2: Single Manager Approval ---
    print("\n--- Test Scenario 2: Logic = 'single_manager' ---")
    set_workflow_config(admin_token, "leave", "single_manager", None)
    leave2 = create_leave(collab_token)
    print(f"Leave status initially: {leave2.get('status')}")
    assert leave2.get('status') == 'pending', "Expected pending status"
    
    # Get pending workflows for manager
    blocked = get_blocked_workflows(admin_token)
    step = next((s for s in blocked if s.get('entity_id') == leave2.get('id')), None)
    print(f"Blocked step details: {step}")
    assert step is not None, "Expected step in blocked list"
    assert step.get('approver_name') == "Manager Test", "Expected manager to be the approver"

    # Manager approves
    approve_leave(mgr_token, leave2.get('id'))
    leave2_updated = get_leave_details(collab_token, leave2.get('id'))
    print(f"Leave status after manager approval: {leave2_updated.get('status')}")
    assert leave2_updated.get('status') == 'approved', "Expected approved status after manager signature"

    # --- Scenario 3: Double Sequential Validation ---
    print("\n--- Test Scenario 3: Logic = 'sequential' (Manager + RH) ---")
    set_workflow_config(admin_token, "leave", "sequential", rh_user_id)
    leave3 = create_leave(collab_token)
    print(f"Leave status initially: {leave3.get('status')}")
    assert leave3.get('status') == 'pending', "Expected pending status"

    # Check blocked list step 1
    blocked = get_blocked_workflows(admin_token)
    step1 = next((s for s in blocked if s.get('entity_id') == leave3.get('id')), None)
    print(f"Step 1 approver: {step1.get('approver_name')}")
    assert step1.get('approver_name') == "Manager Test", "Expected manager first"

    # Manager approves step 1
    approve_leave(mgr_token, leave3.get('id'))
    leave3_after_mgr = get_leave_details(collab_token, leave3.get('id'))
    print(f"Leave status after step 1: {leave3_after_mgr.get('status')}")
    assert leave3_after_mgr.get('status') == 'pending', "Expected still pending after step 1"

    # Check blocked list step 2 (RH)
    blocked = get_blocked_workflows(admin_token)
    step2 = next((s for s in blocked if s.get('entity_id') == leave3.get('id')), None)
    print(f"Step 2 details: {step2}")
    assert step2.get('approver_name') == "RH Test", "Expected RH next"

    # RH approves step 2
    approve_leave(rh_token, leave3.get('id'))
    leave3_after_rh = get_leave_details(collab_token, leave3.get('id'))
    print(f"Leave status after step 2: {leave3_after_rh.get('status')}")
    assert leave3_after_rh.get('status') == 'approved', "Expected approved status after step 2 signature"

    print("\n✅ ALL WORKFLOW SCENARIOS PASSED SUCCESSFULLY!")

def get_token(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "mots_de_passe": password})
    if r.status_code == 200:
        return r.json()["access_token"]
    return None

def set_workflow_config(token, entity_type, logic_type, user_id):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"logic_type": logic_type, "validator_user_id": user_id}
    r = requests.put(f"{BASE_URL}/api/workflows/configs/{entity_type}", json=payload, headers=headers)
    assert r.status_code == 200, f"Failed config: {r.text}"
    print(f"Configured {entity_type} rule to: {logic_type}")

def create_leave(token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "start_date": "2026-08-01",
        "end_date": "2026-08-03",
        "leave_type": "vacation",
        "reason": "Workflow Test"
    }
    r = requests.post(f"{BASE_URL}/api/leaves/", json=payload, headers=headers)
    assert r.status_code == 200, f"Failed create: {r.text}"
    return r.json()

def get_blocked_workflows(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/workflows/blocked", headers=headers)
    assert r.status_code == 200
    return r.json()

def approve_leave(token, leave_id):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"status": "approved"}
    r = requests.put(f"{BASE_URL}/api/leaves/{leave_id}", json=payload, headers=headers)
    assert r.status_code == 200, f"Approve failed: {r.text}"

def get_leave_details(token, leave_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/leaves/{leave_id}", headers=headers)
    assert r.status_code == 200
    return r.json()

if __name__ == "__main__":
    run_tests()
