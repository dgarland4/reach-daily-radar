#!/usr/bin/env python3
"""
REACH Daily Radar — Notion-to-HTML Rebuilder
Fetches all companies from Notion, rebuilds complete index.html
Run by GitHub Action on every REACH Daily trigger.
"""

import os
import json
import requests
from datetime import datetime

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
DATE_LABEL = os.environ.get("DATE_LABEL", datetime.now().strftime("%B %-d, %Y"))
DATABASE_ID = "135c09f5319d41bfa9a92089ee4ac5e6"
TODAY = datetime.now().strftime("%Y-%m-%d")

# SCV logo is stored in scv_logo.py alongside this script
try:
    from scv_logo import SCV_LOGO
except ImportError:
    SCV_LOGO = ""  # fallback: no logo

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

STATUS_COLORS = {
    "New": "#FFF9C4",
    "Researching": "#E3F2FD",
    "Contacted": "#E8F5E9",
    "Portfolio": "#F3E5F5",
    "Pass": "#FAFAFA"
}

REGION_ORDER = [
    ("US",     "🇺🇸 North America"),
    ("LatAm",  "🌎 Latin America"),
    ("Europe", "🇬🇧 Europe"),
    ("MENA",   "🇦🇪 MENA"),
    ("APAC",   "🌏 APAC"),
    ("Global", "🌐 Global"),
]


def clean(s):
    """Strip surrogate characters that cannot be encoded in UTF-8."""
    if not s:
        return s
    try:
        return s.encode("utf-16", "surrogatepass").decode("utf-16")
    except Exception:
        return s.encode("utf-8", "replace").decode("utf-8")


def get_prop(page, name, default=""):
    props = page.get("properties", {})
    p = props.get(name, {})
    t = p.get("type", "")
    if t == "title":
        items = p.get("title", [])
        return clean(items[0]["plain_text"]) if items else default
    if t == "rich_text":
        items = p.get("rich_text", [])
        return clean(items[0]["plain_text"]) if items else default
    if t == "select":
        sel = p.get("select")
        return clean(sel["name"]) if sel else default
    if t == "url":
        return p.get("url") or default
    if t == "date":
        d = p.get("date")
        return d["start"] if d else default
    return default


def fetch_all_companies():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    companies = []
    cursor = None
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        r = requests.post(url, headers=HEADERS, json=payload)
        r.raise_for_status()
        data = r.json()
        companies.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return companies


def urgency_badge(date_added, status):
    if status == "Portfolio":
        return '<span class="badge badge-portfolio">&#11088; Portfolio</span>'
    if date_added == TODAY:
        return '<span class="badge badge-hot">&#128293; Hot</span>'
    return '<span class="badge badge-watch">&#128064; Watch</span>'


def type_badge(type_val):
    if type_val == "Adjacent":
        return '<span class="badge badge-adjacent">Adjacent</span>'
    return '<span class="badge badge-core">Core</span>'


def build_card(company):
    name        = get_prop(company, "Company Name")
    website     = get_prop(company, "Website")
    region      = get_prop(company, "Region", "US")
    category    = get_prop(company, "Category", "PropTech")
    type_val    = get_prop(company, "Type", "Core")
    stage       = get_prop(company, "Stage / Round", "Unknown")
    status      = get_prop(company, "Status", "New")
    description = get_prop(company, "Company Description")
    why_scv     = get_prop(company, "Why SCV / REACH")
    source      = get_prop(company, "Source")
    date_added  = get_prop(company, "Date Added")

    domain = website.replace("https://", "").replace("http://", "").rstrip("/") if website else ""
    logo_url     = f"https://logo.clearbit.com/{domain}" if domain else ""
    status_color = STATUS_COLORS.get(status, "#FFF9C4")
    data_tags    = f"{region} {category} {type_val}"

    # Escape single quotes for JS onerror
    return f"""    <div class="card" data-tags="{data_tags}" data-date="{date_added}">
      <div class="card-top">
        <div class="card-logo-wrap"><img src="{logo_url}" class="card-logo" alt="{name} logo" onerror="this.style.display='none'"></div>
        <div class="card-identity">
          <div class="card-name-row">
            <div class="card-name">{name}</div>
            <a class="card-website" href="{website}" target="_blank">&#8599; {domain}</a>
          </div>
          <div class="card-meta-row">
            {urgency_badge(date_added, status)}
            {type_badge(type_val)}
            <span class="tag">{category}</span>
            <span class="tag">{stage}</span>
          </div>
        </div>
        <div class="status-pill" style="background:{status_color}">{status}</div>
      </div>
      <div class="card-desc-label">Company Description</div>
      <p class="card-tagline">{description}</p>
      <div class="scv-angle">
        <div class="scv-angle-label">Why SCV / REACH</div>
        <div class="scv-angle-text">{why_scv}</div>
      </div>
      <div class="card-footer">
        <div class="card-footer-left">
          <span class="source-label">Source:</span>
          <span class="source-name">{source}</span>
          <span class="card-date">&#183; {date_added}</span>
        </div>
        <div class="owner-chip"><div class="owner-avatar">DG</div>Dave Garland</div>
      </div>
    </div>"""


