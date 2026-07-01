# 🚀 YDAYS API - Complete Usage Examples

Complete usage examples for all YDAYS API endpoints with real-world scenarios.

## Table of Contents
1. [Authentication](#authentication)
2. [Leave Management](#leave-management)
3. [Document Management](#document-management)
4. [Formation Management](#formation-management)
5. [Contract Management](#contract-management)
6. [Testing Script](#testing-script)

---

## 🔐 Authentication

### 1. Create Admin User (one-time setup)
```bash
cd c:\ydays_back
python create_admin.py
```

Admin credentials:
- Email: `admin@example.com`
- Password: `admin123`

---

### 2. Admin Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "mots_de_passe": "admin123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "nom": "Admin",
    "prenom": "User",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true,
    "first_login": true,
    "created_at": "2024-01-20T10:30:00"
  }
}
```

**Save the access_token for next requests**

---

### 3. Admin Creates Users

#### Create Collaborateur (Employee)
```bash
ADMIN_TOKEN="your_admin_token_here"

curl -X POST "http://localhost:8000/api/users/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@example.com",
    "mots_de_passe": "password123",
    "role": "collaborateur"
  }'
```

#### Create Manager
```bash
curl -X POST "http://localhost:8000/api/users/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "nom": "Martin",
    "prenom": "Sophie",
    "email": "sophie.martin@example.com",
    "mots_de_passe": "manager123",
    "role": "manager"
  }'
```

#### Create RH User
```bash
curl -X POST "http://localhost:8000/api/users/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "nom": "Lemoine",
    "prenom": "Marie",
    "email": "marie.lemoine@example.com",
    "mots_de_passe": "rh123",
    "role": "rh"
  }'
```

#### Create Direction User
```bash
curl -X POST "http://localhost:8000/api/users/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "nom": "Leclerc",
    "prenom": "Pierre",
    "email": "pierre.leclerc@example.com",
    "mots_de_passe": "direction123",
    "role": "direction"
  }'
```

---

### 4. Employee Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jean.dupont@example.com",
    "mots_de_passe": "password123"
  }'
```

**Save tokens for different users to test role-based access**

---

## 🏖️ Leave Management

### Setup for Leave Examples
```bash
# Tokens
EMPLOYEE_TOKEN="jean.dupont_token"
MANAGER_TOKEN="sophie.martin_token"
ADMIN_TOKEN="admin_token"
```

### 1. Employee Creates Leave Request
```bash
curl -X POST "http://localhost:8000/api/leaves/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -d '{
    "start_date": "2024-03-01",
    "end_date": "2024-03-05",
    "leave_type": "vacation",
    "reason": "Vacances de printemps"
  }'
```

Response:
```json
{
  "id": 1,
  "employee_id": 2,
  "start_date": "2024-03-01",
  "end_date": "2024-03-05",
  "leave_type": "vacation",
  "status": "pending",
  "reason": "Vacances de printemps",
  "created_at": "2024-01-20T15:30:00"
}
```

---

### 2. Employee Creates Sick Leave
```bash
curl -X POST "http://localhost:8000/api/leaves/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -d '{
    "start_date": "2024-02-26",
    "end_date": "2024-02-27",
    "leave_type": "sick",
    "reason": "Grippe"
  }'
```

---

### 3. Manager Views Team Leaves
```bash
curl -X GET "http://localhost:8000/api/leaves/team" \
  -H "Authorization: Bearer $MANAGER_TOKEN"
```

Response:
```json
[
  {
    "id": 1,
    "employee_id": 2,
    "start_date": "2024-03-01",
    "end_date": "2024-03-05",
    "leave_type": "vacation",
    "status": "pending",
    "reason": "Vacances de printemps",
    "created_at": "2024-01-20T15:30:00"
  },
  {
    "id": 2,
    "employee_id": 2,
    "start_date": "2024-02-26",
    "end_date": "2024-02-27",
    "leave_type": "sick",
    "status": "pending",
    "reason": "Grippe",
    "created_at": "2024-01-20T15:35:00"
  }
]
```

---

### 4. Manager Approves Leave
```bash
curl -X PUT "http://localhost:8000/api/leaves/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -d '{
    "status": "approved",
    "reason": "Approuvé"
  }'
```

