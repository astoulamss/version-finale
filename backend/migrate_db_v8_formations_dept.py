import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent))

from database.db import engine

def run_migration():
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            print("Vérification de la colonne target_department_id...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='formations' and column_name='target_department_id';
            """)).fetchone()
            
            if not result:
                print("Ajout de la colonne...")
                conn.execute(text("ALTER TABLE formations ADD COLUMN target_department_id INTEGER;"))
                conn.execute(text("""
                    ALTER TABLE formations 
                    ADD CONSTRAINT fk_formation_department 
                    FOREIGN KEY (target_department_id) REFERENCES departments(id) ON DELETE SET NULL;
                """))
                print("Colonne ajoutée.")
            else:
                print("La colonne existe déjà.")
            transaction.commit()
        except Exception as e:
            transaction.rollback()
            print(f"Erreur: {e}")

if __name__ == "__main__":
    run_migration()
