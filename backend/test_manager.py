import sys, os, requests
sys.path.append(os.path.abspath('.'))
from core.security import create_access_token

# Test as user 3 (nadir.elmansouri@ydays.company) - le compte reel de connexion
token = create_access_token(data={'sub': 'nadir.elmansouri@ydays.company', 'role': 'manager', 'user_id': 3})
headers = {'Authorization': f'Bearer {token}'}
r = requests.get('http://127.0.0.1:8000/api/onboarding/', headers=headers)
print('Status:', r.status_code)
data = r.json()
print(f'Nombre de plans: {len(data)}')
for p in data:
    print(f'  Plan id={p["id"]} -> {p["employee_prenom"]} {p["employee_nom"]} (status: {p["status"]})')
