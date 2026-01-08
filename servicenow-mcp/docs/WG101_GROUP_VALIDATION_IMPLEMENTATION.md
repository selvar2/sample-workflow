# WG101 Group Validation Implementation

**Date:** January 8, 2026  
**Author:** Development Team  
**Version:** 1.0  

---

## Table of Contents

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Implementation Details](#implementation-details)
4. [Files Modified](#files-modified)
5. [Backup Process](#backup-process)
6. [How to Revert Changes](#how-to-revert-changes)
7. [Testing](#testing)
8. [Configuration](#configuration)

---

## Overview

This document describes the implementation of **WG101 Group Validation** feature for the ServiceNow Incident Processor Web UI. The feature ensures that only incidents assigned to the **WG101 - Redshift Work Group** can be processed through the application.

### Problem Statement

Previously, the application allowed processing of any ServiceNow incident regardless of which group it was assigned to. This created a risk of:
- Processing incidents that don't belong to the Redshift team
- Executing Redshift operations on irrelevant tickets
- Dashboard metrics showing data from all groups instead of WG101 only

### Solution

Implemented a two-layer validation system:
1. **Server-side validation** - API validates assignment_group before processing
2. **Client-side feedback** - User-friendly popup/warning when validation fails

---

## Requirements

| Requirement | Status |
|-------------|--------|
| Filter dashboard metrics to show only WG101 incidents | ✅ Completed |
| Block processing of non-WG101 incidents | ✅ Completed |
| Show user-friendly error message for invalid group | ✅ Completed |
| Allow user to retry with correct incident after error | ✅ Completed |
| Create backups before modifying code | ✅ Completed |

---

## Implementation Details

### 1. Dashboard Metrics Filter (Phase 1)

**File:** `process_servicenow_redshift.py`

Added configuration and modified `list_incidents()` to filter by assignment group:

```python
# Configuration
class Config:
    ASSIGNMENT_GROUP_FILTER = os.getenv("ASSIGNMENT_GROUP_FILTER", "WG101")

# Modified list_incidents method
def list_incidents(self, from_date: str, limit: int = 100, assignment_group: str = None) -> list:
    query = f"sys_created_on>={from_date}"
    
    # Add assignment group filter
    group_filter = assignment_group or Config.ASSIGNMENT_GROUP_FILTER
    if group_filter:
        query += f"^assignment_group.name={group_filter}"
    
    query += "^ORDERBYDESCsys_created_on"
    # ... rest of method
```

**Result:** Dashboard cards (Total Processed, Successful, Errors, This Week) now show only WG101 incidents.

---

### 2. Parse Incident Enhancement (Phase 2)

**File:** `process_servicenow_redshift.py`

Added `assignment_group` field to parsed incident data:

```python
@staticmethod
def parse_incident(incident: Dict[str, Any]) -> Dict[str, Any]:
    # Extract assignment_group from raw incident data
    assignment_group = incident.get("assignment_group", "") or ""
    
    parsed = {
        # ... existing fields ...
        "assignment_group": assignment_group,  # NEW: ServiceNow assignment group
        # ... rest of fields ...
    }
    return parsed
```

---

### 3. Server-Side Validation (Phase 3)

**File:** `web_ui/app.py`

Added validation in the `/api/process/<incident_number>` endpoint:

```python
@app.route('/api/process/<incident_number>', methods=['POST'])
@login_required
def process_incident(incident_number: str):
    # Fetch incident first to validate
    client = ServiceNowClient()
    incident = client.get_incident(incident_number)
    
    # Check assignment_group - must be WG101
    assignment_group = incident.get("assignment_group", "") or ""
    required_group = Config.ASSIGNMENT_GROUP_FILTER  # "WG101"
    
    if assignment_group != required_group:
        return jsonify({
            "success": False,
            "error": f"Only incidents assigned to '{required_group}' can be processed.",
            "error_code": "INVALID_GROUP",
            "current_group": assignment_group,
            "required_group": required_group
        }), 400
    
    # Proceed with processing if valid
    # ...
```

**Error Response Example:**
```json
{
    "success": false,
    "incident_number": "INC0010130",
    "error": "This incident belongs to group 'None (unassigned)'. Only incidents assigned to 'WG101 - Redshift Work Group' can be processed.",
    "error_code": "INVALID_GROUP",
    "current_group": "",
    "required_group": "WG101"
}
```

---

### 4. Client-Side Error Handling (Phase 4)

**File:** `web_ui/templates/index.html`

#### A. Added Group Validation Error Modal

```javascript
function showGroupValidationError(incidentNumber, currentGroup, requiredGroup, errorMessage) {
    const modalHtml = `
        <div class="modal fade" id="groupValidationModal">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content bg-dark border-warning">
                    <div class="modal-header border-warning">
                        <h5 class="modal-title text-warning">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>Group Validation Error
                        </h5>
                    </div>
                    <div class="modal-body">
                        <!-- Error details and action guidance -->
                    </div>
                </div>
            </div>
        </div>
    `;
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('groupValidationModal'));
    modal.show();
}
```

#### B. Updated processSingleIncident() Function

```javascript
async function processSingleIncident(incidentNumber) {
    const result = await response.json();
    
    if (result.success) {
        // Success handling
    } else if (result.error_code === 'INVALID_GROUP') {
        // Show group validation popup
        showGroupValidationError(incidentNumber, result.current_group, result.required_group);
    } else {
        // Other error handling
    }
}
```

#### C. Updated processManualIncident() - Button State Fix

```javascript
} else if (result.error_code === 'INVALID_GROUP') {
    // Show warning message
    resultDiv.innerHTML = `<div class="alert alert-warning">...</div>`;
    
    // Reset button so user can try another incident
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-play-fill me-1"></i>Process Incident';
    
    // Clear input and focus for next entry
    input.value = '';
    input.focus();
    return;
}
```

---

## Files Modified

| File | Purpose | Lines Changed |
|------|---------|---------------|
| `process_servicenow_redshift.py` | Added ASSIGNMENT_GROUP_FILTER config | ~5 lines |
| `process_servicenow_redshift.py` | Modified list_incidents() with group filter | ~15 lines |
| `process_servicenow_redshift.py` | Added assignment_group to parse_incident() | ~5 lines |
| `web_ui/app.py` | Added server-side validation in process_incident() | ~25 lines |
| `web_ui/templates/index.html` | Added showGroupValidationError() function | ~50 lines |
| `web_ui/templates/index.html` | Updated processSingleIncident() error handling | ~10 lines |
| `web_ui/templates/index.html` | Fixed button state in processManualIncident() | ~10 lines |

---

## Backup Process

### Backup Location

All backups are stored in:
```
/workspaces/sample-workflow/servicenow-mcp/backups/code_backup/
```

### Backup Naming Convention

Files are named with timestamp format:
```
<original_filename>_YYYYMMDD_HHMMSS.<extension>
```

**Examples:**
- `app_20260108_114746.py`
- `index_20260108_114746.html`
- `process_servicenow_redshift_20260108_114746.py`

### Backup Files Created

| Timestamp | Files Backed Up | Reason |
|-----------|-----------------|--------|
| 20260108_114746 | app.py, index.html, process_servicenow_redshift.py | Before WG101 validation implementation |
| 20260108_115751 | index.html | Before button state fix |

### Backup Header Comments

Each backup file includes a header comment explaining:
- What changes were made after this backup
- Date/timestamp of backup
- Instructions for reverting

**Python file header:**
```python
# BACKUP: Old file before implementing WG101 group validation logic - 20260108_114746
# This is the original file before adding:
# - Server-side validation to check assignment_group = WG101 before processing
# - Popup error message for non-WG101 tickets
# Revert to this file if the new implementation causes issues
```

**HTML file header:**
```html
<!-- BACKUP: Old file before implementing WG101 group validation logic - 20260108_114746
     This is the original file before adding:
     - Client-side validation to check assignment_group = WG101 before processing
     - Popup error message for non-WG101 tickets
     Revert to this file if the new implementation causes issues
-->
```

---

## How to Revert Changes

### Option 1: Revert All Changes (Full Rollback)

```bash
cd /workspaces/sample-workflow/servicenow-mcp

# Restore original files from backup
cp backups/code_backup/app_20260108_114746.py web_ui/app.py
cp backups/code_backup/index_20260108_114746.html web_ui/templates/index.html
cp backups/code_backup/process_servicenow_redshift_20260108_114746.py process_servicenow_redshift.py

# Restart the application
pkill -f "python web_ui/app.py"
source .venv/bin/activate
python web_ui/app.py
```

### Option 2: Revert Only Button Fix

```bash
cd /workspaces/sample-workflow/servicenow-mcp

# Restore index.html from before button fix (keeps WG101 validation)
cp backups/code_backup/index_20260108_115751.html web_ui/templates/index.html

# Restart the application
pkill -f "python web_ui/app.py"
python web_ui/app.py
```

### Option 3: Remove Group Filter Only

Edit `process_servicenow_redshift.py` and change:
```python
ASSIGNMENT_GROUP_FILTER = os.getenv("ASSIGNMENT_GROUP_FILTER", "WG101")
```
To:
```python
ASSIGNMENT_GROUP_FILTER = os.getenv("ASSIGNMENT_GROUP_FILTER", "")  # Empty = no filter
```

---

## Testing

### Test Case 1: Non-WG101 Incident

1. Login to the application at http://localhost:5000
2. Enter an incident number that is NOT assigned to WG101
3. Click "Process Incident"
4. **Expected:** Warning message appears, button resets, input clears

### Test Case 2: WG101 Incident

1. Enter an incident number assigned to WG101
2. Click "Process Incident"
3. **Expected:** Processing succeeds normally

### Test Case 3: Dashboard Metrics

1. View dashboard cards (Total Processed, Successful, Errors, This Week)
2. **Expected:** Only shows counts for WG101 incidents

### Test Case 4: Incident List Filter

1. View the incident list
2. **Expected:** Only WG101 incidents appear in the list

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ASSIGNMENT_GROUP_FILTER` | `WG101` | ServiceNow group name to filter by |

### Changing the Required Group

To change from WG101 to a different group:

**Option A: Environment Variable**
```bash
export ASSIGNMENT_GROUP_FILTER="NEW_GROUP_NAME"
```

**Option B: Modify Config Class**
Edit `process_servicenow_redshift.py`:
```python
ASSIGNMENT_GROUP_FILTER = os.getenv("ASSIGNMENT_GROUP_FILTER", "NEW_GROUP_NAME")
```

---

## User Experience Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Enters Incident Number                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Clicks "Process Incident"                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Server Fetches Incident from ServiceNow             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Check: assignment_group == "WG101"?                 │
└─────────────────────────────────────────────────────────────────┘
                     │                        │
                    YES                       NO
                     │                        │
                     ▼                        ▼
┌────────────────────────────┐   ┌────────────────────────────────┐
│   Process Redshift         │   │   Return INVALID_GROUP Error   │
│   Operations               │   │                                │
└────────────────────────────┘   └────────────────────────────────┘
                     │                        │
                     ▼                        ▼
┌────────────────────────────┐   ┌────────────────────────────────┐
│   Show Success Message     │   │   Show Warning Popup           │
│                            │   │   Reset Button                 │
│                            │   │   Clear Input                  │
│                            │   │   Focus Input for Retry        │
└────────────────────────────┘   └────────────────────────────────┘
```

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-08 | 1.0 | Initial implementation of WG101 group validation |
| 2026-01-08 | 1.0.1 | Fixed button stuck in "Processing..." state after validation error |

---

## Support

For issues or questions regarding this implementation:
1. Check the backup files for reverting changes
2. Review the error logs in the terminal where Flask is running
3. Verify the ServiceNow assignment_group field is populated correctly

---

*Document generated on January 8, 2026*
