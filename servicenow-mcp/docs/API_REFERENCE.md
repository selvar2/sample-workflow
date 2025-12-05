# API Reference Documentation

This document lists all APIs used in the ServiceNow-Redshift Integration project for the Gen AI Event.

## Overview

The system integrates two primary services:
1. **ServiceNow MCP Server** - For incident management and ITSM operations
2. **AWS Redshift Data API** - For database operations

---

## 1. ServiceNow REST API (Table API)

Base URL: `{instance_url}/api/now/table/{table_name}`

### Incident Management

| API Endpoint | HTTP Methods | Purpose |
|--------------|--------------|---------|
| `/api/now/table/incident` | GET, POST, PATCH | Create, read, update incidents |

**Key Operations:**
- Create new incidents with short description, description, priority, etc.
- Read incident details by incident number or sys_id
- Update incident state, work notes, resolution notes
- List incidents with filtering and pagination

### Change Management

| API Endpoint | HTTP Methods | Purpose |
|--------------|--------------|---------|
| `/api/now/table/change_request` | GET, POST, PATCH | Create, read, update change requests |
| `/api/now/table/change_task` | GET, POST | Manage change tasks |
| `/api/now/table/sysapproval_approver` | GET, PATCH | Manage approvals |

### Service Catalog

| API Endpoint | HTTP Methods | Purpose |
|--------------|--------------|---------|
| `/api/now/table/sc_request` | POST | Create service catalog requests (REQ) |
| `/api/now/table/sc_req_item` | POST | Create requested items (RITM) |
| `/api/now/table/sc_cat_item` | GET, PATCH | Manage service catalog items |
| `/api/now/table/sc_category` | GET, POST, PATCH | Manage catalog categories |
| `/api/now/table/item_option_new` | GET, POST, PATCH | Manage catalog variables |

### User Management

| API Endpoint | HTTP Methods | Purpose |
|--------------|--------------|---------|
| `/api/now/table/sys_user` | GET, POST, PATCH | Manage users |
| `/api/now/table/sys_user_group` | GET, POST, PATCH | Manage user groups |
| `/api/now/table/sys_user_grmember` | GET, POST | Manage group membership |
| `/api/now/table/sys_user_has_role` | GET, POST | Manage user roles |
| `/api/now/table/sys_user_role` | GET | Query available roles |

### Knowledge Base

| API Endpoint | HTTP Methods | Purpose |
|--------------|--------------|---------|
| `/api/now/table/kb_knowledge` | GET, POST, PATCH | Manage knowledge articles |
| `/api/now/table/kb_knowledge_base` | GET, POST | Manage knowledge bases |
| `/api/now/table/kb_category` | GET | Query KB categories |

### Workflow Management

| API Endpoint | HTTP Methods | Purpose |
|--------------|--------------|---------|
| `/api/now/table/wf_workflow` | GET, POST, PATCH, DELETE | Manage workflows |
| `/api/now/table/wf_workflow_version` | GET | Query workflow versions |
| `/api/now/table/wf_activity` | GET, POST, PATCH, DELETE | Manage workflow activities |

### Update Sets / Changesets

| API Endpoint | HTTP Methods | Purpose |
|--------------|--------------|---------|
| `/api/now/table/sys_update_set` | GET, POST, PATCH | Manage changesets/update sets |
| `/api/now/table/sys_update_xml` | GET | Query changeset changes |

### Script Management

| API Endpoint | HTTP Methods | Purpose |
|--------------|--------------|---------|
| `/api/now/table/sys_script_include` | GET, POST, PATCH | Manage script includes |

### Agile / Project Management

| API Endpoint | HTTP Methods | Purpose |
|--------------|--------------|---------|
| `/api/now/table/rm_story` | GET, POST | Manage agile stories |
| `/api/now/table/rm_epic` | GET, POST | Manage agile epics |
| `/api/now/table/rm_scrum_task` | GET, POST | Manage scrum tasks |
| `/api/now/table/m2m_story_dependencies` | GET, POST, DELETE | Manage story dependencies |
| `/api/now/table/pm_project` | GET, POST | Manage projects |

