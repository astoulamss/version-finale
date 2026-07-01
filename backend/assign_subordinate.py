import sys
import os

# Add backend directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from models.user import User, RoleEnum
from models.employees import Employee

def assign_collab():
    db = SessionLocal()
    try:
        # Chercher le vrai Nadir (ID 3)
        nadir = db.query(User).filter(User.email == "nadir.elmansouri@ydays.company").first()
        if not nadir:
            print("Nadir (vrai compte) non trouvé.")
            return

        # S'assurer qu'il est bien Manager
        nadir.role = RoleEnum.MANAGER
        
        # Chercher Sarah Benali et la mettre dans son équipe (pour avoir de vraies données)
        sarah = db.query(User).filter(User.email == "sarah.benali@ydays.company").first()
        if sarah:
            sarah_emp = db.query(Employee).filter(Employee.user_id == sarah.id).first()
            if sarah_emp:
                sarah_emp.manager_id = nadir.id
                print("Sarah Benali assignée à Nadir El Mansouri.")
        
        db.commit()
        print("Mise à jour réussie. Nadir a maintenant Sarah dans son équipe.")

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    assign_collab()
