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

*Document generated for Gen AI Event - December 2025*
