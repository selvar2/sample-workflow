"""
Database Module for ServiceNow MCP Web UI

Provides SQLite-based persistent storage for user authentication.
Designed for simplicity while maintaining production-ready security.

Database Choice Rationale:
- SQLite: Zero-configuration, file-based, perfect for single-instance deployments
- For multi-instance/HA deployments, PostgreSQL adapter can be added

Schema Design:
- users: Core user credentials with bcrypt password hashing
- sessions: Token-based session management with expiration
- audit_log: Login attempts for security monitoring
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager
import threading
import json

# Thread-local storage for connections
_local = threading.local()

# Database path
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, 'auth.db')


# ============================================================================
# Database Schema
# ============================================================================

SCHEMA = """
-- Users table: Core authentication data
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user', 'readonly')),
    display_name TEXT,
    email TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

-- Sessions table: Token-based session management
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    is_valid INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Audit log: Security monitoring
CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    username TEXT,
    user_id INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,
    success INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_username ON audit_log(username);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);

-- Trigger to update updated_at on user changes
CREATE TRIGGER IF NOT EXISTS update_user_timestamp 
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
END;
"""


# ============================================================================
# Connection Management
# ============================================================================

def get_connection() -> sqlite3.Connection:
    """
    Get a thread-local database connection.
    Uses connection pooling pattern for thread safety.
    """
    if not hasattr(_local, 'connection') or _local.connection is None:
        _local.connection = sqlite3.connect(
            DB_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False
        )
        _local.connection.row_factory = sqlite3.Row
        # Enable foreign keys
        _local.connection.execute("PRAGMA foreign_keys = ON")
    return _local.connection


@contextmanager
def get_db():
    """Context manager for database operations with automatic commit/rollback."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_database():
    """Initialize the database schema."""
    with get_db() as conn:
        conn.executescript(SCHEMA)
    print(f"Database initialized at: {DB_PATH}")


def close_connection():
    """Close the thread-local connection."""
    if hasattr(_local, 'connection') and _local.connection:
        _local.connection.close()
        _local.connection = None


# ============================================================================
# User Operations (CRUD)
# ============================================================================

def create_user(
    username: str,
    password_hash: str,
    salt: str,
    role: str = 'user',
    display_name: str = None,
    email: str = None
) -> Optional[int]:
    """
    Create a new user in the database.
    
    Args:
        username: Unique username (case-insensitive)
        password_hash: Pre-hashed password (use auth.hash_password)
        salt: Salt used for password hashing
        role: User role (admin, user, readonly)
        display_name: Optional display name
        email: Optional email address
    
    Returns:
        user_id if created, None if username exists
    """
    try:
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO users (username, password_hash, salt, role, display_name, email)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username.lower(), password_hash, salt, role, display_name or username.title(), email))
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # Username already exists


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT user_id, username, password_hash, salt, role, display_name, 
                   email, is_active, created_at, updated_at, last_login,
                   failed_attempts, locked_until
            FROM users 
            WHERE username = ?
        """, (username.lower(),))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT user_id, username, password_hash, salt, role, display_name,
                   email, is_active, created_at, updated_at, last_login,
                   failed_attempts, locked_until
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def update_user(user_id: int, **kwargs) -> bool:
    """
    Update user fields.
    
    Allowed fields: role, display_name, email, is_active, password_hash, salt
    """
    allowed_fields = {'role', 'display_name', 'email', 'is_active', 'password_hash', 'salt'}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return False
    
    set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [user_id]
    
    with get_db() as conn:
        cursor = conn.execute(f"""
            UPDATE users SET {set_clause} WHERE user_id = ?
        """, values)
        return cursor.rowcount > 0


def delete_user(user_id: int) -> bool:
    """Delete a user (cascades to sessions)."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0


def list_users() -> List[Dict[str, Any]]:
    """List all users (without password hashes)."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT user_id, username, role, display_name, email, is_active,
                   created_at, updated_at, last_login
            FROM users
            ORDER BY username
        """)
        return [dict(row) for row in cursor.fetchall()]