CSS = """  :root {
    --reach-blue:#1B5BA7; --navy:#1B2A5E; --charcoal:#3C3C3C;
    --white:#FFFFFF; --off-white:#F7F9FC; --rule:#E2E8F0;
    --text-secondary:#6B7A99;
  }
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Montserrat',sans-serif;background:var(--off-white);color:var(--charcoal)}
  .site-header{background:var(--white);border-bottom:3px solid var(--reach-blue);padding:0 48px;display:flex;align-items:center;justify-content:space-between;height:76px;position:sticky;top:0;z-index:100;box-shadow:0 2px 12px rgba(27,91,167,.08)}
  .logo-block{display:flex;align-items:center;gap:20px}
  .scv-logo{height:52px;width:auto}
  .logo-divider{width:1px;height:30px;background:var(--rule)}
  .logo-subtitle{font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--text-secondary);line-height:1.3}
  .logo-subtitle span{display:block;font-size:9px;font-weight:500;color:#9AACCC;margin-top:2px}
  .header-meta{display:flex;align-items:center;gap:20px}
  .header-date{font-size:12px;font-weight:600;color:var(--text-secondary);letter-spacing:.06em;text-transform:uppercase}
  .header-pill{background:var(--reach-blue);color:var(--white);font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:6px 16px;border-radius:20px}
  .hero{background:linear-gradient(135deg,var(--navy) 0%,var(--reach-blue) 100%);padding:52px 48px 44px;position:relative;overflow:hidden}
  .hero::before{content:'';position:absolute;right:-60px;top:-60px;width:320px;height:320px;border-radius:50%;border:40px solid rgba(255,255,255,.05)}
  .hero-label{font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:10px}
  .hero-title{font-size:36px;font-weight:700;color:var(--white);letter-spacing:-.01em;line-height:1.1;margin-bottom:10px}
  .hero-title span{color:rgba(255,255,255,.5);font-weight:500}
  .hero-sub{font-size:14px;font-weight:500;color:rgba(255,255,255,.65);max-width:580px;line-height:1.6;margin-bottom:28px}
  .hero-stats{display:flex;gap:36px;flex-wrap:wrap}
  .hero-stat{display:flex;flex-direction:column;gap:3px}
  .hero-stat-num{font-size:28px;font-weight:700;color:var(--white);line-height:1}
  .hero-stat-label{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:rgba(255,255,255,.45)}
  .region-tabs{background:var(--white);border-bottom:1px solid var(--rule);padding:0 48px;display:flex;align-items:center;gap:4px;height:48px;overflow-x:auto}
  .rtab{padding:6px 16px;border-radius:6px;border:none;background:transparent;font-family:'Montserrat',sans-serif;font-size:12px;font-weight:600;color:var(--text-secondary);cursor:pointer;white-space:nowrap;transition:all .15s ease}
  .rtab:hover,.rtab.active{background:var(--reach-blue);color:var(--white)}
  .main{max-width:1280px;margin:0 auto;padding:36px 48px 80px}
  .section-header{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:20px}
  .section-title{font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--reach-blue)}
  .section-count{font-size:12px;font-weight:600;color:var(--text-secondary)}
  .section-divider{display:flex;align-items:center;gap:14px;margin:32px 0 20px}
  .section-divider-label{font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--reach-blue);white-space:nowrap}
  .section-divider-line{flex:1;height:1px;background:var(--rule)}
  .cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(500px,1fr));gap:18px}
  .card{background:var(--white);border:1px solid var(--rule);border-radius:12px;padding:22px 22px 18px;display:flex;flex-direction:column;gap:12px;transition:box-shadow .2s ease,transform .2s ease;animation:fadeUp .4s ease both}
  .card:hover{box-shadow:0 8px 32px rgba(27,91,167,.10);transform:translateY(-2px)}
  @keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
  .card-top{display:flex;align-items:flex-start;gap:12px}
  .card-logo-wrap{flex-shrink:0;width:40px;height:40px;border-radius:8px;border:1px solid var(--rule);display:flex;align-items:center;justify-content:center;overflow:hidden;background:#f8f8f8}
  .card-logo{width:32px;height:32px;object-fit:contain}
  .card-identity{flex:1;display:flex;flex-direction:column;gap:6px}
  .card-name-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
  .card-name{font-size:17px;font-weight:700;color:var(--navy)}
  .card-website{font-size:12px;font-weight:500;color:var(--reach-blue);text-decoration:none;opacity:.8}
  .card-website:hover{opacity:1;text-decoration:underline}
  .card-meta-row{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
  .badge{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:5px}
  .badge-hot{background:#FFF1F1;color:#C0392B}
  .badge-watch{background:#FFFBEB;color:#92400E}
  .badge-intl{background:#EFF6FF;color:#1E40AF}
  .badge-portfolio{background:#F3E5F5;color:#6A0DAD}
  .badge-core{background:#EBF2FF;color:#1B5BA7}
  .badge-adjacent{background:#F0FDF4;color:#166534}
  .tag{font-size:11px;font-weight:600;color:#475569;background:#F1F5F9;padding:3px 8px;border-radius:5px}
  .status-pill{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:20px;white-space:nowrap;align-self:flex-start;color:#5A4000;flex-shrink:0}
  .card-desc-label{font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--text-secondary)}
  .card-tagline{font-size:13px;font-weight:500;color:var(--charcoal);line-height:1.6}
  .scv-angle{background:var(--off-white);border-left:3px solid var(--reach-blue);border-radius:0 8px 8px 0;padding:10px 13px}
  .scv-angle-label{font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--reach-blue);margin-bottom:4px}
  .scv-angle-text{font-size:12px;font-weight:500;color:var(--charcoal);line-height:1.55}
  .card-footer{display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid var(--rule);flex-wrap:wrap;gap:6px}
  .card-footer-left{display:flex;align-items:center;gap:6px}
  .source-label{font-size:11px;font-weight:600;color:var(--text-secondary)}
  .source-name{font-size:11px;font-weight:600;color:var(--charcoal)}
  .card-date{font-size:11px;color:var(--text-secondary)}
  .owner-chip{display:flex;align-items:center;gap:6px;font-size:11px;font-weight:600;color:var(--text-secondary)}
  .owner-avatar{width:22px;height:22px;border-radius:50%;background:var(--reach-blue);color:var(--white);font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center}
  .site-footer{background:var(--navy);padding:20px 48px;display:flex;align-items:center;justify-content:space-between}
  .footer-tagline{font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:rgba(255,255,255,.35)}
  .footer-brand{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.25)}
  .tabs-divider{width:1px;height:22px;background:var(--rule);margin:0 6px;flex-shrink:0}
  .sort-btn{border:1px solid var(--rule) !important;margin-left:2px}
  .sort-btn.sort-active{background:var(--navy) !important;color:var(--white) !important;border-color:var(--navy) !important}
  .view-toggle{display:flex;align-items:center;gap:4px;margin-left:auto;flex-shrink:0}
  .vtab{padding:5px 11px;border-radius:6px;border:1px solid var(--rule);background:transparent;font-family:'Montserrat',sans-serif;font-size:12px;font-weight:600;color:var(--text-secondary);cursor:pointer;line-height:1;transition:all .15s ease}
  .vtab.active,.vtab:hover{background:var(--navy);color:var(--white);border-color:var(--navy)}
  .list-view{display:none;width:100%;border:1px solid var(--rule);border-radius:12px;overflow:hidden;background:var(--white)}
  .list-view.visible{display:block}
  .list-header{display:grid;grid-template-columns:36px 2fr 1fr 1fr 1fr 1fr 100px;gap:0;background:var(--navy);padding:0}
  .list-header-cell{font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);padding:10px 14px}
  .list-row{display:grid;grid-template-columns:36px 2fr 1fr 1fr 1fr 1fr 100px;gap:0;border-top:1px solid var(--rule);align-items:center;transition:background .12s ease;animation:fadeUp .3s ease both}
  .list-row:hover{background:#F0F5FF}
  .list-row.hidden{display:none}
  .list-cell{padding:10px 14px;font-size:12px;font-weight:500;color:var(--charcoal);overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
  .list-cell-logo{padding:8px 6px 8px 10px;display:flex;align-items:center;justify-content:center}
  .list-logo{width:22px;height:22px;object-fit:contain;border-radius:4px}
  .list-name{font-weight:700;color:var(--navy);font-size:13px}
  .list-name a{color:var(--reach-blue);text-decoration:none;font-size:11px;font-weight:500;margin-left:7px;opacity:.7}
  .list-name a:hover{opacity:1;text-decoration:underline}
  .list-badge{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.04em;padding:2px 7px;border-radius:4px;white-space:nowrap}
  .list-status{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:10px;display:inline-block}
  @media(max-width:768px){
    .site-header{padding:0 16px}.hero{padding:32px 16px 28px}
    .region-tabs,.main{padding:0 16px}.main{padding:24px 16px 60px}
    .cards-grid{grid-template-columns:1fr}.hero-title{font-size:24px}
    .site-footer{padding:14px 16px;flex-direction:column;gap:6px;text-align:center}
  }"""

