# Running Python Scripts in ServiceNow MCP

## The Problem
When running Python scripts with `python script.py`, you may get:
```
ModuleNotFoundError: No module named 'dotenv'
```

This happens because the system Python doesn't have the required packages installed.

## Solutions

### Option 1: Use the Virtual Environment Python (Recommended)
Always use the virtual environment's Python interpreter:

```bash
cd /workspaces/sample-workflow/servicenow-mcp
.venv/bin/python create_incident.py
.venv/bin/python read_incident.py INC0010013
.venv/bin/python process_incident.py
```

### Option 2: Use the Wrapper Script
We've created a wrapper script that automatically uses the correct Python:

```bash
cd /workspaces/sample-workflow/servicenow-mcp
./run.sh create_incident.py
./run.sh read_incident.py INC0010013
```

### Option 3: Activate the Virtual Environment First
```bash
cd /workspaces/sample-workflow/servicenow-mcp
source .venv/bin/activate
python create_incident.py  # Now 'python' points to the venv Python
```

Or use the alias:
```bash
activate-sn  # Automatically cd's and activates the venv
python create_incident.py
```

### Option 4: Use the Helper Aliases
These aliases are automatically configured and use the correct Python:

```bash
create-incident   # Creates a new incident
read-incident     # Reads incident details
update-incident   # Updates an incident
```

## Why This Happens

Python packages are installed in the virtual environment (`.venv`), not system-wide. When you run `python`, it uses the system Python which doesn't have access to the packages.

## Automatic Setup

The devcontainer is configured to:
1. Create the virtual environment on initial setup
2. Install all dependencies including `python-dotenv`
3. Reinstall dependencies on every workspace restart
4. Auto-activate the virtual environment in new terminals

If you ever encounter missing packages, run:
```bash
cd /workspaces/sample-workflow/servicenow-mcp
.venv/bin/pip install -e .
.venv/bin/pip install python-dotenv
```

## Quick Reference

| Command | What it does |
|---------|--------------|
| `.venv/bin/python script.py` | Run script with venv Python |
| `./run.sh script.py` | Run script using wrapper |
| `activate-sn` | Activate virtual environment |
| `create-incident` | Create incident (uses venv) |
| `read-incident` | Read incident (uses venv) |
