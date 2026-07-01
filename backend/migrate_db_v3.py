import sys
from pathlib import Path
from sqlalchemy import text

# Add parent directory to path so database module can be imported
sys.path.insert(0, str(Path(__file__).parent))

from database.db import engine

def run_migration():
    print("Running migration to add file_url column to documents table...")
    
    statements = [
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_url VARCHAR(500);"
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
