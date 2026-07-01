import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.security import hash_password
from database.db import engine
from sqlalchemy import text

def reset_all_passwords():
    h = hash_password('YDAYS2026!')
    with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
        conn.execute(text("UPDATE users SET mots_de_passe = :h"), {"h": h})
    print("Passwords successfully reset to YDAYS2026!")

if __name__ == '__main__':
    reset_all_passwords()
