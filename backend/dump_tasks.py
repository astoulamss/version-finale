import sys
import os

# Add backend directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from models.user import User
from models.employees import Employee, Department, Position
from models.absences import Absence
from models.features import ManagerTask, Leave, Formation, Document, Contract

def dump_tasks():
    db = SessionLocal()
    try:
        tasks = db.query(ManagerTask).all()
        if not tasks:
            print("Aucune tâche trouvée dans la DB.")
        for t in tasks:
            print(f"ID: {t.id} | Titre: {t.title} | Status: {t.status} | Assigné à: {t.assigned_to} | Créé par: {t.created_by}")
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    dump_tasks()
