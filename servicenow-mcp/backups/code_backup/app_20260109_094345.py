#!/usr/bin/env python3
"""
ServiceNow Incident Processor - Web User Interface

A Flask-based web application that provides a user-friendly interface for:
- Monitoring ServiceNow incidents
- Processing incidents with Redshift operations
- Viewing incident history and status
- Managing the monitoring service
- User authentication and session management (Database-backed with AG-UI integration)
"""

import os
import sys
import json
import threading
import queue
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import Flask, render_template, jsonify, request, Response, redirect, url_for, session
from flask_cors import CORS
from functools import wraps
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from enum import Enum

# Import database-backed authentication modules
from web_ui import database as db
from web_ui import auth
from web_ui.agui_auth import AuthActionHandler, create_agui_auth_routes

# Import the core Redshift processor
from process_servicenow_redshift import (
    ServiceNowClient, 
    RedshiftClient, 
    IncidentParser, 
    IncidentProcessor,
    Config
)

# Import security group processor functions
from process_security_group_incident import (
    parse_security_group_request,
    process_incident as process_security_group_incident
)


# ============================================================================
# Incident Type Detection
# ============================================================================

class IncidentType(Enum):
    """Enum for different incident types that can be processed."""
    REDSHIFT_USER = "REDSHIFT_USER"  # Redshift user creation/management
    SECURITY_GROUP = "SECURITY_GROUP"  # AWS Security Group modifications
    UNKNOWN = "UNKNOWN"  # Unknown/unrecognized incident type


def detect_incident_type(description: str, short_description: str = "") -> IncidentType:
    """
    Detect the type of incident based on keywords in description.
    
    This function analyzes the incident description to determine which
    processor should handle the incident.
    
    Args:
        description: The full incident description
        short_description: The short description (title) of the incident
        
    Returns:
        IncidentType enum value indicating the incident type
    """
    import re
    
    full_text = f"{description} {short_description}".lower()
    
    # Security Group indicators (check first - more specific)
    security_group_patterns = [
        r'security\s+group',
        r'sg-[a-zA-Z0-9]+',  # Security group ID pattern
        r'inbound\s+rule',
        r'outbound\s+rule',
        r'add\s+(an?\s+)?inbound',
        r'add\s+(an?\s+)?outbound',
        r'remove\s+(an?\s+)?inbound',
        r'remove\s+(an?\s+)?outbound',
        r'cidr\s+range',
        r'firewall\s+rule'
    ]
    
    for pattern in security_group_patterns:
        if re.search(pattern, full_text):
            return IncidentType.SECURITY_GROUP
    
    # Redshift user indicators
    redshift_patterns = [
        r'redshift.*user',
        r'create.*user.*redshift',
        r'user.*redshift.*cluster',
        r'database\s+user',
        r'add.*user.*group',
        r'grant.*privilege',
        r'redshift-cluster-\d+',
        r'username[:\s]',
        r'schema\s+access'
    ]
    
    for pattern in redshift_patterns:
        if re.search(pattern, full_text):
            return IncidentType.REDSHIFT_USER
    
    # Default to unknown if no patterns match
    return IncidentType.UNKNOWN


def get_incident_type_display(incident_type: IncidentType) -> dict:
    """
    Get display information for an incident type.
    
    Args:
        incident_type: The IncidentType enum value
        
    Returns:
        Dictionary with display name, badge color, and description
    """
    type_info = {
        IncidentType.REDSHIFT_USER: {
            "type_code": "REDSHIFT_USER",
            "display_name": "Redshift User",
            "badge_class": "bg-primary",
            "description": "Redshift database user creation/management"
        },
        IncidentType.SECURITY_GROUP: {
            "type_code": "SECURITY_GROUP",
            "display_name": "Security Group",
            "badge_class": "bg-warning text-dark",
            "description": "AWS Security Group rule modifications"
        },
        IncidentType.UNKNOWN: {
            "type_code": "UNKNOWN",
            "display_name": "Unknown",
            "badge_class": "bg-secondary",
            "description": "Unrecognized incident type"
        }
    }
    return type_info.get(incident_type, type_info[IncidentType.UNKNOWN])

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
CORS(app)

# Initialize AG-UI authentication handler
auth_handler = None  # Will be initialized after app setup

