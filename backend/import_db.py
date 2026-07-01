import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database.db import engine

def import_data():
    json_path = os.path.join('database', 'export_data.json')
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Found {len(data)} tables in export.")
    
    # Use autocommit to avoid transaction block errors
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        print("Disabling foreign key constraints (session_replication_role = 'replica')...")
        conn.execute(text("SET session_replication_role = 'replica';"))
        
        tables_to_truncate = [t for t in data.keys() if data[t]]
        if tables_to_truncate:
            tables_str = ', '.join([f'"{t}"' for t in tables_to_truncate])
            print(f"Truncating tables to replace data...")
            conn.execute(text(f"TRUNCATE TABLE {tables_str} CASCADE;"))

        for table_name, rows in data.items():
            if not rows:
                continue
                
            print(f"Importing {len(rows)} rows into {table_name}...")
            
            columns = rows[0].keys()
            cols_str = ', '.join([f'"{col}"' for col in columns])
            vals_str = ', '.join([f":{col}" for col in columns])
            
            stmt = text(f'INSERT INTO "{table_name}" ({cols_str}) VALUES ({vals_str})')
            
            try:
                conn.execute(stmt, rows)
            except Exception as e:
                print(f"Failed to insert into {table_name}: {e}")
            
        print("Re-enabling foreign key constraints...")
        conn.execute(text("SET session_replication_role = 'origin';"))

        print("Resynchronizing sequences with imported data...")
        reset_sequences(conn, data.keys())

        print("Import successful!")


def reset_sequences(conn, table_names):
    """Après un import avec IDs explicites, les séquences PostgreSQL restent en retard
    sur les IDs réellement présents, ce qui provoque des erreurs 'duplicate key' au
    premier INSERT suivant. On les recale sur MAX(id) pour chaque table importée."""
    for table_name in table_names:
        seq = conn.execute(
            text("SELECT pg_get_serial_sequence(:table, 'id')"),
            {"table": table_name}
        ).scalar()
        if not seq:
            continue
        conn.execute(text(
            f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM \"{table_name}\"), 1), "
            f"(SELECT MAX(id) IS NOT NULL FROM \"{table_name}\"))"
        ))

if __name__ == '__main__':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    import_data()
