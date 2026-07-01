import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent))
from database.db import engine

def run_migration():
    print("Running migration: add equipment_returned and administrative_closed columns to offboarding_plans table...")
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            conn.execute(text(
                "ALTER TABLE offboarding_plans ADD COLUMN IF NOT EXISTS equipment_returned BOOLEAN DEFAULT FALSE;"
            ))
            conn.execute(text(
                "ALTER TABLE offboarding_plans ADD COLUMN IF NOT EXISTS administrative_closed BOOLEAN DEFAULT FALSE;"
            ))
            transaction.commit()
            print("Migration completed successfully!")
        except Exception as e:
            transaction.rollback()
            print(f"Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    run_migration()
