import sqlite3
import time
import os


def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Interview tables
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
    # Funnel tables
    c.execute("""CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funnel_id TEXT,
        created_at REAL,
        filename TEXT,
        text TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ats_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funnel_id TEXT,
        created_at REAL,
        score INTEGER,
        details TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funnel_id TEXT,
        created_at REAL,
        problem_key TEXT,
        code_path TEXT,
        score INTEGER,
        feedback TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funnel_id TEXT,
        created_at REAL,
        slot TEXT,
        note TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funnel_id TEXT,
        created_at REAL,
        title TEXT,
        body TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funnel_id TEXT,
        created_at REAL,
        course_name TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS labs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funnel_id TEXT,
        created_at REAL,
        lab_key TEXT,
        code_path TEXT,
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

# Funnel helpers

def save_resume(db_path, funnel_id, filename, text):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO resumes (funnel_id, created_at, filename, text) VALUES (?, ?, ?, ?)",
        (funnel_id, time.time(), filename or "", text or "")
    )
    conn.commit()
    conn.close()


def save_ats_score(db_path, funnel_id, score, details):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO ats_scores (funnel_id, created_at, score, details) VALUES (?, ?, ?, ?)",
        (funnel_id, time.time(), int(score) if score is not None else None, details or "")
    )
    conn.commit()
    conn.close()


def save_assessment(db_path, funnel_id, problem_key, code_path, score, feedback):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO assessments (funnel_id, created_at, problem_key, code_path, score, feedback) VALUES (?, ?, ?, ?, ?, ?)",
        (funnel_id, time.time(), problem_key or "", code_path or "", int(score) if score is not None else None, feedback or "")
    )
    conn.commit()
    conn.close()


def save_schedule(db_path, funnel_id, slot, note):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO schedules (funnel_id, created_at, slot, note) VALUES (?, ?, ?, ?)",
        (funnel_id, time.time(), slot or "", note or "")
    )
    conn.commit()
    conn.close()


def save_offer(db_path, funnel_id, title, body):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO offers (funnel_id, created_at, title, body) VALUES (?, ?, ?, ?)",
        (funnel_id, time.time(), title or "", body or "")
    )
    conn.commit()
    conn.close()


def save_course_enroll(db_path, funnel_id, course_name):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO courses (funnel_id, created_at, course_name) VALUES (?, ?, ?)",
        (funnel_id, time.time(), course_name or "")
    )
    conn.commit()
    conn.close()


def save_lab_submission(db_path, funnel_id, lab_key, code_path, score, feedback):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO labs (funnel_id, created_at, lab_key, code_path, score, feedback) VALUES (?, ?, ?, ?, ?, ?)",
        (funnel_id, time.time(), lab_key or "", code_path or "", int(score) if score is not None else None, feedback or "")
    )
    conn.commit()
    conn.close()


def get_latest_resume_text(db_path, funnel_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT text FROM resumes WHERE funnel_id=? ORDER BY created_at DESC LIMIT 1", (funnel_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else ""
