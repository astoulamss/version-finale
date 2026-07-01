from database.db import SessionLocal
import models.user
from models.features import Leave, LeaveStatusEnum, Document, Contract

db = SessionLocal()

print("Pending leaves:", db.query(Leave).filter(Leave.status == LeaveStatusEnum.PENDING).count())
print("Contracts:", db.query(Contract).count())
print("Documents:", db.query(Document).count())
