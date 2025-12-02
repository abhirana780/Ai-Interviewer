import sqlite3
import time
import os


def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        created_at REAL,
        transcript TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        created_at REAL,
        media_path TEXT,
        answer_text TEXT,
        score INTEGER,
        feedback TEXT
    )""")
    conn.commit()
    conn.close()


def save_transcript(db_path, session_id, transcript):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO sessions (id, created_at, transcript) VALUES (?, ?, ?)",
              (session_id, time.time(), transcript))
    conn.commit()
    conn.close()


def save_answer(db_path, session_id, answer_text, media_path, score, feedback):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO answers (session_id, created_at, media_path, answer_text, score, feedback) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, time.time(), media_path or "", answer_text or "", int(score) if score is not None else None, feedback or "")
    )
    conn.commit()
    conn.close()


def get_transcript(db_path, session_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT transcript FROM sessions WHERE id=?", (session_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
