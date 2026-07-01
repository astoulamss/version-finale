# 🚀 YDAYS Backend - Quick Start Guide

## Prerequisites

- Python 3.10+
- pip (Python package manager)
- SQLite (inclus avec Python) ou PostgreSQL pour la production

## Installation & Setup

### 1. Clone/Navigate to Project
```bash
cd c:\ydays_back
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Initial Admin User
```bash
python create_admin.py
```

This creates:
- Email: `admin@example.com`
- Password: `admin123`

### 5. Start the Server
```bash
# Option 1: Using uvicorn directly
uvicorn main:app --reload

# Option 2: Using Python
python main.py
```

Server will run at: `http://localhost:8000`

---

## 📚 API Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## ✅ Verification

### Test Setup
```bash
# Verify all imports and app creation
python test_setup.py
```

Expected output:
```
✓ Database imports successful
✓ User model imports successful
✓ Features model imports successful
✓ User schema imports successful
✓ Features schema imports successful
✓ Security imports successful
✓ API router imports successful
✓ FastAPI app created successfully
✓ Total routes: X
✓ Found X expected routes

==================================================
All tests passed! Backend is ready.
==================================================
```

### Test API Endpoints
```bash
# Run comprehensive API tests
python test_api.py
```

---

## 📝 Key Files & What They Do

### Core Files
- **main.py** - FastAPI application entry point
- **requirements.txt** - Python package dependencies
- **.env** - Environment variables (create if missing)

### Database & Models
- **database/db.py** - Database connection and configuration
- **models/user.py** - User model with roles
- **models/features.py** - Leave, Document, Formation, Contract models

### API Endpoints
- **api/auth.py** - Authentication (login)
- **api/users.py** - User management (CRUD, role-based)
- **api/dashboard.py** - Role-specific dashboards
- **api/leaves.py** - Leave request management
- **api/documents.py** - Document management
- **api/formations.py** - Formation management
- **api/contracts.py** - Contract management

### Schemas & Security
- **schemas/user.py** - Pydantic validation for users
- **schemas/features.py** - Pydantic validation for features
- **core/security.py** - JWT tokens and password hashing

### Utilities
- **create_admin.py** - Create initial admin user
- **init_db.py** - Initialize database
- **test_setup.py** - Verify setup and imports
- **test_api.py** - Comprehensive API testing

### Documentation
- **README.md** - Project overview and setup
- **FEATURES.md** - Feature documentation with examples
- **EXAMPLES_EXTENDED.md** - Complete usage examples
- **QUICKSTART.md** - This file

---

## 🔍 Quick Admin Setup Flow

```bash
# 1. Start server
uvicorn main:app --reload

# 2. In new terminal, create admin
python create_admin.py

# 3. In browser or curl, login
# GET: http://localhost:8000/docs
# POST: /api/auth/login
# Body: {"email": "admin@example.com", "mots_de_passe": "admin123"}

# 4. Copy the access_token and use for creating users
# POST: /api/users/
# Header: Authorization: Bearer <token>
# Body: {"nom": "...", "prenom": "...", "email": "...", "mots_de_passe": "...", "role": "..."}
```

---

## 🧪 Quick Testing

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

### Test 2: Admin Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","mots_de_passe":"admin123"}'
```

### Test 3: Create User (with token)
```bash
ADMIN_TOKEN="your_token_here"

curl -X POST http://localhost:8000/api/users/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom":"Dupont",
    "prenom":"Jean",
    "email":"jean@example.com",
    "mots_de_passe":"password123",
    "role":"collaborateur"
  }'
