# -*- coding: utf-8 -*-
"""
Script de création des utilisateurs via psycopg2 direct (bypass SQLAlchemy encoding issue).
"""
import sys
import os

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')
os.environ['PGCLIENTENCODING'] = 'UTF8'

import subprocess
import json

CONTAINER = "ydays_db"
DB_USER = "ydays_user"
DB_NAME = "ydays_db"

# Hash bcrypt pour "YDAYS2026!" - pré-calculé pour éviter l'import du backend
# Généré via: bcrypt.hashpw(b"YDAYS2026!", bcrypt.gensalt())
USERS = [
    ("Admin",     "Super",  "admin@ydays.company",             "admin"),
    ("Benali",    "Sarah",  "sarah.benali@ydays.company",      "collaborateur"),
    ("El Mansouri","Nadir", "nadir.elmansouri@ydays.company",  "manager"),
    ("Rachidi",   "Amina",  "amina.rachidi@ydays.company",     "rh"),
    ("QVT",       "Manager","qvt@ydays.company",               "rh"),
]

def run_sql(sql):
    result = subprocess.run(
        ["docker", "exec", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-c", sql],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return result.stdout, result.stderr

# 1. Créer l'extension et les types enum si nécessaires
print("=== Creation des types ENUM ===")
out, err = run_sql("CREATE TYPE roleenum AS ENUM ('admin','rh','manager','collaborateur','medecine_travail','direction') ON CONFLICT DO NOTHING;")
print(out or err)

# 2. Créer la table users si elle n'existe pas
print("=== Creation de la table users ===")
sql_create = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    email VARCHAR(200) UNIQUE NOT NULL,
    mots_de_passe VARCHAR(200) NOT NULL,
    role VARCHAR(50) DEFAULT 'collaborateur',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
"""
out, err = run_sql(sql_create)
print(out or err)

# 3. Insérer les utilisateurs
print("=== Insertion des utilisateurs ===")

# Utilise Python bcrypt depuis le venv pour générer les hash
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from core.security import hash_password
    passwords = {
        "admin": hash_password("YDAYS2026!"),
        "collaborateur": hash_password("YDAYS2026!"),
        "manager": hash_password("MGR2026!"),
        "rh": hash_password("RH2026!"),
    }
    print("Hash passwords generes via core.security")
except Exception as e:
    print(f"Impossible de charger core.security: {e}")
    print("Utilisation de bcrypt direct...")
    import bcrypt
    passwords = {
        "admin": bcrypt.hashpw(b"YDAYS2026!", bcrypt.gensalt()).decode(),
        "collaborateur": bcrypt.hashpw(b"YDAYS2026!", bcrypt.gensalt()).decode(),
        "manager": bcrypt.hashpw(b"MGR2026!", bcrypt.gensalt()).decode(),
        "rh": bcrypt.hashpw(b"RH2026!", bcrypt.gensalt()).decode(),
    }

for nom, prenom, email, role in USERS:
    pwd_hash = passwords.get(role, passwords["collaborateur"])
    sql = f"""
    INSERT INTO users (nom, prenom, email, mots_de_passe, role)
    VALUES ('{nom}', '{prenom}', '{email}', '{pwd_hash}', '{role}')
    ON CONFLICT (email) DO NOTHING;
    """
    out, err = run_sql(sql)
    status = "OK" if "INSERT" in out else ("DEJA EXISTANT" if "0" in out else "ERREUR")
    print(f"  {email} ({role}) -> {status}")

print("\n=== Verification ===")
out, err = run_sql("SELECT email, role FROM users;")
print(out)
print("\nScript termine avec succes !")
