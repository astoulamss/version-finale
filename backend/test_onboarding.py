import sys, os, requests
sys.path.append('.')
from core.security import create_access_token

# Use RH token to trigger the status update on plan 3
rh_token = create_access_token(data={'sub': 'amina.rachidi@ydays.company', 'role': 'rh', 'user_id': 4})
h = {'Authorization': f'Bearer {rh_token}'}

# Get plan 3 tasks
r = requests.get('http://127.0.0.1:8000/api/onboarding/', headers=h)
data = r.json()
for p in data:
    tasks_info = [(t["id"], t["title"][:20], t["status"]) for t in p["tasks"]]
    print(f"Plan {p['id']} | status={p['status']} | tasks={tasks_info}")

# Force re-trigger by toggling last task of plan 3 if all done
plan3 = next((p for p in data if p["id"] == 3), None)
if plan3:
    all_done = all(t["status"] == "done" for t in plan3["tasks"])
    print(f"\nPlan 3 all_done={all_done}, current status={plan3['status']}")
    if all_done and plan3["status"] != "completed":
        last_task = plan3["tasks"][-1]
        # Toggle to trigger the auto-complete
        res = requests.put(f'http://127.0.0.1:8000/api/onboarding/tasks/{last_task["id"]}', json={"status": "done"}, headers=h)
        print(f"Triggered auto-complete: {res.status_code}")
        r2 = requests.get('http://127.0.0.1:8000/api/onboarding/', headers=h)
        for p in r2.json():
            print(f"Plan {p['id']} | status={p['status']}")
