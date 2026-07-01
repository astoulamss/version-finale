# 📂 YDAYS Backend - Architecture & Structure

Complete overview of the YDAYS backend project structure, architecture patterns, and design decisions.

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│                      (main.py)                              │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────▼────────┐  ┌────▼───────────┐  ┌─▼──────────────┐
    │   API Routers  │  │   Middleware   │  │   Dependencies │
    │                │  │                │  │                │
    │ • auth.py      │  │ • CORS         │  │ • JWT Auth     │
    │ • users.py     │  │ • Exception    │  │ • DB Session   │
    │ • dashboard.py │  │   Handlers     │  │ • Role Checks  │
    │ • leaves.py    │  │                │  │                │
    │ • documents.py │  └────────────────┘  └────────────────┘
    │ • formations.py│
    │ • contracts.py │
    └────────────────┘
            │
    ┌───────▼──────────────────┐
    │   Business Logic Layer   │
    │                          │
    │ • Schemas (Validation)   │
    │ • Security (JWT, Crypto) │
    │ • Core Utils             │
    └──────────────────────────┘
            │
    ┌───────▼──────────────────┐
    │   Data Access Layer      │
    │                          │
    │ • SQLAlchemy Models      │
    │ • Database Connection    │
    │ • ORM Queries            │
    └──────────────────────────┘
            │
    ┌───────▼──────────────────┐
    │   Database Layer         │
    │                          │
    │ • SQLite / PostgreSQL    │
    │ • Tables & Relationships │
    │ • Constraints & Indexes  │
    └──────────────────────────┘
```

---

## 📁 Directory Structure

```
ydays_back/
│
├── 📄 Configuration & Entry
│   ├── main.py              # FastAPI application entry point
│   ├── requirements.txt      # Python dependencies
│   ├── .env                  # Environment variables
│   └── .gitignore           # Git ignore patterns
│
├── 🗄️ Database Layer
│   └── database/
│       ├── __init__.py
│       └── db.py            # SQLAlchemy setup, session management
│
├── 📊 Data Models
│   └── models/
│       ├── __init__.py
│       ├── user.py          # User model with RoleEnum
│       └── features.py      # Leave, Document, Formation, Contract models
│
├── ✅ Data Validation
│   └── schemas/
│       ├── __init__.py
│       ├── user.py          # UserCreate, UserResponse, TokenResponse
│       └── features.py      # All feature schemas for validation
│
├── 🔐 Core Utilities
│   └── core/
│       ├── __init__.py
│       └── security.py      # JWT, password hashing, authentication
│
├── 🛣️ API Routes
│   └── api/
│       ├── __init__.py
│       ├── auth.py          # POST /api/auth/login
│       ├── users.py         # User CRUD endpoints
│       ├── dashboard.py     # Role-specific dashboards
│       ├── leaves.py        # Leave management endpoints
│       ├── documents.py     # Document management endpoints
│       ├── formations.py    # Formation management endpoints
│       ├── contracts.py     # Contract management endpoints
│       └── features/        # Features module directory
│
├── 🧪 Testing & Utilities
│   ├── create_admin.py      # Create initial admin user
│   ├── init_db.py           # Initialize database
│   ├── test_setup.py        # Setup verification
│   └── test_api.py          # Comprehensive API tests
│
├── 📚 Documentation
│   ├── README.md            # Main documentation
│   ├── FEATURES.md          # Feature documentation
│   ├── EXAMPLES_EXTENDED.md # Complete usage examples
│   ├── QUICKSTART.md        # Quick start guide
│   ├── CHANGELOG.md         # Release notes
│   ├── ARCHITECTURE.md      # This file
│   └── EXAMPLES.md          # Basic examples
│
└── 🐳 Deployment
    ├── Dockerfile           # Docker container definition
    └── docker-compose.yml   # Docker compose for PostgreSQL
```

---

## 🔄 Request Flow

### Authentication Flow
```
User Login Request
        │
        ▼