---

### 5. Manager Rejects Leave
```bash
curl -X PUT "http://localhost:8000/api/leaves/2" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -d '{
    "status": "rejected",
    "reason": "Trop de congés demandés cette période"
  }'
```

---

### 6. Employee Views Own Leaves
```bash
curl -X GET "http://localhost:8000/api/leaves/my-leaves" \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN"
```

---

### 7. Employee Cancels Pending Leave
```bash
curl -X DELETE "http://localhost:8000/api/leaves/2" \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN"
```

---

## 📄 Document Management

### Setup for Document Examples
```bash
RH_TOKEN="marie.lemoine_token"
ADMIN_TOKEN="admin_token"
EMPLOYEE_TOKEN="jean.dupont_token"
```

### 1. RH Uploads Document for Employee
```bash
curl -X POST "http://localhost:8000/api/documents/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "title": "Certificat de travail",
    "document_type": "certificate",
    "file_path": "/documents/certificat_jean_dupont_2024.pdf"
  }'
```

---

### 2. RH Views Employee Documents
```bash
curl -X GET "http://localhost:8000/api/documents/employee/2" \
  -H "Authorization: Bearer $RH_TOKEN"
```

Response:
```json
[
  {
    "id": 1,
    "user_id": 2,
    "title": "Certificat de travail",
    "document_type": "certificate",
    "file_path": "/documents/certificat_jean_dupont_2024.pdf",
    "created_at": "2024-01-20T16:00:00"
  }
]
```

---

### 3. Employee Views Own Documents
```bash
curl -X GET "http://localhost:8000/api/documents/my-documents" \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN"
```

---

### 4. RH Uploads Multiple Documents
```bash
# Payslip
curl -X POST "http://localhost:8000/api/documents/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "title": "Bulletin de salaire - Janvier 2024",
    "document_type": "payslip",
    "file_path": "/documents/payslip_jean_dupont_01_2024.pdf"
  }'

# Contract
curl -X POST "http://localhost:8000/api/documents/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "title": "Contrat CDI",
    "document_type": "contract",
    "file_path": "/documents/contract_jean_dupont_cdi.pdf"
  }'

# Training Certificate
curl -X POST "http://localhost:8000/api/documents/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "title": "Attestation de formation Python",
    "document_type": "training",
    "file_path": "/documents/training_python_jean_dupont.pdf"
  }'
```

---

### 5. Admin Deletes Document
```bash
curl -X DELETE "http://localhost:8000/api/documents/1" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 🎓 Formation Management

### Setup for Formation Examples
```bash
RH_TOKEN="marie.lemoine_token"
ADMIN_TOKEN="admin_token"
EMPLOYEE_TOKEN="jean.dupont_token"
MANAGER_TOKEN="sophie.martin_token"
```

### 1. RH Creates Formation
```bash
curl -X POST "http://localhost:8000/api/formations/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "title": "Formation Python Avancée",
    "description": "Apprenez les concepts avancés de Python: async/await, type hints, design patterns",
    "start_date": "2024-03-10",
    "end_date": "2024-03-14"
  }'
```

Response:
```json
{
  "id": 1,
  "title": "Formation Python Avancée",
  "description": "Apprenez les concepts avancés de Python...",
  "start_date": "2024-03-10",
  "end_date": "2024-03-14",
  "created_at": "2024-01-20T16:30:00"
}
```

---

### 2. RH Creates More Formations
```bash
# Leadership Training
curl -X POST "http://localhost:8000/api/formations/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "title": "Formation Leadership et Management",
    "description": "Développez vos compétences en leadership et gestion d'\''équipe",
    "start_date": "2024-04-01",
    "end_date": "2024-04-03"
  }'

# Excel Training
curl -X POST "http://localhost:8000/api/formations/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "title": "Maîtriser Excel Avancé",
    "description": "VBA, macros, analyse de données avec Excel",
    "start_date": "2024-03-18",
    "end_date": "2024-03-20"
  }'
