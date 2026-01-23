#!/usr/bin/env python3
"""
Test Redshift Connection with Username and Password

A utility script to test AWS Redshift database connectivity using direct
username/password authentication (JDBC-style connection).

This is different from the Data API which uses IAM authentication.
This script connects directly to Redshift using the username/password credentials.

Usage:
    # Test with specific username and password:
    python test_redshift_password_connection.py --user user31 --password mypassword

    # Test with cluster endpoint:
    python test_redshift_password_connection.py --host redshift-cluster-1.xxxxx.us-east-1.redshift.amazonaws.com --user user31 --password mypassword

    # Use environment variables:
    export REDSHIFT_HOST=redshift-cluster-1.xxxxx.us-east-1.redshift.amazonaws.com
    export REDSHIFT_USER=user31
    export REDSHIFT_PASSWORD=mypassword
    python test_redshift_password_connection.py
"""

import os
import sys
import argparse
import time
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_cluster_endpoint(cluster_id: str, region: str) -> Optional[str]:
    """Get the cluster endpoint from AWS."""
    try:
        import boto3
        client = boto3.client('redshift', region_name=region)
        response = client.describe_clusters(ClusterIdentifier=cluster_id)
        clusters = response.get('Clusters', [])
        if clusters:
            endpoint = clusters[0].get('Endpoint', {})
            host = endpoint.get('Address')
            port = endpoint.get('Port', 5439)
            return host, port
        return None, None
    except Exception as e:
        print(f"Warning: Could not get cluster endpoint: {e}")
        return None, None


def test_password_connection(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str
) -> Dict[str, Any]:
    """
    Test Redshift connection using username/password authentication.
    
    Returns:
        Dictionary with connection test results
    """
    result = {
        "success": False,
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "timestamp": datetime.now().isoformat(),
        "message": "",
        "query_results": None,
        "execution_time": None
    }
    
    print("=" * 70)
    print("AWS Redshift Password Authentication Test")
    print("=" * 70)
    print()
    print("Connection Parameters:")
    print(f"  Host:     {host}")
    print(f"  Port:     {port}")
    print(f"  Database: {database}")
    print(f"  User:     {user}")
    print(f"  Password: {'*' * len(password) if password else 'NOT SET'}")
    print()
    
    try:
        import redshift_connector
    except ImportError:
        result["message"] = "redshift_connector not installed. Run: pip install redshift_connector"
        print(f"✗ {result['message']}")
        return result
    
    print("Connecting to Redshift...")
    start_time = time.time()
    
    try:
        # Connect using username/password
        conn = redshift_connector.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            ssl=True,
            sslmode='require'
        )
        
        connection_time = time.time() - start_time
        print(f"✓ Connected in {connection_time:.2f} seconds")
        
        # Execute test query
        cursor = conn.cursor()
        test_sql = """
        SELECT 
            current_user AS connected_user,
            current_database() AS database_name,
            version() AS version_info,
            current_timestamp AS server_time
        """
        
        print("Executing test query...")
        query_start = time.time()
        cursor.execute(test_sql)
        rows = cursor.fetchall()
        query_time = time.time() - query_start
        
        result["success"] = True
        result["execution_time"] = connection_time + query_time
        result["message"] = "Connection and query successful"
        
        print()
        print("=" * 70)
        print("CONNECTION SUCCESSFUL!")
        print("=" * 70)
        print()
        print(f"  Connection Time: {connection_time:.2f} seconds")
        print(f"  Query Time:      {query_time:.2f} seconds")
        print(f"  Total Time:      {result['execution_time']:.2f} seconds")
        print()
        
        if rows:
            print("Query Results:")
            columns = ['connected_user', 'database_name', 'version_info', 'server_time']
            row_data = {}
            for i, col in enumerate(columns):
                value = str(rows[0][i]) if i < len(rows[0]) else 'N/A'
                # Truncate long values for display
                display_value = value[:60] + '...' if len(value) > 60 else value
                row_data[col] = value
                print(f"  {col}: {display_value}")
            result["query_results"] = row_data
        
        print()
        print("=" * 70)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        error_msg = str(e)
        result["message"] = f"Connection failed: {error_msg}"
        
        print()
        print("=" * 70)
        print("CONNECTION FAILED!")
        print("=" * 70)
        print()
        print(f"  Error: {error_msg}")
        print()
        
        # Provide helpful hints
        if "password" in error_msg.lower() or "authentication" in error_msg.lower():
            print("  Hint: Check that the password is correct")
        if "could not connect" in error_msg.lower() or "timeout" in error_msg.lower():
            print("  Hint: Check that the cluster is publicly accessible or you're in the VPC")
        if "ssl" in error_msg.lower():
            print("  Hint: SSL connection issues - cluster may require specific SSL settings")
        
        print()
        print("=" * 70)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Test AWS Redshift connection with username/password authentication"
    )
    parser.add_argument(
        "--cluster",
        default=os.getenv("REDSHIFT_CLUSTER", "redshift-cluster-1"),
        help="Redshift cluster identifier (used to lookup endpoint)"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("REDSHIFT_HOST"),
        help="Redshift cluster endpoint (overrides --cluster lookup)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("REDSHIFT_PORT", "5439")),
        help="Redshift port (default: 5439)"
    )
    parser.add_argument(
        "--database",
        default=os.getenv("REDSHIFT_DATABASE", "dev"),
        help="Database name (default: dev)"
    )
    parser.add_argument(
        "--user",
        required=True,
        help="Database username"
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Database password"
    )
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_REGION", "us-east-1"),
        help="AWS region (default: us-east-1)"
    )
    
    args = parser.parse_args()
    
    # Get host from cluster if not provided
    host = args.host
    port = args.port
    
    if not host:
        print(f"Looking up endpoint for cluster: {args.cluster}")
        host, port = get_cluster_endpoint(args.cluster, args.region)
        if not host:
            print(f"✗ Could not find endpoint for cluster {args.cluster}")
            print("  Provide --host directly or check cluster name")
            sys.exit(1)
        print(f"✓ Found endpoint: {host}:{port}")
        print()
    
    result = test_password_connection(
        host=host,
        port=port or 5439,
        database=args.database,
        user=args.user,
        password=args.password
    )
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