JS = """let currentFilter='all',sortNewest=false,currentView='card';
function buildListRows(){const allCards=Array.from(document.querySelectorAll('.card'));const container=document.getElementById('list-rows');container.innerHTML='';allCards.forEach(card=>{const tags=card.getAttribute('data-tags')||'';const date=card.getAttribute('data-date')||'';const name=card.querySelector('.card-name')?.textContent||'';const website=card.querySelector('.card-website')?.href||'';const domain=card.querySelector('.card-website')?.textContent?.replace('\u2197 ','')||'';const logo=card.querySelector('.card-logo')?.src||'';const category=[...card.querySelectorAll('.tag')][0]?.textContent||'';const stage=[...card.querySelectorAll('.tag')][1]?.textContent||'';const status=card.querySelector('.status-pill')?.textContent||'';const statusBg=card.querySelector('.status-pill')?.style.background||'#FFF9C4';const typeBadge=card.querySelector('.badge-core,.badge-adjacent');const typeText=typeBadge?.textContent||'';const typeBg=typeBadge?.classList.contains('badge-core')?'#EBF2FF':'#F0FDF4';const typeColor=typeBadge?.classList.contains('badge-core')?'#1B5BA7':'#166534';const region=tags.split(' ')[0]||'';const row=document.createElement('div');row.className='list-row';row.setAttribute('data-tags',tags);row.setAttribute('data-date',date);row.innerHTML=`<div class="list-cell list-cell-logo"><img src="${logo}" class="list-logo" onerror="this.style.display='none'"></div><div class="list-cell list-name">${name}<a href="${website}" target="_blank">\u2197 ${domain}</a></div><div class="list-cell"><span class="list-badge" style="background:#F1F5F9;color:#475569">${category}</span></div><div class="list-cell"><span class="list-badge" style="background:#F1F5F9;color:#475569">${region}</span></div><div class="list-cell">${stage}</div><div class="list-cell"><span class="list-badge" style="background:${typeBg};color:${typeColor}">${typeText}</span></div><div class="list-cell"><span class="list-status" style="background:${statusBg};color:#5A4000">${status}</span></div>`;container.appendChild(row);});}
function setView(view){currentView=view;const cardViewEls=document.querySelectorAll('.section-divider,.cards-grid:not(#sorted-view),#sorted-view');const listView=document.getElementById('list-view');document.getElementById('view-card-btn').classList.toggle('active',view==='card');document.getElementById('view-list-btn').classList.toggle('active',view==='list');if(view==='list'){buildListRows();listView.classList.add('visible');cardViewEls.forEach(el=>el.style.display='none');applyListFilter();}else{listView.classList.remove('visible');applyFilterAndSort();}}
function applyListFilter(){const rows=document.querySelectorAll('#list-rows .list-row');let visible=0;rows.forEach(row=>{const tags=row.getAttribute('data-tags')||'';const show=currentFilter==='all'||tags.includes(currentFilter);row.classList.toggle('hidden',!show);if(show)visible++;});if(sortNewest){const container=document.getElementById('list-rows');const rowArr=Array.from(rows).filter(r=>!r.classList.contains('hidden'));rowArr.sort((a,b)=>(b.getAttribute('data-date')||'').localeCompare(a.getAttribute('data-date')||''));rowArr.forEach(r=>container.appendChild(r));}document.getElementById('card-count').textContent='Showing '+visible+' of '+rows.length;}
function filterCards(tag,btn){currentFilter=tag;document.querySelectorAll('.rtab:not(.sort-btn)').forEach(b=>b.classList.remove('active'));btn.classList.add('active');if(currentView==='list'){applyListFilter();}else{applyFilterAndSort();}}
function toggleSort(btn){sortNewest=!sortNewest;btn.classList.toggle('sort-active',sortNewest);btn.textContent=sortNewest?'\uD83D\uDCC5 Newest First \u2713':'\uD83D\uDCC5 Newest First';if(currentView==='list'){applyListFilter();}else{applyFilterAndSort();}}
function applyFilterAndSort(){const main=document.querySelector('.main');const allCards=Array.from(document.querySelectorAll('.card'));let visible=0;allCards.forEach(card=>{const tags=card.getAttribute('data-tags')||'';const show=currentFilter==='all'||tags.includes(currentFilter);card.style.display=show?'flex':'none';if(show)visible++;});document.getElementById('card-count').textContent='Showing '+visible+' of '+allCards.length;if(sortNewest){const visibleCards=allCards.filter(c=>c.style.display!=='none');visibleCards.sort((a,b)=>{const da=a.getAttribute('data-date')||'2000-01-01';const db=b.getAttribute('data-date')||'2000-01-01';return db.localeCompare(da);});let sortedWrap=document.getElementById('sorted-view');if(!sortedWrap){sortedWrap=document.createElement('div');sortedWrap.id='sorted-view';sortedWrap.className='cards-grid';sortedWrap.style.marginTop='20px';}sortedWrap.innerHTML='';visibleCards.forEach(c=>sortedWrap.appendChild(c.cloneNode(true)));document.querySelectorAll('.section-divider,.cards-grid:not(#sorted-view)').forEach(el=>el.style.display='none');const existing=document.getElementById('sorted-view');if(existing)existing.remove();main.appendChild(sortedWrap);}else{const sortedWrap=document.getElementById('sorted-view');if(sortedWrap)sortedWrap.remove();document.querySelectorAll('.section-divider,.cards-grid').forEach(el=>el.style.display='');allCards.forEach(card=>{const tags=card.getAttribute('data-tags')||'';const show=currentFilter==='all'||tags.includes(currentFilter);card.style.display=show?'flex':'none';});}}"""


