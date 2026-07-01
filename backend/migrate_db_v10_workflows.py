import sys
import os

# Add the ydays directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import engine
from sqlalchemy import text

def run_migration():
    print("Running migration v10: Creating workflow_configs table...")
    with engine.connect() as conn:
        try:
            # Create table if not exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS workflow_configs (
                    id SERIAL PRIMARY KEY,
                    entity_type VARCHAR(100) UNIQUE NOT NULL,
                    logic_type VARCHAR(100) NOT NULL DEFAULT 'single_manager',
                    validator_role VARCHAR(100) NULL,
                    validator_user_id INTEGER REFERENCES users(id) NULL
                );
            """))
            
            # Insert default values if not already present
            conn.execute(text("""
                INSERT INTO workflow_configs (entity_type, logic_type)
                VALUES ('leave', 'single_manager')
                ON CONFLICT (entity_type) DO NOTHING;
            """))
            conn.execute(text("""
                INSERT INTO workflow_configs (entity_type, logic_type)
                VALUES ('absence', 'single_manager')
                ON CONFLICT (entity_type) DO NOTHING;
            """))
            
            conn.commit()
            print("Migration successful: Created workflow_configs table and inserted default configs.")
        except Exception as e:
            conn.rollback()
            print(f"Migration failed or already applied: {e}")

if __name__ == "__main__":
    run_migration()
