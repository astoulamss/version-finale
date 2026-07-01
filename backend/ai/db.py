import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.db import Base

DATABASE_URL = os.getenv("AI_DATABASE_URL") or os.getenv("DATABASE_URL") or "postgresql://ydays_user:ydays_password@localhost:5432/ydays_db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