def build_html(companies):
    by_region = {r[0]: [] for r in REGION_ORDER}
    for c in companies:
        region = get_prop(c, "Region", "US")
        bucket = by_region.get(region)
        if bucket is not None:
            bucket.append(c)
        else:
            by_region.setdefault(region, []).append(c)

    total = len(companies)
    regions_used = sum(1 for r in REGION_ORDER if by_region.get(r[0]))
    categories = set(get_prop(c, "Category", "PropTech") for c in companies)

    try:
        dt = datetime.strptime(DATE_LABEL, "%B %d, %Y")
        short_date = dt.strftime("%b %-d")
    except Exception:
        short_date = DATE_LABEL[:6]

    sections_html = ""
    for region_key, region_label in REGION_ORDER:
        region_companies = by_region.get(region_key, [])
        if not region_companies:
            continue
        cards_html = "\n".join(build_card(c) for c in region_companies)
        sections_html += f"""
  <div class="section-divider">
    <div class="section-divider-label">{region_label}</div>
    <div class="section-divider-line"></div>
  </div>
  <div class="cards-grid">
{cards_html}
  </div>"""

    logo_src = f"data:image/png;base64,{SCV_LOGO}" if SCV_LOGO else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>REACH Daily Radar \u2014 {DATE_LABEL}</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;900&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<header class="site-header">
  <div class="logo-block">
    <img src="{logo_src}" alt="Second Century Ventures" class="scv-logo">
    <div class="logo-divider"></div>
    <div class="logo-subtitle">Daily Radar<span>Second Century Ventures</span></div>
  </div>
  <div class="header-meta">
    <div class="header-date">{DATE_LABEL}</div>
    <div class="header-pill">{total} Companies</div>
  </div>
