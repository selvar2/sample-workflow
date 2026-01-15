#!/bin/bash
# =============================================================================
# GitHub Copilot Agents Setup Script
# =============================================================================
# This script ensures all custom agents in .github/agents/ are properly
# configured and available for GitHub Copilot in Codespaces.
#
# Features:
# - Validates agent files exist
# - Creates agent registry for quick reference
# - Sets up VS Code settings for agent awareness
# - Logs agent availability on startup
# =============================================================================

set -e

WORKSPACE_ROOT="/workspaces/sample-workflow"
AGENTS_DIR="$WORKSPACE_ROOT/.github/agents"
VSCODE_DIR="$WORKSPACE_ROOT/.vscode"
AGENT_REGISTRY="$AGENTS_DIR/.agent-registry.json"

echo ""
echo "================================================"
echo "🤖 GitHub Copilot Agents Setup"
echo "================================================"
echo ""

# Create .github/agents directory if it doesn't exist
if [ ! -d "$AGENTS_DIR" ]; then
    echo "📁 Creating agents directory..."
    mkdir -p "$AGENTS_DIR"
fi

# Count available agents
AGENT_COUNT=$(find "$AGENTS_DIR" -name "*.agent.md" -type f 2>/dev/null | wc -l)
echo "📋 Found $AGENT_COUNT agent definition files"

# List all available agents
if [ "$AGENT_COUNT" -gt 0 ]; then
    echo ""
    echo "🤖 Available Agents:"
    echo "-------------------"
    
    # Create agent registry JSON
    echo '{' > "$AGENT_REGISTRY"
    echo '  "generated": "'$(date -Iseconds)'",' >> "$AGENT_REGISTRY"
    echo '  "workspace": "'$WORKSPACE_ROOT'",' >> "$AGENT_REGISTRY"
    echo '  "agents": [' >> "$AGENT_REGISTRY"
    
    FIRST=true
    for agent_file in "$AGENTS_DIR"/*.agent.md; do
        if [ -f "$agent_file" ]; then
            agent_name=$(basename "$agent_file" .agent.md)
            
            # Extract description from frontmatter if it exists
            description=""
            if grep -q "^description:" "$agent_file" 2>/dev/null; then
                description=$(grep "^description:" "$agent_file" | head -1 | sed 's/^description: *//' | tr -d '"')
            fi
            
            echo "  ✅ @$agent_name"
            if [ -n "$description" ]; then
                echo "     └─ ${description:0:60}..."
            fi
            
            # Add to registry JSON
            if [ "$FIRST" = true ]; then
                FIRST=false
            else
                echo ',' >> "$AGENT_REGISTRY"
            fi
            
            echo -n '    {"name": "'$agent_name'", "file": "'$(basename "$agent_file")'", "path": "'$agent_file'"' >> "$AGENT_REGISTRY"
            if [ -n "$description" ]; then
                # Escape description for JSON
                escaped_desc=$(echo "$description" | sed 's/"/\\"/g' | tr -d '\n')
                echo -n ', "description": "'$escaped_desc'"' >> "$AGENT_REGISTRY"
            fi
            echo -n '}' >> "$AGENT_REGISTRY"
        fi
    done
    
    echo '' >> "$AGENT_REGISTRY"
    echo '  ]' >> "$AGENT_REGISTRY"
    echo '}' >> "$AGENT_REGISTRY"
    
    echo ""
    echo "📄 Agent registry created: $AGENT_REGISTRY"
fi

# Ensure VS Code settings directory exists
mkdir -p "$VSCODE_DIR"

# Update VS Code settings to include agent awareness
VSCODE_SETTINGS="$VSCODE_DIR/settings.json"
if [ -f "$VSCODE_SETTINGS" ]; then
    # Backup existing settings
    cp "$VSCODE_SETTINGS" "$VSCODE_SETTINGS.bak"
fi

# Create or update VS Code settings with agent configuration
cat > "$VSCODE_SETTINGS" << 'SETTINGS_EOF'
{
    "python.defaultInterpreterPath": "/workspaces/sample-workflow/servicenow-mcp/.venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter"
    },
    "files.associations": {
        "*.agent.md": "markdown"
    },
    "github.copilot.chat.codeGeneration.instructions": [
        {
            "text": "Custom agents are available in .github/agents/ directory. Use @agent-name to invoke specific agents."
        }
    ],
    "github.copilot.chat.localeOverride": "en",
    "github.copilot.enable": {
        "*": true,
        "markdown": true,
        "plaintext": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/node_modules": true
    },
    "search.exclude": {
        "**/node_modules": true,
        "**/.venv": true,
        "**/dist": true
    }
}
SETTINGS_EOF

echo ""
echo "✅ VS Code settings updated for agent support"

