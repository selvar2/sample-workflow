#!/usr/bin/env python3
"""Test Redshift connection using AWS Data API with temporary credentials."""

import boto3
from botocore.config import Config
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Remove AWS_PROFILE to avoid profile lookup
if 'AWS_PROFILE' in os.environ:
    del os.environ['AWS_PROFILE']

def test_redshift_connection():
    cluster_id = 'redshift-cluster-1'
    database = 'dev'
    db_user = 'awsuser'
    region = 'us-east-1'
    
    # Get AWS credentials from environment
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    print('Testing Redshift connection with temporary credentials...')
    print(f'Cluster: {cluster_id}')
    print(f'Database: {database}')
    print(f'DB User: {db_user}')
    print(f'Region: {region}')
    print(f'AWS Key: {aws_access_key[:10]}...' if aws_access_key else 'AWS Key: NOT SET')
    print()

    # Create session with explicit credentials (no profile)
    session = boto3.Session(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region
    )
    
    # Create Redshift Data API client from session
    client = session.client('redshift-data')

    # Test query
    try:
        response = client.execute_statement(
            ClusterIdentifier=cluster_id,
            Database=database,
            DbUser=db_user,
            Sql='SELECT current_user, current_database();'
        )
        statement_id = response['Id']
        print(f'Query submitted! Statement ID: {statement_id}')

        for i in range(15):
            status = client.describe_statement(Id=statement_id)
            state = status['Status']
            print(f'Status: {state}')
            if state in ['FINISHED', 'FAILED', 'ABORTED']:
                break
            time.sleep(1)

        if state == 'FINISHED':
            result = client.get_statement_result(Id=statement_id)
            print()
            print('=== CONNECTION SUCCESSFUL ===')
            for row in result['Records']:
                user = row[0].get('stringValue', 'N/A')
                db = row[1].get('stringValue', 'N/A')
                print(f'Current User: {user}')
                print(f'Database: {db}')
            return True
        else:
            error = status.get('Error', 'Unknown error')
            print(f'Query failed: {error}')
            return False
    except Exception as e:
        print(f'ERROR: {e}')
        return False

if __name__ == '__main__':
    test_redshift_connection()
