from database.db import SessionLocal
from models.user import User, RoleEnum
from core.security import hash_password

def seed_users():
    db = SessionLocal()
    try:
        users_to_create = [
            {
                "nom": "Benali",
                "prenom": "Sarah",
                "email": "sarah.benali@ydays.company",
                "mots_de_passe": hash_password("YDAYS2026!"),
                "role": RoleEnum.COLLABORATEUR,
            },
            {
                "nom": "Admin",
                "prenom": "Super",
                "email": "admin@ydays.company",
                "mots_de_passe": hash_password("YDAYS2026!"),
                "role": RoleEnum.ADMIN,
            },
            {
                "nom": "QVT",
                "prenom": "Manager",
                "email": "qvt@ydays.company",
                "mots_de_passe": hash_password("YDAYS2026!"),
                "role": RoleEnum.RH,
            },
            {
                "nom": "El Mansouri",
                "prenom": "Nadir",
                "email": "nadir.elmansouri@ydays.company",
                "mots_de_passe": hash_password("MGR2026!"),
                "role": RoleEnum.MANAGER,
            },
            {
                "nom": "Rachidi",
                "prenom": "Amina",
                "email": "amina.rachidi@ydays.company",
                "mots_de_passe": hash_password("RH2026!"),
                "role": RoleEnum.RH,
            }
        ]
        
        created = 0
        for u_data in users_to_create:
            existing = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing:
                new_user = User(**u_data)
                db.add(new_user)
                created += 1
                
        db.commit()
        print(f"Utilisateurs de test créés avec succès : {created}")
    except Exception as e:
        print(f"Erreur : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
