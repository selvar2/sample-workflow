# AWS Redshift Cluster Removal Guide

## Overview

This guide provides step-by-step instructions for removing an Amazon Redshift cluster that has an associated Lakehouse Glue Catalog. It includes troubleshooting steps for common errors encountered during the deletion process.

---

## Prerequisites

- AWS CLI installed and configured
- Appropriate IAM permissions
- Cluster identifier (e.g., `redshift-cluster-1`)
- Target AWS region (e.g., `us-east-1`)

---

## Quick Reference Commands

```powershell
# Always use --no-cli-pager to avoid waiting for user input
--no-cli-pager --output json
```

---

## Common Error: Lakehouse Glue Catalog Association

### Error Message

```
The cluster has an associated lakehouse glue catalog. Deregister it before you delete the cluster.
```

### Root Cause

The Redshift cluster is registered with Amazon Redshift Lakehouse, which creates an associated AWS Glue Data Catalog. This catalog must be deregistered before the cluster can be deleted.

---

## Step-by-Step Removal Process

### Step 1: Verify Cluster Status and Lakehouse Registration

```powershell
aws redshift describe-clusters `
    --cluster-identifier redshift-cluster-1 `
    --query "Clusters[0].{Status:ClusterStatus,LakehouseStatus:LakehouseRegistrationStatus,Pending:PendingModifiedValues}" `
    --profile default `
    --region us-east-1 `
    --no-cli-pager `
    --output json
```

**Expected Output:**
```json
{
    "Status": "available",
    "LakehouseStatus": "REGISTERED",
    "Pending": {}
}
```

---

### Step 2: Deregister Lakehouse Configuration

```powershell
aws redshift modify-lakehouse-configuration `
    --cluster-identifier redshift-cluster-1 `
    --lakehouse-registration Deregister `
    --profile default `
    --region us-east-1 `
    --no-cli-pager `
    --output json
```

---

## Troubleshooting Errors

### Error 1: Invalid Cluster State

#### Error Message

```
An error occurred (InvalidClusterState) when calling the ModifyLakehouseConfiguration operation: 
There is an operation running on the cluster. Please try again at a later time.
```

#### Cause

Another operation (such as password modification, scaling, or maintenance) is currently running on the cluster.

#### Solution

Wait for the pending operation to complete:

```powershell
# Check for pending modifications
aws redshift describe-clusters `
    --cluster-identifier redshift-cluster-1 `
    --query "Clusters[0].PendingModifiedValues" `
    --profile default `
    --region us-east-1 `
    --no-cli-pager `
    --output json

# Wait loop until cluster is ready
for ($i=1; $i -le 12; $i++) {
    Start-Sleep -Seconds 10
    $status = aws redshift describe-clusters `
        --cluster-identifier redshift-cluster-1 `
        --query "Clusters[0].PendingModifiedValues" `
        --profile default `
        --region us-east-1 `
        --no-cli-pager `
        --output json
    Write-Host "Attempt $i - Pending: $status"
    if ($status -eq "{}") {
        Write-Host "Cluster ready!"
        break
    }
}
```

---

### Error 2: Unauthorized Operation - Glue Permissions

#### Error Message

```
An error occurred (UnauthorizedOperation) when calling the ModifyLakehouseConfiguration operation: 
You don't have permission to run Glue:GetCatalog.
```

#### Cause

The IAM user/role lacks permissions to access the AWS Glue Data Catalog associated with the Redshift Lakehouse.

#### Solution

You need to become a Lake Formation Data Lake Administrator. Follow these steps:

##### Step 2a: Check Current Identity

```powershell
aws sts get-caller-identity `
    --profile default `
    --region us-east-1 `
    --no-cli-pager `
    --output json
```

##### Step 2b: Check Current Lake Formation Settings

```powershell
aws lakeformation get-data-lake-settings `
    --profile default `
    --region us-east-1 `
    --no-cli-pager `
    --output json
```

##### Step 2c: Add User as Data Lake Administrator

```powershell
# Get current settings, add user as admin, and update
$settings = aws lakeformation get-data-lake-settings `
    --profile default `
    --region us-east-1 `
    --no-cli-pager `
    --output json | ConvertFrom-Json

$settings.DataLakeSettings.DataLakeAdmins = @(
    @{DataLakePrincipalIdentifier="arn:aws:iam::YOUR_ACCOUNT_ID:user/YOUR_USERNAME"}
)

$settingsJson = $settings.DataLakeSettings | ConvertTo-Json -Depth 10 -Compress
$settingsJson | Out-File -FilePath "$env:TEMP\settings.json" -Encoding ASCII -NoNewline

aws lakeformation put-data-lake-settings `
    --data-lake-settings "file://$env:TEMP\settings.json" `
    --profile default `
    --region us-east-1 `
    --no-cli-pager `
    --output json