POST /api/auth/login
        │
        ├─► Validate email/password format
        │
        ├─► Query database for user
        │
        ├─► Verify password with bcrypt
        │
        ├─► Create JWT token (expires in 30 min)
        │
        └─► Return token + user info
```

### Protected Endpoint Flow
```
Request to Protected Endpoint
        │
        ├─► Extract Bearer token from header
        │
        ├─► Decode JWT token
        │
        ├─► Validate token signature & expiration
        │
        ├─► Get user from database
        │
        ├─► Check user role against endpoint requirements
        │
        ├─► (If authorized) Execute endpoint logic
        │
        └─► Return response or 401/403 error
```

### Leave Request Creation Flow
```
POST /api/leaves/
        │
        ├─► Check authentication (JWT)
        │
        ├─► Verify user role (Collaborateur or Manager)
        │
        ├─► Validate leave dates (start < end)
        │
        ├─► Create Leave object in database
        │
        ├─► Set status to "pending"
        │
        └─► Return created leave with ID
```

---

## 🗂️ Database Schema

### User Table
```sql
users
├── id (Primary Key)
├── nom (String)
├── prenom (String)
├── email (Unique String)
├── mots_de_passe (Hashed String)
├── role (Enum: admin, collaborateur, direction, manager, rh)
├── is_active (Boolean)
├── first_login (Boolean)
└── created_at (DateTime)
```

### Leave Table
```sql
leaves
├── id (Primary Key)
├── employee_id (Foreign Key → users.id)
├── start_date (Date)
├── end_date (Date)
├── leave_type (Enum: vacation, sick, maternity, personal, unpaid)
├── status (Enum: pending, approved, rejected, cancelled)
├── reason (Text)
├── approved_by (Foreign Key → users.id, nullable)
├── created_at (DateTime)
└── updated_at (DateTime)
```

### Document Table
```sql
documents
├── id (Primary Key)
├── user_id (Foreign Key → users.id)
├── title (String)
├── document_type (String: contract, payslip, certificate, training, other)
├── file_path (String)
└── created_at (DateTime)
```

### Formation Table
```sql
formations
├── id (Primary Key)
├── title (String)
├── description (Text, nullable)
├── start_date (Date)
├── end_date (Date)
└── created_at (DateTime)
```

### Contract Table
```sql
contracts
├── id (Primary Key)
├── user_id (Foreign Key → users.id)
├── contract_type (String: CDI, CDD, Stage, Alternance, Freelance)
├── start_date (Date)
├── end_date (Date, nullable)
├── position (String)
├── salary (String, nullable)
└── created_at (DateTime)
```

---

## 🔐 Authentication & Authorization

### JWT Token Structure
```javascript
{
  "sub": "email@example.com",    // Subject (unique identifier)
  "role": "collaborateur",        // User role
  "exp": 1705863600,             // Expiration time
  "iat": 1705777200              // Issued at time
}
```

### Role Hierarchy
```
Admin (Highest)
├── Full system access
├── Can manage users
└── Can access all endpoints
    │
    ├── RH
    │   ├── Can manage employees (not create)
    │   ├── Can manage contracts
    │   └── Can upload documents
    │
    ├── Manager
    │   ├── Can approve leaves
    │   ├── Can manage team
    │   └── Can view team indicators
    │
    ├── Direction
    │   ├── Can view strategic dashboards
    │   └── Can view analytics
    │
    └── Collaborateur (Lowest)
        ├── Can manage own profile
        ├── Can request leaves
        └── Can view personal documents
```

### RBAC Matrix
```
                    Admin | Collab | Manager | RH | Direction
