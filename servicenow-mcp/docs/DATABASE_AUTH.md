# Database-Backed Authentication System

## Overview

This document describes the new database-backed authentication system for the ServiceNow MCP Web UI, integrated with the AG-UI Protocol.

## Database Choice: SQLite

**Rationale:**
- Zero configuration required
- File-based - easy backup and deployment
- ACID compliant for data integrity
- Suitable for single-instance deployments
- Can be easily migrated to PostgreSQL for multi-instance/HA deployments

**Database Location:** `web_ui/auth.db`

## Database Schema

```sql
-- Users table: Core authentication data
CREATE TABLE users (
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
CREATE TABLE sessions (
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
CREATE TABLE audit_log (
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
```

## New Files Created

| File | Purpose |
|------|---------|
| `web_ui/database.py` | Database connection management, schema, CRUD operations |
| `web_ui/auth.py` | Password hashing (bcrypt), authentication, session management |
| `web_ui/agui_auth.py` | AG-UI Protocol event types and handlers |
| `scripts/migrate_to_db_auth.py` | Migration script and user management CLI |

## Password Hashing

- **Primary:** bcrypt with configurable work factor (default: 12 rounds)
- **Fallback:** PBKDF2-SHA256 with 100,000 iterations (if bcrypt unavailable)
- **Auto-upgrade:** Passwords are automatically rehashed to bcrypt on login

## Security Features

1. **Account Lockout:** After 5 failed attempts, account is locked for 30 minutes
2. **Audit Logging:** All authentication events are logged
3. **Session Management:** Token-based sessions with expiration
4. **Password Security:** bcrypt hashing with per-user salts
5. **IP Tracking:** Client IPs are recorded for security monitoring

## AG-UI Protocol Integration

### Event Types

```python
class AuthEventType(str, Enum):
    AUTH_LOGIN_START = "AUTH_LOGIN_START"
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    AUTH_SESSION_CREATED = "AUTH_SESSION_CREATED"
    AUTH_SESSION_VALIDATED = "AUTH_SESSION_VALIDATED"
    AUTH_SESSION_EXPIRED = "AUTH_SESSION_EXPIRED"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_STATE_SNAPSHOT = "AUTH_STATE_SNAPSHOT"
    AUTH_STATE_DELTA = "AUTH_STATE_DELTA"
```

### New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agui/auth/state` | GET | Get authentication state snapshot |
| `/api/agui/auth/events` | GET | SSE endpoint for auth events |

## Migration Steps

### Step 1: Install Dependencies

```bash
pip install bcrypt>=4.0.0
```

### Step 2: Migrate Users (Automatic)

The system automatically migrates users from `APP_USERS` environment variable on first startup:

```bash
export APP_USERS=admin:password123,demo:demopass
python web_ui/app.py
```

### Step 3: Manual Migration (Alternative)

```bash
# Migrate from environment variables
APP_USERS=admin:password,demo:pass python scripts/migrate_to_db_auth.py

# Create a single user
python scripts/migrate_to_db_auth.py --create-user username:password:role

# Add an admin
python scripts/migrate_to_db_auth.py --add-admin newadmin:password

# List users
python scripts/migrate_to_db_auth.py --list

# View audit log
python scripts/migrate_to_db_auth.py --audit-log
```

### Step 4: Remove Environment Variables (Optional)

Once users are migrated to the database, you can remove the `APP_USERS` environment variable.

## Configuration Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BCRYPT_ROUNDS` | 12 | Bcrypt work factor (10-14 recommended) |
| `MAX_FAILED_ATTEMPTS` | 5 | Failed logins before lockout |
| `LOCKOUT_DURATION_MINUTES` | 30 | Account lockout duration |
| `SESSION_DURATION_HOURS` | 24 | Default session length |
| `REMEMBER_ME_DURATION_HOURS` | 168 | "Remember me" session length (7 days) |
| `INITIAL_ADMIN_PASSWORD` | - | Password for auto-created admin user |

## Backward Compatibility

- **Existing UI:** No changes required - the UI works exactly as before
- **Existing API:** All API endpoints maintain the same interface
- **Environment Variables:** Still supported for initial migration
- **Session Handling:** Flask session management unchanged

## User Management Commands

```bash
# List all users
python scripts/migrate_to_db_auth.py --list

# Create a user
python scripts/migrate_to_db_auth.py --create-user john:password123:user

# Create an admin
python scripts/migrate_to_db_auth.py --add-admin admin2:securepass

# Reset password
python scripts/migrate_to_db_auth.py --reset-password john:newpassword

# View audit log
python scripts/migrate_to_db_auth.py --audit-log

# View audit log for specific user
python scripts/migrate_to_db_auth.py --audit-user john
```

## Example: AG-UI State Snapshot

```json
{
    "type": "AUTH_STATE_SNAPSHOT",
    "timestamp": "2025-12-08T13:38:54.123456Z",
    "authenticated": true,
    "user": {
        "user_id": 1,
        "username": "admin",
        "role": "admin",
        "display_name": "Admin"
    },
    "permissions": [
        "view_incidents",
        "view_history",
        "process_incidents",
        "start_monitoring",
        "stop_monitoring",
        "clear_history",
        "manage_users",
        "view_audit_log"
    ]
}
```

## Troubleshooting

### No users in database
```bash
# Check if APP_USERS is set
echo $APP_USERS

# Run migration manually
APP_USERS=admin:password python scripts/migrate_to_db_auth.py
```

### Account locked
```bash
# Check user status
python scripts/migrate_to_db_auth.py --list

# Reset password (also unlocks account)
python scripts/migrate_to_db_auth.py --reset-password username:newpassword
```

### bcrypt not available
```bash
pip install bcrypt>=4.0.0
```

## Production Recommendations

1. **Database Backups:** Regularly backup `web_ui/auth.db`
2. **File Permissions:** Restrict database file permissions
3. **bcrypt Rounds:** Increase to 13-14 for production
4. **Session Duration:** Reduce for sensitive environments
5. **Audit Log Retention:** Implement log rotation/archival
