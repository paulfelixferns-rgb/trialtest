import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # ✅ SAME PATH ALWAYS
DB_NAME = os.path.join(BASE_DIR, "dc.db")

#def get_connection():
  #  return sqlite3.connect(DB_NAME)

def get_connection():
    db_path = os.path.abspath("dc.db")
    print("DB PATH USED:", db_path)
    return sqlite3.connect(db_path)

def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dc_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dc_date TEXT,
            distributor TEXT,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