### System Configuration

| API Endpoint | HTTP Methods | Purpose |
|--------------|--------------|---------|
| `/api/now/table/sys_properties` | GET | Query system properties |

---

## 2. AWS Redshift Data API

Service: `redshift-data` via AWS boto3 SDK  
Region: `us-east-1`

### API Operations

| API Operation | boto3 Method | Purpose |
|---------------|--------------|---------|
| Execute SQL Statement | `client.execute_statement()` | Execute SQL commands on Redshift cluster |
| Describe Statement | `client.describe_statement()` | Check status of executed statement |
| Get Statement Result | `client.get_statement_result()` | Retrieve query results |

### Execute Statement Parameters

```python
response = client.execute_statement(
    ClusterIdentifier='redshift-cluster-1',
    Database='dev',
    DbUser='awsuser',
    Sql='CREATE USER user1 PASSWORD DISABLE;'
)
```

### Common SQL Operations

| SQL Command | Purpose |
|-------------|---------|
| `CREATE USER {username} PASSWORD DISABLE;` | Create database user with IAM authentication |
| `SELECT usename FROM pg_user WHERE usename = '{username}';` | Check if user exists |
| `SELECT CURRENT_USER, usesuper FROM pg_user WHERE usename = CURRENT_USER;` | Verify current user privileges |

---

## 3. Authentication Methods

### ServiceNow Authentication

| Auth Type | Implementation |
|-----------|----------------|
| Basic Auth | Username/Password via HTTP Basic Authentication header |
| OAuth 2.0 | Token-based authentication |

### AWS Authentication

| Auth Type | Implementation |
|-----------|----------------|
| IAM Authentication | boto3 automatic credential chain (environment variables, IAM roles, etc.) |

---

## 4. API Summary by Category

| Category | Table Count | Primary Use |
|----------|-------------|-------------|
| Incident Management | 1 | Core workflow - incident processing |
| Change Management | 3 | Change request lifecycle |
| Service Catalog | 5 | Request management |
| User Management | 5 | User and group operations |
| Knowledge Base | 3 | KB article management |
| Workflow Management | 3 | Workflow automation |
| Update Sets | 2 | Configuration management |
| Agile/Project | 5 | Agile development tracking |
| Script Management | 1 | Script include operations |
| System Config | 1 | System properties |
| **AWS Redshift** | 3 operations | Database user management |

**Total ServiceNow Tables:** 29  
**Total AWS Redshift Operations:** 3

---

## 5. Integration Workflow

```
┌─────────────────────┐
│  User Creates       │
│  ServiceNow Incident│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  ServiceNow MCP     │
│  Reads Incident     │
│  /api/now/table/    │
│  incident (GET)     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Parse Redshift     │
│  Instructions       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  AWS Redshift       │
│  Data API           │
│  execute_statement  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  ServiceNow MCP     │
│  Updates Incident   │
│  /api/now/table/    │
│  incident (PATCH)   │
└─────────────────────┘
```

---

## 6. Environment Variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `SERVICENOW_INSTANCE_URL` | ServiceNow | Instance URL (e.g., https://dev282453.service-now.com) |
| `SERVICENOW_USERNAME` | ServiceNow | API username |
| `SERVICENOW_PASSWORD` | ServiceNow | API password |
| `AWS_REGION` | AWS | AWS region (us-east-1) |
| `REDSHIFT_CLUSTER_ID` | AWS | Redshift cluster identifier |
| `REDSHIFT_DATABASE` | AWS | Database name (dev) |
| `REDSHIFT_DB_USER` | AWS | Database user for operations (awsuser) |

---

## 7. MCP Tools Reference

The ServiceNow MCP Server exposes the following tools organized by functional area:

### Incident Management Tools

