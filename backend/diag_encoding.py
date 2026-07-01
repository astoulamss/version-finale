import sys, locale, os

print("=== PYTHON ENCODING ===")
print("sys.getdefaultencoding():", sys.getdefaultencoding())
print("sys.stdout.encoding:", sys.stdout.encoding)
print("sys.stderr.encoding:", sys.stderr.encoding)
print("sys.getfilesystemencoding():", sys.getfilesystemencoding())
print("locale.getpreferredencoding():", locale.getpreferredencoding())
try:
    print("locale.getlocale():", locale.getlocale())
except Exception as e:
    print("locale.getlocale() error:", e)

print()
print("=== ENV VARS ===")
for var in ["PYTHONUTF8", "PYTHONIOENCODING", "PGCLIENTENCODING", "LANG", "LC_ALL", "LC_MESSAGES"]:
    print(var + ":", os.environ.get(var, "NOT SET"))

print()
print("=== PSYCOPG2 ===")
import psycopg2
print("psycopg2 version:", psycopg2.__version__)

print()
print("=== CONNEXION TEST ===")
try:
    conn = psycopg2.connect(
        "postgresql://ydays_user:ydays_password@localhost:5432/ydays_db",
        client_encoding="utf8",
        options="-c lc_messages=en_US.UTF-8"
    )
    cur = conn.cursor()
    cur.execute("SELECT version()")
    print("CONNEXION OK:", cur.fetchone()[0][:50])
    conn.close()
except Exception as e:
    print("CONNEXION ERROR:", type(e).__name__, repr(str(e)))

print()
print("=== POSTGRESQL CONFIG ===")
try:
    conn = psycopg2.connect(
        "postgresql://ydays_user:ydays_password@localhost:5432/ydays_db",
        client_encoding="utf8",
        options="-c lc_messages=en_US.UTF-8"
    )
    cur = conn.cursor()
    for param in ["lc_messages", "lc_collate", "lc_ctype", "server_encoding", "client_encoding"]:
        cur.execute("SHOW " + param)
        print(param + ":", cur.fetchone()[0])
    conn.close()
except Exception as e:
    print("CONFIG READ ERROR:", repr(e))
