"""
Authentication Module for ServiceNow MCP Web UI

Provides secure password hashing, session management, and authentication helpers.
Uses bcrypt for password hashing with fallback to PBKDF2 if bcrypt is unavailable.

Security Features:
- Bcrypt password hashing (argon2 compatible interface)
- Configurable work factor for bcrypt
- Rate limiting for login attempts
- Account lockout after failed attempts
- Secure session token generation
- CSRF protection helpers

AG-UI Protocol Integration:
- Authentication events follow AG-UI event patterns
- Session state can be synchronized via StateSnapshotEvent
"""

import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from functools import wraps

# Try to import bcrypt, fallback to PBKDF2 if not available
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    print("Warning: bcrypt not available, using PBKDF2 fallback")

# Import database module
from . import database as db


# ============================================================================
# Configuration
# ============================================================================

# Bcrypt work factor (higher = more secure but slower)
BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', '12'))

# PBKDF2 iterations (fallback)
PBKDF2_ITERATIONS = 100000

# Account lockout settings
MAX_FAILED_ATTEMPTS = int(os.getenv('MAX_FAILED_ATTEMPTS', '5'))
LOCKOUT_DURATION_MINUTES = int(os.getenv('LOCKOUT_DURATION_MINUTES', '30'))

# Session settings
SESSION_DURATION_HOURS = int(os.getenv('SESSION_DURATION_HOURS', '24'))
REMEMBER_ME_DURATION_HOURS = int(os.getenv('REMEMBER_ME_DURATION_HOURS', '168'))  # 7 days


# ============================================================================
# Password Hashing
# ============================================================================