| Tool Name | Description |
|-----------|-------------|
| `create_incident` | Create a new incident in ServiceNow |
| `update_incident` | Update an existing incident (state, work notes, etc.) |
| `add_comment` | Add a comment or work note to an incident |
| `resolve_incident` | Resolve an incident with resolution code and notes |
| `list_incidents` | List incidents with filtering and pagination |
| `get_incident_by_number` | Retrieve incident details by incident number |

### Service Catalog Tools

| Tool Name | Description |
|-----------|-------------|
| `list_catalogs` | List available service catalogs |
| `list_catalog_items` | List catalog items with filtering |
| `get_catalog_item` | Get details of a specific catalog item |
| `create_catalog_item` | Create a new catalog item |
| `update_catalog_item` | Update an existing catalog item |
| `list_catalog_categories` | List catalog categories |
| `create_catalog_category` | Create a new catalog category |
| `update_catalog_category` | Update a catalog category |
| `move_catalog_items` | Move items between categories |
| `get_optimization_recommendations` | Get catalog optimization suggestions |
| `create_catalog_item_variable` | Create a variable for a catalog item |
| `list_catalog_item_variables` | List variables for a catalog item |
| `update_catalog_item_variable` | Update a catalog item variable |
| `delete_catalog_item_variable` | Delete a catalog item variable |
| `create_catalog_variable_choice` | Create choices for a variable |

### Change Management Tools

| Tool Name | Description |
|-----------|-------------|
| `create_change_request` | Create a new change request |
| `update_change_request` | Update an existing change request |
| `list_change_requests` | List change requests with filtering |
| `get_change_request_details` | Get details of a specific change request |
| `add_change_task` | Add a task to a change request |
| `submit_change_for_approval` | Submit change for approval workflow |
| `approve_change` | Approve a change request |
| `reject_change` | Reject a change request |

### User Management Tools

| Tool Name | Description |
|-----------|-------------|
| `create_user` | Create a new user in ServiceNow |
| `update_user` | Update user information |
| `get_user` | Get user details by ID, username, or email |
| `list_users` | List users with filtering |
| `create_group` | Create a new user group |
| `update_group` | Update group information |
| `list_groups` | List user groups |
| `add_group_members` | Add members to a group |
| `remove_group_members` | Remove members from a group |

### Knowledge Base Tools

| Tool Name | Description |
|-----------|-------------|
| `create_knowledge_base` | Create a new knowledge base |
| `list_knowledge_bases` | List available knowledge bases |
| `create_category` | Create a KB category |
| `list_categories` | List KB categories |
| `create_article` | Create a new knowledge article |
| `update_article` | Update an existing article |
| `publish_article` | Publish a knowledge article |
| `list_articles` | List articles with filtering |
| `get_article` | Get article details |

### Workflow Management Tools

| Tool Name | Description |
|-----------|-------------|
| `list_workflows` | List workflows in ServiceNow |
| `get_workflow_details` | Get details of a specific workflow |
| `list_workflow_versions` | List versions of a workflow |
| `get_workflow_activities` | Get activities in a workflow |
| `create_workflow` | Create a new workflow |
| `update_workflow` | Update an existing workflow |
| `activate_workflow` | Activate a workflow |
| `deactivate_workflow` | Deactivate a workflow |
| `add_workflow_activity` | Add an activity to a workflow |
| `update_workflow_activity` | Update a workflow activity |
| `delete_workflow_activity` | Delete a workflow activity |
| `reorder_workflow_activities` | Reorder activities in a workflow |

### Changeset/Update Set Tools

| Tool Name | Description |
|-----------|-------------|
| `list_changesets` | List update sets |
| `get_changeset_details` | Get details of a changeset |
| `create_changeset` | Create a new update set |
| `update_changeset` | Update a changeset |
| `commit_changeset` | Commit a changeset |
| `publish_changeset` | Publish a changeset |
| `add_file_to_changeset` | Add a file to a changeset |

### Script Include Tools