</header>
<div class="hero">
  <div class="hero-label">Global Startup Intelligence \u00b7 Powered by REACH</div>
  <h1 class="hero-title">Today's Radar <span>\u2014 Emerging Companies to Watch</span></h1>
  <p class="hero-sub">Curated daily from global proptech publications, YC, Crunchbase, Inman, TechCrunch, and regional feeds. Sourced from Notion \u00b7 Duplicate-protected \u00b7 Updated every morning.</p>
  <div class="hero-stats">
    <div class="hero-stat"><div class="hero-stat-num">{total}</div><div class="hero-stat-label">Companies Tracked</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{regions_used}</div><div class="hero-stat-label">Regions Covered</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{len(categories)}</div><div class="hero-stat-label">Categories</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{short_date}</div><div class="hero-stat-label">Last Updated</div></div>
  </div>
</div>
<div class="region-tabs">
  <button class="rtab active" onclick="filterCards('all',this)">\U0001f310 All</button>
  <button class="rtab" onclick="filterCards('US',this)">\U0001f1fa\U0001f1f8 US</button>
  <button class="rtab" onclick="filterCards('LatAm',this)">\U0001f30e LatAm</button>
  <button class="rtab" onclick="filterCards('Europe',this)">\U0001f1ec\U0001f1e7 Europe</button>
  <button class="rtab" onclick="filterCards('MENA',this)">\U0001f1e6\U0001f1ea MENA</button>
  <button class="rtab" onclick="filterCards('APAC',this)">\U0001f30f APAC</button>
  <button class="rtab" onclick="filterCards('Core',this)">Core</button>
  <button class="rtab" onclick="filterCards('Adjacent',this)">Adjacent</button>
  <button class="rtab" onclick="filterCards('AI',this)">AI</button>
  <button class="rtab" onclick="filterCards('FinTech',this)">FinTech</button>
  <button class="rtab" onclick="filterCards('PropTech',this)">PropTech</button>
  <div class="tabs-divider"></div>
  <button class="rtab sort-btn" id="sort-btn" onclick="toggleSort(this)">\U0001f4c5 Newest First</button>
  <div class="tabs-divider"></div>
  <div class="view-toggle">
    <button class="vtab active" id="view-card-btn" onclick="setView('card')">\u229e Cards</button>
    <button class="vtab" id="view-list-btn" onclick="setView('list')">\u2630 List</button>
  </div>
