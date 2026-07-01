# 📝 CHANGELOG - YDAYS Backend

## Version 1.1.0 - Features Release (Latest)

### New Features Added

#### 🏖️ Leave Management System
- **Endpoints**: 5 new endpoints for leave management
  - `POST /api/leaves/` - Create leave request
  - `GET /api/leaves/my-leaves` - View personal leaves
  - `GET /api/leaves/team` - Manager views team leaves
  - `PUT /api/leaves/{id}` - Approve/Reject leaves
  - `DELETE /api/leaves/{id}` - Cancel pending leaves
  
- **Leave Types**: vacation, sick, maternity, personal, unpaid
- **Statuses**: pending, approved, rejected, cancelled
- **RBAC**: Collaborateur & Manager create, Manager & Admin approve
- **Model**: Leave table with employee_id, dates, status tracking

#### 📄 Document Management System
- **Endpoints**: 4 new endpoints for document management
  - `POST /api/documents/` - Upload document
  - `GET /api/documents/my-documents` - View personal documents
  - `GET /api/documents/employee/{id}` - RH views employee docs
  - `DELETE /api/documents/{id}` - Remove document
  
- **Document Types**: contract, payslip, certificate, training, other
- **RBAC**: RH & Admin upload, Employees view personal, RH views all
- **Security**: RH cannot view personal documents via RH access
- **Model**: Document table with file tracking and user association

#### 🎓 Formation Management System
- **Endpoints**: 6 new endpoints for training management
  - `POST /api/formations/` - Create formation
  - `GET /api/formations/` - View available formations
  - `GET /api/formations/rh/all` - RH dedicated access
  - `GET /api/formations/{id}` - View formation details
  - `PUT /api/formations/{id}` - Update formation
  - `DELETE /api/formations/{id}` - Delete formation
  
- **RBAC**: RH & Admin create/update, All (except RH regular) view
- **Model**: Formation table with start/end dates and description
- **Permissions**: RH blocked from regular formations endpoint for privacy

#### 📋 Contract Management System
- **Endpoints**: 6 new endpoints for contract management
  - `POST /api/contracts/` - Create contract
  - `GET /api/contracts/my-contract` - View own contract
  - `GET /api/contracts/` - RH views all contracts
  - `GET /api/contracts/employee/{id}` - RH views specific employee
  - `PUT /api/contracts/{id}` - Update contract
  - `DELETE /api/contracts/{id}` - Delete contract
  
- **Contract Types**: CDI, CDD, Stage, Alternance, Freelance
- **RBAC**: RH & Admin manage, Employees view own
- **Model**: Contract table with type, salary, position tracking
- **Security**: One contract per employee, RH cannot view personal

### Models & Database

#### New Models (models/features.py)
- **Leave**: Tracks employee leave requests
  - Fields: employee_id, start_date, end_date, leave_type, status, reason, approved_by
  - Enums: LeaveStatusEnum, LeaveTypeEnum

- **Document**: Stores document metadata
  - Fields: user_id, title, document_type, file_path, created_at
  
- **Formation**: Training programs
  - Fields: title, description, start_date, end_date
  
- **Contract**: Employment contracts
  - Fields: user_id, contract_type, start_date, end_date, position, salary

#### New Schemas (schemas/features.py)
- LeaveCreate, LeaveResponse, LeaveUpdate
- DocumentCreate, DocumentResponse
- FormationCreate, FormationResponse
- ContractCreate, ContractResponse

### API Routes

#### New Route Files (api/)
- **leaves.py** - Leave request management (5 endpoints)
- **documents.py** - Document management (4 endpoints)
- **formations.py** - Formation management (6 endpoints)
- **contracts.py** - Contract management (6 endpoints)

#### Total Endpoints Added: 21

### Dashboard Enhancements (api/dashboard.py)

Updated all role-based dashboards with detailed descriptions:

- **Collaborateur**: Profil, Congés, Documents, Formations, Chatbot RH
- **Manager**: Employee features + Validation congés, Suivi équipe, Évaluations, Indicateurs
- **RH**: Gestion des employés, Contrats, Onboarding, Offboarding, Documents, Reporting
- **Direction**: Tableaux stratégiques, Prévisions RH, KPI globaux, Analyses prédictives
- **Admin**: Accès complet au système, Gestion utilisateurs, Création comptes

### Documentation

#### New Documentation Files
- **FEATURES.md** - Complete feature documentation (500+ lines)
  - Detailed endpoint descriptions
  - Request/response examples
  - Permission matrix
  - Usage examples for each feature

