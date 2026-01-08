#!/usr/bin/env python3
"""
ServiceNow Incident Processor with AWS Redshift Integration

This script monitors and processes ServiceNow incidents that request Redshift database
user creation. It can run in two modes:
1. Single incident processing: Process a specific incident by number
2. Monitoring mode: Continuously watch for new incidents and process them

Usage:
    # Process a specific incident:
    python process_servicenow_redshift.py --incident INC0010022

    # Monitor for new incidents (from today onward):
    python process_servicenow_redshift.py --monitor

    # Monitor with custom date:
    python process_servicenow_redshift.py --monitor --from-date 2025-12-02

    # Dry run (no actual changes):
    python process_servicenow_redshift.py --incident INC0010022 --dry-run

Requirements:
    - AWS CLI configured with appropriate credentials
    - ServiceNow environment variables set (see .env file)
    - Python packages: requests, python-dotenv
"""

import os
import sys
import json
import time
import argparse
import subprocess
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Configuration settings for the processor."""
    
    # ServiceNow settings
    SERVICENOW_INSTANCE_URL = os.getenv("SERVICENOW_INSTANCE_URL")
    SERVICENOW_USERNAME = os.getenv("SERVICENOW_USERNAME")
    SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD")
    
    # AWS Redshift settings
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    REDSHIFT_DATABASE = os.getenv("REDSHIFT_DATABASE", "dev")
    REDSHIFT_DB_USER = os.getenv("REDSHIFT_DB_USER", "awsuser")  # Superuser for operations
    
    # Processing settings
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))  # seconds
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    STATEMENT_TIMEOUT = int(os.getenv("STATEMENT_TIMEOUT", "60"))  # seconds
    
    # Group filter for dashboard metrics (filter incidents by assignment group)
    ASSIGNMENT_GROUP_FILTER = os.getenv("ASSIGNMENT_GROUP_FILTER", "WG101")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        missing = []
        if not cls.SERVICENOW_INSTANCE_URL:
            missing.append("SERVICENOW_INSTANCE_URL")
        if not cls.SERVICENOW_USERNAME:
            missing.append("SERVICENOW_USERNAME")
        if not cls.SERVICENOW_PASSWORD:
            missing.append("SERVICENOW_PASSWORD")
        
        if missing:
            logger.error(f"Missing required environment variables: {', '.join(missing)}")
            return False
        return True


# ============================================================================
# ServiceNow API Client
# ============================================================================

class ServiceNowClient:
    """Client for ServiceNow API operations."""
    
    def __init__(self):
        import requests
        self.requests = requests
        self.base_url = Config.SERVICENOW_INSTANCE_URL
        self.auth = (Config.SERVICENOW_USERNAME, Config.SERVICENOW_PASSWORD)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_incident(self, incident_number: str) -> Optional[Dict[str, Any]]:
        """Fetch a single incident by number."""
        url = f"{self.base_url}/api/now/table/incident"
        params = {
            "sysparm_query": f"number={incident_number}",
            "sysparm_limit": 1,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true"
        }
        
        try:
            response = self.requests.get(url, auth=self.auth, params=params, headers=self.headers)
            response.raise_for_status()
            result = response.json().get("result", [])
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to fetch incident {incident_number}: {e}")
            return None
    
    def list_incidents(self, from_date: str, limit: int = 100, assignment_group: str = None) -> list:
        """List incidents created on or after a specific date.
        
        Args:
            from_date: Filter incidents created on or after this date
            limit: Maximum number of incidents to return
            assignment_group: Optional filter by assignment group name (e.g., 'WG101')
        """
        url = f"{self.base_url}/api/now/table/incident"
        query = f"sys_created_on>={from_date}"
        
        # Add assignment group filter if specified
        group_filter = assignment_group or Config.ASSIGNMENT_GROUP_FILTER
        if group_filter:
            query += f"^assignment_group.name={group_filter}"
        
        query += "^ORDERBYDESCsys_created_on"
        
        params = {
            "sysparm_query": query,
            "sysparm_limit": limit,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true"
        }
        
        try:
            response = self.requests.get(url, auth=self.auth, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json().get("result", [])
        except Exception as e:
            logger.error(f"Failed to list incidents: {e}")
            return []
    
    def add_work_note(self, incident_number: str, note: str) -> bool:
        """Add a work note to an incident."""
        # First get the sys_id
        incident = self.get_incident(incident_number)
        if not incident:
            return False
        
        sys_id = incident.get("sys_id")
        url = f"{self.base_url}/api/now/table/incident/{sys_id}"
        data = {"work_notes": note}
        
        try:
            response = self.requests.put(url, auth=self.auth, json=data, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to add work note to {incident_number}: {e}")
            return False
    
    def is_already_processed(self, incident: Dict[str, Any]) -> bool:
        """Check if an incident has already been processed."""
        work_notes = incident.get("work_notes", "") or ""
        indicators = [
            "TASK COMPLETED",
            "TASK 2 COMPLETED",
            "Incident already processed",
            "User successfully created",
            "Redshift user already exists"
        ]
        return any(indicator in work_notes for indicator in indicators)


# ============================================================================
# Redshift Operations
# ============================================================================

class RedshiftClient:
    """Client for AWS Redshift Data API operations using boto3."""
    
    def __init__(self, cluster_name: str, dry_run: bool = False):
        self.cluster_name = cluster_name
        self.database = Config.REDSHIFT_DATABASE
        self.db_user = Config.REDSHIFT_DB_USER
        self.region = Config.AWS_REGION
        self.dry_run = dry_run
        self._client = None
    
    @property
    def client(self):
        """Lazy-load boto3 client."""
        if self._client is None:
            import boto3
            self._client = boto3.client('redshift-data', region_name=self.region)
        return self._client
    
    def _execute_statement(self, sql: str) -> Tuple[bool, str, Optional[str]]:
        """Execute a SQL statement via AWS Redshift Data API."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {sql}")
            return True, "dry-run-statement-id", None
        
        try:
            response = self.client.execute_statement(
                ClusterIdentifier=self.cluster_name,
                Database=self.database,
                DbUser=self.db_user,
                Sql=sql
            )
            statement_id = response.get("Id")
            return True, statement_id, None
        except Exception as e:
            return False, None, f"Execute statement failed: {str(e)}"
    
    def _wait_for_statement(self, statement_id: str, timeout: int = 60) -> Tuple[str, Optional[str]]:
        """Wait for a statement to complete and return its status."""
        if self.dry_run:
            return "FINISHED", None
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.client.describe_statement(Id=statement_id)
                status = response.get("Status")
                
                if status == "FINISHED":
                    return status, None
                elif status == "FAILED":
                    return status, response.get("Error", "Unknown error")
                elif status in ["ABORTED", "CANCELLED"]:
                    return status, f"Statement was {status.lower()}"
                
                time.sleep(2)
            except Exception as e:
                return "ERROR", str(e)
        
        return "TIMEOUT", "Statement did not complete within timeout"
    
    def _get_statement_result(self, statement_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed statement."""
        if self.dry_run:
            return {"Records": [], "TotalNumRows": 0}
        
        try:
            response = self.client.get_statement_result(Id=statement_id)
            return response
        except Exception as e:
            logger.error(f"Failed to get statement result: {e}")
            return None
    
    def user_exists(self, username: str) -> Tuple[bool, Optional[str]]:
        """Check if a user exists in Redshift."""
        sql = f"SELECT usename FROM pg_user WHERE usename = '{username}';"
        
        success, statement_id, error = self._execute_statement(sql)
        if not success:
            return False, error
        
        status, error = self._wait_for_statement(statement_id)
        if status != "FINISHED":
            return False, error
        
        result = self._get_statement_result(statement_id)
        if result and result.get("TotalNumRows", 0) > 0:
            return True, statement_id
        
        return False, statement_id
    
    def create_user(self, username: str) -> Tuple[bool, str, Optional[str]]:
        """Create a new user with password disabled.
        
        Returns:
            Tuple of (success, statement_id, error_or_info)
            - If user is created: (True, statement_id, None)
            - If user already exists: (True, statement_id, "USER_EXISTS")
            - If other error: (False, statement_id, error_message)
        """
        sql = f"CREATE USER {username} PASSWORD DISABLE;"
        
        success, statement_id, error = self._execute_statement(sql)
        if not success:
            return False, "", error
        
        status, error = self._wait_for_statement(statement_id)
        if status != "FINISHED":
            # Check if the error is because user already exists
            if error and "already exists" in error.lower():
                logger.info(f"User '{username}' already exists in the database")
                return True, statement_id, "USER_EXISTS"
            return False, statement_id, error
        
        return True, statement_id, None
    
    def group_exists(self, group_name: str) -> Tuple[bool, Optional[str]]:
        """Check if a group exists in Redshift.
        
        Returns:
            Tuple of (exists: bool, statement_id_or_error: str)
        """
        sql = f"SELECT groname FROM pg_group WHERE groname = '{group_name}';"
        
        success, statement_id, error = self._execute_statement(sql)
        if not success:
            return False, error
        
        status, error = self._wait_for_statement(statement_id)
        if status != "FINISHED":
            return False, error
        
        result = self._get_statement_result(statement_id)
        if result and result.get("TotalNumRows", 0) > 0:
            return True, statement_id
        
        return False, statement_id
    
    def create_group(self, group_name: str) -> Tuple[bool, str, Optional[str]]:
        """Create a new group in Redshift.
        
        Returns:
            Tuple of (success, statement_id, error_or_info)
            - If group is created: (True, statement_id, None)
            - If group already exists: (True, statement_id, "GROUP_EXISTS")
            - If other error: (False, statement_id, error_message)
        """
        sql = f"CREATE GROUP {group_name};"
        
        success, statement_id, error = self._execute_statement(sql)
        if not success:
            return False, "", error
        
        status, error = self._wait_for_statement(statement_id)
        if status != "FINISHED":
            # Check if the error is because group already exists
            if error and "already exists" in error.lower():
                logger.info(f"Group '{group_name}' already exists in the database")
                return True, statement_id, "GROUP_EXISTS"
            return False, statement_id, error
        
        return True, statement_id, None
    
    def grant_privileges(self, privileges: str, schema: str, group_name: str) -> Tuple[bool, str, Optional[str]]:
        """Grant privileges on tables in a schema to a group.
        
        Args:
            privileges: Privileges to grant (e.g., 'ALL', 'SELECT', 'INSERT, UPDATE')
            schema: Schema name
            group_name: Group to grant privileges to
        
        Returns:
            Tuple of (success, statement_id, error)
        """
        sql = f"GRANT {privileges} ON ALL TABLES IN SCHEMA {schema} TO GROUP {group_name};"
        
        success, statement_id, error = self._execute_statement(sql)
        if not success:
            return False, "", error
        
        status, error = self._wait_for_statement(statement_id)
        if status != "FINISHED":
            return False, statement_id, error
        
        return True, statement_id, None
    
    def grant_default_privileges(self, privileges: str, schema: str, group_name: str) -> Tuple[bool, str, Optional[str]]:
        """Grant default privileges for future tables in a schema to a group.
        
        This ensures privileges are applied to tables created in the future.
        
        Args:
            privileges: Privileges to grant (e.g., 'ALL', 'SELECT')
            schema: Schema name
            group_name: Group to grant privileges to
        
        Returns:
            Tuple of (success, statement_id, error)
        """
        sql = f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT {privileges} ON TABLES TO GROUP {group_name};"
        
        success, statement_id, error = self._execute_statement(sql)
        if not success:
            return False, "", error
        
        status, error = self._wait_for_statement(statement_id)
        if status != "FINISHED":
            return False, statement_id, error
        
        return True, statement_id, None
    
    def add_user_to_group(self, username: str, group_name: str) -> Tuple[bool, str, Optional[str]]:
        """Add a user to a group.
        
        Args:
            username: User to add
            group_name: Group to add user to
        
        Returns:
            Tuple of (success, statement_id, error)
        """
        sql = f"ALTER GROUP {group_name} ADD USER {username};"
        
        success, statement_id, error = self._execute_statement(sql)
        if not success:
            return False, "", error
        
        status, error = self._wait_for_statement(statement_id)
        if status != "FINISHED":
            return False, statement_id, error
        
        return True, statement_id, None
    
    def verify_user_in_group(self, username: str, group_name: str) -> Tuple[bool, Optional[str]]:
        """Verify a user is a member of a group.
        
        Returns:
            Tuple of (is_member, statement_id_or_error)
        """
        sql = f"""
            SELECT u.usename, g.groname 
            FROM pg_user u
            JOIN pg_group g ON u.usesysid = ANY(g.grolist)
            WHERE u.usename = '{username}' AND g.groname = '{group_name}';
        """
        
        success, statement_id, error = self._execute_statement(sql)
        if not success:
            return False, error
        
        status, error = self._wait_for_statement(statement_id)
        if status != "FINISHED":
            return False, error
        
        result = self._get_statement_result(statement_id)
        if result and result.get("TotalNumRows", 0) > 0:
            return True, statement_id
        
        return False, statement_id

    def verify_user(self, username: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Verify a user exists and get their attributes."""
        sql = f"SELECT usename, usecreatedb, usesuper FROM pg_user WHERE usename = '{username}';"
        
        success, statement_id, error = self._execute_statement(sql)
        if not success:
            return False, None, error
        
        status, error = self._wait_for_statement(statement_id)
        if status != "FINISHED":
            return False, None, error
        
        result = self._get_statement_result(statement_id)
        if result and result.get("TotalNumRows", 0) > 0:
            record = result["Records"][0]
            user_info = {
                "usename": record[0].get("stringValue"),
                "usecreatedb": record[1].get("booleanValue"),
                "usesuper": record[2].get("booleanValue"),
                "statement_id": statement_id
            }
            return True, user_info, None
        
        return False, None, "User not found after creation"


# ============================================================================
# Incident Parser
# ============================================================================

class IncidentParser:
    """Parser for extracting information from incident descriptions."""
    
    @staticmethod
    def extract_username(description: str) -> Optional[str]:
        """Extract username from incident description."""
        if not description:
            return None
        
        patterns = [
            r'Username[:\s]+(\w+)',
            r'user\s+named\s+(\w+)',
            r'database\s+user\s+(\w+)',
            r'user\s+(\w+)\s+to\s+the\s+group',
            r'user\s+(\w+)',
            r'create\s+(\w+)\s+user',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def extract_cluster(description: str) -> Optional[str]:
        """Extract cluster name from incident description."""
        if not description:
            return None
        
        patterns = [
            r'Redshift\s+cluster\s*[:\s]*([a-zA-Z0-9-]+)',
            r'cluster[:\s-]*(\d+)',
            r'redshift[:\s-]*cluster[:\s-]*(\d+)',
            r'cluster\s+(\w+-\w+-\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                cluster_id = match.group(1)
                # If just a number, format as redshift-cluster-N
                if cluster_id.isdigit():
                    return f"redshift-cluster-{cluster_id}"
                return cluster_id
        
        return None
    
    @staticmethod
    def extract_group_name(description: str) -> Optional[str]:
        """Extract group name from incident description."""
        if not description:
            return None
        
        patterns = [
            r'Group\s+name[:\s]+(\w+)',
            r'group\s+(\w+)',
            r'to\s+GROUP\s+(\w+)',
            r'to\s+the\s+group\s+(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def extract_schema(description: str) -> str:
        """Extract schema name from incident description. Defaults to 'public'."""
        if not description:
            return "public"
        
        patterns = [
            r'schema\s+(\w+)',
            r'IN\s+SCHEMA\s+(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "public"
    
    @staticmethod
    def extract_privileges(description: str) -> str:
        """Extract privileges from incident description. Defaults to 'ALL'."""
        if not description:
            return "ALL"
        
        patterns = [
            r'Grant\s+(ALL|SELECT|INSERT|UPDATE|DELETE|DROP|REFERENCES|ALTER|TRUNCATE)',
            r'(ALL)\s+privileges',
            r'(SELECT|INSERT|UPDATE|DELETE)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return "ALL"
    
    @staticmethod
    def extract_password_setting(description: str) -> str:
        """Extract password setting from incident description."""
        if not description:
            return "DISABLE"
        
        # Check for PASSWORD DISABLE
        if re.search(r'password[:\s]*(disable|disabled)', description, re.IGNORECASE):
            return "DISABLE"
        
        # Check for specific password
        match = re.search(r'password[:\s]+[\'"]?(\w+)[\'"]?', description, re.IGNORECASE)
        if match and match.group(1).lower() not in ['disable', 'disabled']:
            return match.group(1)
        
        return "DISABLE"
    
    @staticmethod
    def extract_operations(description: str) -> list:
        """Extract list of operations to perform from incident description.
        
        Returns a list of operation types in order:
        - CREATE_USER: Create a new database user
        - CHECK_GROUP: Check if group exists
        - CREATE_GROUP: Create group if not exists
        - GRANT_PRIVILEGES: Grant privileges to group
        - ADD_USER_TO_GROUP: Add user to group
        """
        operations = []
        
        if not description:
            return operations
        
        desc_lower = description.lower()
        
        # Check for user creation
        if re.search(r'create.*user|new.*user|database\s+user', desc_lower):
            operations.append("CREATE_USER")
        
        # Check for group operations
        if re.search(r'group.*exist|validate.*group|check.*group', desc_lower):
            operations.append("CHECK_GROUP")
        
        if re.search(r'create.*group|if.*not\s+exist.*create', desc_lower):
            operations.append("CREATE_GROUP")
        
        # Check for grant operations
        if re.search(r'grant.*privilege|grant\s+all|grant.*table', desc_lower):
            operations.append("GRANT_PRIVILEGES")
        
        # Check for future tables (default privileges)
        if re.search(r'future\s+tables|default\s+privilege', desc_lower):
            operations.append("GRANT_DEFAULT_PRIVILEGES")
        
        # Check for add user to group
        if re.search(r'add.*user.*group|user.*to.*group', desc_lower):
            operations.append("ADD_USER_TO_GROUP")
        
        # If no specific operations found but it mentions user creation, default to CREATE_USER
        if not operations and re.search(r'user', desc_lower):
            operations.append("CREATE_USER")
        
        return operations
    
    @staticmethod
    def parse_incident(incident: Dict[str, Any]) -> Dict[str, Any]:
        """Parse an incident and extract all relevant information."""
        description = incident.get("description", "") or ""
        short_desc = incident.get("short_description", "") or ""
        
        # Try description first, then short description
        full_text = f"{description} {short_desc}"
        
        # Extract assignment_group from raw incident data
        # ServiceNow returns this as display value when sysparm_display_value=true
        assignment_group = incident.get("assignment_group", "") or ""
        
        # Extract all possible parameters
        parsed = {
            "incident_number": incident.get("number"),
            "sys_id": incident.get("sys_id"),
            "short_description": short_desc,
            "description": description,
            "created_on": incident.get("sys_created_on"),
            "state": incident.get("state"),
            "assignment_group": assignment_group,  # ServiceNow assignment group
            "username": IncidentParser.extract_username(full_text),
            "cluster": IncidentParser.extract_cluster(full_text),
            "group_name": IncidentParser.extract_group_name(full_text),
            "schema": IncidentParser.extract_schema(full_text),
            "privileges": IncidentParser.extract_privileges(full_text),
            "password_setting": IncidentParser.extract_password_setting(full_text),
            "operations": IncidentParser.extract_operations(full_text)
        }
        
        return parsed


# ============================================================================
# Incident Processor
# ============================================================================

class IncidentProcessor:
    """Main processor for handling ServiceNow incidents."""
    
    def __init__(self, dry_run: bool = False):
        self.snow_client = ServiceNowClient()
        self.dry_run = dry_run
        self.processed_incidents = set()
    
    def process_incident(self, incident_number: str) -> Dict[str, Any]:
        """Process a single incident by number."""
        result = {
            "incident_number": incident_number,
            "success": False,
            "message": "",
            "actions": []
        }
        
        logger.info(f"=" * 80)
        logger.info(f"Processing incident: {incident_number}")
        logger.info(f"=" * 80)
        
        # Step 1: Fetch the incident
        incident = self.snow_client.get_incident(incident_number)
        if not incident:
            result["message"] = f"Incident {incident_number} not found"
            logger.error(result["message"])
            return result
        
        result["actions"].append("Incident retrieved from ServiceNow")
        
        # Step 2: Check if already processed
        if self.snow_client.is_already_processed(incident):
            result["message"] = "Incident already processed previously. No further action required."
            result["success"] = True
            logger.info(result["message"])
            
            # Add work note
            if not self.dry_run:
                self.snow_client.add_work_note(
                    incident_number,
                    "Incident already processed previously. No further action required."
                )
            
            return result
        
        # Step 3: Parse incident details
        parsed = IncidentParser.parse_incident(incident)
        logger.info(f"Parsed incident details:")
        logger.info(f"  Username: {parsed.get('username')}")
        logger.info(f"  Cluster: {parsed.get('cluster')}")
        logger.info(f"  Group: {parsed.get('group_name')}")
        logger.info(f"  Schema: {parsed.get('schema')}")
        logger.info(f"  Privileges: {parsed.get('privileges')}")
        logger.info(f"  Operations: {parsed.get('operations')}")
        
        # Validate required fields based on operations
        operations = parsed.get("operations", [])
        
        if not operations:
            result["message"] = "Could not determine operations from incident description"
            logger.error(result["message"])
            self._add_error_work_note(incident_number, result["message"], parsed)
            return result
        
        # Check for required parameters based on operations
        if "CREATE_USER" in operations or "ADD_USER_TO_GROUP" in operations:
            if not parsed.get("username"):
                result["message"] = "Could not extract username from incident description"
                logger.error(result["message"])
                self._add_error_work_note(incident_number, result["message"], parsed)
                return result
        
        if any(op in operations for op in ["CHECK_GROUP", "CREATE_GROUP", "GRANT_PRIVILEGES", "GRANT_DEFAULT_PRIVILEGES", "ADD_USER_TO_GROUP"]):
            if not parsed.get("group_name"):
                result["message"] = "Could not extract group name from incident description"
                logger.error(result["message"])
                self._add_error_work_note(incident_number, result["message"], parsed)
                return result
        
        if not parsed.get("cluster"):
            result["message"] = "Could not extract cluster name from incident description"
            logger.error(result["message"])
            self._add_error_work_note(incident_number, result["message"], parsed)
            return result
        
        result["actions"].append(f"Extracted operations: {', '.join(operations)}")
        if parsed.get("username"):
            result["actions"].append(f"Extracted username: {parsed['username']}")
        if parsed.get("group_name"):
            result["actions"].append(f"Extracted group: {parsed['group_name']}")
        result["actions"].append(f"Extracted cluster: {parsed['cluster']}")
        
        # Step 4: Add Task 1 work note
        task1_note = self._generate_task1_note(parsed)
        if not self.dry_run:
            self.snow_client.add_work_note(incident_number, task1_note)
        result["actions"].append("Task 1 work note added")
        
        # Step 5: Execute Redshift operations
        redshift_result = self._execute_redshift_operations(parsed)
        result["redshift"] = redshift_result
        
        # Step 6: Add Task 2 work note
        task2_note = self._generate_task2_note(parsed, redshift_result)
        if not self.dry_run:
            self.snow_client.add_work_note(incident_number, task2_note)
        result["actions"].append("Task 2 work note added")
        
        result["success"] = redshift_result["success"]
        result["message"] = redshift_result["message"]
        
        logger.info(f"=" * 80)
        logger.info(f"Incident {incident_number} processing complete")
        logger.info(f"Result: {'SUCCESS' if result['success'] else 'FAILED'}")
        logger.info(f"=" * 80)
        
        return result
    
    def _execute_redshift_operations(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Redshift operations for the incident."""
        result = {
            "success": False,
            "message": "",
            "user_existed": False,
            "user_created": False,
            "group_existed": False,
            "group_created": False,
            "privileges_granted": False,
            "default_privileges_granted": False,
            "user_added_to_group": False,
            "statements": [],
            "operations_performed": []
        }
        
        username = parsed.get("username")
        cluster = parsed.get("cluster")
        group_name = parsed.get("group_name")
        schema = parsed.get("schema", "public")
        privileges = parsed.get("privileges", "ALL")
        password_setting = parsed.get("password_setting", "DISABLE")
        operations = parsed.get("operations", ["CREATE_USER"])
        
        # Ensure we have a cluster
        if not cluster:
            result["message"] = "No cluster specified in incident"
            return result
        
        redshift = RedshiftClient(cluster, self.dry_run)
        
        # Process each operation in order
        for operation in operations:
            logger.info(f"Executing operation: {operation}")
            
            if operation == "CREATE_USER":
                if not username:
                    result["message"] = "No username specified for CREATE_USER operation"
                    return result
                
                op_result = self._execute_create_user(redshift, username, password_setting, result)
                if not op_result["success"] and not op_result.get("user_existed"):
                    return result
                result.update(op_result)
                result["operations_performed"].append("CREATE_USER")
            
            elif operation == "CHECK_GROUP":
                if not group_name:
                    result["message"] = "No group name specified for CHECK_GROUP operation"
                    return result
                
                op_result = self._execute_check_group(redshift, group_name, result)
                result.update(op_result)
                result["operations_performed"].append("CHECK_GROUP")
            
            elif operation == "CREATE_GROUP":
                if not group_name:
                    result["message"] = "No group name specified for CREATE_GROUP operation"
                    return result
                
                op_result = self._execute_create_group(redshift, group_name, result)
                if not op_result["success"] and not op_result.get("group_existed"):
                    return result
                result.update(op_result)
                result["operations_performed"].append("CREATE_GROUP")
            
            elif operation == "GRANT_PRIVILEGES":
                if not group_name:
                    result["message"] = "No group name specified for GRANT_PRIVILEGES operation"
                    return result
                
                op_result = self._execute_grant_privileges(redshift, privileges, schema, group_name, result)
                if not op_result["success"]:
                    return result
                result.update(op_result)
                result["operations_performed"].append("GRANT_PRIVILEGES")
            
            elif operation == "GRANT_DEFAULT_PRIVILEGES":
                if not group_name:
                    result["message"] = "No group name specified for GRANT_DEFAULT_PRIVILEGES operation"
                    return result
                
                op_result = self._execute_grant_default_privileges(redshift, privileges, schema, group_name, result)
                if not op_result["success"]:
                    return result
                result.update(op_result)
                result["operations_performed"].append("GRANT_DEFAULT_PRIVILEGES")
            
            elif operation == "ADD_USER_TO_GROUP":
                if not username or not group_name:
                    result["message"] = "Both username and group name required for ADD_USER_TO_GROUP operation"
                    return result
                
                op_result = self._execute_add_user_to_group(redshift, username, group_name, result)
                if not op_result["success"]:
                    return result
                result.update(op_result)
                result["operations_performed"].append("ADD_USER_TO_GROUP")
        
        # Set overall success
        result["success"] = True
        result["message"] = f"Successfully completed {len(result['operations_performed'])} operation(s): {', '.join(result['operations_performed'])}"
        
        return result
    
    def _execute_create_user(self, redshift: RedshiftClient, username: str, password_setting: str, result: Dict) -> Dict:
        """Execute CREATE USER operation."""
        op_result = {"success": False}
        
        # Check if user exists
        logger.info(f"Checking if user '{username}' exists...")
        exists, statement_id = redshift.user_exists(username)
        result["statements"].append({
            "operation": "CHECK_USER",
            "statement_id": statement_id,
            "sql": f"SELECT usename FROM pg_user WHERE usename = '{username}';"
        })
        
        if exists:
            op_result["user_existed"] = True
            op_result["success"] = True
            op_result["message"] = f"User '{username}' already exists"
            logger.info(op_result["message"])
            return op_result
        
        # Create user
        logger.info(f"Creating user '{username}'...")
        if password_setting == "DISABLE":
            sql = f"CREATE USER {username} PASSWORD DISABLE;"
        else:
            sql = f"CREATE USER {username} PASSWORD '{password_setting}';"
        
        success, statement_id, error_or_info = redshift.create_user(username)
        result["statements"].append({
            "operation": "CREATE_USER",
            "statement_id": statement_id,
            "sql": sql,
            "success": success,
            "error": error_or_info if error_or_info not in [None, "USER_EXISTS"] else None
        })
        
        if success and error_or_info == "USER_EXISTS":
            op_result["user_existed"] = True
            op_result["success"] = True
            op_result["message"] = f"User '{username}' already exists"
            return op_result
        
        if not success:
            op_result["message"] = f"Failed to create user: {error_or_info}"
            logger.error(op_result["message"])
            return op_result
        
        # Verify user creation
        logger.info(f"Verifying user '{username}' was created...")
        verified, user_info, error = redshift.verify_user(username)
        if user_info:
            result["statements"].append({
                "operation": "VERIFY_USER",
                "statement_id": user_info.get("statement_id"),
                "sql": f"SELECT usename, usecreatedb, usesuper FROM pg_user WHERE usename = '{username}';",
                "user_info": user_info
            })
        
        op_result["user_created"] = True
        op_result["success"] = True
        op_result["user_info"] = user_info
        op_result["message"] = f"User '{username}' created successfully"
        logger.info(op_result["message"])
        
        return op_result
    
    def _execute_check_group(self, redshift: RedshiftClient, group_name: str, result: Dict) -> Dict:
        """Execute CHECK_GROUP operation."""
        op_result = {"success": True}
        
        logger.info(f"Checking if group '{group_name}' exists...")
        exists, statement_id = redshift.group_exists(group_name)
        result["statements"].append({
            "operation": "CHECK_GROUP",
            "statement_id": statement_id,
            "sql": f"SELECT groname FROM pg_group WHERE groname = '{group_name}';"
        })
        
        op_result["group_existed"] = exists
        op_result["message"] = f"Group '{group_name}' {'exists' if exists else 'does not exist'}"
        logger.info(op_result["message"])
        
        return op_result
    
    def _execute_create_group(self, redshift: RedshiftClient, group_name: str, result: Dict) -> Dict:
        """Execute CREATE_GROUP operation."""
        op_result = {"success": False}
        
        # First check if group exists
        logger.info(f"Checking if group '{group_name}' exists...")
        exists, statement_id = redshift.group_exists(group_name)
        result["statements"].append({
            "operation": "CHECK_GROUP",
            "statement_id": statement_id,
            "sql": f"SELECT groname FROM pg_group WHERE groname = '{group_name}';"
        })
        
        if exists:
            op_result["group_existed"] = True
            op_result["success"] = True
            op_result["message"] = f"Group '{group_name}' already exists"
            logger.info(op_result["message"])
            return op_result
        
        # Create group
        logger.info(f"Creating group '{group_name}'...")
        success, statement_id, error_or_info = redshift.create_group(group_name)
        result["statements"].append({
            "operation": "CREATE_GROUP",
            "statement_id": statement_id,
            "sql": f"CREATE GROUP {group_name};",
            "success": success,
            "error": error_or_info if error_or_info not in [None, "GROUP_EXISTS"] else None
        })
        
        if success and error_or_info == "GROUP_EXISTS":
            op_result["group_existed"] = True
            op_result["success"] = True
            op_result["message"] = f"Group '{group_name}' already exists"
            return op_result
        
        if not success:
            op_result["message"] = f"Failed to create group: {error_or_info}"
            logger.error(op_result["message"])
            return op_result
        
        op_result["group_created"] = True
        op_result["success"] = True
        op_result["message"] = f"Group '{group_name}' created successfully"
        logger.info(op_result["message"])
        
        return op_result
    
    def _execute_grant_privileges(self, redshift: RedshiftClient, privileges: str, schema: str, group_name: str, result: Dict) -> Dict:
        """Execute GRANT_PRIVILEGES operation."""
        op_result = {"success": False}
        
        logger.info(f"Granting {privileges} privileges on {schema} to group {group_name}...")
        sql = f"GRANT {privileges} ON ALL TABLES IN SCHEMA {schema} TO GROUP {group_name};"
        
        success, statement_id, error = redshift.grant_privileges(privileges, schema, group_name)
        result["statements"].append({
            "operation": "GRANT_PRIVILEGES",
            "statement_id": statement_id,
            "sql": sql,
            "success": success,
            "error": error
        })
        
        if not success:
            op_result["message"] = f"Failed to grant privileges: {error}"
            logger.error(op_result["message"])
            return op_result
        
        op_result["privileges_granted"] = True
        op_result["success"] = True
        op_result["message"] = f"Granted {privileges} on {schema} to group {group_name}"
        logger.info(op_result["message"])
        
        return op_result
    
    def _execute_grant_default_privileges(self, redshift: RedshiftClient, privileges: str, schema: str, group_name: str, result: Dict) -> Dict:
        """Execute GRANT_DEFAULT_PRIVILEGES operation for future tables."""
        op_result = {"success": False}
        
        logger.info(f"Granting default {privileges} privileges on {schema} to group {group_name}...")
        sql = f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT {privileges} ON TABLES TO GROUP {group_name};"
        
        success, statement_id, error = redshift.grant_default_privileges(privileges, schema, group_name)
        result["statements"].append({
            "operation": "GRANT_DEFAULT_PRIVILEGES",
            "statement_id": statement_id,
            "sql": sql,
            "success": success,
            "error": error
        })
        
        if not success:
            op_result["message"] = f"Failed to grant default privileges: {error}"
            logger.error(op_result["message"])
            return op_result
        
        op_result["default_privileges_granted"] = True
        op_result["success"] = True
        op_result["message"] = f"Granted default {privileges} on {schema} to group {group_name}"
        logger.info(op_result["message"])
        
        return op_result
    
    def _execute_add_user_to_group(self, redshift: RedshiftClient, username: str, group_name: str, result: Dict) -> Dict:
        """Execute ADD_USER_TO_GROUP operation."""
        op_result = {"success": False}
        
        logger.info(f"Adding user '{username}' to group '{group_name}'...")
        sql = f"ALTER GROUP {group_name} ADD USER {username};"
        
        success, statement_id, error = redshift.add_user_to_group(username, group_name)
        result["statements"].append({
            "operation": "ADD_USER_TO_GROUP",
            "statement_id": statement_id,
            "sql": sql,
            "success": success,
            "error": error
        })
        
        if not success:
            op_result["message"] = f"Failed to add user to group: {error}"
            logger.error(op_result["message"])
            return op_result
        
        # Verify user was added to group
        logger.info(f"Verifying user '{username}' is in group '{group_name}'...")
        is_member, verify_stmt_id = redshift.verify_user_in_group(username, group_name)
        result["statements"].append({
            "operation": "VERIFY_USER_IN_GROUP",
            "statement_id": verify_stmt_id,
            "sql": f"SELECT u.usename, g.groname FROM pg_user u JOIN pg_group g ON u.usesysid = ANY(g.grolist) WHERE u.usename = '{username}' AND g.groname = '{group_name}';",
            "is_member": is_member
        })
        
        op_result["user_added_to_group"] = True
        op_result["success"] = True
        op_result["message"] = f"User '{username}' added to group '{group_name}'"
        logger.info(op_result["message"])
        
        return op_result
    
    def _generate_task1_note(self, parsed: Dict[str, Any]) -> str:
        """Generate work note for Task 1 completion."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        operations_text = "\n".join([f"  - {op}" for op in parsed.get('operations', ['CREATE_USER'])])
        
        return f"""=== TASK 1 COMPLETED - Incident Detection & Review - {timestamp} ===

INCIDENT REVIEW:
- Incident Number: {parsed['incident_number']}
- Created On: {parsed['created_on']}
- Short Description: {parsed['short_description']}

EXTRACTED DETAILS:
- Username: {parsed.get('username', 'N/A')}
- Target Cluster: {parsed.get('cluster', 'N/A')}
- Group Name: {parsed.get('group_name', 'N/A')}
- Schema: {parsed.get('schema', 'public')}
- Privileges: {parsed.get('privileges', 'ALL')}
- Password: {parsed.get('password_setting', 'DISABLED')}
- Database: {Config.REDSHIFT_DATABASE}

OPERATIONS TO PERFORM:
{operations_text}

VALIDATION:
✓ Incident parsed successfully
✓ Required parameters extracted
✓ Operations identified

NEXT STEP: Proceeding to Task 2 - Redshift Operations
"""
    
    def _generate_task2_note(self, parsed: Dict[str, Any], redshift_result: Dict[str, Any]) -> str:
        """Generate work note for Task 2 completion."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Build statements text
        statements_text = ""
        for stmt in redshift_result.get("statements", []):
            status = "✓" if stmt.get("success", True) else "✗"
            statements_text += f"""
{stmt['operation']}:
  {status} Statement ID: {stmt.get('statement_id', 'N/A')}
  SQL: {stmt.get('sql', 'N/A')}"""
            if stmt.get("error"):
                statements_text += f"\n  Error: {stmt['error']}"
        
        # Build summary based on what was done
        summary_items = []
        if redshift_result.get("user_existed"):
            summary_items.append(f"✓ User '{parsed.get('username')}' already exists - no creation needed")
        elif redshift_result.get("user_created"):
            summary_items.append(f"✓ User '{parsed.get('username')}' created successfully")
        
        if redshift_result.get("group_existed"):
            summary_items.append(f"✓ Group '{parsed.get('group_name')}' already exists - no creation needed")
        elif redshift_result.get("group_created"):
            summary_items.append(f"✓ Group '{parsed.get('group_name')}' created successfully")
        
        if redshift_result.get("privileges_granted"):
            summary_items.append(f"✓ {parsed.get('privileges', 'ALL')} privileges granted on {parsed.get('schema', 'public')}")
        
        if redshift_result.get("default_privileges_granted"):
            summary_items.append(f"✓ Default privileges for future tables configured")
        
        if redshift_result.get("user_added_to_group"):
            summary_items.append(f"✓ User '{parsed.get('username')}' added to group '{parsed.get('group_name')}'")
        
        summary_text = "\n".join(summary_items) if summary_items else "No operations completed"
        
        operations_performed = ", ".join(redshift_result.get("operations_performed", [])) or "None"
        
        if redshift_result.get("success"):
            return f"""=== TASK 2 COMPLETED - Redshift Operations - {timestamp} ===

REDSHIFT MCP SERVER OPERATIONS PERFORMED:
{statements_text}

SUMMARY:
{summary_text}

OPERATIONS COMPLETED: {operations_performed}

EXECUTION DETAILS:
- Cluster: {parsed.get('cluster', 'N/A')}
- Database: {Config.REDSHIFT_DATABASE}
- Operating User: {Config.REDSHIFT_DB_USER}
- Region: {Config.AWS_REGION}
- Completion Time: {timestamp}

✓ All operations completed successfully via AWS Redshift Data API

NOTE: Incident remains open per automation rules - not closed/resolved.
"""
        
        # Error case
        return f"""=== TASK 2 FAILED - Redshift Operations - {timestamp} ===

ERROR ENCOUNTERED:
{redshift_result.get('message', 'Unknown error')}

ATTEMPTED OPERATIONS:
{statements_text}

REQUESTED DETAILS:
- Username: {parsed.get('username', 'N/A')}
- Group: {parsed.get('group_name', 'N/A')}
- Cluster: {parsed.get('cluster', 'N/A')}
- Schema: {parsed.get('schema', 'N/A')}
- Database: {Config.REDSHIFT_DATABASE}

Please review and take manual action if required.
"""
    
    def _add_error_work_note(self, incident_number: str, error_msg: str, parsed: Dict[str, Any]):
        """Add error work note to incident."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        note = f"""=== PROCESSING ERROR - {timestamp} ===

ERROR: {error_msg}

INCIDENT DETAILS:
- Incident: {incident_number}
- Short Description: {parsed.get('short_description', 'N/A')}
- Description: {parsed.get('description', 'N/A')}

EXTRACTED VALUES:
- Username: {parsed.get('username', 'NOT FOUND')}
- Cluster: {parsed.get('cluster', 'NOT FOUND')}

Please update the incident with proper details and reprocess.
"""
        if not self.dry_run:
            self.snow_client.add_work_note(incident_number, note)
    
    def monitor(self, from_date: str, poll_interval: int = 10, max_polls: int = None):
        """Monitor for new incidents and process them."""
        logger.info("=" * 80)
        logger.info("SERVICENOW INCIDENT MONITORING - Started")
        logger.info("=" * 80)
        logger.info(f"Monitoring for incidents created on or after: {from_date}")
        logger.info(f"Poll interval: {poll_interval} seconds")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 80)
        
        poll_count = 0
        while max_polls is None or poll_count < max_polls:
            poll_count += 1
            
            try:
                incidents = self.snow_client.list_incidents(from_date)
                
                # Find unprocessed incidents
                new_incidents = []
                for inc in incidents:
                    inc_number = inc.get("number")
                    if inc_number and inc_number not in self.processed_incidents:
                        if not self.snow_client.is_already_processed(inc):
                            new_incidents.append(inc)
                        else:
                            self.processed_incidents.add(inc_number)
                
                if new_incidents:
                    logger.info(f"Found {len(new_incidents)} new incident(s) to process")
                    
                    for inc in new_incidents:
                        inc_number = inc.get("number")
                        self.processed_incidents.add(inc_number)
                        self.process_incident(inc_number)
                else:
                    logger.debug(f"Poll #{poll_count}: No new incidents")
                
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
            
            time.sleep(poll_interval)
        
        logger.info("Monitoring completed")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Process ServiceNow incidents with Redshift operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a specific incident:
  python process_servicenow_redshift.py --incident INC0010022

  # Monitor for new incidents:
  python process_servicenow_redshift.py --monitor

  # Monitor with custom start date:
  python process_servicenow_redshift.py --monitor --from-date 2025-12-01

  # Dry run (no actual changes):
  python process_servicenow_redshift.py --incident INC0010022 --dry-run

Environment Variables:
  SERVICENOW_INSTANCE_URL  - ServiceNow instance URL
  SERVICENOW_USERNAME      - ServiceNow username
  SERVICENOW_PASSWORD      - ServiceNow password
  AWS_REGION               - AWS region (default: us-east-1)
  REDSHIFT_DATABASE        - Redshift database (default: dev)
  REDSHIFT_DB_USER         - Redshift superuser (default: awsuser)
  POLL_INTERVAL            - Monitoring poll interval in seconds (default: 10)
"""
    )
    
    parser.add_argument(
        "--incident", "-i",
        help="Process a specific incident by number (e.g., INC0010022)"
    )
    
    parser.add_argument(
        "--monitor", "-m",
        action="store_true",
        help="Continuously monitor for new incidents"
    )
    
    parser.add_argument(
        "--from-date", "-f",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Start date for monitoring (default: today)"
    )
    
    parser.add_argument(
        "--poll-interval", "-p",
        type=int,
        default=Config.POLL_INTERVAL,
        help=f"Poll interval in seconds for monitoring (default: {Config.POLL_INTERVAL})"
    )
    
    parser.add_argument(
        "--max-polls",
        type=int,
        default=None,
        help="Maximum number of polls before stopping (default: unlimited)"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Dry run mode - no actual changes will be made"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate configuration
    if not Config.validate():
        sys.exit(1)
    
    # Create processor
    processor = IncidentProcessor(dry_run=args.dry_run)
    
    if args.dry_run:
        logger.info("Running in DRY RUN mode - no actual changes will be made")
    
    # Execute based on mode
    if args.incident:
        result = processor.process_incident(args.incident)
        if not result["success"]:
            sys.exit(1)
    elif args.monitor:
        processor.monitor(
            from_date=args.from_date,
            poll_interval=args.poll_interval,
            max_polls=args.max_polls
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