def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """
    Hash a password using bcrypt (preferred) or PBKDF2 (fallback).
    
    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)
    
    Returns:
        Tuple of (password_hash, salt)
    
    Note: For bcrypt, the salt is embedded in the hash, but we store it
    separately for compatibility with the existing schema.
    """
    if BCRYPT_AVAILABLE:
        # Bcrypt generates its own salt, but we'll also store a separate salt
        # for the schema compatibility
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Generate bcrypt hash
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=BCRYPT_ROUNDS))
        return hashed.decode('utf-8'), salt
    else:
        # PBKDF2 fallback
        if salt is None:
            salt = secrets.token_hex(16)
        
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            PBKDF2_ITERATIONS
        )
        return hashed.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Stored password hash
        salt: Stored salt
    
    Returns:
        True if password matches, False otherwise
    """
    if BCRYPT_AVAILABLE and password_hash.startswith('$2'):
        # Bcrypt hash detected
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
    else:
        # PBKDF2 verification
        new_hash, _ = hash_password_pbkdf2(password, salt)
        return hmac.compare_digest(new_hash, password_hash)


def hash_password_pbkdf2(password: str, salt: str) -> Tuple[str, str]:
    """PBKDF2 hashing for backward compatibility."""
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        PBKDF2_ITERATIONS
    )
    return hashed.hex(), salt


def needs_rehash(password_hash: str) -> bool:
    """
    Check if a password hash needs to be upgraded.
    
    Returns True if:
    - Using PBKDF2 but bcrypt is now available
    - Bcrypt rounds are lower than current setting
    """
    if not BCRYPT_AVAILABLE:
        return False
    
    # If not a bcrypt hash, needs upgrade
    if not password_hash.startswith('$2'):
        return True
    
    # Check bcrypt rounds
    try:
        # Extract rounds from bcrypt hash
        parts = password_hash.split('$')
        if len(parts) >= 3:
            current_rounds = int(parts[2])
            return current_rounds < BCRYPT_ROUNDS
    except Exception:
        pass
    
    return False


# ============================================================================
# Session Token Generation
# ============================================================================

def generate_session_token() -> str:
    """Generate a cryptographically secure session token."""
    return secrets.token_urlsafe(32)


def generate_csrf_token() -> str:
    """Generate a CSRF protection token."""
    return secrets.token_urlsafe(24)


# ============================================================================
# Authentication Functions
# ============================================================================

def authenticate_user(
    username: str,
    password: str,
    ip_address: str = None,
    user_agent: str = None
) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user and return user data if successful.
    
    This function:
    1. Checks if user exists
    2. Checks if account is locked
    3. Verifies password
    4. Updates login tracking
    5. Logs audit event
    
    Args:
        username: Username to authenticate
        password: Password to verify
        ip_address: Client IP for audit logging
        user_agent: Client user agent for audit logging
    
    Returns:
        User data dict if authenticated, None otherwise
    """
    # Get user from database
    user = db.get_user_by_username(username)
    
    if not user:
        # Log failed attempt (user not found)
        db.log_audit_event(
            event_type='LOGIN_FAILED',
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            details={'reason': 'user_not_found'},
            success=False
        )
        return None
    
    # Check if account is active
    if not user.get('is_active', True):
        db.log_audit_event(
            event_type='LOGIN_FAILED',
            username=username,
            user_id=user['user_id'],
            ip_address=ip_address,
            user_agent=user_agent,
            details={'reason': 'account_disabled'},
            success=False
        )
        return None
    
    # Check if account is locked
    if db.is_user_locked(username):
        db.log_audit_event(
            event_type='LOGIN_FAILED',
            username=username,
            user_id=user['user_id'],
            ip_address=ip_address,
            user_agent=user_agent,
            details={'reason': 'account_locked'},
            success=False
        )
        return None
    
    # Verify password
    if not verify_password(password, user['password_hash'], user['salt']):
        # Increment failed attempts
        failed_count = db.increment_failed_attempts(username)
        
        # Lock account if too many failures
        if failed_count >= MAX_FAILED_ATTEMPTS:
            db.lock_user(username, LOCKOUT_DURATION_MINUTES)
            db.log_audit_event(
                event_type='ACCOUNT_LOCKED',
                username=username,
                user_id=user['user_id'],
                ip_address=ip_address,
                user_agent=user_agent,
                details={'failed_attempts': failed_count},
                success=False
            )
        else:
            db.log_audit_event(
                event_type='LOGIN_FAILED',
                username=username,
                user_id=user['user_id'],
                ip_address=ip_address,
                user_agent=user_agent,
                details={'reason': 'invalid_password', 'failed_attempts': failed_count},
                success=False
            )
        return None
    
    # Successful authentication
    db.update_last_login(user['user_id'])
    
    # Check if password needs rehash
    if needs_rehash(user['password_hash']):
        new_hash, new_salt = hash_password(password)
        db.update_user(user['user_id'], password_hash=new_hash, salt=new_salt)
    
    # Log successful login
    db.log_audit_event(
        event_type='LOGIN_SUCCESS',
        username=username,
        user_id=user['user_id'],
        ip_address=ip_address,
        user_agent=user_agent,
        success=True
    )
    
    return {
        'user_id': user['user_id'],
        'username': user['username'],
        'role': user.get('role', 'user'),
        'display_name': user.get('display_name', username),
        'email': user.get('email')
    }


