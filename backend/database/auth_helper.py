import os
import sqlite3
import bcrypt
from datetime import datetime

def init_auth_db(db_path):
    """Initialize authentication database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(db_path, name, email, password):
    """Create a new user"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute(
            'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
            (name, email, password_hash)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        user = get_user_by_id(db_path, user_id)
        return user
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(db_path, email):
    """Get user by email"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'password_hash': row[3],
            'created_at': row[4],
            'updated_at': row[5]
        }
    return None

def get_user_by_id(db_path, user_id):
    """Get user by ID"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'created_at': row[4],
            'updated_at': row[5]
        }
    return None

def verify_password(password, password_hash):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

def link_session_to_user(db_path, user_id, session_id):
    """Link an interview session to a user"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO user_sessions (user_id, session_id) VALUES (?, ?)',
        (user_id, session_id)
    )
    conn.commit()
    conn.close()

def get_user_sessions(db_path, user_id):
    """Get all sessions for a user"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT session_id, created_at FROM user_sessions WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [{'session_id': row[0], 'created_at': row[1]} for row in rows]
