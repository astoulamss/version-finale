import sys
import os

# Add backend directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from models.user import User, RoleEnum
from models.employees import Employee
from datetime import date

def update_existing_nadir():
    db = SessionLocal()
    try:
        # Chercher tous les utilisateurs s'appelant Nadir Elmansouri
        nadirs = db.query(User).filter(
            User.prenom.ilike('%nadir%'),
            User.nom.ilike('%elmansouri%')
        ).all()
        
        if not nadirs:
            print("Aucun compte existant trouvé pour Nadir Elmansouri.")
            return

        print(f"Trouvé {len(nadirs)} compte(s) pour Nadir Elmansouri.")
        
        for nadir in nadirs:
            print(f"- Mise à jour du rôle pour : {nadir.email} (ID: {nadir.id})")
            nadir.role = RoleEnum.MANAGER
            
            # Assurer qu'il a un profil employé
            nadir_emp = db.query(Employee).filter(Employee.user_id == nadir.id).first()
            if not nadir_emp:
                nadir_emp = Employee(
                    user_id=nadir.id,
                    status="active",
                    hire_date=date(2023, 1, 15)
                )
                db.add(nadir_emp)
            
            # Lui assigner le collaborateur de test
            collab_email = "collab.test@ydays.com"
            collab = db.query(User).filter(User.email == collab_email).first()
            if collab:
                collab_emp = db.query(Employee).filter(Employee.user_id == collab.id).first()
                if collab_emp:
                    collab_emp.manager_id = nadir.id
                    print(f"  -> Collaborateur {collab_email} assigné à son équipe.")
        
        db.commit()
        print("\nSUCCÈS : Tous les comptes existants de Nadir Elmansouri sont maintenant des Managers.")
        if nadirs:
            print("Vous pouvez vous connecter avec votre adresse email habituelle :", nadirs[0].email)

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_existing_nadir()