# ============================================================================
# Persistent Storage (Processing History - unchanged)
# ============================================================================

HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'processing_history.json')

def load_history() -> List[Dict[str, Any]]:
    """Load processing history from file."""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load history file: {e}")
    return []

def save_history(history: List[Dict[str, Any]]):
    """Save processing history to file."""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history[:500], f, indent=2)  # Keep last 500 entries
    except Exception as e:
        print(f"Warning: Could not save history file: {e}")

def add_to_history(result: Dict[str, Any]):
    """Add a result to history and persist it."""
    result["timestamp"] = datetime.now().isoformat()
    state.processed_incidents.insert(0, result)
    save_history(state.processed_incidents)

# ============================================================================
# User Authentication (Database-backed with AG-UI Integration)
# ============================================================================

def get_users_from_env() -> Dict[str, Any]:
    """
    LEGACY: Get users from environment variables.
    Used only for migration purposes.
    
    Set credentials using: APP_USERS=admin:password1,demo:password2
    """
    users = {}
    
    combined_users = os.getenv('APP_USERS', '')
    if combined_users:
        for user_pair in combined_users.split(','):
            if ':' in user_pair:
                username, password = user_pair.split(':', 1)
                username = username.strip().lower()
                password = password.strip()
                if username and password:
                    hashed, salt = auth.hash_password(password)
                    users[username] = {
                        'password_hash': hashed,
                        'salt': salt,
                        'role': 'admin' if username == 'admin' else 'user',
                        'display_name': username.title()
                    }
    
    for key, value in os.environ.items():
        if key.startswith('APP_USER_') and value:
            username = key[9:].lower()
            if username not in users:
                hashed, salt = auth.hash_password(value)
                users[username] = {
                    'password_hash': hashed,
                    'salt': salt,
                    'role': 'admin' if username == 'admin' else 'user',
                    'display_name': username.title()
                }
    
    return users


