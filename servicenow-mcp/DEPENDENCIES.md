# ServiceNow MCP Dependencies

## Automatic Installation

All dependencies including `python-dotenv` are automatically installed when the codespace is created or rebuilt through:

1. **postCreateCommand**: Runs `setup.sh` on first creation
2. **postStartCommand**: Ensures dependencies are up-to-date on every start
3. **Package Definition**: Dependencies defined in `pyproject.toml`

## Required Dependencies

The following packages are automatically installed:
- `python-dotenv>=1.0.0` - For loading environment variables
- `mcp[cli]==1.3.0` - Model Context Protocol
- `requests>=2.28.0` - HTTP library
- `pydantic>=2.0.0` - Data validation
- `starlette>=0.27.0` - ASGI framework
- `uvicorn>=0.22.0` - ASGI server
- `httpx>=0.24.0` - Async HTTP client
- `PyYAML>=6.0` - YAML support

## Manual Installation/Verification

If you ever need to manually verify or reinstall dependencies:

```bash
# Quick check and fix
bash .devcontainer/ensure-dependencies.sh

# Manual reinstall
cd /workspaces/sample-workflow/servicenow-mcp
source .venv/bin/activate
pip install -e .
```

## Activation

The Python virtual environment is automatically configured in VS Code settings. To manually activate:

```bash
source /workspaces/sample-workflow/servicenow-mcp/.venv/bin/activate
```

Or use the alias:

```bash
activate-sn
```

## Troubleshooting

If dependencies are missing after codespace restart:

1. Run the dependency check script:
   ```bash
   bash .devcontainer/ensure-dependencies.sh
   ```

2. Rebuild the container:
   - Press `F1` or `Ctrl+Shift+P`
   - Type "Rebuild Container"
   - Select "Dev Containers: Rebuild Container"

## Configuration Files

- **pyproject.toml** - Package dependencies definition
- **devcontainer.json** - Automatic installation commands
- **.devcontainer/setup.sh** - Initial setup script
- **.devcontainer/ensure-dependencies.sh** - Dependency verification script
