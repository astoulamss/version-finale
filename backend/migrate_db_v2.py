import sys
from pathlib import Path
from sqlalchemy import text

# Add parent directory to path so database module can be imported
sys.path.insert(0, str(Path(__file__).parent))

from database.db import engine

def run_migration():
    print("Running migration to add new columns to employees table...")
    
    statements = [
        "ALTER TABLE employees ADD COLUMN IF NOT EXISTS date_naissance DATE;",
        "ALTER TABLE employees ADD COLUMN IF NOT EXISTS nationalite VARCHAR(100);",
        "ALTER TABLE employees ADD COLUMN IF NOT EXISTS adresse VARCHAR(255);",
        "ALTER TABLE employees ADD COLUMN IF NOT EXISTS numero_telephone VARCHAR(50);",
        "ALTER TABLE employees ADD COLUMN IF NOT EXISTS sexe VARCHAR(50);"
    ]
    
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            for statement in statements:
                print(f"Executing: {statement}")
                conn.execute(text(statement))
            transaction.commit()
            print("Migration completed successfully!")
        except Exception as e:
            transaction.rollback()
            print(f"Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    run_migration()
