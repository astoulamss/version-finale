import os
os.environ["DATABASE_URL"] = "postgresql://ydays_user:ydays_password@localhost:5432/ydays_db"
from database.db import SessionLocal
from api.dashboard import get_dashboard_stats
from models.user import User

db = SessionLocal()

# We need a dummy user to bypass the require_role dependency, but wait...
# get_dashboard_stats takes db and current_user as kwargs.
# Let's just create a dummy admin user
admin_user = db.query(User).first()

stats = get_dashboard_stats(db=db, current_user=admin_user)
print("Stats from get_dashboard_stats:")
print(f"total_contracts: {stats.total_contracts}")
print(f"total_documents: {stats.total_documents}")
print(f"leaves_pending: {stats.leaves_pending}")
