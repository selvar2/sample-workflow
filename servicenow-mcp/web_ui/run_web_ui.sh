#!/bin/bash
# Start the ServiceNow Incident Processor Web UI

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install web UI dependencies if needed
pip install flask flask-cors boto3 -q

# Set environment variables if not already set
export FLASK_DEBUG="${FLASK_DEBUG:-false}"
export WEB_UI_PORT="${WEB_UI_PORT:-5000}"

echo "========================================"
echo "ServiceNow Incident Processor - Web UI"
echo "========================================"
echo ""
echo "Starting server on http://localhost:$WEB_UI_PORT"
echo ""

# Run the web UI
python web_ui/app.py "$@"
