# System Architecture Documentation

## ServiceNow-Redshift Integration Platform

**Version:** 1.0  
**Date:** December 2025  
**Purpose:** Gen AI Event Documentation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture Diagrams](#3-architecture-diagrams)
4. [Component Details](#4-component-details)
5. [Data Flow](#5-data-flow)
6. [Integration Patterns](#6-integration-patterns)
7. [Security Architecture](#7-security-architecture)
8. [Deployment Architecture](#8-deployment-architecture)
9. [Directory Structure](#9-directory-structure)
10. [Key Classes and Modules](#10-key-classes-and-modules)

---

## 1. Executive Summary

This platform provides an automated integration between **ServiceNow** (IT Service Management) and **AWS Redshift** (Data Warehouse) using the **Model Context Protocol (MCP)**. The system enables:

- **Automated Incident Processing**: Reading and parsing ServiceNow incidents
- **Intelligent Instruction Parsing**: Extracting database operations from natural language
- **AWS Redshift Operations**: Executing database user management via Data API
- **Real-time Monitoring**: Continuous detection of new incidents
- **Web-based Management**: User-friendly interface for operations and monitoring

### Key Capabilities

| Capability | Description |
|------------|-------------|
| Incident Detection | Automatically detects newly created ServiceNow incidents |
| Instruction Parsing | Uses regex patterns to extract Redshift operations from incident descriptions |
| Database Operations | Creates/manages database users via AWS Redshift Data API |
| Status Updates | Automatically updates incidents with operation results |
| Multi-incident Processing | Handles both single and batch incident processing |
| Dry Run Mode | Test operations without executing actual changes |

---

## 2. System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE LAYER                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         Flask Web Application                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │   │
│  │  │    Login     │  │  Dashboard   │  │   Monitor    │  │   History   │  │   │
│  │  │    Page      │  │    View      │  │   Control    │  │    View     │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            APPLICATION LAYER                                     │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────────┐   │
│  │   ServiceNow MCP Server     │  │      Incident Processor                 │   │
│  │  ┌───────────────────────┐  │  │  ┌─────────────────────────────────┐   │   │
│  │  │    Tool Registry      │  │  │  │      IncidentProcessor          │   │   │
│  │  │  (80+ MCP Tools)      │  │  │  │  ┌───────────┐ ┌────────────┐   │   │   │
│  │  └───────────────────────┘  │  │  │  │  Parser   │ │  Executor  │   │   │   │
│  │  ┌───────────────────────┐  │  │  │  └───────────┘ └────────────┘   │   │   │
│  │  │   Auth Manager        │  │  │  └─────────────────────────────────┘   │   │
│  │  │  (Basic/OAuth/API)    │  │  │  ┌─────────────────────────────────┐   │   │
│  │  └───────────────────────┘  │  │  │      ServiceNowClient           │   │   │
│  │  ┌───────────────────────┐  │  │  └─────────────────────────────────┘   │   │
│  │  │   Config Manager      │  │  │  ┌─────────────────────────────────┐   │   │
│  │  └───────────────────────┘  │  │  │      RedshiftClient             │   │   │
│  └─────────────────────────────┘  │  └─────────────────────────────────┘   │   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
┌─────────────────────────────────┐    ┌─────────────────────────────────────────┐
│         SERVICENOW              │    │              AWS CLOUD                   │
│  ┌───────────────────────────┐  │    │  ┌─────────────────────────────────┐    │
│  │     REST Table API        │  │    │  │      Redshift Data API          │    │
│  │     /api/now/table/*      │  │    │  │  ┌───────────────────────────┐  │    │
│  └───────────────────────────┘  │    │  │  │  execute_statement        │  │    │
│                                 │    │  │  │  describe_statement       │  │    │
│  Tables:                        │    │  │  │  get_statement_result     │  │    │
│  • incident                     │    │  │  └───────────────────────────┘  │    │
│  • change_request               │    │  └─────────────────────────────────┘    │
│  • sc_cat_item                  │    │                                         │
│  • sys_user                     │    │  ┌─────────────────────────────────┐    │
│  • kb_knowledge                 │    │  │    Redshift Cluster             │    │
│  • wf_workflow                  │    │  │    (redshift-cluster-1)         │    │
│  • ... (29 tables)              │    │  │    Database: dev                │    │
│                                 │    │  └─────────────────────────────────┘    │
└─────────────────────────────────┘    └─────────────────────────────────────────┘
```

---

## 3. Architecture Diagrams

### 3.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SERVICENOW MCP PLATFORM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        WEB UI LAYER (Flask)                          │   │
│  │                                                                       │   │
│  │   app.py ─────┬──── templates/index.html (Dashboard)                 │   │
│  │               ├──── templates/login.html (Authentication)            │   │
│  │               └──── Static Assets (Bootstrap 5.3.2)                  │   │
│  │                                                                       │   │
│  │   Features:                                                           │   │
│  │   • Session-based authentication                                      │   │
│  │   • Real-time SSE event streaming                                     │   │
│  │   • REST API endpoints                                                │   │
│  │   • Processing history persistence                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     PROCESSING LAYER (Python)                        │   │
│  │                                                                       │   │
│  │                                        │   │
│  │   ┌─────────────────┐ ┌─────────────────┐ ┌──────────────────────┐  │   │
│  │   │     Config      │ │ ServiceNowClient│ │   RedshiftClient     │  │   │
│  │   │  (Environment)  │ │  (REST API)     │ │   (boto3 SDK)        │  │   │
│  │   └─────────────────┘ └─────────────────┘ └──────────────────────┘  │   │
│  │   ┌─────────────────┐ ┌─────────────────────────────────────────┐   │   │
│  │   │ IncidentParser  │ │         IncidentProcessor               │   │   │
│  │   │ (Regex Patterns)│ │  (Orchestrates full workflow)           │   │   │
│  │   └─────────────────┘ └─────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      MCP SERVER LAYER (src/)                         │   │
│  │                                                                       │   │
│  │   servicenow_mcp/                                                     │   │
│  │   ├── server.py ──────────── MCP Protocol Implementation             │   │
│  │   ├── server_sse.py ──────── SSE Transport Layer                     │   │
│  │   ├── cli.py ─────────────── Command Line Interface                  │   │
│  │   │                                                                   │   │
│  │   ├── auth/                                                           │   │
│  │   │   └── auth_manager.py ── Authentication (Basic/OAuth/API Key)    │   │
│  │   │                                                                   │   │
│  │   ├── utils/                                                          │   │
│  │   │   ├── config.py ──────── Configuration Models (Pydantic)         │   │
│  │   │   └── tool_utils.py ──── Tool Registration & Discovery           │   │
│  │   │                                                                   │   │
│  │   └── tools/ ─────────────── 80+ MCP Tool Implementations            │   │
│  │       ├── incident_tools.py                                          │   │
│  │       ├── change_tools.py                                            │   │
│  │       ├── catalog_tools.py                                           │   │
│  │       ├── user_tools.py                                              │   │
│  │       ├── workflow_tools.py                                          │   │
│  │       ├── knowledge_base.py                                          │   │
│  │       └── ... (12 tool modules)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Workflow Processing Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INCIDENT PROCESSING WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

   ┌──────────┐
   │   User   │
   └────┬─────┘
        │ Creates Incident
        ▼
┌───────────────────┐
│    ServiceNow     │
│  Incident Record  │
│                   │
│  Description:     │
│  "Create user     │
│   user11 in       │
│   redshift        │
│   cluster 1"      │
└────────┬──────────┘
         │
         ▼
┌───────────────────────────────────────────────────────────────────┐
│                     INCIDENT PROCESSOR                             │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Step 1: FETCH INCIDENT                                       │  │
│  │ ServiceNowClient.get_incident(incident_number)               │  │
│  │ GET /api/now/table/incident?number=INC0010015                │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Step 2: CHECK IF PROCESSED                                   │  │
│  │ ServiceNowClient.is_already_processed(incident)              │  │
│  │ Check work_notes for completion indicators                   │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Step 3: PARSE INCIDENT                                       │  │
│  │ IncidentParser.parse_incident(incident)                      │  │
│  │                                                              │  │
│  │ Regex Patterns:                                              │  │
│  │ • Username: r'user\s+named\s+(\w+)'                         │  │
│  │ • Cluster:  r'cluster[:\s-]*(\d+)'                          │  │
│  │                                                              │  │
│  │ Result: {username: "user11", cluster: "redshift-cluster-1"} │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Step 4: EXECUTE REDSHIFT OPERATIONS                          │  │
│  │                                                              │  │
│  │ RedshiftClient.user_exists(username)                         │  │
│  │ → SQL: SELECT usename FROM pg_user WHERE usename='user11'   │  │
│  │                                                              │  │
│  │ RedshiftClient.create_user(username)                         │  │
│  │ → SQL: CREATE USER user11 PASSWORD DISABLE                   │  │
│  │                                                              │  │
│  │ RedshiftClient.verify_user(username)                         │  │
│  │ → SQL: SELECT * FROM pg_user WHERE usename='user11'         │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Step 5: UPDATE INCIDENT                                      │  │
│  │ ServiceNowClient.add_work_note(incident_number, result)      │  │
│  │ PUT /api/now/table/incident/{sys_id}                         │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌───────────────────┐
│    ServiceNow     │
│  Updated Incident │
│                   │
│  Work Notes:      │
│  "✓ TASK          │
│   COMPLETED..."   │
│  State: Resolved  │
└───────────────────┘
```

### 3.3 MCP Server Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MCP SERVER ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

                           ┌─────────────────┐
                           │   AI Assistant  │
                           │    (Claude)     │
                           └────────┬────────┘
                                    │ MCP Protocol
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ServiceNowMCP Server                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      Transport Layer                                   │ │
│  │   ┌─────────────────┐          ┌─────────────────────────────────┐    │ │
│  │   │   stdio (CLI)   │          │   SSE (HTTP Server)             │    │ │
│  │   │   cli.py        │          │   server_sse.py                 │    │ │
│  │   │                 │          │   Starlette + Uvicorn           │    │ │
│  │   └─────────────────┘          └─────────────────────────────────┘    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        MCP Protocol Handler                            │ │
│  │                          (server.py)                                   │ │
│  │                                                                        │ │
│  │   ┌─────────────────────────────────────────────────────────────┐     │ │
│  │   │  list_tools() → Returns available tool definitions          │     │ │
│  │   │  call_tool(name, args) → Executes tool and returns result   │     │ │
│  │   └─────────────────────────────────────────────────────────────┘     │ │
│  │                                                                        │ │
│  │   ┌─────────────────────────────────────────────────────────────┐     │ │
│  │   │                  Tool Package System                         │     │ │
│  │   │  config/tool_packages.yaml                                   │     │ │
│  │   │  MCP_TOOL_PACKAGE env var selects active package            │     │ │
│  │   │                                                              │     │ │
│  │   │  Packages: full, service_desk, catalog_builder,              │     │ │
│  │   │           change_coordinator, platform_developer, etc.       │     │ │
│  │   └─────────────────────────────────────────────────────────────┘     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         Tool Registry                                  │ │
│  │                       (utils/tool_utils.py)                           │ │
│  │                                                                        │ │
│  │   get_tool_definitions() → Returns mapping of:                        │ │
│  │     tool_name → (impl_func, params_model, return_type, description)   │ │
│  │                                                                        │ │
│  │   80+ registered tools across 12 modules                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        Tool Modules (tools/)                          │ │
│  │                                                                        │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │ │
│  │  │ incident_tools   │  │  change_tools    │  │  catalog_tools   │    │ │
│  │  │ • create         │  │  • create        │  │  • list_items    │    │ │
│  │  │ • update         │  │  • update        │  │  • get_item      │    │ │
│  │  │ • resolve        │  │  • approve       │  │  • create        │    │ │
│  │  │ • list           │  │  • reject        │  │  • update        │    │ │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘    │ │
│  │                                                                        │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │ │
│  │  │   user_tools     │  │ workflow_tools   │  │ knowledge_base   │    │ │
│  │  │ • create_user    │  │ • list           │  │ • create_article │    │ │
│  │  │ • update_user    │  │ • create         │  │ • publish        │    │ │
│  │  │ • create_group   │  │ • activate       │  │ • list           │    │ │
│  │  │ • add_members    │  │ • add_activity   │  │ • get            │    │ │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘    │ │
│  │                                                                        │ │
│  │  + changeset_tools, story_tools, epic_tools, project_tools,           │ │
│  │    scrum_task_tools, script_include_tools, catalog_variables          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     Authentication Layer                               │ │
│  │                     (auth/auth_manager.py)                            │ │
│  │                                                                        │ │
│  │   AuthManager                                                          │ │
│  │   ├── Basic Auth (username:password → Base64)                         │ │
│  │   ├── OAuth 2.0 (client credentials → token)                          │ │
│  │   └── API Key (custom header)                                         │ │
│  │                                                                        │ │
│  │   get_headers() → {"Authorization": "...", "Content-Type": "..."}     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Details

### 4.1 Web UI Layer (`web_ui/`)

| File | Purpose |
|------|---------|
| `app.py` | Flask application with routing, authentication, SSE streaming |
| `templates/index.html` | Main dashboard with Bootstrap 5.3.2 UI |
| `templates/login.html` | Authentication page |
| `run_server.py` | Production server startup with Gunicorn |

**Key Features:**
- Session-based authentication (APP_USERS environment variable)
- Real-time Server-Sent Events (SSE) for live updates
- Processing history persistence (JSON file)
- Responsive design with Bootstrap 5.3.2

### 4.2 Processing Layer (`process_servicenow_redshift.py`)

| Class | Responsibility |
|-------|----------------|
| `Config` | Environment variable management |
| `ServiceNowClient` | ServiceNow REST API interactions |
| `RedshiftClient` | AWS Redshift Data API operations |
| `IncidentParser` | Regex-based instruction extraction |
| `IncidentProcessor` | Main orchestration logic |

### 4.3 MCP Server Layer (`src/servicenow_mcp/`)

| Module | Purpose |
|--------|---------|
| `server.py` | Core MCP protocol implementation |
| `server_sse.py` | SSE transport for web clients |
| `cli.py` | Command-line interface |
| `auth/auth_manager.py` | Multi-method authentication |
| `utils/config.py` | Pydantic configuration models |
| `utils/tool_utils.py` | Tool registration and discovery |
| `tools/*.py` | 80+ tool implementations |

### 4.4 Tool Modules

| Module | Tools | ServiceNow Table |
|--------|-------|------------------|
| `incident_tools.py` | 6 | incident |
| `change_tools.py` | 8 | change_request, change_task |
| `catalog_tools.py` | 7 | sc_cat_item, sc_category |
| `user_tools.py` | 9 | sys_user, sys_user_group |
| `workflow_tools.py` | 12 | wf_workflow, wf_activity |
| `knowledge_base.py` | 9 | kb_knowledge, kb_knowledge_base |
| `changeset_tools.py` | 7 | sys_update_set |
| `story_tools.py` | 6 | rm_story |
| `epic_tools.py` | 3 | rm_epic |
| `project_tools.py` | 3 | pm_project |
| `scrum_task_tools.py` | 3 | rm_scrum_task |
| `script_include_tools.py` | 6 | sys_script_include |

---

## 5. Data Flow

### 5.1 Single Incident Processing Flow

```
User → ServiceNow UI → Create Incident
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │         Web UI Dashboard              │
        │     "Process Single Incident"         │
        └───────────────────┬───────────────────┘
                            │ POST /api/process
                            ▼
        ┌───────────────────────────────────────┐
        │      IncidentProcessor.process()      │
        │                                       │
        │  1. Fetch incident from ServiceNow    │
        │  2. Check if already processed        │
        │  3. Parse description (regex)         │
        │  4. Execute Redshift operations       │
        │  5. Update incident with results      │
        └───────────────────┬───────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌──────────────────────┐    ┌──────────────────────┐
│     ServiceNow       │    │    AWS Redshift      │
│  • GET incident      │    │  • execute_statement │
│  • PUT work_notes    │    │  • describe_statement│
│  • PATCH state       │    │  • get_result        │
└──────────────────────┘    └──────────────────────┘
```

### 5.2 Continuous Monitoring Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MONITORING MODE                               │
│                                                                  │
│   ┌─────────────┐                                               │
│   │   Start     │                                               │
│   │  Monitor    │                                               │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    Poll Loop                             │   │
│   │                                                          │   │
│   │   while monitoring:                                      │   │
│   │       incidents = ServiceNow.list_incidents(from_date)   │   │
│   │       for incident in incidents:                         │   │
│   │           if not processed and is_redshift_related:      │   │
│   │               process_incident(incident)                 │   │
│   │       sleep(POLL_INTERVAL)  # default: 10 seconds        │   │
│   │                                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────┐                                               │
│   │   Stop      │                                               │
│   │  Monitor    │                                               │
│   └─────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Integration Patterns

### 6.1 ServiceNow Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                  SERVICENOW REST API PATTERN                     │
│                                                                  │
│   Request:                                                       │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  GET {instance_url}/api/now/table/{table}               │   │
│   │  Headers:                                                │   │
│   │    Authorization: Basic {base64(user:pass)}             │   │
│   │    Accept: application/json                              │   │
│   │    Content-Type: application/json                        │   │
│   │  Params:                                                 │   │
│   │    sysparm_query: {encoded_query}                        │   │
│   │    sysparm_limit: {number}                               │   │
│   │    sysparm_display_value: true                           │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Response:                                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  {                                                       │   │
│   │    "result": [                                           │   │
│   │      {                                                   │   │
│   │        "sys_id": "...",                                  │   │
│   │        "number": "INC0010001",                           │   │
│   │        "short_description": "...",                       │   │
│   │        ...                                               │   │
│   │      }                                                   │   │
│   │    ]                                                     │   │
│   │  }                                                       │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 AWS Redshift Integration

```
┌─────────────────────────────────────────────────────────────────┐
│               AWS REDSHIFT DATA API PATTERN                      │
│                                                                  │
│   Step 1: Execute Statement                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  client.execute_statement(                               │   │
│   │      ClusterIdentifier='redshift-cluster-1',             │   │
│   │      Database='dev',                                     │   │
│   │      DbUser='example',                                   │   │
│   │      Sql='CREATE USER user11 PASSWORD DISABLE;'          │   │
│   │  )                                                       │   │
│   │  → Returns: {"Id": "statement-id-xxx"}                   │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Step 2: Poll for Completion                                    │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  while status not in ['FINISHED', 'FAILED']:             │   │
│   │      response = client.describe_statement(Id=stmt_id)    │   │
│   │      status = response['Status']                         │   │
│   │      sleep(2)                                            │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Step 3: Get Results (if needed)                                │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  result = client.get_statement_result(Id=stmt_id)        │   │
│   │  → Returns: {"Records": [...], "TotalNumRows": n}        │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Security Architecture

### 7.1 Authentication Methods

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION ARCHITECTURE                   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    Web UI Authentication                 │   │
│   │                                                          │   │
│   │   Environment Variable: APP_USERS                        │   │
│   │   Format: username:password,username2:password2          │   │
│   │                                                          │   │
│   │   Storage: Session-based (Flask secret key)              │   │
│   │   Hashing: PBKDF2-HMAC-SHA256 (100,000 iterations)      │   │
│   │   Session Lifetime: 24 hours                             │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                  ServiceNow Authentication               │   │
│   │                                                          │   │
│   │   Option 1: Basic Auth                                   │   │
│   │     Authorization: Basic {base64(username:password)}     │   │
│   │                                                          │   │
│   │   Option 2: OAuth 2.0                                    │   │
│   │     Token URL: {instance}/oauth_token.do                 │   │
│   │     Grant Type: password                                 │   │
│   │                                                          │   │
│   │   Option 3: API Key                                      │   │
│   │     Custom Header: X-ServiceNow-API-Key                  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    AWS Authentication                    │   │
│   │                                                          │   │
│   │   Method: IAM Credentials (boto3 credential chain)       │   │
│   │   Options:                                               │   │
│   │     • Environment variables (AWS_ACCESS_KEY_ID, etc.)    │   │
│   │     • IAM Role (EC2/ECS/Lambda)                          │   │
│   │     • AWS credentials file (~/.aws/credentials)          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Security Best Practices

| Layer | Practice |
|-------|----------|
| **Environment** | Secrets in environment variables, not code |
| **Password Storage** | PBKDF2 hashing with random salt |
| **Sessions** | Cryptographically secure session keys |
| **API** | HTTPS only, token-based auth |
| **AWS** | IAM roles preferred over access keys |
| **Git** | `.env` files in `.gitignore` |

---

## 8. Deployment Architecture

### 8.1 Local Development

```
┌─────────────────────────────────────────────────────────────────┐
│                   LOCAL DEVELOPMENT SETUP                        │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                GitHub Codespaces                         │   │
│   │                                                          │   │
│   │   Base Image: python:3.12-bullseye                       │   │
│   │                                                          │   │
│   │   Features:                                              │   │
│   │   • AWS CLI                                              │   │
│   │   • Docker-in-Docker                                     │   │
│   │   • Git                                                  │   │
│   │                                                          │   │
│   │   VS Code Extensions:                                    │   │
│   │   • Python, Pylance, Debugpy                             │   │
│   │   • Jupyter, YAML, Docker                                │   │
│   │                                                          │   │
│   │   Virtual Environment: .venv/                            │   │
│   │   Port Forwarding: 5000, 8000, 3000                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Startup Command:                                               │
│   source .venv/bin/activate && \                                │
│   APP_USERS='admin:pass' python web_ui/app.py                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Production Deployment (Render.com)

```
┌─────────────────────────────────────────────────────────────────┐
│                   RENDER.COM DEPLOYMENT                          │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    Web Service                           │   │
│   │                                                          │   │
│   │   Name: servicenow-incident-processor                    │   │
│   │   Runtime: Python 3.11                                   │   │
│   │   Plan: Free                                             │   │
│   │                                                          │   │
│   │   Build Command:                                         │   │
│   │     pip install -r requirements.txt                      │   │
│   │     pip install -r web_ui/requirements.txt               │   │
│   │                                                          │   │
│   │   Start Command:                                         │   │
│   │     cd web_ui && gunicorn \                              │   │
│   │       --bind 0.0.0.0:$PORT \                             │   │
│   │       --workers 2 \                                      │   │
│   │       --threads 2 \                                      │   │
│   │       --timeout 120 \                                    │   │
│   │       app:app                                            │   │
│   │                                                          │   │
│   │   Health Check: /api/status                              │   │
│   │   Auto Deploy: Enabled                                   │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Environment Variables:                                         │
│   • SERVICENOW_INSTANCE_URL                                      │
│   • SERVICENOW_USERNAME                                          │
│   • SERVICENOW_PASSWORD                                          │
│   • AWS_REGION (us-east-1)                                       │
│   • AWS_ACCESS_KEY_ID                                            │
│   • AWS_SECRET_ACCESS_KEY                                        │
│   • REDSHIFT_DATABASE (dev)                                      │
│   • REDSHIFT_DB_USER (awsuser)                                   │
│   • DRY_RUN (false)                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
RUN pip install -e .
EXPOSE 8080
CMD ["servicenow-mcp"]
```

---

## 9. Directory Structure

```
servicenow-mcp/
├── src/                              # MCP Server Source Code
│   └── servicenow_mcp/
│       ├── __init__.py
│       ├── server.py                 # Core MCP Server
│       ├── server_sse.py             # SSE Transport
│       ├── cli.py                    # Command Line Interface
│       ├── auth/
│       │   ├── __init__.py
│       │   └── auth_manager.py       # Authentication Manager
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── config.py             # Configuration Models
│       │   └── tool_utils.py         # Tool Registration
│       └── tools/                    # Tool Implementations (80+)
│           ├── __init__.py
│           ├── incident_tools.py
│           ├── change_tools.py
│           ├── catalog_tools.py
│           ├── catalog_variables.py
│           ├── catalog_optimization.py
│           ├── user_tools.py
│           ├── workflow_tools.py
│           ├── knowledge_base.py
│           ├── changeset_tools.py
│           ├── story_tools.py
│           ├── epic_tools.py
│           ├── project_tools.py
│           ├── scrum_task_tools.py
│           └── script_include_tools.py
│
├── web_ui/                           # Flask Web Application
│   ├── __init__.py
│   ├── app.py                        # Main Flask App
│   ├── run_server.py                 # Production Server
│   ├── requirements.txt              # Web UI Dependencies
│   └── templates/
│       ├── index.html                # Dashboard
│       └── login.html                # Login Page
│
├── config/
│   └── tool_packages.yaml            # MCP Tool Package Definitions
│
├── tests/                            # Unit Tests
│   ├── test_incident_tools.py
│   ├── test_change_tools.py
│   ├── test_catalog_tools.py
│   └── ... (20+ test files)
│
├── scripts/                          # Utility Scripts
│   ├── setup_auth.py
│   ├── setup_oauth.py
│   ├── test_connection.py
│   └── check_pdi_status.py
│
├── examples/                         # Demo Scripts
│   ├── claude_incident_demo.py
│   ├── change_management_demo.py
│   └── workflow_management_demo.py
│
├── docs/                             # Documentation
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md               # This Document
│   ├── incident_management.md
│   └── ...
│
├── process_servicenow_redshift.py    # Main Processor Script
├── pyproject.toml                    # Project Configuration
├── requirements.txt                  # Python Dependencies
├── Dockerfile                        # Container Definition
├── render.yaml                       # Render.com Deployment
└── README.md                         # Project Overview
```

---

## 10. Key Classes and Modules

### 10.1 Core Classes

| Class | Module | Description |
|-------|--------|-------------|
| `ServiceNowMCP` | `server.py` | Main MCP server implementation |
| `AuthManager` | `auth_manager.py` | Handles all authentication methods |
| `ServerConfig` | `config.py` | Pydantic configuration model |
| `IncidentProcessor` | `process_servicenow_redshift.py` | Orchestrates incident workflow |
| `ServiceNowClient` | `process_servicenow_redshift.py` | ServiceNow REST API client |
| `RedshiftClient` | `process_servicenow_redshift.py` | AWS Redshift Data API client |
| `IncidentParser` | `process_servicenow_redshift.py` | Regex-based instruction parser |

### 10.2 Pydantic Models

| Model | Purpose |
|-------|---------|
| `AuthConfig` | Authentication configuration |
| `BasicAuthConfig` | Basic auth credentials |
| `OAuthConfig` | OAuth 2.0 settings |
| `ApiKeyConfig` | API key settings |
| `ServerConfig` | Full server configuration |
| `*Params` | Tool parameter models (per tool) |
| `*Response` | Tool response models (per tool) |

### 10.3 API Endpoints (Web UI)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Dashboard page |
| `/login` | GET/POST | Authentication |
| `/logout` | GET | End session |
| `/api/status` | GET | Health check |
| `/api/process` | POST | Process single incident |
| `/api/monitor/start` | POST | Start continuous monitoring |
| `/api/monitor/stop` | POST | Stop monitoring |
| `/api/incidents` | GET | List processed incidents |
| `/api/events` | GET | SSE event stream |

---

## Summary

This architecture provides a robust, scalable platform for integrating ServiceNow incident management with AWS Redshift database operations. The modular design allows for:

- **Extensibility**: Easy addition of new MCP tools
- **Flexibility**: Multiple deployment options (local, Docker, cloud)
- **Security**: Multi-layer authentication and secure credential handling
- **Observability**: Real-time monitoring and event streaming
- **Maintainability**: Clear separation of concerns and comprehensive testing

---

*Architecture Document - Gen AI Event December 2025*