def update_last_login(user_id: int):
    """Update the last login timestamp."""
    with get_db() as conn:
        conn.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP, failed_attempts = 0
            WHERE user_id = ?
        """, (user_id,))


def increment_failed_attempts(username: str) -> int:
    """Increment failed login attempts and return new count."""
    with get_db() as conn:
        conn.execute("""
            UPDATE users SET failed_attempts = failed_attempts + 1
            WHERE username = ?
        """, (username.lower(),))
        cursor = conn.execute("""
            SELECT failed_attempts FROM users WHERE username = ?
        """, (username.lower(),))
        row = cursor.fetchone()
        return row['failed_attempts'] if row else 0


def lock_user(username: str, duration_minutes: int = 30):
    """Lock a user account for a specified duration."""
    locked_until = datetime.now() + timedelta(minutes=duration_minutes)
    with get_db() as conn:
        conn.execute("""
            UPDATE users SET locked_until = ? WHERE username = ?
        """, (locked_until, username.lower()))


def is_user_locked(username: str) -> bool:
    """Check if a user account is locked."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT locked_until FROM users WHERE username = ?
        """, (username.lower(),))
        row = cursor.fetchone()
        if row and row['locked_until']:
            return datetime.fromisoformat(row['locked_until']) > datetime.now()
    return False


# ============================================================================
# Session Operations
# ============================================================================

def create_session(
    user_id: int,
    token: str,
    expires_hours: int = 24,
    ip_address: str = None,
    user_agent: str = None
) -> int:
    """Create a new session."""
    expires_at = datetime.now() + timedelta(hours=expires_hours)
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO sessions (user_id, token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, token, expires_at, ip_address, user_agent))
        return cursor.lastrowid


def get_session(token: str) -> Optional[Dict[str, Any]]:
    """Get session by token if valid and not expired."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT s.*, u.username, u.role, u.display_name
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.token = ? AND s.is_valid = 1 AND s.expires_at > CURRENT_TIMESTAMP
        """, (token,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def invalidate_session(token: str) -> bool:
    """Invalidate a session (logout)."""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE sessions SET is_valid = 0 WHERE token = ?
        """, (token,))
        return cursor.rowcount > 0


def invalidate_all_user_sessions(user_id: int) -> int:
    """Invalidate all sessions for a user."""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE sessions SET is_valid = 0 WHERE user_id = ?
        """, (user_id,))
        return cursor.rowcount


def cleanup_expired_sessions():
    """Remove expired sessions from the database."""
    with get_db() as conn:
        cursor = conn.execute("""
            DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP
        """)
        return cursor.rowcount


# ============================================================================
# Audit Log Operations
# ============================================================================

def log_audit_event(
    event_type: str,
    username: str = None,
    user_id: int = None,
    ip_address: str = None,
    user_agent: str = None,
    details: Dict = None,
    success: bool = True
):
    """Log an audit event."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO audit_log (event_type, username, user_id, ip_address, 
                                   user_agent, details, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event_type,
            username,
            user_id,
            ip_address,
            user_agent,
            json.dumps(details) if details else None,
            1 if success else 0
        ))


def get_audit_log(
    username: str = None,
    event_type: str = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get audit log entries with optional filters."""
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []
    
    if username:
        query += " AND username = ?"
        params.append(username.lower())
    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    with get_db() as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# Migration Helpers
# ============================================================================

def migrate_env_users_to_db(env_users: Dict[str, Dict]) -> Tuple[int, int]:
    """
    Migrate users from environment variable format to database.
    
    Args:
        env_users: Dict from get_users_from_env() in the old system
    
    Returns:
        Tuple of (created_count, skipped_count)
    """
    created = 0
    skipped = 0
    
    for username, user_data in env_users.items():
        result = create_user(
            username=username,
            password_hash=user_data['password_hash'],
            salt=user_data['salt'],
            role=user_data.get('role', 'user'),
            display_name=user_data.get('display_name', username.title())
        )
        if result:
            created += 1
        else:
            skipped += 1
    
    return created, skipped


def user_exists(username: str) -> bool:
    """Check if a user exists."""
    return get_user_by_username(username) is not None


def get_user_count() -> int:
    """Get total user count."""
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM users")
        return cursor.fetchone()['count']


# Initialize database on module import
if not os.path.exists(DB_PATH):
    init_database()