```

---

### Error 3: Lake Formation Access Denied

#### Error Message

```
An error occurred (AccessDeniedException) when calling the GetCatalog operation: 
Insufficient Lake Formation permission(s) on Catalog
```

#### Cause

Lake Formation permissions are not configured for the user to access the Glue catalog.

#### Solution

Same as Error 2 - add the user as a Data Lake Administrator using the steps above.

---

### Error 4: Cannot Delete Glue Catalog Directly

#### Error Message

```
An error occurred (InvalidInputException) when calling the DeleteCatalog operation: 
REDSHIFT_NATIVE catalogs can only be deleted by Redshift caller service
```

#### Cause

Attempting to delete the Glue catalog directly using `aws glue delete-catalog` command.

#### Solution

**Do NOT attempt to delete the Glue catalog directly.** The catalog must be deregistered through the Redshift service using `modify-lakehouse-configuration`. The catalog will be automatically cleaned up when deregistration completes.

---

### Error 5: Insufficient Glue Permissions for Grant

#### Error Message

```
An error occurred (AccessDeniedException) when calling the GrantPermissions operation: 
Insufficient Glue permissions to access catalog ACCOUNT_ID:redshift-cluster-1
```

#### Cause

Attempting to grant Lake Formation permissions without being a Data Lake Administrator.

#### Solution

First become a Data Lake Administrator (see Error 2 solution), then retry the deregistration.

---

## Step 3: Wait for Lakehouse Deregistration

After successfully initiating deregistration, wait for it to complete:

```powershell
for ($i=1; $i -le 24; $i++) {
    Start-Sleep -Seconds 10
    $result = aws redshift describe-clusters `
        --cluster-identifier redshift-cluster-1 `
        --query "Clusters[0].{Status:ClusterStatus,LakehouseStatus:LakehouseRegistrationStatus}" `
        --profile default `
        --region us-east-1 `
        --no-cli-pager `
        --output json | ConvertFrom-Json
    
    Write-Host "Attempt $i - Cluster: $($result.Status), Lakehouse: $($result.LakehouseStatus)"
    
    if ($result.LakehouseStatus -eq "DEREGISTERED") {
        Write-Host "Lakehouse deregistered successfully!"
        break
    }
}
```

**Lakehouse Status Progression:**
1. `REGISTERED` → Initial state
2. `DEREGISTRATION_REQUESTED` → Deregistration in progress
3. `DEREGISTERED` → Ready for cluster deletion

---

## Step 4: Delete the Cluster

Once lakehouse is deregistered, delete the cluster:

### Delete Without Final Snapshot

```powershell
aws redshift delete-cluster `
    --cluster-identifier redshift-cluster-1 `
    --skip-final-cluster-snapshot `
    --profile default `
    --region us-east-1 `
    --no-cli-pager `
    --output json
```

### Delete With Final Snapshot (Optional)

```powershell
aws redshift delete-cluster `
    --cluster-identifier redshift-cluster-1 `
    --final-cluster-snapshot-identifier my-final-snapshot `
    --profile default `
    --region us-east-1 `
    --no-cli-pager `
    --output json
