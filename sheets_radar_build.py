import gspread
from google.oauth2.service_account import Credentials
import json, os, re
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

# Get all values from sheet (row 4 is header)
all_values = sheet.get_all_values()
headers = all_values[3]
rows = all_values[4:]
all_rows = []
for row in rows:
    record = dict(zip(headers, row))
    all_rows.append(record)

TODAY = datetime.now().strftime('%Y-%m-%d')
DATE_LABEL = datetime.now().strftime('%B %-d, %Y')

try:
    from scv_logo import SCV_LOGO
except ImportError:
    SCV_LOGO = ''

STATUS_COLORS = {
    'New': '#FFF9C4', 'Researching': '#E3F2FD',
    'Contacted': '#E8F5E9', 'Portfolio': '#F3E5F5', 'Pass': '#FAFAFA'
}

REGION_ORDER = [
    ('US', '\U0001f1fa\U0001f1f8 North America'),
    ('LatAm', '\U0001f30e Latin America'),
    ('Europe', '\U0001f1ec\U0001f1e7 Europe'),
    ('MENA', '\U0001f1e6\U0001f1ea MENA'),
    ('APAC', '\U0001f1ef APAC'),
    ('ANZ', '\U0001f1e6\U0001f1fa ANZ'),
    ('Global', '\U0001f310 Global'),
]

def clean_id(text):
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

by_region = {r[0]: [] for r in REGION_ORDER}
regions = set()
categories = set()
total_cards = 0
list_rows = []

for row in all_rows:
    name = str(row.get('Company Name', '')).strip()
    if not name or name == 'Unknown' or name == '':
        continue
    website = str(row.get('Website', '#')).strip()
    desc = str(row.get('Company Description', '')).strip()
    cat = str(row.get('Category', 'PropTech')).strip()
    subcat = str(row.get('Subcategory', '')).strip()
    region = str(row.get('Region', 'US')).strip()
    stage = str(row.get('Stage / Round', 'Seed')).strip()
    source = str(row.get('Source', 'Direct')).strip()
    date_added = str(row.get('Date Added', '')).strip()
    why_scv = str(row.get('Why SCV / REACH', '')).strip()
    status = str(row.get('Status', 'New')).strip() or 'New'
    ctype = str(row.get('Type', 'Core')).strip() or 'Core'

    if region:
        regions.add(region)
    if cat:
        categories.add(cat)

    clean_url = website.replace('https://', '').replace('http://', '').split('/')[0]
    tags = f"{clean_id(region)} {clean_id(cat)}"
    sc = STATUS_COLORS.get(status, '#FFF9C4')
    badge_class = 'badge-adjacent' if ctype == 'Adjacent' else 'badge-core'
    urgency_badge = '<span class="badge badge-hot">\U0001f525 Hot</span>' if date_added == TODAY else '<span class="badge badge-watch">\U0001f440 Watch</span>'
    if status == 'Portfolio':
        urgency_badge = '<span class="badge badge-portfolio">\u2b50 Portfolio</span>'

    card = f'''<div class="card" data-tags="{tags}" data-date="{date_added}">
  <div class="card-top">
    <div class="card-logo-wrap">
      <div class="owner-avatar" style="background: #1B5BA7; color: white; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-weight: 700;">{name[0] if name else '?'}</div>
    </div>
    <div class="card-identity">
      <div class="card-name-row">
        <span class="card-name">{name}</span>
        <a href="{website}" target="_blank" class="card-website">\u2197 {clean_url}</a>
      </div>
      <div class="card-meta-row">
        {urgency_badge}
        <span class="badge {badge_class}">{ctype}</span>
        <span class="tag">{cat}</span>
        <span class="tag">{stage}</span>
      </div>
    </div>
    <span class="status-pill" style="background:{sc};">{status}</span>
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
      <span class="card-date">\u00b7 {date_added}</span>
    </div>
    <div class="owner-chip">
      <div class="owner-avatar">DG</div>
      <span>Dave Garland</span>
    </div>
  </div>
</div>'''
    by_region.setdefault(region, []).append(card)
    total_cards += 1

    # Build list-row HTML for this company
    list_row = f'''<div class="list-row" data-tags="{tags}" data-date="{date_added}">
            <div class="list-col list-col-name">{name}</div>
                    <div class="list-col list-col-category">{cat}</div>
                            <div class="list-col list-col-stage">{stage}</div>
                                    <div class="list-col list-col-region">{region}</div>
                                            <div class="list-col list-col-status">{status}</div>
                                                    <div class="list-col list-col-website"><a href="{website}" target="_blank">Visit</a></div>
                                                        </div>'''
    list_rows.append(list_row)

# Build sections HTML
sections = ''
for rk, rl in REGION_ORDER:
    rc = by_region.get(rk, [])
    if not rc:
        continue
    cards_html = '\n'.join(rc)
    sections += f'''<div class="section-divider" data-region="{rk}">
  <div class="section-divider-label">{rl}</div>
  <div class="section-divider-line"></div>
</div>
<div class="cards-grid">{cards_html}</div>'''

region_count = len([r for r, _ in REGION_ORDER if by_region.get(r)])
category_count = len(categories)

# Build the new hero-stats block with correct numbers and white labels
new_hero_stats = f'''<div class="hero-stats">
<div class="hero-stat"><div class="hero-stat-num">{total_cards}</div><div class="hero-stat-label">Companies Tracked</div></div>
<div class="hero-stat"><div class="hero-stat-num">{region_count}</div><div class="hero-stat-label">Regions Covered</div></div>
<div class="hero-stat"><div class="hero-stat-num">{category_count}</div><div class="hero-stat-label">Categories</div></div>
<div class="hero-stat"><div class="hero-stat-num">{DATE_LABEL}</div><div class="hero-stat-label">Last Updated</div></div>
</div>'''

# Read existing index.html
with open('index.html', 'r') as f:
    template = f.read()

# Fix CSS: make hero-stat-label solid white (not semi-transparent)
template = re.sub(
    r'\.hero-stat-label\{[^}]+\}',
    '.hero-stat-label{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#FFFFFF}',
    template
)

# Replace the entire hero-stats block
template = re.sub(
    r'<div class="hero-stats">.*?</div>\s*</div>\s*</div>\s*</div>',
    new_hero_stats + '\n</div>\n</div>\n</div>',
    template,
    flags=re.DOTALL
)

# Replace header stats
template = re.sub(r'<span class="header-date">[^<]+</span>', f'<span class="header-date">{DATE_LABEL}</span>', template)
template = re.sub(r'<span class="header-pill">[^<]+</span>', f'<span class="header-pill">{total_cards} Companies</span>', template)

# Replace showing count
template = re.sub(r'Showing \d+ of \d+', f'Showing {total_cards} of {total_cards}', template)

# Replace all company cards sections
sections_pattern = r'(?s)(<div id="list-rows"></div>\s*</div>).*?(<div class="site-footer">)'
if re.search(sections_pattern, template):
    template = re.sub(sections_pattern, f'\\1\n{sections}\n\\2', template)
else:
    template = re.sub(sections_pattern, '', template)

# Build list_rows HTML
list_rows_html = '\n'.join(list_rows)

# Replace list-rows content
template = re.sub(r'<div id="list-rows"></div>', f'<div id="list-rows">{list_rows_html}</div>', template)


# Replace title
template = re.sub(r'<title>[^<]+</title>', f'<title>{DATE_LABEL}</title>', template)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(template)

print(f'\u2705 Rebuilt Radar: {total_cards} companies, {region_count} regions, {category_count} categories. Date: {DATE_LABEL}')
