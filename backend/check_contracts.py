import os
os.environ["DATABASE_URL"] = "postgresql://ydays_user:ydays_password@localhost:5432/ydays_db"

from database.db import SessionLocal
from models.user import User
from models.features import Contract

# Import all other models to prevent SQLAlchemy relationship resolution errors
import models.employees
import models.chatbot
import models.features

db = SessionLocal()
count = db.query(Contract).count()
print(f"TOTAL_CONTRACTS_IN_DB: {count}")

print("Details:")
for c in db.query(Contract).all():
    print(f"- ID: {c.id}, User ID: {c.user_id}, Position: {c.position}, Type: {c.contract_type}")
