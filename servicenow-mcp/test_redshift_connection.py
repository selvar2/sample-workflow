#!/usr/bin/env python3
"""
Test Redshift Connection

A utility script to test AWS Redshift database connectivity using username/password authentication.
Uses boto3 redshift-data API (consistent with the existing codebase).

Usage:
    # Test with default cluster and environment variables:
    python test_redshift_connection.py

    # Test with specific cluster:
    python test_redshift_connection.py --cluster redshift-cluster-1

    # Test with specific user:
    python test_redshift_connection.py --cluster redshift-cluster-1 --user user31

    # Test with custom database:
    python test_redshift_connection.py --cluster redshift-cluster-1 --database dev
"""

import os
import sys
import argparse
import time
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_redshift_client(region: str):
    """Get boto3 redshift-data client."""
    import boto3
    return boto3.client('redshift-data', region_name=region)


def execute_and_wait(
    client,
    cluster: str,
    database: str,
    db_user: str,
    sql: str,
    timeout: int = 60
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Execute a SQL statement and wait for results.
    
    Returns:
        Tuple of (success, result_data, error_message)
    """
    try:
        # Execute the statement
        start_time = time.time()
        response = client.execute_statement(
            ClusterIdentifier=cluster,
            Database=database,
            DbUser=db_user,
            Sql=sql
        )
        statement_id = response.get("Id")
        
        # Wait for completion
        while time.time() - start_time < timeout:
            status_response = client.describe_statement(Id=statement_id)
            status = status_response.get("Status")
            
            if status == "FINISHED":
                execution_time = time.time() - start_time
                # Get results
                result = client.get_statement_result(Id=statement_id)
                result["execution_time"] = execution_time
                return True, result, None
            elif status == "FAILED":
                error = status_response.get("Error", "Unknown error")
                return False, None, error
            elif status in ["ABORTED", "CANCELLED"]:
                return False, None, f"Statement was {status.lower()}"
            
            time.sleep(1)
        
        return False, None, "Statement timed out"
        
    except Exception as e:
        return False, None, str(e)


def test_connection(
    cluster: str,
    database: str,
    db_user: str,
    region: str
) -> Dict[str, Any]:
    """
    Test Redshift connection by executing a simple query.
    
    Returns:
        Dictionary with connection test results
    """
    result = {
        "success": False,
        "cluster": cluster,
        "database": database,
        "user": db_user,
        "region": region,
        "timestamp": datetime.now().isoformat(),
        "message": "",
        "query_results": None,
        "execution_time": None
    }
    
    print("=" * 70)
    print("AWS Redshift Connection Test")
    print("=" * 70)
    print()
    print("Connection Parameters:")
    print(f"  Cluster:  {cluster}")
    print(f"  Database: {database}")
    print(f"  User:     {db_user}")
    print(f"  Region:   {region}")
    print()
    
    try:
        client = get_redshift_client(region)
        print("✓ Boto3 Redshift Data client created")
    except Exception as e:
        result["message"] = f"Failed to create Redshift client: {e}"
        print(f"✗ {result['message']}")
        return result
    
    # Test query - get current user, database, and version info
    test_sql = """
    SELECT 
        current_user AS connected_user,
        current_database() AS database_name,
        version() AS version_info,
        current_timestamp AS server_time
    """
    
    print(f"Executing test query...")
    print(f"  SQL: SELECT current_user, current_database(), version(), current_timestamp")
    print()
    
    success, query_result, error = execute_and_wait(
        client=client,
        cluster=cluster,
        database=database,
        db_user=db_user,
        sql=test_sql
    )
    
    if success:
        result["success"] = True
        result["execution_time"] = query_result.get("execution_time", 0)
        result["message"] = "Connection successful"
        
        # Parse results
        records = query_result.get("Records", [])
        columns = query_result.get("ColumnMetadata", [])
        
        print("=" * 70)
        print("CONNECTION SUCCESSFUL!")
        print("=" * 70)
        print()
        print(f"  Execution Time: {result['execution_time']:.2f} seconds")
        print()
        
        if records:
            print("Query Results:")
            for i, record in enumerate(records):
                row_data = {}
                for j, col in enumerate(columns):
                    col_name = col.get("name", f"col_{j}")
                    value = record[j].get("stringValue", record[j].get("longValue", "N/A"))
                    row_data[col_name] = value
                    print(f"  {col_name}: {value}")
                result["query_results"] = row_data
        
        print()
        print("=" * 70)
        
    else:
        result["message"] = f"Connection failed: {error}"
        print("=" * 70)
        print("CONNECTION FAILED!")
        print("=" * 70)
        print()
        print(f"  Error: {error}")
        print()
        print("=" * 70)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Test AWS Redshift database connectivity"
    )
    parser.add_argument(
        "--cluster",
        default=os.getenv("REDSHIFT_CLUSTER", "redshift-cluster-1"),
        help="Redshift cluster identifier (default: from env or redshift-cluster-1)"
    )
    parser.add_argument(
        "--database",
        default=os.getenv("REDSHIFT_DATABASE", "dev"),
        help="Database name (default: from env or dev)"
    )
    parser.add_argument(
        "--user",
        default=os.getenv("REDSHIFT_DB_USER", "awsuser"),
        help="Database user (default: from env or awsuser)"
    )
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_REGION", "us-east-1"),
        help="AWS region (default: from env or us-east-1)"
    )
    
    args = parser.parse_args()
    
    result = test_connection(
        cluster=args.cluster,
        database=args.database,
        db_user=args.user,
        region=args.region
    )
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
