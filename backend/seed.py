import os
import sys

# Ajouter le répertoire courant au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from models.user import User, RoleEnum
from models.employees import Employee

def fix_db():
    db = SessionLocal()
    # On assigne tout à User ID 11 (le nouveau Nadir)
    manager_id = 11
    emps = db.query(Employee).filter(Employee.user_id != manager_id).all()
    count = 0
    for e in emps:
        e.manager_id = manager_id
        count += 1
    db.commit()
    print(f"{count} employés mis à jour vers le manager {manager_id}.")

if __name__ == "__main__":
    fix_db()
