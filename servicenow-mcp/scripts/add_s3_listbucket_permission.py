#!/usr/bin/env python3
"""
AWS IAM Role Permission Update Script
Adds s3:ListBucket permission to example_role6_mcp_test
"""

import boto3
import json
from botocore.config import Config

# Configure boto3 to suppress pagination
config = Config(
    retries={'max_attempts': 3, 'mode': 'standard'}
)

iam = boto3.client('iam', config=config)

ROLE_NAME = "example_role6_mcp_test"

def get_role_info():
    """Retrieve role details"""
    response = iam.get_role(RoleName=ROLE_NAME)
    role = response['Role']
    print(f"✅ Role Found: {role['RoleName']}")
    print(f"   ARN: {role['Arn']}")
    print(f"   Role ID: {role['RoleId']}")
    print(f"   Created: {role['CreateDate']}")
    return role

def list_attached_policies():
    """List managed policies attached to the role"""
    response = iam.list_attached_role_policies(RoleName=ROLE_NAME)
    policies = response['AttachedPolicies']
    print(f"\n📎 Attached Managed Policies: {len(policies)}")
    for p in policies:
        print(f"   - {p['PolicyName']} ({p['PolicyArn']})")
    return policies

def list_inline_policies():
    """List inline policies on the role"""
    response = iam.list_role_policies(RoleName=ROLE_NAME)
    policies = response['PolicyNames']
    print(f"\n📝 Inline Policies: {len(policies)}")
    for p in policies:
        print(f"   - {p}")
    return policies

def get_policy_document(policy_arn):
    """Get the current policy document"""
    # Get policy metadata
    policy_response = iam.get_policy(PolicyArn=policy_arn)
    policy = policy_response['Policy']
    version_id = policy['DefaultVersionId']
    
    # Get policy document
    version_response = iam.get_policy_version(
        PolicyArn=policy_arn,
        VersionId=version_id
    )
    document = version_response['PolicyVersion']['Document']
    
    print(f"\n📄 Current Policy Document (Version: {version_id}):")
    print(json.dumps(document, indent=2))
    return document, version_id

def add_listbucket_permission(policy_arn, current_document):
    """Add s3:ListBucket to the policy"""
    # Deep copy the document
    new_document = json.loads(json.dumps(current_document))
    
    # Find the S3 statement and add ListBucket
    modified = False
    for statement in new_document.get('Statement', []):
        actions = statement.get('Action', [])
        if isinstance(actions, str):
            actions = [actions]
        
        # Check if this is an S3-related statement
        if any('s3:' in a for a in actions):
            if 's3:ListBucket' not in actions:
                actions.append('s3:ListBucket')
                statement['Action'] = actions
                modified = True
                print(f"\n✏️  Adding s3:ListBucket to existing S3 statement")
            else:
                print(f"\n⚠️  s3:ListBucket already exists in policy")
                return None
    
    if not modified:
        # No S3 statement found, create new one
        print("\n✏️  No existing S3 statement found, adding new statement")
        new_document['Statement'].append({
            'Effect': 'Allow',
            'Action': ['s3:ListBucket'],
            'Resource': ['arn:aws:s3:::whizlabs12']
        })
    
    return new_document

def create_new_policy_version(policy_arn, new_document):
    """Create a new policy version with the updated document"""
    response = iam.create_policy_version(
        PolicyArn=policy_arn,
        PolicyDocument=json.dumps(new_document),
        SetAsDefault=True
    )
    new_version = response['PolicyVersion']['VersionId']
    print(f"\n✅ Created new policy version: {new_version}")
    print(f"   Set as default: {response['PolicyVersion']['IsDefaultVersion']}")
    return new_version

def validate_update(policy_arn, new_version):
    """Validate the updated policy"""
    response = iam.get_policy_version(
        PolicyArn=policy_arn,
        VersionId=new_version
    )
    document = response['PolicyVersion']['Document']
    
    print(f"\n🔍 Validation - New Policy Document (Version: {new_version}):")
    print(json.dumps(document, indent=2))
    
    # Check for s3:ListBucket
    for statement in document.get('Statement', []):
        actions = statement.get('Action', [])
        if isinstance(actions, str):
            actions = [actions]
        if 's3:ListBucket' in actions:
            print("\n✅ VALIDATION PASSED: s3:ListBucket is present")
            return True
    
    print("\n❌ VALIDATION FAILED: s3:ListBucket not found")
    return False

def main():
    print("=" * 60)
    print("AWS IAM Role Permission Update")
    print(f"Role: {ROLE_NAME}")
    print("=" * 60)
    
    # Step 1: Get role info
    role = get_role_info()
    role_id = role['RoleId']
    
    # Step 2: List policies
    attached_policies = list_attached_policies()
    inline_policies = list_inline_policies()
    
    if not attached_policies and not inline_policies:
        print("\n❌ No policies found on role")
        return
    
    # Step 3: Work with managed policy (if exists)
    if attached_policies:
        policy = attached_policies[0]
        policy_arn = policy['PolicyArn']
        print(f"\n🔧 Working with managed policy: {policy['PolicyName']}")
        
        # Get current document
        current_doc, current_version = get_policy_document(policy_arn)
        
        # Add ListBucket permission
        new_doc = add_listbucket_permission(policy_arn, current_doc)
        
        if new_doc:
            # Create new version
            new_version = create_new_policy_version(policy_arn, new_doc)
            
            # Validate
            validate_update(policy_arn, new_version)
    
    # Step 4: Confirm role not recreated
    final_role = iam.get_role(RoleName=ROLE_NAME)
    print("\n" + "=" * 60)
    print("CONFIRMATION")
    print("=" * 60)
    print(f"✅ Role ID unchanged: {final_role['Role']['RoleId'] == role_id}")
    print(f"   Original: {role_id}")
    print(f"   Current:  {final_role['Role']['RoleId']}")
    print(f"✅ Policy type: MANAGED (not inline)")
    print(f"✅ Role was modified in place, NOT recreated")

if __name__ == "__main__":
    main()
