"""
Test script to verify all imports and functionality
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    
    try:
        from database.db import Base, engine, get_db
        print("[OK] Database imports successful")
    except Exception as e:
        print(f"[FAIL] Database import failed: {e}")
        return False
    
    try:
        from models.user import User, RoleEnum
        print("[OK] User model imports successful")
    except Exception as e:
        print(f"[FAIL] User model import failed: {e}")
        return False
    
    try:
        from models.features import Leave, Document, Formation, Contract
        print("[OK] Features model imports successful")
    except Exception as e:
        print(f"[FAIL] Features model import failed: {e}")
        return False
    
    try:
        from schemas.user import UserCreate, UserResponse, TokenResponse
        print("[OK] User schema imports successful")
    except Exception as e:
        print(f"[FAIL] User schema import failed: {e}")
        return False
    
    try:
        from schemas.features import (
            LeaveCreate, LeaveResponse, LeaveUpdate,
            DocumentManualCreate, DocumentGenerateRequest, DocumentResponse,
            FormationCreate, FormationResponse,
            ContractCreate, ContractResponse
        )
        print("[OK] Features schema imports successful")
    except Exception as e:
        print(f"[FAIL] Features schema import failed: {e}")
        return False
    
    try:
        from core.security import hash_password, verify_password, create_access_token
        print("[OK] Security imports successful")
    except Exception as e:
        print(f"[FAIL] Security import failed: {e}")
        return False
    
    try:
        from api import auth, dashboard, users, leaves, documents, formations, contracts
        print("[OK] API router imports successful")
    except Exception as e:
        print(f"[FAIL] API router import failed: {e}")
        return False
    
    print("\n[OK] All imports successful!")
    return True


def test_app_creation():
    """Test FastAPI app creation"""
    print("\nTesting app creation...")
    
    try:
        from main import app
        print("[OK] FastAPI app created successfully")
        
        # Check routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print(f"\n[OK] Total routes: {len(routes)}")
        
        # Check specific routes
        expected_routes = [
            "/api/auth/login",
            "/api/users/",
            "/api/leaves/",
            "/api/documents/",
            "/api/formations/",
            "/api/contracts/",
            "/dashboard/home"
        ]
        
        found_routes = [r for r in expected_routes if any(r in route for route in routes)]
        print(f"[OK] Found {len(found_routes)} expected routes")
        
        return True
    except Exception as e:
        print(f"[FAIL] App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    if success:
        success = test_app_creation()
    
    if success:
        print("\n" + "="*50)
        print("All tests passed! Backend is ready.")
        print("="*50)
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("Some tests failed. Please fix the errors above.")
        print("="*50)
        sys.exit(1)