| Tool Name | Description |
|-----------|-------------|
| `list_script_includes` | List script includes |
| `get_script_include` | Get script include details |
| `create_script_include` | Create a new script include |
| `update_script_include` | Update a script include |
| `delete_script_include` | Delete a script include |
| `execute_script_include` | Execute a script include |

### Agile/Project Management Tools

| Tool Name | Description |
|-----------|-------------|
| `create_story` | Create an agile story |
| `update_story` | Update an agile story |
| `list_stories` | List agile stories |
| `list_story_dependencies` | List story dependencies |
| `create_story_dependency` | Create a story dependency |
| `delete_story_dependency` | Delete a story dependency |
| `create_epic` | Create an epic |
| `update_epic` | Update an epic |
| `list_epics` | List epics |
| `create_scrum_task` | Create a scrum task |
| `update_scrum_task` | Update a scrum task |
| `list_scrum_tasks` | List scrum tasks |
| `create_project` | Create a project |
| `update_project` | Update a project |
| `list_projects` | List projects |

### UI Policy Tools

| Tool Name | Description |
|-----------|-------------|
| `create_ui_policy` | Create a UI policy |
| `create_ui_policy_action` | Create a UI policy action |
| `create_user_criteria` | Create user criteria |
| `create_user_criteria_condition` | Create user criteria condition |

### System Tools

| Tool Name | Description |
|-----------|-------------|
| `list_syslog_entries` | List system log entries |
| `get_syslog_entry` | Get a specific syslog entry |
| `list_tool_packages` | List available MCP tool packages |

---

## 8. AWS Redshift MCP Tools

The Redshift integration provides the following operations via the `RedshiftClient` class:

| Tool/Method | Description |
|-------------|-------------|
| `execute_statement` | Execute SQL statement on Redshift cluster |
| `describe_statement` | Check status of executed statement |
| `get_statement_result` | Retrieve query results |
| `user_exists` | Check if a database user exists |
| `create_user` | Create a new database user with password disabled |
| `verify_user` | Verify user creation and retrieve user info |

---

## 9. Tool Packages

The MCP server supports loading specific tool packages based on role:

| Package Name | Description | Tool Count |
|--------------|-------------|------------|
| `full` | All available tools | 80+ |
| `service_desk` | Incident and user lookup tools | 11 |
| `catalog_builder` | Catalog management tools | 15 |
| `change_coordinator` | Change management tools | 8 |
| `knowledge_author` | Knowledge base tools | 9 |
| `platform_developer` | Scripting and workflow tools | 20 |
| `agile_management` | Agile/project tools | 15 |
| `system_administrator` | User and group management | 12 |
| `none` | No tools (introspection only) | 0 |

Set the `MCP_TOOL_PACKAGE` environment variable to load a specific package.

---

## 10. Technology Stack

### Programming Languages

| Language | Version | Usage |
|----------|---------|-------|
| **Python** | 3.11+ | Backend, MCP Server, API integrations |
| **HTML5** | - | Web UI templates |
| **CSS3** | - | Styling and responsive design |
| **JavaScript** | ES6+ | Frontend interactivity |

### Backend Frameworks & Libraries

| Technology | Version | Purpose |
|------------|---------|---------|
| **Flask** | ≥2.3.0 | Web application framework for UI |
| **Flask-CORS** | ≥4.0.0 | Cross-Origin Resource Sharing support |
| **Gunicorn** | ≥21.0.0 | Production WSGI HTTP Server |
| **Starlette** | ≥0.27.0 | ASGI framework for MCP server |
| **Uvicorn** | ≥0.22.0 | ASGI server for async operations |
| **MCP SDK** | 1.3.0 | Model Context Protocol implementation |

### Data & API Libraries

