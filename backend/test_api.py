import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from models.user import User
from core.security import create_access_token
from fastapi.testclient import TestClient
from main import app

def test_api():
    db = SessionLocal()
    try:
        nadir = db.query(User).filter(User.id == 3).first()
        token = create_access_token(data={"sub": nadir.email, "user_id": nadir.id, "role": nadir.role.value})
        
        client = TestClient(app)
        response = client.get("/api/manager/tasks", headers={"Authorization": f"Bearer {token}"})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_api()
