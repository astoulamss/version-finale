import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from models.user import User
from ai.services.chat_service import chat

db = SessionLocal()
user = db.query(User).filter(User.email == "sarah.benali@ydays.company").first()

if not user:
    print("User not found!")
else:
    print("User found:", user.email)
    response_text, doc_info, sources, chart_b64, conv_id = chat("Explique moi les congés", user, db, conversation_id=1)
    print("Response:", response_text)
    print("Conv ID:", conv_id)
    
db.close()