| Technology | Version | Purpose |
|------------|---------|---------|
| **Requests** | ≥2.28.0 | HTTP client for ServiceNow REST API |
| **HTTPX** | ≥0.24.0 | Async HTTP client |
| **Boto3** | ≥1.34.0 | AWS SDK for Python (Redshift Data API) |
| **Pydantic** | ≥2.0.0 | Data validation and serialization |
| **PyYAML** | ≥6.0 | YAML configuration parsing |
| **python-dotenv** | ≥1.0.0 | Environment variable management |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Bootstrap** | 5.3.2 | CSS framework for responsive UI |
| **Bootstrap Icons** | 1.11.1 | Icon library |
| **Vanilla JavaScript** | ES6+ | DOM manipulation, async fetch calls |

### Cloud Services & APIs

| Service | Provider | Purpose |
|---------|----------|---------|
| **ServiceNow Instance** | ServiceNow | ITSM platform (incidents, changes, catalog) |
| **AWS Redshift** | Amazon Web Services | Data warehouse for database operations |
| **AWS Redshift Data API** | Amazon Web Services | Serverless SQL execution |
| **AWS IAM** | Amazon Web Services | Authentication and authorization |

### Development Tools

| Tool | Purpose |
|------|---------|
| **pytest** | Unit testing framework |
| **pytest-cov** | Code coverage reporting |
| **black** | Code formatting |
| **isort** | Import sorting |
| **mypy** | Static type checking |
| **ruff** | Fast Python linter |

### DevOps & Deployment

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **GitHub Codespaces** | Cloud development environment |
| **Render.com** | Cloud deployment platform |
| **Git** | Version control |
| **VS Code Dev Containers** | Development environment |

### Container & Runtime

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python Base Image** | 3.11-slim | Docker container base |
| **Dev Container Image** | python:3.12-bullseye | Development environment |
| **AWS CLI** | Latest | AWS command-line operations |
| **Docker-in-Docker** | Latest | Container builds in dev |

### Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web UI (Flask)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Bootstrap  │  │   Jinja2    │  │   JavaScript (ES6+)     │ │
│  │    5.3.2    │  │  Templates  │  │   Async Fetch API       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Services                              │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │   ServiceNow MCP Server │  │   Incident Processor        │  │
│  │   (Starlette/Uvicorn)   │  │   (Python + Boto3)          │  │
│  │                         │  │                             │  │
│  │   - MCP Protocol 1.3.0  │  │   - Redshift Data API       │  │
│  │   - Pydantic Models     │  │   - ServiceNow REST API     │  │
│  │   - Tool Registration   │  │   - Incident Parsing        │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐    ┌─────────────────────────────────┐
│      ServiceNow         │    │         AWS Redshift            │
│  ┌─────────────────┐    │    │   ┌─────────────────────────┐   │
│  │  REST Table API │    │    │   │   Redshift Data API     │   │
│  │  /api/now/table │    │    │   │   execute_statement     │   │
│  └─────────────────┘    │    │   │   describe_statement    │   │
│                         │    │   │   get_statement_result  │   │
│  Tables:                │    │   └─────────────────────────┘   │
│  - incident             │    │                                 │
│  - change_request       │    │   Cluster: redshift-cluster-1   │
│  - sc_cat_item          │    │   Database: dev                 │
│  - sys_user             │    │   Region: us-east-1             │
│  - kb_knowledge         │    │                                 │
└─────────────────────────┘    └─────────────────────────────────┘
```

### Protocol & Standards

| Standard | Usage |
|----------|-------|
| **MCP (Model Context Protocol)** | AI-to-service communication |
| **REST API** | ServiceNow integration |
| **JSON** | Data interchange format |
| **YAML** | Configuration files |
| **OAuth 2.0** | ServiceNow authentication (optional) |
| **HTTP Basic Auth** | ServiceNow authentication (default) |
| **IAM** | AWS authentication |

### Environment Requirements

| Requirement | Specification |
|-------------|---------------|
| Python Version | ≥3.11 |
| Node.js | Not required (vanilla JS) |
| Docker | Optional (for containerization) |
| AWS Account | Required for Redshift operations |
| ServiceNow Instance | Required (PDI or enterprise) |

---

*Document generated for Gen AI Event - December 2025*
