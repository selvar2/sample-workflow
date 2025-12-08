#!/usr/bin/env python3
"""
Migration Script: Environment Variables to Database Authentication

This script migrates user credentials from the old environment variable-based
authentication system to the new database-backed system.

Usage:
    # Migrate from APP_USERS environment variable
    python scripts/migrate_to_db_auth.py
    
    # Migrate and create additional admin
    python scripts/migrate_to_db_auth.py --add-admin admin2:password123
    
    # Force migration (overwrite existing users)
    python scripts/migrate_to_db_auth.py --force
    
    # List current database users
    python scripts/migrate_to_db_auth.py --list
    
    # Create a single user
    python scripts/migrate_to_db_auth.py --create-user username:password:role

Environment Variables:
    APP_USERS: Comma-separated list of username:password pairs
    APP_USER_<NAME>: Individual user passwords
    INITIAL_ADMIN_PASSWORD: Password for initial admin user

Security Notes:
    - Passwords are hashed with bcrypt (or PBKDF2 fallback)
    - Original environment variable passwords are not stored
    - Database file permissions should be restricted
"""

import os
import sys
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Import the new authentication modules
from web_ui import database as db
from web_ui import auth


def get_env_users():
    """Get users from environment variables (legacy format)."""
    users = {}
    
    # Get users from APP_USERS env var
    combined_users = os.getenv('APP_USERS', '')
    if combined_users:
        for user_pair in combined_users.split(','):
            if ':' in user_pair:
                username, password = user_pair.split(':', 1)
                username = username.strip().lower()
                password = password.strip()
                if username and password:
                    users[username] = {
                        'password': password,
                        'role': 'admin' if username == 'admin' else 'user',
                        'display_name': username.title()
                    }
    
    # Also support individual env vars
    for key, value in os.environ.items():
        if key.startswith('APP_USER_') and value:
            username = key[9:].lower()
            if username not in users:
                users[username] = {
                    'password': value,
                    'role': 'admin' if username == 'admin' else 'user',
                    'display_name': username.title()
                }
    
    return users


def migrate_users(force: bool = False):
    """Migrate users from environment variables to database."""
    print("=" * 60)
    print("User Migration: Environment Variables → Database")
    print("=" * 60)
    
    # Initialize database
    db.init_database()
    print(f"Database location: {db.DB_PATH}")
    
    # Get existing users
    existing_users = {u['username']: u for u in db.list_users()}
    print(f"Existing database users: {list(existing_users.keys()) or 'None'}")
    
    # Get environment users
    env_users = get_env_users()
    print(f"Environment users to migrate: {list(env_users.keys()) or 'None'}")
    
    if not env_users:
        print("\n⚠️  No users found in environment variables!")
        print("\nTo set users, use:")
        print("  export APP_USERS=admin:password,user1:password1")
        return 0, 0
    
    created = 0
    skipped = 0
    updated = 0
    
    for username, user_data in env_users.items():
        if username in existing_users:
            if force:
                # Update existing user
                user_id = existing_users[username]['user_id']
                password_hash, salt = auth.hash_password(user_data['password'])
                db.update_user(
                    user_id,
                    password_hash=password_hash,
                    salt=salt,
                    role=user_data['role']
                )
                print(f"  ✓ Updated: {username}")
                updated += 1
            else:
                print(f"  ⊘ Skipped (exists): {username}")
                skipped += 1
        else:
            # Create new user
            user_id = auth.register_user(
                username=username,
                password=user_data['password'],
                role=user_data['role'],
                display_name=user_data['display_name'],
                created_by='migration_script'
            )
            if user_id:
                print(f"  ✓ Created: {username} (role: {user_data['role']})")
                created += 1
            else:
                print(f"  ✗ Failed: {username}")
    
    print("-" * 60)
    print(f"Migration complete: {created} created, {updated} updated, {skipped} skipped")
    
    return created, skipped


