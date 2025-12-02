#!/usr/bin/env python
"""
Script to list ServiceNow incidents created within specified date ranges.
Supports specific date, week, month, or custom date ranges.
"""

import os
import sys
import requests
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

def get_week_range(date_str):
    """Get the Monday to Sunday week range for a given date."""
    date = datetime.strptime(date_str, "%Y-%m-%d")
    # Find Monday of the week
    monday = date - timedelta(days=date.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

def get_month_range(month_str):
    """Get the first and last day of the month."""
    year, month = map(int, month_str.split("-"))
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

# Load environment variables
load_dotenv()

# Get configuration from environment variables
instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
username = os.getenv("SERVICENOW_USERNAME")
password = os.getenv("SERVICENOW_PASSWORD")

if not instance_url or not username or not password:
    print("Error: Missing required environment variables.")
    print("Please set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD.")
    sys.exit(1)

# Parse command line arguments
parser = argparse.ArgumentParser(description="List ServiceNow incidents by date range")
parser.add_argument("--date", help="Specific date (YYYY-MM-DD)")
parser.add_argument("--week", help="Week containing this date (YYYY-MM-DD)")
parser.add_argument("--month", help="Month (YYYY-MM)")
parser.add_argument("--from-date", dest="from_date", help="Start date (YYYY-MM-DD)")
parser.add_argument("--to-date", dest="to_date", help="End date (YYYY-MM-DD)")
parser.add_argument("--limit", type=int, default=1000, help="Maximum number of incidents to return")

args = parser.parse_args()

# Determine date range
start_date = None
end_date = None
description = ""

if args.date:
    start_date = args.date
    end_date = (datetime.strptime(args.date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    description = f"on {args.date}"
elif args.week:
    start_date, end_date = get_week_range(args.week)
    description = f"in the week of {args.week} ({start_date} to {end_date})"
elif args.month:
    start_date, end_date = get_month_range(args.month)
    description = f"in {args.month}"
elif args.from_date and args.to_date:
    start_date = args.from_date
    end_date = (datetime.strptime(args.to_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    description = f"between {args.from_date} and {args.to_date}"
else:
    print("Error: Please specify a date range using --date, --week, --month, or --from-date/--to-date")
    sys.exit(1)

# API URL
api_url = f"{instance_url}/api/now/table/incident"

# Query for incidents created in the specified range
query = f"sys_created_on>={start_date}^sys_created_on<{end_date}"

params = {
    "sysparm_query": query,
    "sysparm_limit": args.limit,
    "sysparm_display_value": "true",
}

print(f"Fetching incidents created {description}...")

response = requests.get(api_url, auth=(username, password), params=params)

if response.status_code == 200:
    data = response.json()
    incidents = data.get("result", [])
    print(f"\n✓ Found {len(incidents)} incidents created {description}:")
    if incidents:
        print("\n" + "="*80)
        for incident in incidents:
            print(f"Number: {incident['number']}")
            print(f"Short Description: {incident['short_description']}")
            print(f"State: {incident['state']}")
            print(f"Priority: {incident['priority']}")
            print(f"Created On: {incident['sys_created_on']}")
            assigned_to = incident.get('assigned_to')
            if isinstance(assigned_to, dict):
                assigned_to = assigned_to.get('display_value', 'Unassigned')
            print(f"Assigned To: {assigned_to or 'Unassigned'}")
            print("-" * 40)
else:
    print(f"\n✗ Failed to fetch incidents")
    print(f"  Error: {response.status_code} - {response.text}")
    sys.exit(1)