import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent))
from database.db import engine

def run_migration():
    print("Running migration: add manager_id to departments table...")
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            conn.execute(text(
                "ALTER TABLE departments ADD COLUMN IF NOT EXISTS manager_id INTEGER REFERENCES users(id) ON DELETE SET NULL;"
            ))
            transaction.commit()
            print("Migration completed successfully!")
        except Exception as e:
            transaction.rollback()
            print(f"Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    run_migration()