```

### Test 4: Access Dashboard
```bash
curl http://localhost:8000/api/dashboard/home \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 🗂️ Project Structure
```
c:\ydays_back\
├── main.py                  # FastAPI app
├── requirements.txt         # Dependencies
├── .env                     # Environment (create if needed)
├── create_admin.py          # Admin setup
├── test_setup.py            # Setup verification
├── test_api.py              # API tests
├── QUICKSTART.md            # This file
├── README.md                # Full documentation
├── FEATURES.md              # Feature documentation
├── EXAMPLES_EXTENDED.md     # Usage examples
│
├── database/
│   ├── __init__.py
│   └── db.py                # DB config & session
│
├── models/
│   ├── __init__.py
│   ├── user.py              # User model
│   └── features.py          # Leave, Document, Formation, Contract models
│
├── schemas/
│   ├── __init__.py
│   ├── user.py              # User schemas
│   └── features.py          # Feature schemas
│
├── api/
│   ├── __init__.py
│   ├── auth.py              # Login endpoint
│   ├── users.py             # User management
│   ├── dashboard.py         # Role-based dashboards
│   ├── leaves.py            # Leave management
│   ├── documents.py         # Document management
│   ├── formations.py        # Formation management
│   ├── contracts.py         # Contract management
│   └── features/            # Features module
│
└── core/
    ├── __init__.py
    └── security.py          # JWT & password hashing
```

---

## 🔐 Default Admin Credentials

After running `python create_admin.py`:

- **Email**: `admin@example.com`
- **Password**: `admin123`

⚠️ **Change these in production!**

---

## 📊 Available Roles

1. **admin** - Full system access, user management
2. **collaborateur** - Employee access, personal dashboard
3. **manager** - Team management, leave approval
4. **rh** - HR functions, contracts, documents
5. **direction** - Strategic dashboards, analytics

---

## 🔄 Typical Workflow

1. **Admin creates users** via `POST /api/users/`
2. **Users login** via `POST /api/auth/login`
3. **Users access dashboard** based on role
4. **Different features** available per role:
   - Employees: view profile, request leaves, view docs
   - Managers: approve leaves, manage team
   - HR: manage contracts, upload documents
   - Direction: view analytics

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill the process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti :8000 | xargs kill -9
```

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Database Errors
```bash
# Reset database
rm ydays.db  # or your database file
python init_db.py
python create_admin.py
```

### Token Expired
```bash
# Re-login to get new token
python -c "from core.security import create_access_token; print(create_access_token({'sub': 'admin@example.com'}))"
```

---

## 📈 Next Steps

1. ✅ Verify setup with `python test_setup.py`
2. ✅ Start server with `uvicorn main:app --reload`
3. ✅ Access Swagger UI at http://localhost:8000/docs
4. ✅ Read [FEATURES.md](FEATURES.md) for feature details
5. ✅ Check [EXAMPLES_EXTENDED.md](EXAMPLES_EXTENDED.md) for usage examples
6. ✅ Deploy to production (update .env, database, CORS settings)

---

## 📚 Documentation Files

- **README.md** - Full project documentation
- **FEATURES.md** - All features with examples
- **EXAMPLES_EXTENDED.md** - Complete usage examples with cURL
- **QUICKSTART.md** - This file

---

## 🎯 Common Tasks

### Create a New User
```bash
# 1. Login as admin (get token)
# 2. POST /api/users/ with admin token
```

### Request Leave
```bash
# 1. Login as employee
# 2. POST /api/leaves/ with leave details
```

### Approve Leave
```bash
# 1. Login as manager
# 2. GET /api/leaves/team to see pending leaves
# 3. PUT /api/leaves/{id} to approve/reject
```

### Manage Contracts
```bash
# 1. Login as RH
# 2. POST /api/contracts/ to create
# 3. PUT /api/contracts/{id} to update
# 4. GET /api/contracts/ to list all
```

---

## 💡 Tips

- Always add `Authorization: Bearer <token>` header for protected endpoints
- Use Swagger UI at /docs for interactive testing
- Check HTTP status codes: 200=OK, 400=Bad Request, 401=Unauthorized, 403=Forbidden, 404=Not Found
- Keep tokens safe - they expire after 30 minutes
- Test with different roles to verify RBAC

---

## 📞 Getting Help

1. Check the logs for error messages
2. Read the relevant documentation file
3. Test endpoints in Swagger UI (/docs)
4. Run `python test_setup.py` to verify setup
5. Run `python test_api.py` for comprehensive testing

---

**Ready to go! Start with step 5 in the Installation section above.** 🚀