def migrate_env_users_if_needed():
    """
    Automatically migrate users from environment variables to database
    if the database is empty and APP_USERS is set.
    """
    if db.get_user_count() == 0:
        env_users = get_users_from_env()
        if env_users:
            print("Migrating users from environment variables to database...")
            created, skipped = db.migrate_env_users_to_db(env_users)
            print(f"Migration complete: {created} users created, {skipped} skipped")
        else:
            # Check for INITIAL_ADMIN_PASSWORD
            auth.ensure_admin_user()


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user using the database-backed authentication.
    Returns user data if successful, None otherwise.
    """
    ip_address = auth.get_client_ip(request) if request else None
    user_agent = auth.get_user_agent(request) if request else None
    
    return auth.authenticate_user(
        username=username,
        password=password,
        ip_address=ip_address,
        user_agent=user_agent
    )


def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Authentication required', 'redirect': '/login'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Add cache control headers to prevent back button bypass
@app.after_request
def add_security_headers(response):
    """Add security headers to prevent caching of ALL pages."""
    # Prevent caching of all pages to fix back/forward button issues
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ============================================================================
# Global State
# ============================================================================

class AppState:
    def __init__(self):
        self.monitoring_active = False
        self.monitor_thread = None
        self.processed_incidents: List[Dict[str, Any]] = load_history()  # Load from file
        self.event_queue = queue.Queue()
        self.last_poll_time = None
        self.poll_count = 0
        self.error_count = 0
        self.success_count = len([h for h in self.processed_incidents if h.get('success')])
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        
state = AppState()

# ============================================================================
# API Routes
# ============================================================================

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'GET':
        # If already logged in, redirect to dashboard
        if 'user' in session:
            return redirect(url_for('index'))
        return render_template('login.html')
    
    # POST - handle login
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    remember = request.form.get('remember') == 'on'
    
    if not username or not password:
        return render_template('login.html', error='Please enter both username and password')
    
    user = authenticate_user(username, password)
    if user:
        session['user'] = user
        session.permanent = remember
        return redirect(url_for('index'))
    
    return render_template('login.html', error='Invalid username or password')

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/api/auth/status')
def auth_status():
    """Get current authentication status."""
    if 'user' in session:
        return jsonify({
            'authenticated': True,
            'user': session['user']
        })
    return jsonify({'authenticated': False})

@app.route('/')
@login_required
def index():
    """Serve the main dashboard page."""
    return render_template('index.html', user=session.get('user'))


@app.route('/api/config')
@login_required
def get_config():
    """Get current configuration status."""
    return jsonify({
        "servicenow_url": Config.SERVICENOW_INSTANCE_URL,
        "servicenow_configured": bool(Config.SERVICENOW_INSTANCE_URL and Config.SERVICENOW_USERNAME),
        "aws_region": Config.AWS_REGION,
        "redshift_database": Config.REDSHIFT_DATABASE,
        "redshift_db_user": Config.REDSHIFT_DB_USER,
        "poll_interval": Config.POLL_INTERVAL,
        "dry_run": state.dry_run
    })


@app.route('/api/status')
@login_required
def get_status():
    """Get current system status."""
    # Calculate this week's count
    from datetime import timedelta
    now = datetime.now()
    # Start of week (Monday)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    this_week_count = 0
    for incident in state.processed_incidents:
        ts = incident.get('timestamp')
        if ts:
            try:
                incident_time = datetime.fromisoformat(ts.replace('Z', '+00:00').replace('+00:00', ''))
                if incident_time >= start_of_week:
                    this_week_count += 1
            except:
                pass
    
    return jsonify({
        "monitoring_active": state.monitoring_active,
        "last_poll_time": state.last_poll_time.isoformat() if state.last_poll_time else None,
        "processed_count": len(state.processed_incidents),
        "success_count": state.success_count,
        "error_count": state.error_count,
        "dry_run": state.dry_run,
        "this_week_count": this_week_count
    })


@app.route('/api/incidents')
@login_required
def list_incidents():
    """List recent incidents from ServiceNow."""
    from_date = request.args.get('from_date', datetime.now().strftime("%Y-%m-%d"))
    limit = int(request.args.get('limit', 100))
    
    try:
        client = ServiceNowClient()
        incidents = client.list_incidents(from_date, limit)
        
        # Parse each incident and detect type
        parsed_incidents = []
        for inc in incidents:
            parsed = IncidentParser.parse_incident(inc)
            
            # Detect incident type from description
            description = inc.get("description", "") or ""
            short_desc = inc.get("short_description", "") or ""
            incident_type = detect_incident_type(description, short_desc)
            type_info = get_incident_type_display(incident_type)
            
            # Add type information to parsed incident
            parsed["incident_type"] = type_info["type_code"]
            parsed["incident_type_display"] = type_info["display_name"]
            parsed["incident_type_badge"] = type_info["badge_class"]
            
            # Determine processability based on incident type
            if incident_type == IncidentType.REDSHIFT_USER:
                parsed["is_processable"] = bool(parsed["username"] and parsed["cluster"])
            elif incident_type == IncidentType.SECURITY_GROUP:
                # Parse security group request to check if processable
                sg_request = parse_security_group_request(description)
                parsed["is_processable"] = bool(
                    sg_request.get("operation") and 
                    sg_request.get("security_group_id") and 
                    sg_request.get("cidrs") and 
                    sg_request.get("port")
                )
                # Add security group specific fields for display
                parsed["sg_operation"] = sg_request.get("operation", "").replace("_", " ").title()
                parsed["sg_id"] = sg_request.get("security_group_id")
                parsed["sg_cidrs"] = sg_request.get("cidrs", [])
            else:
                parsed["is_processable"] = False
            
            parsed["is_processed"] = client.is_already_processed(inc)
            parsed_incidents.append(parsed)
        
        return jsonify({
            "success": True,
            "incidents": parsed_incidents,
            "count": len(parsed_incidents)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "incidents": []
        }), 500


@app.route('/api/incidents/<incident_number>')
@login_required
def get_incident(incident_number: str):
    """Get details of a specific incident."""
    try:
        client = ServiceNowClient()
        incident = client.get_incident(incident_number)
        
        if not incident:
            return jsonify({
                "success": False,
                "error": f"Incident {incident_number} not found"
            }), 404
        
        parsed = IncidentParser.parse_incident(incident)
        
        # Detect incident type from description
        description = incident.get("description", "") or ""
        short_desc = incident.get("short_description", "") or ""
        incident_type = detect_incident_type(description, short_desc)
        type_info = get_incident_type_display(incident_type)
        
        # Add type information to parsed incident
        parsed["incident_type"] = type_info["type_code"]
        parsed["incident_type_display"] = type_info["display_name"]
        parsed["incident_type_badge"] = type_info["badge_class"]
        
        # Determine processability based on incident type
        if incident_type == IncidentType.REDSHIFT_USER:
            parsed["is_processable"] = bool(parsed["username"] and parsed["cluster"])
        elif incident_type == IncidentType.SECURITY_GROUP:
            # Parse security group request to check if processable
            sg_request = parse_security_group_request(description)
            parsed["is_processable"] = bool(
                sg_request.get("operation") and 
                sg_request.get("security_group_id") and 
                sg_request.get("cidrs") and 
                sg_request.get("port")
            )
            # Add security group specific fields for display
            parsed["sg_operation"] = sg_request.get("operation", "").replace("_", " ").title()
            parsed["sg_id"] = sg_request.get("security_group_id")
            parsed["sg_cidrs"] = sg_request.get("cidrs", [])
            parsed["sg_port"] = sg_request.get("port")
            parsed["sg_region"] = sg_request.get("region", "us-east-1")
        else:
            parsed["is_processable"] = False
        
        parsed["is_processed"] = client.is_already_processed(incident)
        parsed["raw_data"] = incident
        
        return jsonify({
            "success": True,
            "incident": parsed
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/process/<incident_number>', methods=['POST'])
@login_required
def process_incident_route(incident_number: str):
    """Process a specific incident.
    
    Routes incident to the appropriate processor based on incident type:
    - REDSHIFT_USER: Uses IncidentProcessor for Redshift user operations
    - SECURITY_GROUP: Uses process_security_group_incident for SG modifications
    
    Validates that the incident belongs to WG101 group before processing.
    Returns error if incident is from a different group.
    """
    dry_run = request.json.get('dry_run', state.dry_run) if request.json else state.dry_run
    
    try:
        # First, fetch the incident to validate assignment_group
        client = ServiceNowClient()
        incident = client.get_incident(incident_number)
        
        if not incident:
            return jsonify({
                "success": False,
                "incident_number": incident_number,
                "error": f"Incident {incident_number} not found",
                "error_code": "NOT_FOUND"
            }), 404
        
        # Check assignment_group - must be WG101
        assignment_group = incident.get("assignment_group", "") or ""
        required_group = Config.ASSIGNMENT_GROUP_FILTER  # Default: "WG101"
        
        if assignment_group != required_group:
            group_display = assignment_group if assignment_group else "None (unassigned)"
            return jsonify({
                "success": False,
                "incident_number": incident_number,
                "error": f"This incident belongs to group '{group_display}'. Only incidents assigned to '{required_group} - Redshift Work Group' can be processed.",
                "error_code": "INVALID_GROUP",
                "current_group": assignment_group,
                "required_group": required_group
            }), 400
        
        # Detect incident type and route to appropriate processor
        description = incident.get("description", "") or ""
        short_desc = incident.get("short_description", "") or ""
        incident_type = detect_incident_type(description, short_desc)
        
        result = None
        
        if incident_type == IncidentType.SECURITY_GROUP:
            # Route to Security Group processor
            # process_security_group_incident now returns a detailed dict with sg_details
            sg_result = process_security_group_incident(incident_number)
            
            # Handle both new dict return and legacy bool return for compatibility
            if isinstance(sg_result, dict):
                result = {
                    "incident_number": sg_result.get("incident_number", incident_number),
                    "success": sg_result.get("success", False),
                    "message": sg_result.get("message", "Security Group operation completed"),
                    "incident_type": "SECURITY_GROUP",
                    "actions": sg_result.get("actions", ["Security Group rule modification processed"]),
                    "sg_details": sg_result.get("sg_details")
                }
            else:
                # Legacy bool return - fallback
                result = {
                    "incident_number": incident_number,
                    "success": bool(sg_result),
                    "message": "Security Group operation completed successfully" if sg_result else "Security Group operation failed",
                    "incident_type": "SECURITY_GROUP",
                    "actions": ["Security Group rule modification processed"],
                    "sg_details": None
                }
        elif incident_type == IncidentType.REDSHIFT_USER:
            # Route to Redshift processor
            processor = IncidentProcessor(dry_run=dry_run)
            result = processor.process_incident(incident_number)
            result["incident_type"] = "REDSHIFT_USER"
        else:
            # Unknown incident type
            return jsonify({
                "success": False,
                "incident_number": incident_number,
                "error": "Could not determine incident type. The incident description does not match any known patterns (Redshift User or Security Group).",
                "error_code": "UNKNOWN_INCIDENT_TYPE",
                "incident_type": "UNKNOWN"
            }), 400
        
        # Store in history (persistent)
        add_to_history(result)
        
        # Update counters
        if result["success"]:
            state.success_count += 1
        else:
            state.error_count += 1
        
        # Emit event
        state.event_queue.put({
            "type": "incident_processed",
            "data": result
        })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "incident_number": incident_number,
            "error": str(e)
        }), 500


@app.route('/api/process-batch', methods=['POST'])
@login_required
def process_batch():
    """Process multiple incidents."""
    data = request.json or {}
    incident_numbers = data.get('incident_numbers', [])
    dry_run = data.get('dry_run', state.dry_run)
    
    results = []
    processor = IncidentProcessor(dry_run=dry_run)
    
    for incident_number in incident_numbers:
        try:
            result = processor.process_incident(incident_number)
            result["timestamp"] = datetime.now().isoformat()
            results.append(result)
            state.processed_incidents.insert(0, result)
            
            if result["success"]:
                state.success_count += 1
            else:
                state.error_count += 1
                
            state.event_queue.put({
                "type": "incident_processed",
                "data": result
            })
        except Exception as e:
            results.append({
                "success": False,
                "incident_number": incident_number,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            state.error_count += 1
    
    return jsonify({
        "success": True,
        "results": results,
        "processed_count": len(results)
    })


@app.route('/api/history')
@login_required
def get_history():
    """Get processing history."""
    limit = int(request.args.get('limit', 50))
    return jsonify({
        "success": True,
        "history": state.processed_incidents[:limit],
        "total_count": len(state.processed_incidents)
    })


@app.route('/api/monitor/start', methods=['POST'])
@login_required
def start_monitoring():
    """Start the monitoring service."""
    if state.monitoring_active:
        return jsonify({
            "success": False,
            "message": "Monitoring is already active"
        })
    
    data = request.json or {}
    from_date = data.get('from_date', datetime.now().strftime("%Y-%m-%d"))
    poll_interval = data.get('poll_interval', Config.POLL_INTERVAL)
    dry_run = data.get('dry_run', state.dry_run)
    
    def monitor_thread():
        processor = IncidentProcessor(dry_run=dry_run)
        client = ServiceNowClient()
        processed_in_session = set()
        
        state.event_queue.put({
            "type": "monitoring_started",
            "data": {"from_date": from_date, "poll_interval": poll_interval}
        })
        
        while state.monitoring_active:
            try:
                state.last_poll_time = datetime.now()
                state.poll_count += 1
                
                incidents = client.list_incidents(from_date)
                new_incidents = []
                
                for inc in incidents:
                    inc_number = inc.get("number")
                    if inc_number and inc_number not in processed_in_session:
                        if not client.is_already_processed(inc):
                            new_incidents.append(inc)
                        else:
                            processed_in_session.add(inc_number)
                
                state.event_queue.put({
                    "type": "poll_complete",
                    "data": {
                        "poll_count": state.poll_count,
                        "incidents_found": len(incidents),
                        "new_incidents": len(new_incidents)
                    }
                })
                
                for inc in new_incidents:
                    inc_number = inc.get("number")
                    processed_in_session.add(inc_number)
                    
                    result = processor.process_incident(inc_number)
                    add_to_history(result)  # Persistent storage
                    
                    if result["success"]:
                        state.success_count += 1
                    else:
                        state.error_count += 1
                    
                    state.event_queue.put({
                        "type": "incident_processed",
                        "data": result
                    })
                
            except Exception as e:
                state.event_queue.put({
                    "type": "error",
                    "data": {"message": str(e)}
                })
            
            time.sleep(poll_interval)
        
        state.event_queue.put({
            "type": "monitoring_stopped",
            "data": {}
        })
    
    state.monitoring_active = True
    state.monitor_thread = threading.Thread(target=monitor_thread, daemon=True)
    state.monitor_thread.start()
    
    return jsonify({
        "success": True,
        "message": "Monitoring started",
        "from_date": from_date,
        "poll_interval": poll_interval
    })


@app.route('/api/monitor/stop', methods=['POST'])
@login_required
def stop_monitoring():
    """Stop the monitoring service."""
    if not state.monitoring_active:
        return jsonify({
            "success": False,
            "message": "Monitoring is not active"
        })
    
    state.monitoring_active = False
    
    return jsonify({
        "success": True,
        "message": "Monitoring stopped"
    })


@app.route('/api/events')
@login_required
def events():
    """Server-Sent Events endpoint for real-time updates."""
    def generate():
        while True:
            try:
                event = state.event_queue.get(timeout=30)
                data = json.dumps(event)
                yield f"data: {data}\n\n"
            except queue.Empty:
                # Send heartbeat to keep connection alive
                yield f"data: {json.dumps({'type': 'heartbeat', 'data': {}})}\n\n"
            except Exception as e:
                # Log error but don't break the connection
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


@app.route('/api/test-connection')
@login_required
def test_connection():
    """Test connections to ServiceNow and AWS."""
    results = {
        "servicenow": {"success": False, "message": ""},
        "aws": {"success": False, "message": ""}
    }
    
    # Test ServiceNow
    try:
        client = ServiceNowClient()
        incidents = client.list_incidents(datetime.now().strftime("%Y-%m-%d"), limit=1)
        results["servicenow"] = {
            "success": True,
            "message": "Successfully connected to ServiceNow"
        }
    except Exception as e:
        results["servicenow"] = {
            "success": False,
            "message": str(e)
        }
    
    # Test AWS
    try:
        import subprocess
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity", "--no-cli-pager"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            results["aws"] = {
                "success": True,
                "message": f"Connected as {identity.get('Arn', 'Unknown')}"
            }
        else:
            results["aws"] = {
                "success": False,
                "message": result.stderr
            }
    except Exception as e:
        results["aws"] = {
            "success": False,
            "message": str(e)
        }
    
    return jsonify(results)


@app.route('/api/clear-history', methods=['POST'])
@login_required
def clear_history():
    """Clear processing history."""
    state.processed_incidents.clear()
    state.success_count = 0
    state.error_count = 0
    state.poll_count = 0
    
    # Clear persistent storage
    save_history([])
    
    return jsonify({
        "success": True,
        "message": "History cleared"
    })


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    # Validate configuration
    if not Config.validate():
        print("Error: Missing required environment variables.")
        print("Please set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD.")
        sys.exit(1)
    
    # Initialize database and migrate users if needed
    db.init_database()
    migrate_env_users_if_needed()
    
    # Initialize AG-UI authentication routes
    auth_handler = create_agui_auth_routes(app, auth)
    
    # Get user count from database
    user_count = db.get_user_count()
    users_list = db.list_users()
    
    port = int(os.getenv("WEB_UI_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    print("=" * 70)
    print("ServiceNow Incident Processor - Web UI")
    print("=" * 70)
    print(f"Starting server on http://localhost:{port}")
    print(f"ServiceNow Instance: {Config.SERVICENOW_INSTANCE_URL}")
    print(f"AWS Region: {Config.AWS_REGION}")
    print(f"Dry Run Mode: {state.dry_run}")
    print("-" * 70)
    print("Authentication: Database-backed with AG-UI Protocol Integration")
    print(f"Database: {db.DB_PATH}")
    if user_count > 0:
        print(f"Users configured: {[u['username'] for u in users_list]}")
    else:
        print("⚠️  NO USERS CONFIGURED - Login will not work!")
        print("")
        print("Option 1: Set APP_USERS env var (auto-migrates to database):")
        print("  export APP_USERS=admin:yourpassword,demo:anotherpass")
        print("")
        print("Option 2: Set INITIAL_ADMIN_PASSWORD for first admin:")
        print("  export INITIAL_ADMIN_PASSWORD=securepassword")
        print("")
        print("Option 3: Run migration script:")
        print("  python scripts/migrate_to_db_auth.py")
        print("")
        print("Then restart the application.")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)
