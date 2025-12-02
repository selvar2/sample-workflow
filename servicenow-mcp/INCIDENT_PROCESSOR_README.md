# ServiceNow Incident Processor with AWS Redshift Integration

This script automates the processing of ServiceNow incidents that request Redshift database user creation. It integrates with ServiceNow's REST API and AWS Redshift Data API to handle the complete workflow.

## Features

- **Single Incident Processing**: Process a specific incident by number
- **Continuous Monitoring**: Watch for new incidents and process them automatically
- **Redshift Integration**: Create database users via AWS Redshift Data API
- **Work Notes**: Automatically document all actions in ServiceNow work notes
- **Duplicate Prevention**: Never reprocesses already-handled incidents
- **Dry Run Mode**: Test without making actual changes
- **Error Handling**: Comprehensive error handling and logging

## Prerequisites

### 1. Environment Setup

Ensure you have the following installed:
- Python 3.8+
- AWS CLI configured with appropriate credentials
- Required Python packages

```bash
# Install required packages
pip install requests python-dotenv
```

### 2. Environment Variables

Create a `.env` file in the project directory or set these environment variables:

```bash
# ServiceNow Configuration (Required)
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password

# AWS Redshift Configuration (Optional - defaults shown)
AWS_REGION=us-east-1
REDSHIFT_DATABASE=dev
REDSHIFT_DB_USER=awsuser

# Processing Settings (Optional)
POLL_INTERVAL=10
MAX_RETRIES=3
STATEMENT_TIMEOUT=60
```

### 3. AWS Credentials

Ensure AWS CLI is configured with credentials that have access to Redshift Data API:

```bash
aws configure
# Or use environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

## Usage

### Process a Specific Incident

```bash
# Basic usage
python process_servicenow_redshift.py --incident INC0010022

# Or using short form
python process_servicenow_redshift.py -i INC0010022
```

### Monitor for New Incidents

```bash
# Start monitoring (from today onward)
python process_servicenow_redshift.py --monitor

# Monitor with custom start date
python process_servicenow_redshift.py --monitor --from-date 2025-12-01

# Monitor with custom poll interval (in seconds)
python process_servicenow_redshift.py --monitor --poll-interval 30

# Monitor with maximum polls (e.g., for testing)
python process_servicenow_redshift.py --monitor --max-polls 10
```

### Dry Run Mode

Test without making actual changes:

```bash
# Dry run for single incident
python process_servicenow_redshift.py --incident INC0010022 --dry-run

# Dry run for monitoring
python process_servicenow_redshift.py --monitor --dry-run
```

### Verbose Logging

Enable detailed logging:

```bash
python process_servicenow_redshift.py --incident INC0010022 --verbose
```

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--incident` | `-i` | Process a specific incident by number |
| `--monitor` | `-m` | Continuously monitor for new incidents |
| `--from-date` | `-f` | Start date for monitoring (default: today) |
| `--poll-interval` | `-p` | Poll interval in seconds (default: 10) |
| `--max-polls` | | Maximum polls before stopping (default: unlimited) |
| `--dry-run` | `-d` | No actual changes will be made |
| `--verbose` | `-v` | Enable verbose logging |
| `--help` | `-h` | Show help message |

## Incident Format

The script parses incident descriptions to extract:
- **Username**: Extracted from patterns like "user named xyz" or "create xyz user"
- **Cluster**: Extracted from patterns like "cluster 1" or "redshift-cluster-1"

### Example Incident Description
```
Create database user named user15 with password disabled in redshift cluster 1
```

Extracted:
- Username: `user15`
- Cluster: `redshift-cluster-1`

## Workflow

### Task 1: Incident Detection & Review
1. Fetch incident from ServiceNow
2. Check if already processed
3. Extract username and cluster from description
4. Validate extracted information
5. Add work note documenting the review

### Task 2: Redshift Operations
1. Check if user already exists in Redshift
2. If exists: Document and skip creation
3. If not exists: Create user with PASSWORD DISABLE
4. Verify user creation
5. Add work note documenting the operations

## Work Notes

The script automatically adds detailed work notes to each incident:

### Task 1 Work Note
```
=== TASK 1 COMPLETED - Incident Detection & Review ===
- Incident parsed successfully
- Username extracted: user15
- Cluster identified: redshift-cluster-1
```

### Task 2 Work Note
```
=== TASK 2 COMPLETED - Redshift Operations ===
- User 'user15' successfully created in redshift-cluster-1
- Statement ID: xxx-xxx-xxx
- All operations executed via real Redshift MCP Server
```

## Error Handling

- **Missing Environment Variables**: Script exits with error message
- **Incident Not Found**: Logged and skipped
- **Parse Failure**: Error work note added to incident
- **Redshift Errors**: Documented in work notes with details
- **Network Errors**: Logged with retry information

## Examples

### Full Workflow Example

```bash
# 1. Activate virtual environment
cd /workspaces/sample-workflow/servicenow-mcp
source .venv/bin/activate

# 2. Process a specific incident
python process_servicenow_redshift.py --incident INC0010022

# 3. Or start monitoring for new incidents
python process_servicenow_redshift.py --monitor --from-date 2025-12-02
```

### Integration with Automation

```bash
# Run in background with nohup
nohup python process_servicenow_redshift.py --monitor > monitor.log 2>&1 &

# Or run with systemd, cron, or other schedulers
```

### Cron Job Example

```bash
# Process incidents every 5 minutes (in crontab)
*/5 * * * * cd /workspaces/sample-workflow/servicenow-mcp && source .venv/bin/activate && python process_servicenow_redshift.py --monitor --max-polls 1
```

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Ensure `.env` file exists with all required variables
   - Or set environment variables directly

2. **"Incident not found"**
   - Verify the incident number is correct
   - Check ServiceNow connectivity

3. **"Could not extract username/cluster"**
   - Ensure incident description follows expected format
   - Check for typos in the description

4. **"Failed to execute Redshift command"**
   - Verify AWS credentials are configured
   - Check Redshift cluster is accessible
   - Ensure awsuser has appropriate permissions

### Debug Mode

```bash
# Enable verbose logging for debugging
python process_servicenow_redshift.py --incident INC0010022 --verbose --dry-run
```

## Security Notes

- Credentials are loaded from environment variables or `.env` file
- Never commit `.env` file to version control
- Use IAM roles when running in AWS environments
- The script uses `awsuser` (superuser) for Redshift operations

## License

See LICENSE file in the project root.
