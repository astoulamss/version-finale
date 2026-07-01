from database.db import engine
from sqlalchemy import text

def upgrade():
    print("Migrating absences table to add is_archived column...")
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='absences' AND column_name='is_archived';"))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE absences ADD COLUMN is_archived BOOLEAN DEFAULT FALSE NOT NULL;"))
                conn.commit()
                print("Column 'is_archived' added successfully to 'absences'.")
            else:
                print("Column 'is_archived' already exists in 'absences'.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    upgrade()
