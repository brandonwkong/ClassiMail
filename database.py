import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "seen_emails.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS seen_emails (
        id TEXT PRIMARY KEY,
        sender_name TEXT,
        subject TEXT,
        category TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

def is_seen(msg_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM seen_emails WHERE id = ?", (msg_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def mark_seen(msg_id, sender_name, subject, category):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
    "INSERT OR REPLACE INTO seen_emails (id, sender_name, subject, category) VALUES (?, ?, ?, ?)",
    (msg_id, sender_name, subject, category)
)
    conn.commit()
    conn.close()

def get_saved_info(msg_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT subject, sender_name, category FROM seen_emails WHERE id = ?", (msg_id,))
    row = c.fetchone()
    conn.close()
    if row:
        subject, sender_name, category = row
        return subject, sender_name, category
    else:
        return "(Unknown)", "(Unknown Sender)", "Other"

