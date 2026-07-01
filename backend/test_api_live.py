import sys
import os
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from models.user import User
from core.security import create_access_token

def test_api():
    db = SessionLocal()
    try:
        nadir = db.query(User).filter(User.id == 3).first()
        token = create_access_token(data={"sub": nadir.email, "user_id": nadir.id, "role": nadir.role.value})
        
        response_tasks = requests.get("http://127.0.0.1:8000/api/manager/tasks/", headers={"Authorization": f"Bearer {token}"})
        print(f"Tasks Status: {response_tasks.status_code}")
        
        response_stats = requests.get("http://127.0.0.1:8000/api/manager/tasks/stats/summary", headers={"Authorization": f"Bearer {token}"})
        print(f"Stats Status: {response_stats.status_code}")

        response_team = requests.get("http://127.0.0.1:8000/api/employees/", headers={"Authorization": f"Bearer {token}"})
        print(f"Employees Status: {response_team.status_code}")

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_api()
