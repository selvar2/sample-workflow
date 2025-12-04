#!/usr/bin/env python3
"""
ServiceNow Incident Processor - Web User Interface

A Flask-based web application that provides a user-friendly interface for:
- Monitoring ServiceNow incidents
- Processing incidents with Redshift operations
- Viewing incident history and status
- Managing the monitoring service
- User authentication and session management
"""

import os
import sys
import json
import threading
import queue
import hashlib
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

# Import the core processor
from process_servicenow_redshift import (
    ServiceNowClient, 
    RedshiftClient, 
    IncidentParser, 
    IncidentProcessor,
    Config
)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
CORS(app)

# ============================================================================
# Persistent Storage
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
# User Authentication (Environment Variable Based - No File Storage)
# ============================================================================

def hash_password(password: str, salt: str = None) -> tuple:
    """Hash a password with salt for secure storage."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hashed.hex(), salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify a password against its hash."""
    new_hash, _ = hash_password(password, salt)
    return new_hash == hashed

def get_users_from_env() -> Dict[str, Any]:
    """
    Get users from environment variables.
    
    Set credentials using: APP_USERS=admin:password1,demo:password2
    
    Example:
        export APP_USERS=admin:secretpass,demo:demopass
    """
    users = {}
    
    # Get users from APP_USERS env var (format: username:password,username2:password2)
    combined_users = os.getenv('APP_USERS', '')
    if combined_users:
        for user_pair in combined_users.split(','):
            if ':' in user_pair:
                username, password = user_pair.split(':', 1)
                username = username.strip().lower()
                password = password.strip()
                if username and password:
                    hashed, salt = hash_password(password)
                    users[username] = {
                        'password_hash': hashed,
                        'salt': salt,
                        'role': 'admin' if username == 'admin' else 'user',
                        'display_name': username.title()
                    }
    
    # Also support individual env vars (APP_USER_ADMIN=password)
    for key, value in os.environ.items():
        if key.startswith('APP_USER_') and value:
            username = key[9:].lower()  # Remove 'APP_USER_' prefix
            if username not in users:  # Don't override APP_USERS
                hashed, salt = hash_password(value)
                users[username] = {
                    'password_hash': hashed,
                    'salt': salt,
                    'role': 'admin' if username == 'admin' else 'user',
                    'display_name': username.title()
                }
    
    return users

# Cache for user credentials (computed once at startup)
_cached_users = None

def load_users() -> Dict[str, Any]:
    """Load users from environment variables (cached)."""
    global _cached_users
    if _cached_users is None:
        _cached_users = get_users_from_env()
    return _cached_users

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user and return user data if successful."""
    users = load_users()
    user = users.get(username.lower())
    if user and verify_password(password, user['password_hash'], user['salt']):
        return {
            'username': username,
            'role': user.get('role', 'user'),
            'display_name': user.get('display_name', username)
        }
    return None

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
        
        # Parse each incident
        parsed_incidents = []
        for inc in incidents:
            parsed = IncidentParser.parse_incident(inc)
            parsed["is_processable"] = bool(parsed["username"] and parsed["cluster"])
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
        parsed["is_processable"] = bool(parsed["username"] and parsed["cluster"])
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
def process_incident(incident_number: str):
    """Process a specific incident."""
    dry_run = request.json.get('dry_run', state.dry_run) if request.json else state.dry_run
    
    try:
        processor = IncidentProcessor(dry_run=dry_run)
        result = processor.process_incident(incident_number)
        
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
    
    # Load users from environment (will use defaults if USE_DEFAULT_AUTH=true)
    users = load_users()
    
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
    print("Authentication: Environment Variable Based (No Hardcoded Passwords)")
    if users:
        print(f"Users configured: {list(users.keys())}")
    else:
        print("⚠️  NO USERS CONFIGURED - Login will not work!")
        print("")
        print("Set credentials using environment variable:")
        print("  export APP_USERS=admin:yourpassword,demo:anotherpass")
        print("")
        print("Then restart the application.")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)
