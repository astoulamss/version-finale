import os
from sqlalchemy import create_engine, text

# Assurez-vous que l'URL est correcte par rapport à votre environnement
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ydays")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        # Essayer d'ajouter 'received' à l'enum absencestatusenum
        # Si la valeur existe déjà, PostgreSQL renverra une erreur, mais avec IF NOT EXISTS (PG 12+) ce sera ignoré ou on peut l'attraper.
        # Attention: sqlalchemy va autocommit si on execute raw avec certains pilotes, on bind l'execution.
        conn.execute(text("COMMIT")) # psycopg2 needs this before ALTER TYPE
        conn.execute(text("ALTER TYPE absencestatusenum ADD VALUE IF NOT EXISTS 'received';"))
        print("Success: 'received' added to absencestatusenum")
    except Exception as e:
        print("Error or already exists:", e)

