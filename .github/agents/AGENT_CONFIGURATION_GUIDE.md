# GitHub Copilot Agents Configuration Guide

## Overview

This guide documents the complete setup and configuration of custom GitHub Copilot agents for the sample-workflow repository. Agents are specialized AI assistants that can be invoked in GitHub Copilot Chat using the `@agent-name` syntax.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Directory Structure](#directory-structure)
3. [Agent File Format](#agent-file-format)
4. [Automatic Setup Process](#automatic-setup-process)
5. [DevContainer Integration](#devcontainer-integration)
6. [Manual Configuration](#manual-configuration)
7. [Available Agents](#available-agents)
8. [Usage Examples](#usage-examples)
9. [Troubleshooting](#troubleshooting)
10. [Creating New Agents](#creating-new-agents)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     GitHub Codespaces Lifecycle                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ postCreate    │         │ postStart     │         │ postAttach    │
│ Command       │         │ Command       │         │ Command       │
└───────┬───────┘         └───────┬───────┘         └───────┬───────┘
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   setup-agents.sh       │
                    │   ─────────────────     │
                    │   • Validates agents    │
                    │   • Creates registry    │
                    │   • Updates VS Code     │
                    │   • Adds bash aliases   │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   .github/agents/       │
                    │   ─────────────────     │
                    │   • *.agent.md files    │
                    │   • .agent-registry.json│
                    │   • Quick reference     │
                    └─────────────────────────┘
```

---

## Directory Structure

```
sample-workflow/
├── .devcontainer/
│   ├── devcontainer.json          # Lifecycle hooks configuration
│   ├── setup-agents.sh            # Agent setup script
│   └── setup.sh                   # Main setup script
├── .github/
│   └── agents/
│       ├── *.agent.md             # Agent definition files (58 agents)
│       ├── .agent-registry.json   # Auto-generated agent registry
│       ├── AGENTS_QUICK_REFERENCE.md
│       └── AGENT_CONFIGURATION_GUIDE.md  # This file
└── .vscode/
    └── settings.json              # VS Code settings with agent config
```

---

## Agent File Format

Each agent is defined in a Markdown file with the `.agent.md` extension. The file can include optional YAML frontmatter for metadata.

### Basic Structure

```markdown
---
name: agent-name
description: Brief description of the agent's expertise
tools: Read, Write, Edit, Bash, Glob, Grep
---

You are a [role description] with expertise in [domains].

When invoked:

1. [First action]
2. [Second action]
3. [Third action]
4. [Fourth action]

[Agent-specific instructions and checklists...]
```

### Example: python-pro.agent.md

```markdown
---
name: python-pro
description: Expert Python developer specializing in modern Python 3.11+ development
tools: Read, Write, Edit, Bash, Glob, Grep
---

You are a senior Python developer with mastery of Python 3.11+ and its ecosystem...

When invoked:

1. Query context manager for existing Python codebase patterns
2. Review project structure and dependencies
3. Analyze code style and testing conventions
4. Implement solutions following Pythonic patterns

Python development checklist:

- Type hints for all function signatures
- PEP 8 compliance with black formatting
- Comprehensive docstrings (Google style)
- Test coverage exceeding 90%
```

---

## Automatic Setup Process

The agent configuration happens automatically through the DevContainer lifecycle. Here's the complete flow:

### 1. Codespace Creation (postCreateCommand)

```bash
bash .devcontainer/setup.sh && \
bash .devcontainer/ensure-dependencies.sh && \
bash .devcontainer/setup-jules.sh && \
bash .devcontainer/setup-agents.sh
```

### 2. Codespace Restart (postStartCommand)

```bash
bash .devcontainer/ensure-dependencies.sh && \
bash .devcontainer/setup-agents.sh && \
[Python environment setup...]
```

### 3. Terminal Attach (postAttachCommand)

```bash
bash .devcontainer/ensure-dependencies.sh && \
bash .devcontainer/setup-agents.sh && \
cd /workspaces/sample-workflow/servicenow-mcp && \
source .venv/bin/activate
```

---

## DevContainer Integration

### devcontainer.json Configuration

```jsonc
{
  "name": "ServiceNow MCP Workflow",

  // Lifecycle commands with agent setup
  "postCreateCommand": "bash .devcontainer/setup.sh && bash .devcontainer/ensure-dependencies.sh && bash .devcontainer/setup-jules.sh && bash .devcontainer/setup-agents.sh",
  "postStartCommand": "bash .devcontainer/ensure-dependencies.sh && bash .devcontainer/setup-agents.sh && ...",
  "postAttachCommand": "bash .devcontainer/ensure-dependencies.sh && bash .devcontainer/setup-agents.sh && ...",

  // VS Code customizations
  "customizations": {
    "vscode": {
      "settings": {
        "github.copilot.chat.codeGeneration.instructions": [
          {
            "text": "Custom agents are available in .github/agents/ directory. Use @agent-name to invoke specific agents."
          }
        ]
      }
    }
  }
}
```

---

## Manual Configuration

If you need to manually configure agents, follow these steps:

### Step 1: Create Agent Directory

```bash
mkdir -p /workspaces/sample-workflow/.github/agents
```

### Step 2: Create Agent Files

Create `.agent.md` files in the agents directory:

```bash
cat > /workspaces/sample-workflow/.github/agents/my-agent.agent.md << 'EOF'
---
name: my-agent
description: My custom agent description
tools: Read, Write, Edit, Bash
---

You are an expert in [your domain]...

When invoked:
1. [Action 1]
2. [Action 2]

[Additional instructions...]
EOF
```

### Step 3: Run Setup Script

```bash
bash /workspaces/sample-workflow/.devcontainer/setup-agents.sh
```

### Step 4: Verify Installation

```bash
# List all agents
list-agents

# Count agents
count-agents

# View quick reference
agent-info
```

---

## Available Agents

### Development Agents (Language-Specific)

| Agent                | Description               | Use Case                          |
| -------------------- | ------------------------- | --------------------------------- |
| `@python-pro`        | Python 3.11+ expert       | Backend, scripts, data processing |
| `@typescript-pro`    | TypeScript 5.0+ expert    | Full-stack, type-safe development |
| `@javascript-pro`    | Modern ES2023+ expert     | Frontend, Node.js                 |
| `@golang-pro`        | Go expert                 | High-performance systems          |
| `@rust-engineer`     | Rust systems programmer   | Memory-safe systems               |
| `@java-architect`    | Java enterprise architect | Enterprise applications           |
| `@csharp-developer`  | C# .NET developer         | .NET applications                 |
| `@cpp-pro`           | Modern C++20/23 expert    | Systems, performance-critical     |
| `@php-pro`           | PHP 8.3+ expert           | Web applications                  |
| `@kotlin-specialist` | Kotlin expert             | Android, multiplatform            |
| `@swift-expert`      | Swift 5.9+ expert         | iOS/macOS development             |
| `@elixir-expert`     | Elixir/Phoenix expert     | Concurrent systems                |

### Framework Specialists

| Agent                 | Description            | Framework      |
| --------------------- | ---------------------- | -------------- |
| `@nextjs-developer`   | Next.js 14+ expert     | Next.js, React |
| `@vue-expert`         | Vue 3 Composition API  | Vue, Nuxt      |
| `@angular-architect`  | Angular 15+ architect  | Angular        |
| `@django-developer`   | Django 4+ developer    | Django, DRF    |
| `@laravel-specialist` | Laravel 10+ specialist | Laravel, PHP   |
| `@flutter-expert`     | Flutter 3+ expert      | Flutter, Dart  |
| `@electron-pro`       | Electron expert        | Desktop apps   |
| `@dotnet-core-expert` | .NET Core specialist   | ASP.NET Core   |

### DevOps & Infrastructure

| Agent                   | Description          | Domain                   |
| ----------------------- | -------------------- | ------------------------ |
| `@devops-engineer`      | DevOps automation    | CI/CD, containers        |
| `@terraform-engineer`   | IaC expert           | Terraform, multi-cloud   |
| `@cloud-architect`      | Cloud architecture   | AWS, Azure, GCP          |
| `@sre-engineer`         | Site reliability     | SLOs, reliability        |
| `@ansible-expert`       | Ansible automation   | Configuration management |
| `@azure-infra-engineer` | Azure infrastructure | Azure services           |
| `@incident-responder`   | Incident management  | On-call, recovery        |

### AI/ML Specialists

| Agent             | Description      | Domain                     |
| ----------------- | ---------------- | -------------------------- |
| `@ml-engineer`    | ML pipelines     | Model training, deployment |
| `@data-scientist` | Data analysis    | Statistics, visualization  |
| `@nlp-engineer`   | NLP specialist   | Language processing        |
| `@llm-architect`  | LLM integration  | Prompts, RAG               |
| `@mlops-engineer` | MLOps automation | Model lifecycle            |
| `@data-engineer`  | Data pipelines   | ETL, data warehousing      |

### Quality & Security

| Agent               | Description         | Focus                     |
| ------------------- | ------------------- | ------------------------- |
| `@security-auditor` | Security assessment | Vulnerability, compliance |
| `@code-reviewer`    | Code review         | Quality, best practices   |
| `@prompt-optimizer` | Prompt engineering  | AI prompt optimization    |

### Project & Process

| Agent               | Description        | Role                |
| ------------------- | ------------------ | ------------------- |
| `@technical-writer` | Documentation      | API docs, guides    |
| `@scrum-master`     | Agile facilitation | Scrum, ceremonies   |
| `@project-manager`  | Project planning   | Timeline, resources |
| `@ux-researcher`    | UX research        | User insights       |
| `@ui-designer`      | UI/UX design       | Visual design       |

### Coordination Agents

| Agent                      | Description              | Purpose               |
| -------------------------- | ------------------------ | --------------------- |
| `@agent-organizer`         | Agent coordination       | Multi-agent workflows |
| `@multi-agent-coordinator` | Distributed coordination | Complex tasks         |
| `@workflow-orchestrator`   | Workflow management      | Process automation    |
| `@context-manager`         | Context management       | State tracking        |
| `@task-distributor`        | Task distribution        | Load balancing        |

---

## Usage Examples

### Basic Usage

```
@python-pro Create an async API client for the ServiceNow REST API
```

### With Context

```
@typescript-pro I'm using Next.js 14 with App Router. Create a server component
that fetches user data and displays it in a table with sorting.
```

### Chain Agents

```
@prompt-optimizer Improve this prompt: "help me write code for login"

[After optimization]

@python-pro [paste optimized prompt]
```

### Security Review

```
@security-auditor Review this authentication code for vulnerabilities:
[paste code]
```

### Multi-Agent Workflow

```
@agent-organizer I need to:
1. Design a REST API
2. Implement it in Python
3. Add authentication
4. Write documentation

Which agents should handle each part?
```

---

## Troubleshooting

### Agents Not Loading

**Symptom:** Agents don't appear in Copilot Chat suggestions

**Solution:**

```bash
# Re-run agent setup
bash /workspaces/sample-workflow/.devcontainer/setup-agents.sh

# Verify agents exist
ls -la /workspaces/sample-workflow/.github/agents/*.agent.md

# Check registry
cat /workspaces/sample-workflow/.github/agents/.agent-registry.json
```

### Agent Not Recognized

**Symptom:** `@agent-name` doesn't invoke the correct behavior

**Solution:**

1. Verify agent file exists: `ls .github/agents/agent-name.agent.md`
2. Check file format has correct frontmatter
3. Reload VS Code window: `Ctrl+Shift+P` → "Developer: Reload Window"

### Setup Script Fails

**Symptom:** `setup-agents.sh` throws errors

**Solution:**

```bash
# Check permissions
chmod +x /workspaces/sample-workflow/.devcontainer/setup-agents.sh

# Run with debug output
bash -x /workspaces/sample-workflow/.devcontainer/setup-agents.sh

# Check for syntax errors
bash -n /workspaces/sample-workflow/.devcontainer/setup-agents.sh
```

### Agents Not Persisting

**Symptom:** Agents disappear after Codespace restart

**Solution:**

1. Verify `devcontainer.json` includes `setup-agents.sh` in all lifecycle hooks
2. Check that agent files are committed to the repository
3. Re-run: `bash .devcontainer/setup-agents.sh`

---

## Creating New Agents

### Step 1: Create Agent File

```bash
cat > .github/agents/my-new-agent.agent.md << 'EOF'
---
name: my-new-agent
description: Expert in [your domain] specializing in [specific skills]
tools: Read, Write, Edit, Bash, Glob, Grep
---

You are a senior [role] with expertise in [domains]. Your focus spans
[area 1], [area 2], and [area 3] with emphasis on [key focus].

When invoked:

1. Query context for existing codebase patterns
2. Review project structure and requirements
3. Analyze current implementation
4. Implement solutions following best practices

[Your domain] checklist:

- [Requirement 1]
- [Requirement 2]
- [Requirement 3]
- [Requirement 4]

[Additional specialized sections...]
EOF
```

### Step 2: Update Registry

```bash
bash /workspaces/sample-workflow/.devcontainer/setup-agents.sh
```

### Step 3: Verify

```bash
# Check agent appears in list
list-agents | grep my-new-agent

# Test agent
# In Copilot Chat: @my-new-agent Hello, what's your specialty?
```

### Step 4: Commit Changes

```bash
git add .github/agents/my-new-agent.agent.md
git commit -m "Add my-new-agent for [purpose]"
git push
```

---

## Files Reference

| File                                       | Purpose            | Auto-Generated        |
| ------------------------------------------ | ------------------ | --------------------- |
| `.devcontainer/setup-agents.sh`            | Agent setup script | No                    |
| `.devcontainer/devcontainer.json`          | Lifecycle hooks    | No                    |
| `.github/agents/*.agent.md`                | Agent definitions  | No                    |
| `.github/agents/.agent-registry.json`      | Agent registry     | Yes                   |
| `.github/agents/AGENTS_QUICK_REFERENCE.md` | Quick reference    | Yes                   |
| `.vscode/settings.json`                    | VS Code settings   | Yes (by setup script) |

---

## Quick Commands Reference

| Command                              | Description                    |
| ------------------------------------ | ------------------------------ |
| `list-agents`                        | List all available agent names |
| `count-agents`                       | Count total number of agents   |
| `agent-info`                         | Display quick reference guide  |
| `bash .devcontainer/setup-agents.sh` | Re-run agent setup             |

---

## Version History

| Date       | Version | Changes                                |
| ---------- | ------- | -------------------------------------- |
| 2026-01-15 | 1.0.0   | Initial agent configuration setup      |
| 2026-01-15 | 1.1.0   | Added 58 specialized agents            |
| 2026-01-15 | 1.2.0   | Integrated with DevContainer lifecycle |

---

_Document generated: January 15, 2026_
_Repository: selvar2/sample-workflow_
_Branch: workflowag5_