</div>
<main class="main">
  <div class="section-header">
    <div class="section-title">\u26a1 All Companies \u00b7 REACH Daily Radar</div>
    <div class="section-count" id="card-count">Showing {total} of {total}</div>
  </div>
  <div class="list-view" id="list-view">
    <div class="list-header">
      <div class="list-header-cell"></div>
      <div class="list-header-cell">Company</div>
      <div class="list-header-cell">Category</div>
      <div class="list-header-cell">Region</div>
      <div class="list-header-cell">Stage</div>
      <div class="list-header-cell">Type</div>
      <div class="list-header-cell">Status</div>
    </div>
    <div id="list-rows"></div>
  </div>
{sections_html}
</main>
<footer class="site-footer">
  <div class="footer-tagline">Accelerating Real Estate \u00b7 REACH Daily Radar</div>
  <div class="footer-brand">Second Century Ventures \u00b7 \u00a9 2026</div>
</footer>
<script>
{JS}
</script>
</body>
</html>"""


if __name__ == "__main__":
    print(f"Date: {DATE_LABEL}")
    print(f"Fetching from Notion DB {DATABASE_ID}...")
    companies = fetch_all_companies()
    print(f"Fetched {len(companies)} companies")
    html = build_html(companies)
    # Sanitize surrogate characters that can't be encoded in UTF-8
    html = html.encode("utf-8", errors="replace").decode("utf-8")
    with open("index.html", "w", encoding="utf-8", errors="replace") as f:
        f.write(html)
    print(f"Done: index.html written ({len(html):,} bytes, {len(companies)} companies)")
