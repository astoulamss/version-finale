"""
Migration v13: Ajout de la colonne is_deleted_by_user à chatbot_conversations.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ydays_user:ydays_password@localhost:5433/ydays_db")

def get_pg_conn_params(url: str):
    # Parse postgresql://user:password@host:port/dbname
    url = url.replace("postgresql://", "")
    user_pass, rest = url.split("@")
    user, password = user_pass.split(":")
    host_port, dbname = rest.split("/")
    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host, port = host_port, "5432"
    return {"user": user, "password": password, "host": host, "port": int(port), "dbname": dbname}

def migrate():
    params = get_pg_conn_params(DATABASE_URL)
    conn = psycopg2.connect(**params)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'chatbot_conversations' AND column_name = 'is_deleted_by_user'
    """)
    if cursor.fetchone():
        print("Colonne 'is_deleted_by_user' existe déjà.")
    else:
        print("Ajout de 'is_deleted_by_user' à chatbot_conversations...")
        cursor.execute("""
            ALTER TABLE chatbot_conversations
            ADD COLUMN is_deleted_by_user BOOLEAN NOT NULL DEFAULT FALSE
        """)
        conn.commit()
        print("Migration réussie.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    migrate()