- **EXAMPLES_EXTENDED.md** - Comprehensive usage examples (600+ lines)
  - Complete cURL examples for all endpoints
  - Python testing script
  - End-to-end workflows
  - Common errors & solutions
  - Postman setup guide

- **QUICKSTART.md** - Quick start guide (300+ lines)
  - Installation steps
  - Server startup
  - Quick testing commands
  - Troubleshooting guide
  - Project structure

#### Updated Documentation
- **README.md**
  - Added new endpoints section
  - Updated permissions table (24 rows)
  - Added feature descriptions
  - Reference to FEATURES.md

### Utilities & Testing

#### New Testing File
- **test_setup.py** - Setup verification script
  - Verifies all imports
  - Tests app creation
  - Counts total routes
  - Checks for expected endpoints

#### Updated Main Application
- **main.py**
  - Added 4 new router imports
  - Added feature models import for table creation
  - Integrated all new routers
  - Updated app title and version

### Integration

#### RBAC Enhancement
- Enhanced permission checking across all new endpoints
- Consistent dependency injection pattern
- Role-based access control for all features
- Proper error handling with HTTP status codes

#### Database Schema
- All new models automatically create tables via SQLAlchemy
- Foreign key relationships maintained
- Enum types for standardization
- Timestamp tracking (created_at, updated_at)

### Breaking Changes
- **None** - This is a backward-compatible release

### Deprecations
- **None**

### Bug Fixes
- **None** - Feature release, no bug fixes

### Security Improvements
- Added RBAC for new features
- Protected sensitive endpoints (contracts, documents)
- Proper authentication on all new endpoints
- Input validation via Pydantic schemas
- Prevented RH from accessing personal information they shouldn't

### Performance Notes
- All endpoints optimized for standard operations
- Proper database indexing via SQLAlchemy
- Efficient query patterns used
- No N+1 query issues

### Compatibility
- ✅ Python 3.10+
- ✅ FastAPI 0.104.1+
- ✅ SQLAlchemy 2.0.23+
- ✅ SQLite (default)
- ✅ PostgreSQL (production-ready)

### Migration Guide

No database migration needed - tables created automatically on first run via SQLAlchemy.

### Known Issues
- None known

### Future Enhancements
- Employee-Formation enrollment tracking
- Leave balance management
- Document versioning
- Contract templates
- Chatbot RH endpoint integration
- Team/Department associations
- Leave approval workflow notifications
- Document digital signature support

---

## Version 1.0.0 - Initial Release

### Features
- User authentication with JWT
- Role-based access control (5 roles)
- Admin user creation
- User management (CRUD)
- Role-specific dashboards
- Password hashing with bcrypt
- Token expiration (30 minutes)
- CORS middleware
- SQLAlchemy ORM support
- PostgreSQL and SQLite support
- Docker support
- Comprehensive documentation

### Endpoints
- Authentication: 1 endpoint
- Users: 7 endpoints
- Dashboards: 6 endpoints
- Total: 14 endpoints

### Documentation
- README.md
- EXAMPLES.md
- setup instructions

---

## Statistics

### Code Metrics (v1.1.0)
- Total Python Files: 20+
- Total Endpoints: 35 (14 in v1.0 + 21 new)
- Models: 5 (1 User + 4 Features)
- Schemas: 9 total
- API Routes: 7 files
- Lines of Documentation: 2000+

### Feature Coverage
- ✅ Authentication & Authorization
- ✅ User Management
- ✅ Leave Management
- ✅ Document Management
- ✅ Formation Management
- ✅ Contract Management
- ✅ Role-based Dashboards
- ⏳ Chatbot Integration (planned)
- ⏳ Notifications (planned)
- ⏳ Reporting & Analytics (planned)

---

## Release Notes

### What's New in v1.1.0
This release adds comprehensive HR management capabilities with leave, document, formation, and contract management systems. Each system includes proper role-based access control and comprehensive documentation.

### What Changed
- Dashboard endpoints now provide detailed role descriptions
- New feature endpoints fully integrated with RBAC
- Extensive documentation with examples
- Setup verification tools included

### Installation
```bash
pip install -r requirements.txt
python create_admin.py
uvicorn main:app --reload
```

### Quick Links
- [Features Documentation](FEATURES.md)
- [Usage Examples](EXAMPLES_EXTENDED.md)
- [Quick Start Guide](QUICKSTART.md)
- [Main Documentation](README.md)

---

## Contributors

YDAYS Backend Development Team

---

## Support & Issues

For issues or feature requests, please contact the development team or check the documentation files.

---

**Last Updated**: January 20, 2024  
**Current Version**: 1.1.0  
**Status**: ✅ Production Ready
