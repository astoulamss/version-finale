import sys
import os

# Add backend directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from models.user import User, RoleEnum
from models.employees import Employee, Department, Position
from core.security import hash_password
from datetime import date

def seed_test_data():
    db = SessionLocal()
    try:
        # 1. Vérifier si Nadir existe déjà
        nadir_email = "nadir.elmansouri@manager.com"
        nadir = db.query(User).filter(User.email == nadir_email).first()
        
        if not nadir:
            print("Création du compte Manager Nadir Elmansouri...")
            nadir = User(
                nom="Elmansouri",
                prenom="Nadir",
                email=nadir_email,
                mots_de_passe=hash_password("password123"),
                role=RoleEnum.MANAGER,
                is_active=True,
                first_login=False
            )
            db.add(nadir)
            db.commit()
            db.refresh(nadir)
        else:
            print("Nadir Elmansouri existe déjà.")
            nadir.role = RoleEnum.MANAGER
            db.commit()

        # Vérifier si Nadir a un profil employé
        nadir_emp = db.query(Employee).filter(Employee.user_id == nadir.id).first()
        if not nadir_emp:
            nadir_emp = Employee(
                user_id=nadir.id,
                status="active",
                hire_date=date(2023, 1, 15)
            )
            db.add(nadir_emp)
            db.commit()
            db.refresh(nadir_emp)

        # 2. Créer un collaborateur de test pour être dans l'équipe de Nadir
        collab_email = "collab.test@ydays.com"
        collab = db.query(User).filter(User.email == collab_email).first()
        
        if not collab:
            print("Création d'un collaborateur de test...")
            collab = User(
                nom="Test",
                prenom="Collaborateur",
                email=collab_email,
                mots_de_passe=hash_password("password123"),
                role=RoleEnum.COLLABORATEUR,
                is_active=True,
                first_login=False
            )
            db.add(collab)
            db.commit()
            db.refresh(collab)

        # Assigner le collaborateur à l'équipe de Nadir
        collab_emp = db.query(Employee).filter(Employee.user_id == collab.id).first()
        if not collab_emp:
            collab_emp = Employee(
                user_id=collab.id,
                manager_id=nadir.id,
                status="active",
                hire_date=date(2024, 2, 1)
            )
            db.add(collab_emp)
        else:
            collab_emp.manager_id = nadir.id
            
        db.commit()

        print("\n--- SUCCÈS ---")
        print("Compte Manager créé avec succès pour tester :")
        print(f"Email : {nadir_email}")
        print("Mot de passe : password123")
        print(f"L'employé 'Collaborateur Test' ({collab_email}) a été ajouté à son équipe pour avoir quelqu'un à qui assigner des tâches.")

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_data()