def create_user(user_spec: str):
    """Create a single user from command line spec."""
    parts = user_spec.split(':')
    if len(parts) < 2:
        print("Error: User spec must be username:password[:role]")
        return False
    
    username = parts[0].lower()
    password = parts[1]
    role = parts[2] if len(parts) > 2 else 'user'
    
    if role not in ('admin', 'user', 'readonly'):
        print(f"Error: Invalid role '{role}'. Must be admin, user, or readonly")
        return False
    
    db.init_database()
    
    if db.user_exists(username):
        print(f"Error: User '{username}' already exists")
        return False
    
    user_id = auth.register_user(
        username=username,
        password=password,
        role=role,
        created_by='cli'
    )
    
    if user_id:
        print(f"✓ Created user: {username} (role: {role}, id: {user_id})")
        return True
    else:
        print(f"✗ Failed to create user: {username}")
        return False


def list_users():
    """List all users in the database."""
    db.init_database()
    users = db.list_users()
    
    print("=" * 60)
    print("Database Users")
    print("=" * 60)
    
    if not users:
        print("No users found in database.")
        return
    
    print(f"{'Username':<15} {'Role':<10} {'Display Name':<20} {'Last Login':<20}")
    print("-" * 65)
    
    for user in users:
        last_login = user.get('last_login') or 'Never'
        if last_login != 'Never':
            try:
                last_login = datetime.fromisoformat(last_login).strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        print(f"{user['username']:<15} {user['role']:<10} {user.get('display_name', ''):<20} {last_login:<20}")
    
    print("-" * 65)
    print(f"Total: {len(users)} users")


def reset_password(username: str, new_password: str):
    """Reset a user's password."""
    db.init_database()
    
    user = db.get_user_by_username(username)
    if not user:
        print(f"Error: User '{username}' not found")
        return False
    
    result = auth.change_password(
        user_id=user['user_id'],
        new_password=new_password,
        changed_by='cli'
    )
    
    if result:
        print(f"✓ Password reset for: {username}")
        return True
    else:
        print(f"✗ Failed to reset password for: {username}")
        return False


def show_audit_log(username: str = None, limit: int = 20):
    """Show recent audit log entries."""
    db.init_database()
    entries = db.get_audit_log(username=username, limit=limit)
    
    print("=" * 80)
    print(f"Audit Log (last {limit} entries)")
    print("=" * 80)
    
    if not entries:
        print("No audit entries found.")
        return
    
    for entry in entries:
        timestamp = entry.get('created_at', '')
        event_type = entry.get('event_type', '')
        user = entry.get('username', 'N/A')
        success = '✓' if entry.get('success') else '✗'
        ip = entry.get('ip_address', '')
        
        print(f"{timestamp} | {success} {event_type:<20} | {user:<15} | {ip}")


def main():
    parser = argparse.ArgumentParser(
        description='Migrate authentication from environment variables to database'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force update existing users'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List current database users'
    )
    parser.add_argument(
        '--create-user', '-c',
        metavar='USER:PASS[:ROLE]',
        help='Create a single user (role: admin, user, readonly)'
    )
    parser.add_argument(
        '--add-admin', '-a',
        metavar='USER:PASS',
        help='Add an admin user'
    )
    parser.add_argument(
        '--reset-password', '-r',
        metavar='USER:NEWPASS',
        help='Reset a user password'
    )
    parser.add_argument(
        '--audit-log',
        action='store_true',
        help='Show recent audit log'
    )
    parser.add_argument(
        '--audit-user',
        metavar='USERNAME',
        help='Show audit log for specific user'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_users()
    elif args.create_user:
        create_user(args.create_user)
    elif args.add_admin:
        parts = args.add_admin.split(':')
        if len(parts) >= 2:
            create_user(f"{parts[0]}:{parts[1]}:admin")
        else:
            print("Error: --add-admin requires username:password")
    elif args.reset_password:
        parts = args.reset_password.split(':')
        if len(parts) >= 2:
            reset_password(parts[0], parts[1])
        else:
            print("Error: --reset-password requires username:newpassword")
    elif args.audit_log or args.audit_user:
        show_audit_log(username=args.audit_user)
    else:
        migrate_users(force=args.force)


if __name__ == '__main__':
    main()
