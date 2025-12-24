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
    # Add candidate details columns
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN candidate_name TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN mobile_number TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN qualification TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN college_name TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN track TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN final_score REAL")
    except sqlite3.OperationalError:
        pass
    c.execute("""CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        created_at REAL,
        media_path TEXT,
        answer_text TEXT,
        score INTEGER,
        feedback TEXT
    )""")
    # No additional tables needed for basic interviewer functionality
    conn.commit()
    conn.close()


def save_transcript(db_path, session_id, transcript, candidate_name=None, mobile_number=None, email=None, qualification=None, college_name=None, track=None, final_score=None):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check if session exists
    c.execute("SELECT id FROM sessions WHERE id=?", (session_id,))
    exists = c.fetchone()
    
    if exists:
        # Update existing session
        c.execute(
            """UPDATE sessions SET transcript=?, candidate_name=COALESCE(?, candidate_name),
               mobile_number=COALESCE(?, mobile_number), email=COALESCE(?, email),
               qualification=COALESCE(?, qualification), college_name=COALESCE(?, college_name),
               track=COALESCE(?, track), final_score=COALESCE(?, final_score)
               WHERE id=?""",
            (transcript, candidate_name, mobile_number, email, qualification, college_name, track, final_score, session_id)
        )
    else:
        # Insert new session
        c.execute(
            """INSERT INTO sessions (id, created_at, candidate_name, mobile_number, email, 
               qualification, college_name, track, transcript, final_score) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, time.time(), candidate_name or "", mobile_number or "", email or "",
             qualification or "", college_name or "", track or "", transcript, final_score)
        )
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

# No funnel helpers needed for basic interviewer functionality


def list_sessions(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""SELECT id, created_at, candidate_name, mobile_number, email, 
                 qualification, college_name, track, final_score 
                 FROM sessions ORDER BY created_at DESC""")
    rows = c.fetchall()
    conn.close()
    return [{
        "id": r[0], 
        "created_at": r[1], 
        "candidate_name": r[2],
        "mobile_number": r[3],
        "email": r[4],
        "qualification": r[5],
        "college_name": r[6],
        "track": r[7],
        "final_score": r[8]
    } for r in rows]


def get_session(db_path, session_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""SELECT id, created_at, candidate_name, transcript, mobile_number, email,
                 qualification, college_name, track, final_score
                 FROM sessions WHERE id=?""", (session_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0], 
            "created_at": row[1], 
            "candidate_name": row[2], 
            "transcript": row[3],
            "mobile_number": row[4],
            "email": row[5],
            "qualification": row[6],
            "college_name": row[7],
            "track": row[8],
            "final_score": row[9]
        }
    return None


def get_answers_for_session(db_path, session_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT created_at, media_path, answer_text, score, feedback FROM answers WHERE session_id=? ORDER BY created_at ASC", (session_id,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "created_at": r[0],
            "media_path": r[1],
            "answer_text": r[2],
            "score": r[3],
            "feedback": r[4],
        }
        for r in rows
    ]


def update_answer_text_by_media(db_path, session_id, media_path, text):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "UPDATE answers SET answer_text=?, score=NULL, feedback='' WHERE session_id=? AND media_path=?",
        (text or "", session_id, media_path or "")
    )
    conn.commit()
    conn.close()

def update_answer_score(db_path, session_id, answer_index, score, feedback):
    """Update the score and feedback for a specific answer by index"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Get all answers for this session ordered by creation time
    c.execute("SELECT id FROM answers WHERE session_id=? ORDER BY created_at ASC", (session_id,))
    rows = c.fetchall()
    
    # Update the answer at the specified index (0-based)
    if answer_index < len(rows):
        answer_id = rows[answer_index][0]
        c.execute(
            "UPDATE answers SET score=?, feedback=? WHERE id=?",
            (int(score) if score is not None else None, feedback or "", answer_id)
        )
        conn.commit()
    conn.close()

def update_final_score(db_path, session_id, final_score):
    """Update the final overall score for a session"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "UPDATE sessions SET final_score=? WHERE id=?",
        (float(final_score) if final_score is not None else None, session_id)
    )
    conn.commit()
    conn.close()
