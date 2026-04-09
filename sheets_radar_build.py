import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime

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
html_content = html_content.replace(
    '<span id="company-count">119</span>',
    f'<span id="company-count">{company_count}</span>'
)
html_content = html_content.replace(
    '<span id="last-updated">April 2, 2026</span>',
    f'<span id="last-updated">{latest_date}</span>'
)

with open('index.html', 'w') as f:
    f.write(html_content)

print(f"✅ Updated: {company_count} companies as of {latest_date}")
