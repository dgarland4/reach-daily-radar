import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime
import re

# Setup credentials
creds_json = os.environ.get('GOOGLE_SHEETS_CREDS')
creds_dict = json.loads(creds_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=[
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])

# Connect to Google Sheets
gc = gspread.authorize(creds)
sheet_id = os.environ.get('SHEET_ID')
sheet = gc.open_by_key(sheet_id).sheet1

# Get all records
records = sheet.get_all_records()

# Count companies
company_count = len(records)

# Get latest date
latest_date = datetime.now().strftime('%B %d, %Y')

# Update index.html
with open('index.html', 'r') as f:
    html_content = f.read()

# Replace count and date
# Replace date (e.g., ">April 2, 2026<")
    html_content = re.sub(
        r'(>)[^<]+ \d+, \d{4}(<)',
        rf'\1{latest_date}\2',
        html_content
    )
    
    # Replace company count (e.g., ">83 Companies<" and ">83<")
    html_content = re.sub(
        r'(>)\d+( Companies<)',
        rf'\1{company_count}\2',
        html_content
    )
    html_content = re.sub(
        r'(hero-stat-num">)\d+(<)',
        rf'\1{company_count}\2',
        html_content
    )
