import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "seen_emails.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Original emails table (with new columns)
    c.execute("""
    CREATE TABLE IF NOT EXISTS seen_emails (
        id TEXT PRIMARY KEY,
        sender_name TEXT,
        subject TEXT,
        body TEXT,
        category TEXT,
        rank_score REAL,
        features_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Interactions table for CTR training
    c.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id TEXT NOT NULL,
        action TEXT NOT NULL,
        position_shown INTEGER,
        time_spent_ms INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (email_id) REFERENCES seen_emails(id)
    )
    """)

    # Add new columns to existing table if they don't exist
    try:
        c.execute("ALTER TABLE seen_emails ADD COLUMN rank_score REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE seen_emails ADD COLUMN features_json TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE seen_emails ADD COLUMN created_at TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE seen_emails ADD COLUMN body TEXT")
    except sqlite3.OperationalError:
        pass

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
    c.execute("SELECT subject, sender_name, category, rank_score, features_json, body FROM seen_emails WHERE id = ?", (msg_id,))
    row = c.fetchone()
    conn.close()
    if row:
        subject, sender_name, category, rank_score, features_json, body = row
        features = json.loads(features_json) if features_json else {}
        return subject, sender_name, category, rank_score, features, body or ""
    else:
        return "(Unknown)", "(Unknown Sender)", "Other", 0.0, {}, ""


def update_email_features(msg_id, rank_score, features):
    """Update rank score and features for an email."""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE seen_emails SET rank_score = ?, features_json = ? WHERE id = ?",
        (rank_score, json.dumps(features), msg_id)
    )
    conn.commit()
    conn.close()


def save_email_full(msg_id, sender_name, subject, category, rank_score, features, body=""):
    """Save email with all fields including features and body."""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT OR REPLACE INTO seen_emails
           (id, sender_name, subject, body, category, rank_score, features_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (msg_id, sender_name, subject, body, category, rank_score, json.dumps(features), datetime.now())
    )
    conn.commit()
    conn.close()


# ----- Interaction logging for CTR training -----

def log_interaction(email_id, action, position_shown=None, time_spent_ms=None):
    """
    Log a user interaction with an email.

    Args:
        email_id: The email that was interacted with
        action: 'click', 'open', 'skip', 'ignore'
        position_shown: Where in the list the email was shown (1-indexed)
        time_spent_ms: How long user spent viewing (if opened)
    """
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT INTO interactions (email_id, action, position_shown, time_spent_ms, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        (email_id, action, position_shown, time_spent_ms, datetime.now())
    )
    conn.commit()
    conn.close()


def get_interactions_for_training():
    """
    Get all interactions for training CTR model.

    Returns list of dicts with email features and interaction labels.
    """
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT
            e.id,
            e.features_json,
            i.action,
            i.position_shown,
            i.time_spent_ms
        FROM interactions i
        JOIN seen_emails e ON i.email_id = e.id
        WHERE e.features_json IS NOT NULL
        ORDER BY i.timestamp
    """)
    rows = c.fetchall()
    conn.close()

    data = []
    for row in rows:
        email_id, features_json, action, position, time_spent = row
        features = json.loads(features_json) if features_json else {}
        data.append({
            'email_id': email_id,
            'features': features,
            'action': action,
            'position_shown': position,
            'time_spent_ms': time_spent,
            'clicked': action in ('click', 'open'),
        })

    return data


def get_interaction_stats():
    """Get summary stats for interactions (useful for debugging)."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT action, COUNT(*) as count
        FROM interactions
        GROUP BY action
    """)
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


def get_email_ctr(email_id):
    """Get click-through rate for an email based on past interactions."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM interactions WHERE email_id = ? AND action IN ('click', 'open')", (email_id,))
    clicks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM interactions WHERE email_id = ?", (email_id,))
    total = c.fetchone()[0]
    conn.close()
    return clicks / total if total > 0 else 0.0


def get_detailed_stats():
    """Get detailed interaction stats including time spent."""
    conn = get_conn()
    c = conn.cursor()

    stats = {}

    # Basic counts by action
    c.execute("""
        SELECT action, COUNT(*) as count
        FROM interactions
        GROUP BY action
    """)
    stats['counts'] = {row[0]: row[1] for row in c.fetchall()}

    # Average time spent (only for 'open' actions that have time_spent_ms)
    c.execute("""
        SELECT AVG(time_spent_ms), MIN(time_spent_ms), MAX(time_spent_ms), COUNT(*)
        FROM interactions
        WHERE time_spent_ms IS NOT NULL AND time_spent_ms > 0
    """)
    row = c.fetchone()
    if row and row[0]:
        stats['time_spent'] = {
            'avg_ms': round(row[0], 0),
            'min_ms': row[1],
            'max_ms': row[2],
            'count': row[3],
            'avg_seconds': round(row[0] / 1000, 1),
        }
    else:
        stats['time_spent'] = {'avg_ms': 0, 'min_ms': 0, 'max_ms': 0, 'count': 0, 'avg_seconds': 0}

    # Top emails by time spent
    c.execute("""
        SELECT e.subject, e.category, i.time_spent_ms, i.position_shown
        FROM interactions i
        JOIN seen_emails e ON i.email_id = e.id
        WHERE i.time_spent_ms IS NOT NULL AND i.time_spent_ms > 0
        ORDER BY i.time_spent_ms DESC
        LIMIT 10
    """)
    stats['top_by_time'] = [
        {
            'subject': row[0][:50] + '...' if len(row[0]) > 50 else row[0],
            'category': row[1],
            'time_spent_ms': row[2],
            'time_spent_sec': round(row[2] / 1000, 1),
            'position': row[3]
        }
        for row in c.fetchall()
    ]

    # Recent interactions
    c.execute("""
        SELECT e.subject, i.action, i.time_spent_ms, i.position_shown, i.timestamp
        FROM interactions i
        JOIN seen_emails e ON i.email_id = e.id
        ORDER BY i.timestamp DESC
        LIMIT 15
    """)
    stats['recent'] = [
        {
            'subject': row[0][:40] + '...' if len(row[0]) > 40 else row[0],
            'action': row[1],
            'time_spent_ms': row[2],
            'position': row[3],
            'timestamp': row[4]
        }
        for row in c.fetchall()
    ]

    # Click-through rate by position (important for CTR modeling)
    c.execute("""
        SELECT
            position_shown,
            COUNT(*) as total,
            SUM(CASE WHEN action IN ('click', 'open') THEN 1 ELSE 0 END) as clicks
        FROM interactions
        WHERE position_shown IS NOT NULL
        GROUP BY position_shown
        ORDER BY position_shown
    """)
    stats['ctr_by_position'] = [
        {
            'position': row[0],
            'total': row[1],
            'clicks': row[2],
            'ctr': round(row[2] / row[1] * 100, 1) if row[1] > 0 else 0
        }
        for row in c.fetchall()
    ]

    # CTR by category
    c.execute("""
        SELECT
            e.category,
            COUNT(*) as total,
            SUM(CASE WHEN i.action IN ('click', 'open') THEN 1 ELSE 0 END) as clicks
        FROM interactions i
        JOIN seen_emails e ON i.email_id = e.id
        GROUP BY e.category
        ORDER BY clicks DESC
    """)
    stats['ctr_by_category'] = [
        {
            'category': row[0],
            'total': row[1],
            'clicks': row[2],
            'ctr': round(row[2] / row[1] * 100, 1) if row[1] > 0 else 0
        }
        for row in c.fetchall()
    ]

    conn.close()
    return stats

