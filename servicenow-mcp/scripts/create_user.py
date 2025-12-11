#!/usr/bin/env python3
"""
User Creation Script for ServiceNow MCP Web UI

Creates a new user in the SQLite authentication database.

Usage:
    python scripts/create_user.py --username <username> --password <password> [options]

Examples:
    # Create a basic user
    python scripts/create_user.py --username john --password secret123

    # Create an admin user with all details
    python scripts/create_user.py --username admin2 --password admin123 --role admin --display-name "Admin User" --email admin@example.com

    # Interactive mode (prompts for password)
    python scripts/create_user.py --username john --interactive
"""

import os
import sys
import argparse
import getpass
import sqlite3
import secrets

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_DIR)

try:
    import bcrypt
except ImportError:
    print("Error: bcrypt module not found. Install it with: pip install bcrypt")
    sys.exit(1)

# Database path
DB_PATH = os.path.join(PROJECT_DIR, 'web_ui', 'auth.db')


def hash_password(password: str) -> tuple[str, str]:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Tuple of (password_hash, salt)
    """
    salt = secrets.token_hex(16)
    password_hash = bcrypt.hashpw(
        password.encode('utf-8'), 
        bcrypt.gensalt(12)
    ).decode('utf-8')
    return password_hash, salt


def create_user(
    username: str,
    password: str,
    role: str = 'user',
    display_name: str = None,
    email: str = None
) -> int:
    """
    Create a new user in the database.
    
    Args:
        username: Unique username (case-insensitive)
        password: Plain text password (will be hashed)
        role: User role - 'admin', 'user', or 'readonly'
        display_name: Optional display name
        email: Optional email address
        
    Returns:
        user_id of the created user
        
    Raises:
        ValueError: If username already exists or invalid role
        FileNotFoundError: If database doesn't exist
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Please run the web UI first to initialize the database."
        )
    
    # Validate role
    valid_roles = ['admin', 'user', 'readonly']
    if role not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. Must be one of: {valid_roles}")
    
    # Hash the password
    password_hash, salt = hash_password(password)
    
    # Set default display name
    if not display_name:
        display_name = username.title()
    
    # Insert user
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, role, display_name, email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username.lower(), password_hash, salt, role, display_name, email))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        raise ValueError(f"Username '{username}' already exists")


def list_users():
    """List all users in the database."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, role, display_name, email, is_active, created_at 
        FROM users ORDER BY user_id
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("No users found.")
        return
    
    print("\n{:<8} {:<15} {:<10} {:<20} {:<25} {:<8} {}".format(
        "ID", "Username", "Role", "Display Name", "Email", "Active", "Created"
    ))
    print("-" * 100)
    for row in rows:
        print("{:<8} {:<15} {:<10} {:<20} {:<25} {:<8} {}".format(
            row['user_id'],
            row['username'],
            row['role'],
            row['display_name'] or '',
            row['email'] or '',
            'Yes' if row['is_active'] else 'No',
            row['created_at'][:19] if row['created_at'] else ''
        ))
    print()


def delete_user(username: str) -> bool:
    """Delete a user from the database."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE username = ?', (username.lower(),))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def main():
    parser = argparse.ArgumentParser(
        description='Create and manage users for ServiceNow MCP Web UI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Create a user:
    python create_user.py --username john --password secret123
    
  Create an admin:
    python create_user.py --username admin2 --password admin123 --role admin
    
  Interactive mode:
    python create_user.py --username john --interactive
    
  List all users:
    python create_user.py --list
    
  Delete a user:
    python create_user.py --delete john
        """
    )
    
    # Action arguments
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all users')
    parser.add_argument('--delete', '-d', metavar='USERNAME',
                        help='Delete a user by username')
    
    # User creation arguments
    parser.add_argument('--username', '-u', 
                        help='Username for the new user')
    parser.add_argument('--password', '-p',
                        help='Password for the new user')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Prompt for password interactively (more secure)')
    parser.add_argument('--role', '-r', default='user',
                        choices=['admin', 'user', 'readonly'],
                        help='User role (default: user)')
    parser.add_argument('--display-name', '-n',
                        help='Display name for the user')
    parser.add_argument('--email', '-e',
                        help='Email address for the user')
    
    args = parser.parse_args()
    
    # Handle list action
    if args.list:
        list_users()
        return
    
    # Handle delete action
    if args.delete:
        try:
            if delete_user(args.delete):
                print(f"✓ User '{args.delete}' deleted successfully")
            else:
                print(f"✗ User '{args.delete}' not found")
                sys.exit(1)
        except FileNotFoundError as e:
            print(f"✗ Error: {e}")
            sys.exit(1)
        return
    
    # Handle create action
    if not args.username:
        parser.print_help()
        print("\nError: --username is required for creating a user")
        sys.exit(1)
    
    # Get password
    if args.interactive:
        password = getpass.getpass(f"Enter password for '{args.username}': ")
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("✗ Passwords do not match")
            sys.exit(1)
    elif args.password:
        password = args.password
    else:
        print("Error: Either --password or --interactive is required")
        sys.exit(1)
    
    # Validate password strength
    if len(password) < 6:
        print("✗ Password must be at least 6 characters long")
        sys.exit(1)
    
    # Create the user
    try:
        user_id = create_user(
            username=args.username,
            password=password,
            role=args.role,
            display_name=args.display_name,
            email=args.email
        )
        print(f"✓ User '{args.username}' created successfully!")
        print(f"  User ID: {user_id}")
        print(f"  Role: {args.role}")
        if args.display_name:
            print(f"  Display Name: {args.display_name}")
        if args.email:
            print(f"  Email: {args.email}")
    except ValueError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
