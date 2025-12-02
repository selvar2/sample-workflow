# ServiceNow Incident Processor - Web User Interface

A modern, user-friendly web interface for monitoring and processing ServiceNow incidents with AWS Redshift integration.

## Features

### Dashboard Overview
- **Real-time Statistics**: View total processed incidents, success/error counts, and poll count
- **Connection Status**: Live connection status indicators for ServiceNow and AWS
- **Workflow Visualization**: Visual pipeline showing the processing flow

### Incident Management
- **List Incidents**: View all incidents from ServiceNow with filtering by date
- **Incident Details**: Click on any incident to view full details
- **Parse Preview**: See extracted username and cluster information before processing
- **Status Indicators**: Quickly identify processed, ready, and unparseable incidents

### Processing Capabilities
- **Single Incident Processing**: Process individual incidents with one click
- **Batch Processing**: Select multiple incidents and process them together
- **Dry Run Mode**: Test processing without making actual changes
- **Real-time Updates**: Watch processing results as they happen

### Monitoring Service
- **Continuous Monitoring**: Automatically watch for new incidents
- **Configurable Polling**: Set custom date range and poll intervals
- **Auto-Processing**: New incidents are automatically processed when detected

### Activity Logging
- **Live Activity Log**: Real-time log of all system activities
- **Processing History**: Complete history of processed incidents with details
- **Error Tracking**: Easy identification and tracking of errors

## Quick Start

### Prerequisites

1. Ensure environment variables are set (`.env` file):
```bash
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password
AWS_REGION=us-east-1
REDSHIFT_DATABASE=dev
REDSHIFT_DB_USER=awsuser
```

2. Install dependencies:
```bash
pip install flask flask-cors
```

### Running the Web UI

**Option 1: Using the startup script**
```bash
cd servicenow-mcp
chmod +x web_ui/run_web_ui.sh
./web_ui/run_web_ui.sh
```

**Option 2: Direct Python execution**
```bash
cd servicenow-mcp
python web_ui/app.py
```

**Option 3: With custom port**
```bash
WEB_UI_PORT=8080 python web_ui/app.py
```

The web UI will be available at `http://localhost:5000` (or your custom port).

## User Interface Guide

### Main Dashboard

#### Statistics Cards
The top row shows four key metrics:
- **Total Processed**: Number of incidents processed in the current session
- **Successful**: Number of successfully processed incidents
- **Errors**: Number of failed processing attempts
- **Poll Count**: Number of monitoring polls executed

#### Workflow Pipeline
Visual representation of the processing flow:
1. **ServiceNow** → Read incidents from ServiceNow
2. **Detect** → Identify new/unprocessed incidents
3. **Parse** → Extract Redshift commands (username, cluster)
4. **Execute** → Run operations via Redshift MCP
5. **Update** → Update ServiceNow with results

#### Dry Run Mode
Toggle the "Dry Run Mode" switch to test processing without making actual changes.

### Monitoring Control Panel

Configure and control the automatic monitoring service:

1. **From Date**: Set the start date for incident monitoring
2. **Poll Interval**: How often to check for new incidents (seconds)
3. **Start/Stop**: Control the monitoring service

When active, the monitoring service will:
- Poll ServiceNow at the configured interval
- Automatically detect new incidents
- Process each new incident found
- Update the incident in ServiceNow

### Incidents Tab

View and manage ServiceNow incidents:

- **Checkbox Selection**: Select multiple incidents for batch processing
- **Incident Column**: Shows incident number and creation date
- **Description**: Short description of the incident
- **Parsed Details**: Extracted username and cluster information
- **Status**: Processing status (Processed/Ready/Cannot Parse)
- **Actions**: View details or process individual incidents

### Processing History Tab

View the history of processed incidents:

- **Timestamp**: When the incident was processed
- **Incident**: Incident number
- **Result**: Success or failure status
- **Message**: Processing result message
- **Details**: Click to view full processing details

### Activity Log

Real-time log of system activities:
- Color-coded entries (success, error, info, warning)
- Timestamp for each entry
- Automatic cleanup of old entries

## API Endpoints

The web UI exposes the following REST API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | Get current configuration |
| `/api/status` | GET | Get system status |
| `/api/incidents` | GET | List incidents from ServiceNow |
| `/api/incidents/<number>` | GET | Get specific incident details |
| `/api/process/<number>` | POST | Process a specific incident |
| `/api/process-batch` | POST | Process multiple incidents |
| `/api/history` | GET | Get processing history |
| `/api/monitor/start` | POST | Start monitoring service |
| `/api/monitor/stop` | POST | Stop monitoring service |
| `/api/events` | GET | Server-Sent Events stream |
| `/api/test-connection` | GET | Test ServiceNow/AWS connections |
| `/api/clear-history` | POST | Clear processing history |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB_UI_PORT` | 5000 | Web server port |
| `FLASK_DEBUG` | false | Enable Flask debug mode |
| `DRY_RUN` | false | Default dry run mode |
| `POLL_INTERVAL` | 10 | Default monitoring poll interval (seconds) |

## Architecture

```
web_ui/
├── app.py              # Flask application and API endpoints
├── templates/
│   └── index.html      # Main dashboard HTML/CSS/JavaScript
├── requirements.txt    # Python dependencies
├── run_web_ui.sh       # Startup script
└── README.md           # This documentation
```

The web UI is built with:
- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5, vanilla JavaScript
- **Real-time**: Server-Sent Events (SSE)
- **Icons**: Bootstrap Icons

## Troubleshooting

### Connection Issues

1. **ServiceNow Connection Failed**
   - Verify `SERVICENOW_INSTANCE_URL` is correct
   - Check username/password in environment variables
   - Ensure the ServiceNow instance is accessible

2. **AWS Connection Failed**
   - Run `aws configure` to set up credentials
   - Verify AWS CLI is installed and configured
   - Check IAM permissions for Redshift Data API

### Processing Issues

1. **Cannot Parse Incident**
   - Incident description must contain username and cluster info
   - Expected format: "user named USERNAME" and "cluster N"
   
2. **Redshift Operations Failed**
   - Verify cluster name exists
   - Check AWS credentials have proper permissions
   - Review Redshift security group settings

### Web UI Issues

1. **Page Not Loading**
   - Check if Flask is running on the correct port
   - Verify no other service is using the port

2. **Events Not Updating**
   - Refresh the page to reconnect SSE
   - Check browser console for errors