# Create agent quick reference file
QUICK_REF="$AGENTS_DIR/AGENTS_QUICK_REFERENCE.md"
cat > "$QUICK_REF" << 'QUICKREF_EOF'
# 🤖 GitHub Copilot Agents - Quick Reference

## How to Use Agents

In GitHub Copilot Chat, type `@agent-name` followed by your prompt to invoke a specific agent.

### Example Usage
```
@prompt-optimizer Help me write a function to parse JSON
@python-pro Create a FastAPI endpoint for user authentication
@typescript-pro Build a React component for data visualization
@security-auditor Review this code for vulnerabilities
```

## Available Agent Categories

### Development Agents
| Agent | Description |
|-------|-------------|
| `@python-pro` | Expert Python developer with async, type hints, and testing |
| `@typescript-pro` | Advanced TypeScript with full-stack type safety |
| `@javascript-pro` | Modern JavaScript patterns and optimization |
| `@golang-pro` | Go development with concurrency patterns |
| `@rust-engineer` | Systems programming with memory safety |

### Framework Specialists
| Agent | Description |
|-------|-------------|
| `@react-developer` | React 18+ with hooks and modern patterns |
| `@vue-expert` | Vue 3 Composition API and Nuxt |
| `@nextjs-developer` | Next.js with App Router and SSR |
| `@django-developer` | Django REST framework and ORM |
| `@laravel-specialist` | Laravel with Eloquent and API resources |

### DevOps & Infrastructure
| Agent | Description |
|-------|-------------|
| `@devops-engineer` | CI/CD, containers, and automation |
| `@terraform-engineer` | Infrastructure as code across clouds |
| `@kubernetes-specialist` | K8s deployments and Helm charts |
| `@cloud-architect` | Multi-cloud architecture design |
| `@sre-engineer` | Reliability, SLOs, and incident response |

### AI/ML Specialists
| Agent | Description |
|-------|-------------|
| `@ml-engineer` | Machine learning pipelines and models |
| `@data-scientist` | Data analysis and visualization |
| `@nlp-engineer` | Natural language processing |
| `@llm-architect` | LLM integration and prompt design |

### Quality & Security
| Agent | Description |
|-------|-------------|
| `@security-auditor` | Security assessments and compliance |
| `@code-reviewer` | Code quality and best practices |
| `@qa-expert` | Testing strategies and automation |

### Project & Process
| Agent | Description |
|-------|-------------|
| `@prompt-optimizer` | Optimize prompts for better AI responses |
| `@technical-writer` | Documentation and API references |
| `@scrum-master` | Agile facilitation and process |
| `@project-manager` | Project planning and tracking |

## Agent Files Location

All agent definitions are stored in:
```
.github/agents/*.agent.md
```

Each agent file contains:
- Name and description
- Specialized instructions
- Available tools
- Domain expertise

## Tips for Best Results

1. **Be specific**: Include context about your tech stack
2. **Chain agents**: Use output from one agent as input to another
3. **Provide examples**: Show desired output format when helpful
4. **Set constraints**: Specify requirements like "no external dependencies"

---
*Auto-generated by setup-agents.sh*
*Last updated: $(date)*
QUICKREF_EOF

echo "📖 Quick reference created: $QUICK_REF"

# Add agent aliases to bashrc
if ! grep -q "# GitHub Copilot Agents" ~/.bashrc 2>/dev/null; then
    cat >> ~/.bashrc << 'BASHRC_EOF'

# GitHub Copilot Agents
export AGENTS_DIR="/workspaces/sample-workflow/.github/agents"
alias list-agents='ls -1 $AGENTS_DIR/*.agent.md 2>/dev/null | xargs -I {} basename {} .agent.md | sort'
alias count-agents='ls -1 $AGENTS_DIR/*.agent.md 2>/dev/null | wc -l'
alias agent-info='cat $AGENTS_DIR/AGENTS_QUICK_REFERENCE.md'
BASHRC_EOF
    echo "🔗 Agent aliases added to ~/.bashrc"
fi

# Final summary
echo ""
echo "================================================"
echo "✅ GitHub Copilot Agents Setup Complete!"
echo "================================================"
echo ""
echo "📋 Summary:"
echo "   - Agents directory: $AGENTS_DIR"
echo "   - Total agents: $AGENT_COUNT"
echo "   - Registry file: $AGENT_REGISTRY"
echo "   - Quick reference: $QUICK_REF"
echo ""
echo "💡 Quick Commands:"
echo "   list-agents   - List all available agents"
echo "   count-agents  - Count total agents"
echo "   agent-info    - Show quick reference guide"
echo ""
echo "🚀 Usage: Type @agent-name in Copilot Chat"
echo ""
