"""
Migration v11: Ajout du champ is_sent à la table documents.
Ce champ permet de contrôler la visibilité des documents côté collaborateur :
- Si is_sent=False (défaut), le collaborateur ne voit pas le document.
- Si is_sent=True, il devient visible dans l'espace du collaborateur.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ydays.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(documents)")
    columns = [row[1] for row in cursor.fetchall()]

    if "is_sent" not in columns:
        print("Ajout de la colonne 'is_sent' à la table 'documents'...")
        cursor.execute("ALTER TABLE documents ADD COLUMN is_sent BOOLEAN NOT NULL DEFAULT 0")
        conn.commit()
        print("Migration réussie.")
    else:
        print("La colonne 'is_sent' existe déjà. Migration non nécessaire.")

    conn.close()

if __name__ == "__main__":
    migrate()
