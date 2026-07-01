"""
Migration v8 — Création de la table manager_tasks
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import engine, Base
from models.features import ManagerTask, TaskPriorityEnum, TaskStatusEnum

def run_migration():
    print("[...] Migration v8 : Creation de la table manager_tasks...")
    try:
        # Cree uniquement les tables manquantes (checkfirst=True)
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("[OK] Table 'manager_tasks' creee avec succes (ou deja existante).")
    except Exception as e:
        print(f"[ERREUR] lors de la migration: {e}")
        raise

if __name__ == "__main__":
    run_migration()
