"""
Migration v14 : Création de la table user_devices pour les tokens Expo push.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ydays_user:ydays_password@localhost:5433/ydays_db")


def get_pg_conn_params(url: str):
    url = url.replace("postgresql://", "")
    user_pass, rest = url.split("@")
    user, password = user_pass.split(":")
    host_port, dbname = rest.split("/")
    host, port = (host_port.split(":") if ":" in host_port else (host_port, "5432"))
    return {"user": user, "password": password, "host": "127.0.0.1", "port": int(port), "dbname": dbname}


def migrate():
    params = get_pg_conn_params(DATABASE_URL)
    conn = psycopg2.connect(**params)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_name = 'user_devices'
    """)
    if cursor.fetchone():
        print("Table 'user_devices' existe déjà.")
    else:
        print("Création de la table 'user_devices'...")
        cursor.execute("""
            CREATE TABLE user_devices (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expo_push_token VARCHAR(255) NOT NULL UNIQUE,
                platform VARCHAR(20),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cursor.execute("CREATE INDEX idx_user_devices_user_id ON user_devices(user_id)")
        conn.commit()
        print("Migration réussie.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    migrate()
