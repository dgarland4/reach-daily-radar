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

# Get all values to count rows (excluding headeal
all_values = sheet.get_all_values()ws minus header row)

# Count companies (total rows minus header row)
    company_count = len(all_values) - 1 if len(all_values) > 1 else 0