```

---

### 3. Employee Views Available Formations
```bash
curl -X GET "http://localhost:8000/api/formations/" \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN"
```

Response:
```json
[
  {
    "id": 1,
    "title": "Formation Python Avancée",
    "description": "Apprenez les concepts avancés de Python...",
    "start_date": "2024-03-10",
    "end_date": "2024-03-14",
    "created_at": "2024-01-20T16:30:00"
  },
  {
    "id": 2,
    "title": "Formation Leadership et Management",
    "description": "Développez vos compétences en leadership...",
    "start_date": "2024-04-01",
    "end_date": "2024-04-03",
    "created_at": "2024-01-20T16:35:00"
  },
  {
    "id": 3,
    "title": "Maîtriser Excel Avancé",
    "description": "VBA, macros, analyse de données...",
    "start_date": "2024-03-18",
    "end_date": "2024-03-20",
    "created_at": "2024-01-20T16:40:00"
  }
]
```

---

### 4. Manager Views Formations
```bash
curl -X GET "http://localhost:8000/api/formations/" \
  -H "Authorization: Bearer $MANAGER_TOKEN"
```

---

### 5. RH Updates Formation
```bash
curl -X PUT "http://localhost:8000/api/formations/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "title": "Formation Python Avancée (Mise à jour)",
    "description": "Apprenez les concepts avancés de Python: async/await, type hints, design patterns - Édition 2024",
    "start_date": "2024-03-10",
    "end_date": "2024-03-15"
  }'
```

---

### 6. RH Views All Formations
```bash
curl -X GET "http://localhost:8000/api/formations/rh/all" \
  -H "Authorization: Bearer $RH_TOKEN"
```

---

### 7. Admin Deletes Formation
```bash
curl -X DELETE "http://localhost:8000/api/formations/3" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 📋 Contract Management

### Setup for Contract Examples
```bash
RH_TOKEN="marie.lemoine_token"
ADMIN_TOKEN="admin_token"
EMPLOYEE_TOKEN="jean.dupont_token"
```

### 1. RH Creates Contract for Employee
```bash
curl -X POST "http://localhost:8000/api/contracts/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "user_id": 2,
    "contract_type": "CDI",
    "start_date": "2023-09-01",
    "end_date": null,
    "position": "Développeur Python Senior",
    "salary": "45000€"
  }'
```

Response:
```json
{
  "id": 1,
  "user_id": 2,
  "contract_type": "CDI",
  "start_date": "2023-09-01",
  "end_date": null,
  "position": "Développeur Python Senior",
  "salary": "45000€",
  "created_at": "2024-01-20T17:00:00"
}
```

---

### 2. Employee Views Own Contract
```bash
curl -X GET "http://localhost:8000/api/contracts/my-contract" \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN"
```

---

### 3. RH Views All Contracts
```bash
curl -X GET "http://localhost:8000/api/contracts/" \
  -H "Authorization: Bearer $RH_TOKEN"
```

---

### 4. RH Views Specific Employee Contract
```bash
curl -X GET "http://localhost:8000/api/contracts/employee/2" \
  -H "Authorization: Bearer $RH_TOKEN"
```

---

### 5. RH Updates Contract
```bash
curl -X PUT "http://localhost:8000/api/contracts/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "contract_type": "CDI",
    "start_date": "2023-09-01",
    "end_date": null,
    "position": "Développeur Python Senior",
    "salary": "48000€"
  }'
```

---

### 6. Create CDD Contract
```bash
curl -X POST "http://localhost:8000/api/contracts/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "user_id": 3,
    "contract_type": "CDD",
    "start_date": "2024-02-01",
    "end_date": "2024-12-31",
    "position": "Développeur Full Stack (Contrat)",
    "salary": "2500€/mois"
  }'
```

---

### 7. Create Internship Contract
```bash
curl -X POST "http://localhost:8000/api/contracts/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RH_TOKEN" \
  -d '{
    "user_id": 4,
    "contract_type": "Stage",
    "start_date": "2024-02-15",
    "end_date": "2024-05-15",
    "position": "Stagiaire - Développement Web",
    "salary": "Gratifié"
  }'
```

---

### 8. Admin Deletes Contract
```bash
curl -X DELETE "http://localhost:8000/api/contracts/2" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 🧪 Testing Script

### Complete Test Flow in Python
```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Admin Login
print("1. Admin Login...")
admin_login = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "email": "admin@example.com",
        "mots_de_passe": "admin123"
    }
)
admin_token = admin_login.json()["access_token"]
print(f"✓ Admin logged in: {admin_token[:20]}...")

