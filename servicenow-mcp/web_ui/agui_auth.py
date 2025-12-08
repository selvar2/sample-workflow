"""
AG-UI Protocol Integration for Authentication

This module provides AG-UI compatible event types and handlers for the
authentication system. It follows the AG-UI event-driven architecture
while integrating with the database-backed authentication system.

AG-UI Protocol Concepts:
- Events: Typed messages for agent-UI communication
- State: Synchronized state between agent and UI
- Actions: Backend operations triggered by UI events

Authentication Events:
- AUTH_LOGIN_START: Login attempt initiated
- AUTH_LOGIN_SUCCESS: Login successful
- AUTH_LOGIN_FAILED: Login failed
- AUTH_LOGOUT: User logged out
- AUTH_SESSION_VALIDATED: Session token validated
- AUTH_SESSION_EXPIRED: Session has expired
- AUTH_STATE_SNAPSHOT: Full authentication state

This module is designed to be used WITHOUT modifying the existing UI.
It provides backend event handling that the existing UI can consume
through the existing API endpoints.
"""

import json
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field


# ============================================================================
# AG-UI Event Types for Authentication
# ============================================================================

class AuthEventType(str, Enum):
    """Authentication event types following AG-UI naming conventions."""
    
    # Login events
    AUTH_LOGIN_START = "AUTH_LOGIN_START"
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    
    # Session events
    AUTH_SESSION_CREATED = "AUTH_SESSION_CREATED"
    AUTH_SESSION_VALIDATED = "AUTH_SESSION_VALIDATED"
    AUTH_SESSION_EXPIRED = "AUTH_SESSION_EXPIRED"
    AUTH_SESSION_INVALIDATED = "AUTH_SESSION_INVALIDATED"
    
    # Logout events
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_LOGOUT_ALL = "AUTH_LOGOUT_ALL"
    
    # State events (following AG-UI patterns)
    AUTH_STATE_SNAPSHOT = "AUTH_STATE_SNAPSHOT"
    AUTH_STATE_DELTA = "AUTH_STATE_DELTA"
    
    # User management events
    AUTH_USER_CREATED = "AUTH_USER_CREATED"
    AUTH_USER_UPDATED = "AUTH_USER_UPDATED"
    AUTH_USER_DEACTIVATED = "AUTH_USER_DEACTIVATED"
    AUTH_PASSWORD_CHANGED = "AUTH_PASSWORD_CHANGED"
    AUTH_ACCOUNT_LOCKED = "AUTH_ACCOUNT_LOCKED"
    AUTH_ACCOUNT_UNLOCKED = "AUTH_ACCOUNT_UNLOCKED"


# ============================================================================
# AG-UI Event Data Classes
# ============================================================================

@dataclass
class BaseAuthEvent:
    """Base class for all authentication events."""
    type: AuthEventType
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['type'] = self.type.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    def to_sse(self) -> str:
        """Convert to Server-Sent Event format."""
        return f"data: {self.to_json()}\n\n"


@dataclass
class AuthLoginStartEvent(BaseAuthEvent):
    """Event emitted when login attempt starts."""
    type: AuthEventType = field(default=AuthEventType.AUTH_LOGIN_START)
    username: str = ""


@dataclass
class AuthLoginSuccessEvent(BaseAuthEvent):
    """Event emitted on successful login."""
    type: AuthEventType = field(default=AuthEventType.AUTH_LOGIN_SUCCESS)
    user_id: int = 0
    username: str = ""
    role: str = "user"
    display_name: str = ""


@dataclass
class AuthLoginFailedEvent(BaseAuthEvent):
    """Event emitted on failed login."""
    type: AuthEventType = field(default=AuthEventType.AUTH_LOGIN_FAILED)
    username: str = ""
    reason: str = ""
    attempts_remaining: Optional[int] = None


@dataclass
class AuthSessionCreatedEvent(BaseAuthEvent):
    """Event emitted when a new session is created."""
    type: AuthEventType = field(default=AuthEventType.AUTH_SESSION_CREATED)
    user_id: int = 0
    username: str = ""
    expires_at: str = ""


@dataclass
class AuthSessionValidatedEvent(BaseAuthEvent):
    """Event emitted when a session is validated."""
    type: AuthEventType = field(default=AuthEventType.AUTH_SESSION_VALIDATED)
    user_id: int = 0
    username: str = ""
    role: str = "user"


@dataclass
class AuthSessionExpiredEvent(BaseAuthEvent):
    """Event emitted when a session has expired."""
    type: AuthEventType = field(default=AuthEventType.AUTH_SESSION_EXPIRED)
    username: Optional[str] = None