def create_user_session(
    user_id: int,
    remember_me: bool = False,
    ip_address: str = None,
    user_agent: str = None
) -> str:
    """
    Create a new session for a user.
    
    Args:
        user_id: ID of the authenticated user
        remember_me: Whether to extend session duration
        ip_address: Client IP address
        user_agent: Client user agent
    
    Returns:
        Session token
    """
    token = generate_session_token()
    duration = REMEMBER_ME_DURATION_HOURS if remember_me else SESSION_DURATION_HOURS
    
    db.create_session(
        user_id=user_id,
        token=token,
        expires_hours=duration,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return token


def validate_session(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a session token and return user data.
    
    Args:
        token: Session token to validate
    
    Returns:
        Session data with user info if valid, None otherwise
    """
    return db.get_session(token)


def logout_user(token: str, ip_address: str = None, user_agent: str = None):
    """
    Log out a user by invalidating their session.
    
    Args:
        token: Session token to invalidate
        ip_address: Client IP for audit logging
        user_agent: Client user agent for audit logging
    """
    session = db.get_session(token)
    if session:
        db.invalidate_session(token)
        db.log_audit_event(
            event_type='LOGOUT',
            username=session.get('username'),
            user_id=session.get('user_id'),
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )


def logout_all_sessions(user_id: int, ip_address: str = None):
    """Log out all sessions for a user."""
    user = db.get_user_by_id(user_id)
    count = db.invalidate_all_user_sessions(user_id)
    
    if user:
        db.log_audit_event(
            event_type='LOGOUT_ALL',
            username=user.get('username'),
            user_id=user_id,
            ip_address=ip_address,
            details={'sessions_invalidated': count},
            success=True
        )


# ============================================================================
# User Management Functions
# ============================================================================

def register_user(
    username: str,
    password: str,
    role: str = 'user',
    display_name: str = None,
    email: str = None,
    created_by: str = None
) -> Optional[int]:
    """
    Register a new user.
    
    Args:
        username: Unique username
        password: Plain text password (will be hashed)
        role: User role (admin, user, readonly)
        display_name: Optional display name
        email: Optional email address
        created_by: Username of admin creating this user
    
    Returns:
        user_id if created, None if username exists
    """
    password_hash, salt = hash_password(password)
    user_id = db.create_user(
        username=username,
        password_hash=password_hash,
        salt=salt,
        role=role,
        display_name=display_name,
        email=email
    )
    
    if user_id:
        db.log_audit_event(
            event_type='USER_CREATED',
            username=username,
            user_id=user_id,
            details={'role': role, 'created_by': created_by},
            success=True
        )
    
    return user_id


def change_password(
    user_id: int,
    new_password: str,
    changed_by: str = None,
    ip_address: str = None
) -> bool:
    """
    Change a user's password.
    
    Args:
        user_id: ID of user to update
        new_password: New plain text password
        changed_by: Username of person changing password
        ip_address: Client IP for audit logging
    
    Returns:
        True if successful, False otherwise
    """
    password_hash, salt = hash_password(new_password)
    result = db.update_user(user_id, password_hash=password_hash, salt=salt)
    
    if result:
        user = db.get_user_by_id(user_id)
        db.log_audit_event(
            event_type='PASSWORD_CHANGED',
            username=user.get('username') if user else None,
            user_id=user_id,
            ip_address=ip_address,
            details={'changed_by': changed_by},
            success=True
        )
        # Invalidate all existing sessions
        db.invalidate_all_user_sessions(user_id)
    
    return result


def deactivate_user(user_id: int, deactivated_by: str = None) -> bool:
    """Deactivate a user account."""
    result = db.update_user(user_id, is_active=False)
    
    if result:
        user = db.get_user_by_id(user_id)
        db.invalidate_all_user_sessions(user_id)
        db.log_audit_event(
            event_type='USER_DEACTIVATED',
            username=user.get('username') if user else None,
            user_id=user_id,
            details={'deactivated_by': deactivated_by},
            success=True
        )
    
    return result


def activate_user(user_id: int, activated_by: str = None) -> bool:
    """Activate a user account."""
    result = db.update_user(user_id, is_active=True)
    
    if result:
        user = db.get_user_by_id(user_id)
        db.log_audit_event(
            event_type='USER_ACTIVATED',
            username=user.get('username') if user else None,
            user_id=user_id,
            details={'activated_by': activated_by},
            success=True
        )
    
    return result


# ============================================================================
# Flask Integration Helpers
# ============================================================================

def get_client_ip(request) -> str:
    """Get the client IP address from a Flask request."""
    # Check for proxy headers
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr


def get_user_agent(request) -> str:
    """Get the user agent from a Flask request."""
    return request.headers.get('User-Agent', '')[:500]  # Limit length


# ============================================================================
# Initialization
# ============================================================================

def ensure_admin_user():
    """
    Ensure at least one admin user exists.
    Creates a default admin if no users exist.
    
    This is called on startup to ensure the system is usable.
    """
    if db.get_user_count() == 0:
        # Check for env var with initial admin password
        admin_password = os.getenv('INITIAL_ADMIN_PASSWORD')
        
        if admin_password:
            register_user(
                username='admin',
                password=admin_password,
                role='admin',
                display_name='Administrator',
                created_by='system'
            )
            print("Created initial admin user from INITIAL_ADMIN_PASSWORD")
        else:
            print("=" * 60)
            print("WARNING: No users in database!")
            print("Set INITIAL_ADMIN_PASSWORD env var to create admin user")
            print("Or run the migration script to import from APP_USERS")
            print("=" * 60)


# Initialize on import
db.init_database()
