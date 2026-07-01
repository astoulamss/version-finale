import subprocess
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db import engine, Base
from models.user import User
from models.employees import Employee, Department, Position
from models.features import Document, DocumentTemplate, DocumentType, Leave, Formation, FormationEnrollment, Contract
from models.absences import Absence
from models.history import HistoryLog
from models.notification import Notification
from sqlalchemy import text

Base.metadata.create_all(bind=engine)

from sqlalchemy.orm import Session
session = Session(bind=engine)
has_data = session.query(User).first() is not None
session.close()

if not has_data:
    with engine.connect() as conn:
        conn.execute(text("SET session_replication_role = 'replica'"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
        conn.execute(text("SET session_replication_role = 'origin'"))
        for table in Base.metadata.sorted_tables:
            seq = f"{table.name}_id_seq"
            conn.execute(text(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1"))
        conn.commit()
        print("Tables truncated and sequences reset")

    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.dirname(__file__)), "seed_data.py")], check=True)
    print("Database initialized successfully (seed data inserted)")
else:
    print("Database already contains data — skipping truncate and seed.")