@dataclass
class AuthLogoutEvent(BaseAuthEvent):
    """Event emitted on logout."""
    type: AuthEventType = field(default=AuthEventType.AUTH_LOGOUT)
    user_id: int = 0
    username: str = ""


@dataclass
class AuthStateSnapshot(BaseAuthEvent):
    """
    Full authentication state snapshot.
    Following AG-UI's STATE_SNAPSHOT pattern.
    """
    type: AuthEventType = field(default=AuthEventType.AUTH_STATE_SNAPSHOT)
    authenticated: bool = False
    user: Optional[Dict[str, Any]] = None
    permissions: List[str] = field(default_factory=list)


@dataclass
class AuthStateDelta(BaseAuthEvent):
    """
    Authentication state delta update.
    Following AG-UI's STATE_DELTA pattern with JSON Patch operations.
    """
    type: AuthEventType = field(default=AuthEventType.AUTH_STATE_DELTA)
    operations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AuthAccountLockedEvent(BaseAuthEvent):
    """Event emitted when an account is locked."""
    type: AuthEventType = field(default=AuthEventType.AUTH_ACCOUNT_LOCKED)
    username: str = ""
    locked_until: str = ""
    reason: str = "too_many_failed_attempts"


# ============================================================================
# AG-UI Event Encoder
# ============================================================================

class AuthEventEncoder:
    """
    Encoder for authentication events.
    Follows AG-UI's EventEncoder pattern.
    """
    
    @staticmethod
    def encode(event: BaseAuthEvent) -> str:
        """Encode event for HTTP streaming (SSE)."""
        return event.to_sse()
    
    @staticmethod
    def encode_json(event: BaseAuthEvent) -> str:
        """Encode event as JSON."""
        return event.to_json()
    
    @staticmethod
    def encode_batch(events: List[BaseAuthEvent]) -> str:
        """Encode multiple events."""
        return ''.join(event.to_sse() for event in events)


# ============================================================================
# AG-UI Protocol Action Handlers
# ============================================================================

