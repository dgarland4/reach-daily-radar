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

# Get all values from sheet
all_rows = sheet.get_all_records()

# Process data
company_count = len(all_rows)
regions = set()
categories = set()
company_cards_html = ""

def clean_id(text):
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

for row in all_rows:
    name = row.get('Company Name', 'Unknown')
    website = row.get('Website', '#')
    desc = row.get('Company Description', '')
    problem = row.get('Problem Solved', '')
    cat = row.get('Category', 'PropTech')
    subcat = row.get('Subcategory', '')
    region = row.get('Region', 'US')
    stage = row.get('Stage / Round', 'Seed')
    source = row.get('Source', 'Direct')
    date_added = row.get('Date Added', '')
    why_scv = row.get('Why SCV / REACH', '')
    
    regions.add(region)
    categories.add(cat)
    
    clean_url = website.replace('https://', '').replace('http://', '').split('/')[0]
    
    tags = f"{clean_id(region)} {clean_id(cat)}"
    
    card = f"""
    <div class="card" data-tags="{tags}" data-date="{date_added}">
        <div class="card-top">
            <div class="card-logo-wrap">
                <div class="owner-avatar">{name[0]}</div>
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
template = re.sub(r'<div class="hero-stat-num">(\d+)</div>\s*<div class="hero-stat-label">Companies Tracked</div>', 
                  f'<div class="hero-stat-num">{company_count}</div><div class="hero-stat-label">Companies Tracked</div>', template)
template = re.sub(r'<div class="hero-stat-num">(\d+)</div>\s*<div class="hero-stat-label">Regions Covered</div>', 
                  f'<div class="hero-stat-num">{region_count}</div><div class="hero-stat-label">Regions Covered</div>', template)
template = re.sub(r'<div class="hero-stat-num">(\d+)</div>\s*<div class="hero-stat-label">Categories</div>', 
                  f'<div class="hero-stat-num">{category_count}</div><div class="hero-stat-label">Categories</div>', template)

# Replace count display
template = re.sub(r'<div class="header-pill">\d+ COMPANIES</div>', f'<div class="header-pill">{company_count} COMPANIES</div>', template)
template = re.sub(r'<span id="cc">Showing \d+ of \d+</span>', f'<span id="cc">Showing {company_count} of {company_count}</span>', template)

# Replace company grid
grid_start = template.find('<div class="cards-grid">')
grid_end = template.find('</div>', grid_start) + 6
# Look for the end of the cards grid properly
# Since the template has many nested divs, we use a more robust replacement for the cards container
template = re.sub(r'<div class="cards-grid">.*?</div>\s*</div>\s*</div>\s*<footer', 
                  f'<div class="cards-grid">{company_cards_html}</div></div></div><footer', template, flags=re.DOTALL)

with open('index.html', 'w') as f:
    f.write(template)

print(f"✅ Rebuilt Radar: {company_count} companies across {region_count} regions.")
