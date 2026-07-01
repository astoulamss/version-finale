import os
os.environ['PYTHONUTF8'] = '1'
os.environ['PGCLIENTENCODING'] = 'UTF8'

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ydays_user:ydays_password@localhost:5432/ydays_db")

# Créer l'engine
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "client_encoding": "utf8",
        "options": "-c lc_messages=en_US.UTF-8"
    }
)

# Créer la session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
class Base(DeclarativeBase):
    pass


def get_db():
    """Dépendance pour obtenir la session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