class AuthActionHandler:
    """
    Handles authentication actions following AG-UI protocol patterns.
    
    Actions are operations that can be triggered by the UI.
    Each action returns an event indicating the result.
    """
    
    def __init__(self, auth_module):
        """
        Initialize with the authentication module.
        
        Args:
            auth_module: The auth module (web_ui.auth)
        """
        self.auth = auth_module
    
    def handle_login(
        self,
        username: str,
        password: str,
        remember_me: bool = False,
        ip_address: str = None,
        user_agent: str = None
    ) -> BaseAuthEvent:
        """
        Handle login action.
        
        Returns appropriate event based on result.
        """
        # Emit start event (could be sent via SSE)
        start_event = AuthLoginStartEvent(username=username)
        
        # Attempt authentication
        user = self.auth.authenticate_user(
            username=username,
            password=password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if user:
            # Create session
            token = self.auth.create_user_session(
                user_id=user['user_id'],
                remember_me=remember_me,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return AuthLoginSuccessEvent(
                user_id=user['user_id'],
                username=user['username'],
                role=user['role'],
                display_name=user['display_name']
            )
        else:
            # Determine failure reason
            from . import database as db
            db_user = db.get_user_by_username(username)
            
            if not db_user:
                reason = "Invalid username or password"
                attempts = None
            elif not db_user.get('is_active'):
                reason = "Account is disabled"
                attempts = None
            elif db.is_user_locked(username):
                reason = "Account is locked"
                attempts = 0
            else:
                from . import auth
                remaining = auth.MAX_FAILED_ATTEMPTS - db_user.get('failed_attempts', 0)
                reason = "Invalid username or password"
                attempts = max(0, remaining)
            
            return AuthLoginFailedEvent(
                username=username,
                reason=reason,
                attempts_remaining=attempts
            )
    
    def handle_logout(
        self,
        token: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> BaseAuthEvent:
        """Handle logout action."""
        from . import database as db
        
        session = db.get_session(token)
        if session:
            self.auth.logout_user(token, ip_address, user_agent)
            return AuthLogoutEvent(
                user_id=session.get('user_id', 0),
                username=session.get('username', '')
            )
        
        return AuthLogoutEvent()
    
    def handle_validate_session(self, token: str) -> BaseAuthEvent:
        """Validate a session token."""
        session = self.auth.validate_session(token)
        
        if session:
            return AuthSessionValidatedEvent(
                user_id=session.get('user_id', 0),
                username=session.get('username', ''),
                role=session.get('role', 'user')
            )
        
        return AuthSessionExpiredEvent()
    
    def get_auth_state(self, token: str = None) -> AuthStateSnapshot:
        """
        Get full authentication state snapshot.
        
        This follows the AG-UI STATE_SNAPSHOT pattern.
        """
        if token:
            session = self.auth.validate_session(token)
            if session:
                permissions = self._get_permissions(session.get('role', 'user'))
                return AuthStateSnapshot(
                    authenticated=True,
                    user={
                        'user_id': session.get('user_id'),
                        'username': session.get('username'),
                        'role': session.get('role'),
                        'display_name': session.get('display_name')
                    },
                    permissions=permissions
                )
        
        return AuthStateSnapshot(
            authenticated=False,
            user=None,
            permissions=[]
        )
    
    def _get_permissions(self, role: str) -> List[str]:
        """Get permissions for a role."""
        base_permissions = ['view_incidents', 'view_history']
        
        if role == 'admin':
            return base_permissions + [
                'process_incidents',
                'start_monitoring',
                'stop_monitoring',
                'clear_history',
                'manage_users',
                'view_audit_log'
            ]
        elif role == 'user':
            return base_permissions + [
                'process_incidents',
                'start_monitoring',
                'stop_monitoring'
            ]
        else:  # readonly
            return base_permissions


# ============================================================================
# AG-UI Protocol JSON Definitions
# ============================================================================

# These can be used to document the protocol or generate TypeScript types

AUTH_PROTOCOL_SCHEMA = {
    "events": {
        "AUTH_LOGIN_START": {
            "description": "Emitted when login attempt starts",
            "fields": {
                "type": "AuthEventType",
                "timestamp": "ISO8601 string",
                "username": "string"
            }
        },
        "AUTH_LOGIN_SUCCESS": {
            "description": "Emitted on successful login",
            "fields": {
                "type": "AuthEventType",
                "timestamp": "ISO8601 string",
                "user_id": "integer",
                "username": "string",
                "role": "string",
                "display_name": "string"
            }
        },
        "AUTH_LOGIN_FAILED": {
            "description": "Emitted on failed login",
            "fields": {
                "type": "AuthEventType",
                "timestamp": "ISO8601 string",
                "username": "string",
                "reason": "string",
                "attempts_remaining": "integer | null"
            }
        },
        "AUTH_STATE_SNAPSHOT": {
            "description": "Full authentication state",
            "fields": {
                "type": "AuthEventType",
                "timestamp": "ISO8601 string",
                "authenticated": "boolean",
                "user": "UserInfo | null",
                "permissions": "string[]"
            }
        }
    },
    "actions": {
        "login": {
            "description": "Authenticate user",
            "input": {
                "username": "string",
                "password": "string",
                "remember_me": "boolean (optional)"
            },
            "output": "AUTH_LOGIN_SUCCESS | AUTH_LOGIN_FAILED"
        },
        "logout": {
            "description": "End user session",
            "input": {
                "token": "string"
            },
            "output": "AUTH_LOGOUT"
        },
        "validate_session": {
            "description": "Validate session token",
            "input": {
                "token": "string"
            },
            "output": "AUTH_SESSION_VALIDATED | AUTH_SESSION_EXPIRED"
        }
    }
}


# ============================================================================
# Flask Integration - Maintains Existing UI Compatibility
# ============================================================================

def create_agui_auth_routes(app, auth_module):
    """
    Create AG-UI compatible authentication routes.
    
    These routes maintain backward compatibility with the existing UI
    while providing AG-UI event semantics.
    
    Args:
        app: Flask application
        auth_module: The auth module
    """
    from flask import request, jsonify, session
    
    handler = AuthActionHandler(auth_module)
    
    @app.route('/api/agui/auth/state', methods=['GET'])
    def agui_auth_state():
        """
        Get authentication state snapshot.
        
        AG-UI compatible endpoint that returns the current auth state.
        """
        # Get token from session or header
        token = session.get('auth_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        state = handler.get_auth_state(token)
        return jsonify(state.to_dict())
    
    @app.route('/api/agui/auth/events', methods=['GET'])
    def agui_auth_events():
        """
        SSE endpoint for authentication events.
        
        This allows the UI to receive real-time auth events
        without modifying the existing UI code.
        """
        from flask import Response
        import queue
        
        def generate():
            # Send initial state
            token = request.args.get('token')
            state = handler.get_auth_state(token)
            yield state.to_sse()
            
            # Keep connection alive with heartbeats
            while True:
                import time
                time.sleep(30)
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    return handler
