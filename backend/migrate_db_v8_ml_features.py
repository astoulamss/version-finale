import sys
from pathlib import Path
from sqlalchemy import text

# Add parent directory to path so database module can be imported
sys.path.insert(0, str(Path(__file__).parent))

from database.db import engine, Base
import models.user
import models.employees
import models.ml_features

def migrate_ml_features():
    print("Starting ML features DB migration...")
    
    with engine.connect() as conn:
        print("Checking for distance_from_home_km column...")
        try:
            conn.execute(text("ALTER TABLE employees ADD COLUMN distance_from_home_km INTEGER;"))
            conn.commit()
            print("Added distance_from_home_km to employees.")
        except Exception as e:
            conn.rollback()
            print(f"distance_from_home_km probably already exists: {e}")

    print("Creating new ML tables (SalaryHistory, PerformanceReview, Timesheet)...")
    Base.metadata.create_all(bind=engine)
    print("Migration successful.")

if __name__ == "__main__":
    migrate_ml_features()