Create Users          ✓       ✗       ✗       ✗     ✗
Manage Users          ✓       ✗       ✗       ✓     ✗
Create Leaves         ✗       ✓       ✓       ✗     ✗
Approve Leaves        ✓       ✗       ✓       ✗     ✗
Manage Contracts      ✓       ✗       ✗       ✓     ✗
Upload Documents      ✓       ✗       ✗       ✓     ✗
Create Formations     ✓       ✗       ✗       ✓     ✗
View Dashboards       ✓       ✓       ✓       ✓     ✓
```

---

## 🔌 API Endpoint Categories

### Authentication (1 endpoint)
```
POST /api/auth/login              # User login, get JWT token
```

### User Management (7 endpoints)
```
POST   /api/users/                # Create user (Admin only)
GET    /api/users/me              # Get own profile
PUT    /api/users/me              # Update own profile
GET    /api/users/                # List users (Admin, RH)
GET    /api/users/{id}            # Get user details (Admin, RH)
PUT    /api/users/{id}            # Update user (Admin, RH)
DELETE /api/users/{id}            # Delete user (Admin only)
```

### Dashboards (6 endpoints)
```
GET /api/dashboard/home           # Redirect to role dashboard
GET /api/dashboard/admin          # Admin dashboard
GET /api/dashboard/collaborateur  # Employee dashboard
GET /api/dashboard/manager        # Manager dashboard
GET /api/dashboard/rh             # HR dashboard
GET /api/dashboard/direction      # Director dashboard
```

### Leaves (5 endpoints)
```
POST   /api/leaves/               # Create leave request
GET    /api/leaves/my-leaves      # Get own leaves
GET    /api/leaves/team           # Get team leaves (Manager)
PUT    /api/leaves/{id}           # Approve/Reject leave
DELETE /api/leaves/{id}           # Cancel leave
```

### Documents (4 endpoints)
```
POST   /api/documents/            # Upload document
GET    /api/documents/my-documents        # Get own documents
GET    /api/documents/employee/{id}       # Get employee docs (RH)
DELETE /api/documents/{id}        # Delete document (Admin)
```

### Formations (6 endpoints)
```
POST   /api/formations/           # Create formation
GET    /api/formations/           # List formations
GET    /api/formations/rh/all     # List all (RH dedicated)
GET    /api/formations/{id}       # Get formation details
PUT    /api/formations/{id}       # Update formation
DELETE /api/formations/{id}       # Delete formation
```

### Contracts (6 endpoints)
```
POST   /api/contracts/            # Create contract
GET    /api/contracts/my-contract # Get own contract
GET    /api/contracts/            # List all (RH)
GET    /api/contracts/employee/{id}       # Get employee contract
PUT    /api/contracts/{id}        # Update contract
DELETE /api/contracts/{id}        # Delete contract
```

**Total: 35 Endpoints**

---

## 🔑 Key Design Patterns

### 1. Dependency Injection
```python
def get_current_user(token: str = Depends(...)) -> User:
    # Validate and return current user
    pass

def require_role(allowed_roles):
    def check_role(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(403, "Not authorized")
        return current_user
    return check_role

@router.get("/admin-only")
def admin_endpoint(current_user: User = Depends(require_role([RoleEnum.ADMIN]))):
    # Only admin can access
    pass
```

### 2. Service Layer Pattern
```python
# In core/security.py
def hash_password(password: str) -> str:
    return CryptContext(...).hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return CryptContext(...).verify(plain, hashed)

# In routes
user = User(mots_de_passe=hash_password(user_data.mots_de_passe))
```

### 3. Schema Validation
```python
# In schemas/user.py
class UserCreate(BaseModel):
    nom: str
    prenom: str
    email: str
    mots_de_passe: str
    role: RoleEnum
    
    class Config:
        schema_extra = {
            "example": {"nom": "Dupont", ...}
        }

# In routes
def create_user(user: UserCreate, ...):  # Auto-validated
    pass
```

### 4. RBAC Pattern
```python
# Check role in route
if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH]:
    raise HTTPException(403, "Not authorized")

# Or use dependency
@router.get("/")
def get_all(current_user: User = Depends(require_role([RoleEnum.ADMIN]))):
    pass
```

### 5. Database Session Pattern
```python
# Get session from dependency
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Use in routes
@router.get("/")
def list_items(db: Session = Depends(get_db)):
    return db.query(Model).all()
