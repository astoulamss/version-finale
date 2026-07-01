"""
Script pour créer le premier administrateur
À exécuter une seule fois pour initialiser le système
"""

from database.db import SessionLocal, engine, Base
from models.user import User, RoleEnum
from core.security import hash_password

def create_admin():
    """Créer un utilisateur administrateur"""
    
    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Vérifier si un admin existe déjà
        existing_admin = db.query(User).filter(User.role == RoleEnum.ADMIN).first()
        if existing_admin:
            print("⚠️  Un administrateur existe déjà!")
            print(f"   Email: {existing_admin.email}")
            return
        
        # Créer l'admin
        admin = User(
            nom="Admin",
            prenom="Super",
            email="admin@example.com",
            mots_de_passe=hash_password("admin123"),
            role=RoleEnum.ADMIN,
            is_active=True,
            first_login=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("✅ Administrateur créé avec succès!")
        print(f"   Email: {admin.email}")
        print(f"   Mot de passe: admin123")
        print(f"   ⚠️  IMPORTANT: Changez ce mot de passe en production!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'admin: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
