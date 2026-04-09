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

# Get all values from sheet (using row 4 as header)
all_rows = sheet.get_all_records(head=4)

# Process data
company_count = len(all_rows)
regions = set()
categories = set()
company_cards_html = ""

def clean_id(text):
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

for row in all_rows:
    name = str(row.get('Company Name', 'Unknown'))
    if not name or name == 'Unknown': continue
    
    website = str(row.get('Website', '#'))
    desc = str(row.get('Company Description', ''))
    cat = str(row.get('Category', 'PropTech'))
    subcat = str(row.get('Subcategory', ''))
    region = str(row.get('Region', 'US'))
    stage = str(row.get('Stage / Round', 'Seed'))
    source = str(row.get('Source', 'Direct'))
    date_added = str(row.get('Date Added', ''))
    why_scv = str(row.get('Why SCV / REACH', ''))
    
    regions.add(region)
    categories.add(cat)
    
    clean_url = website.replace('https://', '').replace('http://', '').split('/')[0]
    tags = f"{clean_id(region)} {clean_id(cat)}"
    
    card = f"""
    <div class="card" data-tags="{tags}" data-date="{date_added}">
        <div class="card-top">
            <div class="card-logo-wrap">
                <div class="owner-avatar">{name[0] if name else '?'}</div>
            </div>
            <div class="card-identity">
                <div class="card-name-row">
                    <span class="card-name">{name}</span>
                    <a href="{website}" target="_blank" class="card-website">↗ {clean_url}</a>
                </div>
                <div class="card-meta-row">
                    <span class="badge badge-watch">👀 Watch</span>
                    <span class="tag">{cat}</span>
                    <span class="tag">{subcat}</span>
                    <span class="tag">{stage}</span>
                </div>
            </div>
            <span class="status-pill" style="background: #FFF9C4;">NEW</span>
        </div>
        <div class="card-desc-label">Company Description</div>
        <div class="card-tagline">{desc}</div>
        <div class="scv-angle">
            <div class="scv-angle-label">Why SCV / REACH</div>
            <div class="scv-angle-text">{why_scv}</div>
        </div>
        <div class="card-footer">
            <div class="card-footer-left">
                <span class="source-label">Source:</span>
                <span class="source-name">{source}</span>
                <span class="card-date">· {date_added}</span>
            </div>
            <div class="owner-chip">
                <div class="owner-avatar">DG</div>
                <span>Dave Garland</span>
            </div>
        </div>
    </div>
    """
    company_cards_html += card

# Build final HTML
latest_date = datetime.now().strftime('%B %d, %Y')
region_count = len(regions)
category_count = len(categories)

with open('index.html', 'r') as f:
    template = f.read()

# Replace header stats
template = re.sub(r'<span class="header-date">[^<]+</span>', f'<span class="header-date">{latest_date}</span>', template)
template = re.sub(r'Today’s Radar — [^<]+', f'Today’s Radar — {latest_date}', template)

# Replace hero stats
template = re.sub(r'<div class="hero-stat-num">[^<]*</div>(\s*)<div class="hero-stat-label">Companies Tracked</div>', 
                  f'<div class="hero-stat-num">{company_count}</div>\\1<div class="hero-stat-label">Companies Tracked</div>', template)
template = re.sub(r'<div class="hero-stat-num">[^<]*</div>(\s*)<div class="hero-stat-label">Regions Covered</div>', 
                  f'<div class="hero-stat-num">{region_count}</div>\\1<div class="hero-stat-label">Regions Covered</div>', template)
template = re.sub(r'<div class="hero-stat-num">[^<]*</div>(\s*)<div class="hero-stat-label">Categories</div>', 
                  f'<div class="hero-stat-num">{category_count}</div>\\1<div class="hero-stat-label">Categories</div>', template)

# Replace count display
template = re.sub(r'<div class="header-pill">[^<]+</div>', f'<div class="header-pill">{company_count} COMPANIES</div>', template)
template = re.sub(r'<span id="cc">Showing \d+ of \d+</span>', f'<span id="cc">Showing {company_count} of {company_count}</span>', template)

# Robust replacement of cards-grid content
# This replaces the content between <div class="cards-grid"> and its matching closing </div>
# Assuming no nested div with class "cards-grid"
template = re.sub(r'(<div class="cards-grid">)(.*?)(</div>\s*</div>\s*</div>\s*<footer)', 
                  r'\1' + company_cards_html + r'\3', template, flags=re.DOTALL)

with open('index.html', 'w') as f:
    f.write(template)

print(f"✅ Rebuilt Radar: {company_count} companies across {region_count} regions.")
