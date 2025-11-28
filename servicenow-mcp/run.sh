#!/bin/bash
# Wrapper script to run Python scripts with the correct virtual environment
cd /workspaces/sample-workflow/servicenow-mcp
exec .venv/bin/python "$@"