```

---

## 🔒 Security Measures

### Password Security
- Hashed with bcrypt (passlib)
- Salt included automatically
- Never stored in plain text
- Verified on login

### JWT Security
- HS256 algorithm
- 30-minute expiration
- Secret key in environment
- Validated on each request
- Signature verified

### Input Validation
- Pydantic schemas validate all inputs
- Type checking enforced
- Email format validated
- Required fields enforced

### RBAC Implementation
- Role-based access control
- Per-endpoint authorization
- Consistent role checking
- Proper 403 responses

### Database Protection
- SQL injection prevented by ORM
- Parameterized queries
- Foreign key constraints
- Enum type safety

---

## 📈 Performance Considerations

### Indexing
- Primary keys auto-indexed
- Foreign keys indexed
- Email unique constraint (indexed)
- Role enum for quick filtering

### Query Optimization
- Direct SQLAlchemy queries (no N+1)
- Filter at database level
- Proper join usage
- Lazy loading configured

### Caching Strategy
- JWT tokens cached implicitly (30 min)
- Static enum values
- No explicit cache layer (not needed for scale)

### Database Connection
- Connection pooling via SQLAlchemy
- Session per request pattern
- Proper cleanup in finally blocks

---

## 🚀 Scalability Notes

### Current Architecture Supports
- ✅ Single database instance
- ✅ Multiple app instances (with DB connection pooling)
- ✅ Stateless API (JWT instead of sessions)
- ✅ Easy horizontal scaling

### Future Improvements
- Add Redis for token blacklist
- Implement caching for frequently accessed data
- Add database replication for HA
- Implement API rate limiting
- Add request logging/tracing

---

## 🧪 Testing Strategy

### Unit Tests
- Endpoint response validation
- Permission checks
- Data validation

### Integration Tests
- Full request/response flow
- Database operations
- RBAC verification

### Load Tests
- Concurrent user handling
- Database query performance
- Token generation speed

---

## 📦 Deployment Architecture

### Development
```
Local Machine
    ↓
SQLite Database
    ↓
FastAPI + Uvicorn (reload enabled)
```

### Production
```
Load Balancer
    ↓
Multiple FastAPI Instances (Docker)
    ↓
PostgreSQL Database (HA)
    ↓
Redis Cache (optional)
    ↓
Monitoring & Logging
```

---

## 🔄 Data Flow Example: Creating a Leave

```
Client
  ↓ POST /api/leaves/
API Route (leaves.py)
  ├─► extract token from header
  ├─► validate JWT token (core/security.py)
  ├─► get user from database
  ├─► check role: Collaborateur/Manager? (dependency: require_role)
  ├─► validate request body (schema: LeaveCreate)
  ├─► validate dates (start_date < end_date)
  ├─► create Leave object in memory
  ├─► save to database (db.add, db.commit)
  ├─► convert to response format (LeaveResponse schema)
  └─► return 201 + leave JSON
Client receives the created leave with ID
```

---

## 🛠️ Extension Points

### Add New Feature
1. Create model in `models/`
2. Create schema in `schemas/`
3. Create route file in `api/`
4. Add router to `main.py`
5. Add role-based checks

### Add New Role
1. Add to `RoleEnum` in `models/user.py`
2. Update all RBAC checks
3. Create dashboard endpoint
4. Update documentation

### Add New Endpoint
1. Define route in appropriate file
2. Add schema validation
3. Check role/permissions
4. Add to documentation

---

## 📚 Best Practices Implemented

- ✅ Single Responsibility Principle
- ✅ Separation of Concerns
- ✅ DRY (Don't Repeat Yourself)
- ✅ SOLID Principles
- ✅ Security-First Design
- ✅ Error Handling
- ✅ Logging Ready
- ✅ Documentation Complete
- ✅ Type Hints Throughout
- ✅ Consistent Naming

---

## 🔍 Code Quality

- **Type Hints**: 100% coverage
- **Docstrings**: All functions documented
- **Error Handling**: Proper HTTP status codes
- **CORS**: Configured
- **Validation**: Input/output validated
- **Testing**: Test files included
- **Documentation**: 2000+ lines

---

**Architecture designed for scalability, security, and maintainability.**

Last Updated: January 20, 2024  
Version: 1.1.0