# 2. Admin Creates Employees
print("\n2. Creating test users...")
headers = {"Authorization": f"Bearer {admin_token}"}

employee_data = {
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@test.com",
    "mots_de_passe": "password123",
    "role": "collaborateur"
}
resp = requests.post(f"{BASE_URL}/api/users/", json=employee_data, headers=headers)
print(f"✓ Employee created: {resp.json()['id']}")

# 3. Employee Login
print("\n3. Employee Login...")
employee_login = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "email": "jean.dupont@test.com",
        "mots_de_passe": "password123"
    }
)
employee_token = employee_login.json()["access_token"]
print(f"✓ Employee logged in")

# 4. Employee Creates Leave
print("\n4. Creating leave request...")
emp_headers = {"Authorization": f"Bearer {employee_token}"}
leave_data = {
    "start_date": "2024-03-01",
    "end_date": "2024-03-05",
    "leave_type": "vacation",
    "reason": "Vacances"
}
resp = requests.post(f"{BASE_URL}/api/leaves/", json=leave_data, headers=emp_headers)
print(f"✓ Leave created: {resp.json()}")

# 5. Dashboard Access
print("\n5. Dashboard Access...")
resp = requests.get(f"{BASE_URL}/api/dashboard/home", headers=emp_headers)
print(f"✓ Dashboard: {resp.json()['message']}")
```

---

## ⚠️ Common Errors & Solutions

### 401 Unauthorized
**Problem**: Invalid or missing token
```bash
# Solution: Make sure to use a valid token
Authorization: Bearer <valid_token>
```

### 403 Forbidden
**Problem**: User doesn't have permission
```bash
# Example: RH trying to create a leave
# RH cannot create leaves, only collaborateur and manager can
```

### 400 Bad Request
**Problem**: Invalid data format
```bash
# Example: start_date > end_date
# Solution: Ensure start_date <= end_date
```

### 404 Not Found
**Problem**: Resource doesn't exist
```bash
# Example: /api/leaves/999 (leave with id 999 doesn't exist)
# Solution: Use existing resource IDs
```

---

## 📊 Testing with Postman

1. Create a new Postman Collection
2. Set up environment variables:
   - `admin_token` - Admin's JWT token
   - `employee_token` - Employee's JWT token
   - `rh_token` - RH's JWT token
   - `base_url` - http://localhost:8000

3. Add requests for each endpoint
4. Use Pre-request Script to set up tokens:
```javascript
pm.sendRequest({
    url: pm.variables.get("base_url") + "/api/auth/login",
    method: 'POST',
    header: {
        'Content-Type': 'application/json'
    },
    body: {
        mode: 'raw',
        raw: JSON.stringify({
            email: "admin@example.com",
            mots_de_passe: "admin123"
        })
    }
}, (err, response) => {
    if (!err) {
        pm.environment.set("admin_token", response.json().access_token);
    }
});
```

---

## 🎯 End-to-End Workflow Example

### Scenario: New Employee Onboarding

1. **Admin creates employee**
   ```bash
   POST /api/users/ - Create new employee
   ```

2. **RH creates contract**
   ```bash
   POST /api/contracts/ - Create CDI contract for employee
   ```

3. **RH uploads documents**
   ```bash
   POST /api/documents/ - Upload contract document
   POST /api/documents/ - Upload training materials
   ```

4. **RH creates formations**
   ```bash
   POST /api/formations/ - Create onboarding training
   ```

5. **Employee logs in and views profile**
   ```bash
   POST /api/auth/login - Employee logs in
   GET /api/dashboard/home - Access personal dashboard
   ```

6. **Employee checks contract and documents**
   ```bash
   GET /api/contracts/my-contract
   GET /api/documents/my-documents
   ```

---

## 💡 Tips & Tricks

1. **Always save tokens** after login for subsequent requests
2. **Check HTTP status codes** to debug issues
3. **Use Postman collections** to organize and reuse requests
4. **Test with different roles** to verify RBAC works
5. **Use realistic dates** in leave and contract requests
6. **Remember RH restrictions** - RH cannot view personal documents/contracts

---

## 📞 Support

For issues or questions, check the logs or contact the development team.
