import sys
import os
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
import models.employees
from models.user import User
from core.security import create_access_token
from models.features import Recommendation

def run():
    db = SessionLocal()
    try:
        qvt = db.query(User).filter(User.email == 'qvt@ydays.company').first()
        if not qvt:
            print("QVT user not found")
            return
        
        token = create_access_token(data={
            "sub": qvt.email,
            "user_id": qvt.id,
            "role": qvt.role.value if hasattr(qvt.role, 'value') else qvt.role
        })
        print(f"Token generated for {qvt.email} (role: {qvt.role})")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Test GET /api/manager/risks
        url_get = "http://127.0.0.1:8000/api/manager/risks"
        r_get = requests.get(url_get, headers=headers)
        print(f"GET {url_get} status: {r_get.status_code}")
        if r_get.status_code == 200:
            risks = r_get.json()
            print(f"Successfully retrieved {len(risks)} team risks:")
            for risk in risks[:3]:
                print(f"  Employee: {risk.get('employee_name')}, Burnout: {risk.get('burnout_risk')}, Turnover: {risk.get('turnover_risk')}, Engagement: {risk.get('engagement_risk')}")
                print(f"  Recommendations count: {len(risk.get('recommendations', []))}")
        else:
            print("Failed GET:", r_get.text)
            
        # 2. Test PUT /api/manager/risks/recommendations/{rec_id}/status
        rec = db.query(Recommendation).first()
        if rec:
            url_put = f"http://127.0.0.1:8000/api/manager/risks/recommendations/{rec.id}/status"
            new_status = "in_progress" # RecommendationStatusEnum has options like pending, completed, in_progress, rejected, etc. Let's make sure it's valid
            payload = {"status": new_status}
            r_put = requests.put(url_put, json=payload, headers=headers)
            print(f"PUT {url_put} status: {r_put.status_code}")
            if r_put.status_code == 200:
                print("Successfully updated recommendation status:", r_put.json())
            else:
                print("Failed PUT:", r_put.text)
        else:
            print("No recommendations found in database to test status update.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
