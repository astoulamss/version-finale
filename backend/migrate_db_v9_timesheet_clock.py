import sys
import os

# Add the ydays directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import engine
from sqlalchemy import text

def run_migration():
    print("Running migration v9: Adding clock_in and clock_out to timesheets...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE timesheets ADD COLUMN clock_in TIMESTAMP WITH TIME ZONE;"))
            conn.execute(text("ALTER TABLE timesheets ADD COLUMN clock_out TIMESTAMP WITH TIME ZONE;"))
            conn.execute(text("ALTER TABLE timesheets ALTER COLUMN hours_worked DROP NOT NULL;"))
            conn.commit()
            print("Migration successful: Added clock_in and clock_out.")
        except Exception as e:
            conn.rollback()
            print(f"Migration failed or already applied: {e}")

if __name__ == "__main__":
    run_migration()