```

---

## Step 5: Verify Cluster Deletion

```powershell
for ($i=1; $i -le 30; $i++) {
    Start-Sleep -Seconds 15
    $result = aws redshift describe-clusters `
        --cluster-identifier redshift-cluster-1 `
        --profile default `
        --region us-east-1 `
        --no-cli-pager `
        --output json 2>&1
    
    if ($result -match "ClusterNotFound") {
        Write-Host "Cluster successfully deleted!"
        break
    } else {
        $status = ($result | ConvertFrom-Json).Clusters[0].ClusterStatus
        Write-Host "Attempt $i - Status: $status"
    }
}
```

---

## Complete Removal Script

Here's a complete PowerShell script that handles the entire process:

```powershell
# Configuration
$ClusterIdentifier = "redshift-cluster-1"
$Region = "us-east-1"
$Profile = "default"

# Common parameters
$CommonParams = "--profile $Profile --region $Region --no-cli-pager --output json"

Write-Host "=== Redshift Cluster Removal Script ===" -ForegroundColor Cyan

# Step 1: Check cluster status
Write-Host "`n[Step 1] Checking cluster status..." -ForegroundColor Yellow
$clusterInfo = Invoke-Expression "aws redshift describe-clusters --cluster-identifier $ClusterIdentifier $CommonParams" | ConvertFrom-Json

if ($clusterInfo.Clusters[0].LakehouseRegistrationStatus -eq "REGISTERED") {
    Write-Host "Lakehouse is registered. Proceeding with deregistration..." -ForegroundColor Yellow
    
    # Step 2: Deregister lakehouse
    Write-Host "`n[Step 2] Deregistering lakehouse..." -ForegroundColor Yellow
    try {
        Invoke-Expression "aws redshift modify-lakehouse-configuration --cluster-identifier $ClusterIdentifier --lakehouse-registration Deregister $CommonParams"
    }
    catch {
        Write-Host "Error: May need Lake Formation admin permissions. Adding user as admin..." -ForegroundColor Red
        
        # Get current user
        $identity = Invoke-Expression "aws sts get-caller-identity $CommonParams" | ConvertFrom-Json
        
        # Add as Lake Formation admin
        $settings = Invoke-Expression "aws lakeformation get-data-lake-settings $CommonParams" | ConvertFrom-Json
        $settings.DataLakeSettings.DataLakeAdmins = @(@{DataLakePrincipalIdentifier=$identity.Arn})
        $settingsJson = $settings.DataLakeSettings | ConvertTo-Json -Depth 10 -Compress
        $settingsJson | Out-File -FilePath "$env:TEMP\lf-settings.json" -Encoding ASCII -NoNewline
        Invoke-Expression "aws lakeformation put-data-lake-settings --data-lake-settings `"file://$env:TEMP\lf-settings.json`" $CommonParams"
        
        # Retry deregistration
        Invoke-Expression "aws redshift modify-lakehouse-configuration --cluster-identifier $ClusterIdentifier --lakehouse-registration Deregister $CommonParams"
    }
    
    # Step 3: Wait for deregistration
    Write-Host "`n[Step 3] Waiting for lakehouse deregistration..." -ForegroundColor Yellow
    do {
        Start-Sleep -Seconds 10
        $status = Invoke-Expression "aws redshift describe-clusters --cluster-identifier $ClusterIdentifier --query 'Clusters[0].LakehouseRegistrationStatus' $CommonParams"
        Write-Host "  Lakehouse Status: $status"
    } while ($status -match "REGISTERED|DEREGISTRATION_REQUESTED")
}

# Step 4: Delete cluster
Write-Host "`n[Step 4] Deleting cluster without snapshot..." -ForegroundColor Yellow
Invoke-Expression "aws redshift delete-cluster --cluster-identifier $ClusterIdentifier --skip-final-cluster-snapshot $CommonParams"

# Step 5: Wait for deletion
Write-Host "`n[Step 5] Waiting for cluster deletion..." -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 15
    $result = Invoke-Expression "aws redshift describe-clusters --cluster-identifier $ClusterIdentifier $CommonParams 2>&1"
    if ($result -match "ClusterNotFound") {
        Write-Host "`nCluster successfully deleted!" -ForegroundColor Green
        break
    }
    Write-Host "  Cluster still deleting..."
} while ($true)

Write-Host "`n=== Removal Complete ===" -ForegroundColor Cyan
```

---

## Summary

| Step | Action | Expected Duration |
|------|--------|-------------------|
| 1 | Check cluster status | Instant |
| 2 | Add user as Lake Formation admin (if needed) | Instant |
| 3 | Deregister lakehouse | 30-60 seconds |
| 4 | Wait for deregistration | 1-2 minutes |
| 5 | Delete cluster | Instant to initiate |
| 6 | Wait for deletion | 5-10 minutes |

---

## Required IAM Permissions

To perform all operations, ensure your IAM user/role has:

- `redshift:DescribeClusters`
- `redshift:ModifyLakehouseConfiguration`
- `redshift:DeleteCluster`
- `lakeformation:GetDataLakeSettings`
- `lakeformation:PutDataLakeSettings`
- `glue:GetCatalog`
- `sts:GetCallerIdentity`

---

## References

- [AWS Redshift CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/redshift/)
- [AWS Lake Formation Documentation](https://docs.aws.amazon.com/lake-formation/)
- [Redshift Lakehouse Documentation](https://docs.aws.amazon.com/redshift/latest/mgmt/lakehouse.html)
