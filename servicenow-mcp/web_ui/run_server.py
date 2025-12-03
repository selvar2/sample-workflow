#!/usr/bin/env python3
"""
Server Runner - Supports multiple deployment modes

Usage:
    # Local development (default)
    python run_server.py
    
    # Public access via ngrok
    python run_server.py --public
    
    # Production with gunicorn
    python run_server.py --production
    
    # Custom host/port
    python run_server.py --host 0.0.0.0 --port 8080
"""

import os
import sys
import argparse
import subprocess
import threading
import time
import signal

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_banner(mode: str, host: str, port: int, public_url: str = None):
    """Print startup banner."""
    print("=" * 70)
    print("ServiceNow Incident Processor - Web UI")
    print("=" * 70)
    print(f"Mode: {mode}")
    print(f"Local URL: http://{host}:{port}")
    if public_url:
        print(f"Public URL: {public_url}")
    print("=" * 70)

def run_development(host: str, port: int, debug: bool = False):
    """Run Flask development server."""
    from app import app
    print_banner("Development", host, port)
    app.run(host=host, port=port, debug=debug, threaded=True)

def run_with_ngrok(host: str, port: int):
    """Run with ngrok for public access."""
    from app import app
    import json
    
    # Start ngrok in background
    ngrok_process = subprocess.Popen(
        ["ngrok", "http", str(port), "--log=stdout", "--log-format=json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for ngrok to start and get public URL
    public_url = None
    time.sleep(2)  # Give ngrok time to start
    
    try:
        # Get ngrok tunnels via API
        result = subprocess.run(
            ["curl", "-s", "http://localhost:4040/api/tunnels"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            tunnels = json.loads(result.stdout)
            for tunnel in tunnels.get("tunnels", []):
                if tunnel.get("proto") == "https":
                    public_url = tunnel.get("public_url")
                    break
    except Exception as e:
        print(f"Warning: Could not get ngrok URL: {e}")
    
    print_banner("Public (ngrok)", host, port, public_url)
    
    if public_url:
        print(f"\n🌐 Share this URL for public access: {public_url}\n")
    else:
        print("\n⚠️  ngrok started but couldn't retrieve public URL")
        print("   Check http://localhost:4040 for the ngrok dashboard\n")
    
    def cleanup(signum, frame):
        print("\nShutting down ngrok...")
        ngrok_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        app.run(host=host, port=port, debug=False, threaded=True)
    finally:
        ngrok_process.terminate()

def run_production(host: str, port: int, workers: int = 4):
    """Run with gunicorn for production."""
    print_banner("Production (gunicorn)", host, port)
    
    # Check if gunicorn is available
    try:
        import gunicorn
    except ImportError:
        print("Installing gunicorn...")
        subprocess.run([sys.executable, "-m", "pip", "install", "gunicorn"], check=True)
    
    # Run gunicorn
    cmd = [
        "gunicorn",
        "--bind", f"{host}:{port}",
        "--workers", str(workers),
        "--threads", "2",
        "--timeout", "120",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "app:app"
    ]
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run(cmd)

def run_codespaces_public():
    """Instructions for Codespaces port forwarding."""
    print("=" * 70)
    print("GitHub Codespaces Public Access")
    print("=" * 70)
    print("""
For GitHub Codespaces, use the built-in port forwarding:

1. Open the PORTS tab in VS Code (bottom panel)
2. Find port 5000 in the list
3. Right-click → Port Visibility → Public
4. Copy the forwarded URL

The URL will look like: https://xxx-5000.app.github.dev

This is the recommended method for Codespaces as it:
- Requires no additional setup
- Provides HTTPS automatically
- Integrates with GitHub authentication
""")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(
        description="Run the ServiceNow Incident Processor Web UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Local development
  python run_server.py
  
  # Public access via ngrok
  python run_server.py --public
  
  # Production with gunicorn
  python run_server.py --production --workers 4
  
  # Custom port
  python run_server.py --port 8080
  
  # Show Codespaces instructions
  python run_server.py --codespaces
"""
    )
    
    parser.add_argument(
        "--host", "-H",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=5000,
        help="Port to listen on (default: 5000)"
    )
    
    parser.add_argument(
        "--public",
        action="store_true",
        help="Enable public access via ngrok tunnel"
    )
    
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode with gunicorn"
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=4,
        help="Number of gunicorn workers (default: 4)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (development only)"
    )
    
    parser.add_argument(
        "--codespaces",
        action="store_true",
        help="Show instructions for GitHub Codespaces public access"
    )
    
    args = parser.parse_args()
    
    if args.codespaces:
        run_codespaces_public()
        return
    
    if args.public:
        run_with_ngrok(args.host, args.port)
    elif args.production:
        run_production(args.host, args.port, args.workers)
    else:
        run_development(args.host, args.port, args.debug)

if __name__ == "__main__":
    main()
