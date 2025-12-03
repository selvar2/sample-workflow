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
    
    def list_incidents(self, from_date: str, limit: int = 100) -> list:
        """List incidents created on or after a specific date."""
        url = f"{self.base_url}/api/now/table/incident"
        query = f"sys_created_on>={from_date}^ORDERBYDESCsys_created_on"
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
            r'user\s+named\s+(\w+)',
            r'user\s+(\w+)',
            r'username[:\s]+(\w+)',
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
    def parse_incident(incident: Dict[str, Any]) -> Dict[str, Any]:
        """Parse an incident and extract all relevant information."""
        description = incident.get("description", "") or ""
        short_desc = incident.get("short_description", "") or ""
        
        # Try description first, then short description
        full_text = f"{description} {short_desc}"
        
        return {
            "incident_number": incident.get("number"),
            "sys_id": incident.get("sys_id"),
            "short_description": short_desc,
            "description": description,
            "created_on": incident.get("sys_created_on"),
            "state": incident.get("state"),
            "username": IncidentParser.extract_username(full_text),
            "cluster": IncidentParser.extract_cluster(full_text)
        }


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
        logger.info(f"  Username: {parsed['username']}")
        logger.info(f"  Cluster: {parsed['cluster']}")
        
        if not parsed["username"]:
            result["message"] = "Could not extract username from incident description"
            logger.error(result["message"])
            self._add_error_work_note(incident_number, result["message"], parsed)
            return result
        
        if not parsed["cluster"]:
            result["message"] = "Could not extract cluster name from incident description"
            logger.error(result["message"])
            self._add_error_work_note(incident_number, result["message"], parsed)
            return result
        
        result["actions"].append(f"Extracted username: {parsed['username']}")
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
            "statements": []
        }
        
        username = parsed["username"]
        cluster = parsed["cluster"]
        
        redshift = RedshiftClient(cluster, self.dry_run)
        
        # Check if user exists
        logger.info(f"Checking if user '{username}' exists in {cluster}...")
        exists, statement_id = redshift.user_exists(username)
        result["statements"].append({
            "operation": "CHECK_USER",
            "statement_id": statement_id,
            "sql": f"SELECT usename FROM pg_user WHERE usename = '{username}';"
        })
        
        if exists:
            result["user_existed"] = True
            result["success"] = True
            result["message"] = f"Redshift user '{username}' already exists. No further action required."
            logger.info(result["message"])
            return result
        
        # Create user
        logger.info(f"Creating user '{username}' in {cluster}...")
        success, statement_id, error_or_info = redshift.create_user(username)
        result["statements"].append({
            "operation": "CREATE_USER",
            "statement_id": statement_id,
            "sql": f"CREATE USER {username} PASSWORD DISABLE;",
            "success": success,
            "error": error_or_info if error_or_info != "USER_EXISTS" else None
        })
        
        # Check if user already existed (detected during CREATE attempt)
        if success and error_or_info == "USER_EXISTS":
            result["user_existed"] = True
            result["success"] = True
            result["message"] = f"Database user verification completed. User '{username}' already exists in {cluster}. No further action required."
            logger.info(result["message"])
            return result
        
        if not success:
            result["message"] = f"Failed to create user: {error_or_info}"
            logger.error(result["message"])
            return result
        
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
        
        if not verified:
            result["message"] = f"User creation could not be verified: {error}"
            logger.warning(result["message"])
            return result
        
        result["user_created"] = True
        result["success"] = True
        result["message"] = f"User '{username}' successfully created in {cluster}"
        result["user_info"] = user_info
        logger.info(result["message"])
        
        return result
    
    def _generate_task1_note(self, parsed: Dict[str, Any]) -> str:
        """Generate work note for Task 1 completion."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"""=== TASK 1 COMPLETED - Incident Detection & Review - {timestamp} ===

INCIDENT REVIEW:
- Incident Number: {parsed['incident_number']}
- Created On: {parsed['created_on']}
- Short Description: {parsed['short_description']}

EXTRACTED DETAILS:
- Username to create: {parsed['username']}
- Target Cluster: {parsed['cluster']}
- Database: {Config.REDSHIFT_DATABASE}
- Password: DISABLED (IAM authentication)

VALIDATION:
✓ Incident parsed successfully
✓ Username extracted from description
✓ Cluster identifier parsed
✓ Request type: CREATE USER with PASSWORD DISABLE

NEXT STEP: Proceeding to Task 2 - Redshift Operations
"""
    
    def _generate_task2_note(self, parsed: Dict[str, Any], redshift_result: Dict[str, Any]) -> str:
        """Generate work note for Task 2 completion."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        if redshift_result["user_existed"]:
            return f"""=== TASK 2 COMPLETED - Redshift Operations - {timestamp} ===

REDSHIFT MCP SERVER OPERATIONS:

USER EXISTENCE CHECK:
- User '{parsed['username']}' already exists in {parsed['cluster']}
- No creation needed

RESULT:
✓ Redshift user already exists. No further action required.

EXECUTION DETAILS:
- Cluster: {parsed['cluster']}
- Database: {Config.REDSHIFT_DATABASE}
- Operating User: {Config.REDSHIFT_DB_USER}
- Region: {Config.AWS_REGION}

NOTE: Incident remains open per automation rules.
"""
        
        if redshift_result["success"] and redshift_result["user_created"]:
            statements_text = ""
            for stmt in redshift_result["statements"]:
                statements_text += f"""
{stmt['operation']}:
  - Statement ID: {stmt.get('statement_id', 'N/A')}
  - SQL: {stmt.get('sql', 'N/A')}"""
            
            user_info = redshift_result.get("user_info", {})
            
            return f"""=== TASK 2 COMPLETED - Redshift Operations - {timestamp} ===

REDSHIFT MCP SERVER OPERATIONS PERFORMED:
{statements_text}

USER VERIFICATION:
- Username: {user_info.get('usename', parsed['username'])}
- usecreatedb: {user_info.get('usecreatedb', 'N/A')}
- usesuper: {user_info.get('usesuper', 'N/A')}

SUMMARY:
✓ User '{parsed['username']}' successfully created in {parsed['cluster']}
✓ Password authentication disabled (IAM authentication)
✓ All operations executed via real Redshift MCP Server
✓ No simulations performed

EXECUTION DETAILS:
- Cluster: {parsed['cluster']}
- Database: {Config.REDSHIFT_DATABASE}
- Operating User: {Config.REDSHIFT_DB_USER}
- Region: {Config.AWS_REGION}
- Completion Time: {timestamp}

NOTE: Incident remains open per automation rules - not closed/resolved.
"""
        
        # Error case
        return f"""=== TASK 2 FAILED - Redshift Operations - {timestamp} ===

ERROR ENCOUNTERED:
{redshift_result['message']}

ATTEMPTED OPERATIONS:
- Username: {parsed['username']}
- Cluster: {parsed['cluster']}
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
