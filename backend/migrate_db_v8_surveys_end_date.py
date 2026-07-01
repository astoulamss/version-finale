import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def run_migration():
    with engine.connect() as conn:
        print("Ajout de la colonne end_date à la table surveys...")
        try:
            conn.execute(text("ALTER TABLE surveys ADD COLUMN end_date DATE;"))
            conn.commit()
            print("Colonne end_date ajoutée avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'ajout de la colonne (elle existe peut-être déjà) : {e}")

if __name__ == "__main__":
    run_migration()
