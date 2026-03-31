#!/usr/bin/env python3
import os, requests
from datetime import datetime

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
DATE_LABEL = os.environ.get("DATE_LABEL") or datetime.now().strftime("%B %-d, %Y")
DATABASE_ID = "135c09f5319d41bfa9a92089ee4ac5e6"
TODAY = datetime.now().strftime("%Y-%m-%d")

try:
    from scv_logo import SCV_LOGO
except ImportError:
    SCV_LOGO = ""

HEADERS = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

STATUS_COLORS = {
    "New": "#FFF9C4", "Researching": "#E3F2FD",
    "Contacted": "#E8F5E9", "Portfolio": "#F3E5F5", "Pass": "#FAFAFA"
}

REGION_ORDER = [
    ("US", "&#127482;&#127480; North America"),
    ("LatAm", "&#127758; Latin America"),
    ("Europe", "&#127468;&#127463; Europe"),
    ("MENA", "&#127462;&#127466; MENA"),
    ("APAC", "&#127471; APAC"),
    ("Global", "&#127760; Global"),
]

def clean(s):
    if not s:
        return s
    try:
        return s.encode("utf-16", "surrogatepass").decode("utf-16")
    except Exception:
        return s.encode("utf-8", "replace").decode("utf-8")

def get_prop(page, name, default=""):
    p = page.get("properties", {}).get(name, {})
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

def fetch_all():
    url = "https://api.notion.com/v1/databases/" + DATABASE_ID + "/query"
    companies, cursor = [], None
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

def urgency(date_added, status):
    if status == "Portfolio":
        return '<span class="badge badge-portfolio">&#11088; Portfolio</span>'
    if date_added == TODAY:
        return '<span class="badge badge-hot">&#128293; Hot</span>'
    return '<span class="badge badge-watch">&#128064; Watch</span>'

def typebadge(t):
    if t == "Adjacent":
        return '<span class="badge badge-adjacent">Adjacent</span>'
    return '<span class="badge badge-core">Core</span>'

def build_card(c):
    nm = get_prop(c, "Company Name")
    ws = get_prop(c, "Website")
    rg = get_prop(c, "Region", "US")
    cat = get_prop(c, "Category", "PropTech")
    tv = get_prop(c, "Type", "Core")
    st = get_prop(c, "Stage / Round", "Unknown")
    ss = get_prop(c, "Status", "New")
    ds = get_prop(c, "Company Description")
    wh = get_prop(c, "Why SCV / REACH")
    sr = get_prop(c, "Source")
    da = get_prop(c, "Date Added")
    dm = ws.replace("https://", "").replace("http://", "").rstrip("/") if ws else ""
    lg = "https://logo.clearbit.com/" + dm if dm else ""
    sc = STATUS_COLORS.get(ss, "#FFF9C4")
    lines = [
        '    <div class="card" data-tags="' + rg + ' ' + cat + ' ' + tv + '" data-date="' + da + '">',
        '      <div class="card-top">',
        '        <div class="card-logo-wrap"><img src="' + lg + '" class="card-logo" onerror="this.style.display=\'none\'"></div>',
        '        <div class="card-identity">',
        '          <div class="card-name-row"><div class="card-name">' + nm + '</div><a class="card-website" href="' + ws + '" target="_blank">&#8599; ' + dm + '</a></div>',
        '          <div class="card-meta-row">' + urgency(da, ss) + typebadge(tv) + '<span class="tag">' + cat + '</span><span class="tag">' + st + '</span></div>',
        '        </div>',
        '        <div class="status-pill" style="background:' + sc + '">' + ss + '</div>',
        '      </div>',
        '      <div class="card-desc-label">Company Description</div>',
        '      <p class="card-tagline">' + ds + '</p>',
        '      <div class="scv-angle"><div class="scv-angle-label">Why SCV / REACH</div><div class="scv-angle-text">' + wh + '</div></div>',
        '      <div class="card-footer">',
        '        <div class="card-footer-left"><span class="source-label">Source:</span><span class="source-name">' + sr + '</span><span class="card-date">&#183; ' + da + '</span></div>',
        '        <div class="owner-chip"><div class="owner-avatar">DG</div>Dave Garland</div>',
        '      </div>',
        '    </div>',
    ]
    return "\n".join(lines)

CSS = """:root{--reach-blue:#1B5BA7;--navy:#1B2A5E;--charcoal:#3C3C3C;--white:#FFFFFF;--off-white:#F7F9FC;--rule:#E2E8F0;--text-secondary:#6B7A99}*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}body{font-family:'Montserrat',sans-serif;background:var(--off-white);color:var(--charcoal)}.site-header{background:var(--white);border-bottom:3px solid var(--reach-blue);padding:0 48px;display:flex;align-items:center;justify-content:space-between;height:76px;position:sticky;top:0;z-index:100;box-shadow:0 2px 12px rgba(27,91,167,.08)}.logo-block{display:flex;align-items:center;gap:20px}.scv-logo{height:52px;width:auto}.logo-divider{width:1px;height:30px;background:var(--rule)}.logo-subtitle{font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--text-secondary);line-height:1.3}.logo-subtitle span{display:block;font-size:9px;font-weight:500;color:#9AACCC;margin-top:2px}.header-meta{display:flex;align-items:center;gap:20px}.header-date{font-size:12px;font-weight:600;color:var(--text-secondary);letter-spacing:.06em;text-transform:uppercase}.header-pill{background:var(--reach-blue);color:var(--white);font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:6px 16px;border-radius:20px}.hero{background:linear-gradient(135deg,var(--navy) 0%,var(--reach-blue) 100%);padding:52px 48px 44px;position:relative;overflow:hidden}.hero::before{content:'';position:absolute;right:-60px;top:-60px;width:320px;height:320px;border-radius:50%;border:40px solid rgba(255,255,255,.05)}.hero-label{font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:10px}.hero-title{font-size:36px;font-weight:700;color:var(--white);letter-spacing:-.01em;line-height:1.1;margin-bottom:10px}.hero-title span{color:rgba(255,255,255,.5);font-weight:500}.hero-sub{font-size:14px;font-weight:500;color:rgba(255,255,255,.65);max-width:580px;line-height:1.6;margin-bottom:28px}.hero-stats{display:flex;gap:36px;flex-wrap:wrap}.hero-stat{display:flex;flex-direction:column;gap:3px}.hero-stat-num{font-size:28px;font-weight:700;color:var(--white);line-height:1}.hero-stat-label{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:rgba(255,255,255,.45)}.region-tabs{background:var(--white);border-bottom:1px solid var(--rule);padding:0 48px;display:flex;align-items:center;gap:4px;height:48px;overflow-x:auto}.rtab{padding:6px 16px;border-radius:6px;border:none;background:transparent;font-family:'Montserrat',sans-serif;font-size:12px;font-weight:600;color:var(--text-secondary);cursor:pointer;white-space:nowrap;transition:all .15s ease}.rtab:hover,.rtab.active{background:var(--reach-blue);color:var(--white)}.main{max-width:1280px;margin:0 auto;padding:36px 48px 80px}.section-header{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:20px}.section-title{font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--reach-blue)}.section-count{font-size:12px;font-weight:600;color:var(--text-secondary)}.section-divider{display:flex;align-items:center;gap:14px;margin:32px 0 20px}.section-divider-label{font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--reach-blue);white-space:nowrap}.section-divider-line{flex:1;height:1px;background:var(--rule)}.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(500px,1fr));gap:18px}.card{background:var(--white);border:1px solid var(--rule);border-radius:12px;padding:22px 22px 18px;display:flex;flex-direction:column;gap:12px;transition:box-shadow .2s ease,transform .2s ease;animation:fadeUp .4s ease both}.card:hover{box-shadow:0 8px 32px rgba(27,91,167,.10);transform:translateY(-2px)}@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}.card-top{display:flex;align-items:flex-start;gap:12px}.card-logo-wrap{flex-shrink:0;width:40px;height:40px;border-radius:8px;border:1px solid var(--rule);display:flex;align-items:center;justify-content:center;overflow:hidden;background:#f8f8f8}.card-logo{width:32px;height:32px;object-fit:contain}.card-identity{flex:1;display:flex;flex-direction:column;gap:6px}.card-name-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.card-name{font-size:17px;font-weight:700;color:var(--navy)}.card-website{font-size:12px;font-weight:500;color:var(--reach-blue);text-decoration:none;opacity:.8}.card-website:hover{opacity:1;text-decoration:underline}.card-meta-row{display:flex;align-items:center;gap:7px;flex-wrap:wrap}.badge{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:5px}.badge-hot{background:#FFF1F1;color:#C0392B}.badge-watch{background:#FFFBEB;color:#92400E}.badge-intl{background:#EFF6FF;color:#1E40AF}.badge-portfolio{background:#F3E5F5;color:#6A0DAD}.badge-core{background:#EBF2FF;color:#1B5BA7}.badge-adjacent{background:#F0FDF4;color:#166534}.tag{font-size:11px;font-weight:600;color:#475569;background:#F1F5F9;padding:3px 8px;border-radius:5px}.status-pill{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:20px;white-space:nowrap;align-self:flex-start;color:#5A4000;flex-shrink:0}.card-desc-label{font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--text-secondary)}.card-tagline{font-size:13px;font-weight:500;color:var(--charcoal);line-height:1.6}.scv-angle{background:var(--off-white);border-left:3px solid var(--reach-blue);border-radius:0 8px 8px 0;padding:10px 13px}.scv-angle-label{font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--reach-blue);margin-bottom:4px}.scv-angle-text{font-size:12px;font-weight:500;color:var(--charcoal);line-height:1.55}.card-footer{display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid var(--rule);flex-wrap:wrap;gap:6px}.card-footer-left{display:flex;align-items:center;gap:6px}.source-label{font-size:11px;font-weight:600;color:var(--text-secondary)}.source-name{font-size:11px;font-weight:600;color:var(--charcoal)}.card-date{font-size:11px;color:var(--text-secondary)}.owner-chip{display:flex;align-items:center;gap:6px;font-size:11px;font-weight:600;color:var(--text-secondary)}.owner-avatar{width:22px;height:22px;border-radius:50%;background:var(--reach-blue);color:var(--white);font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center}.site-footer{background:var(--navy);padding:20px 48px;display:flex;align-items:center;justify-content:space-between}.footer-tagline{font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:rgba(255,255,255,.35)}.footer-brand{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.25)}.tabs-divider{width:1px;height:22px;background:var(--rule);margin:0 6px;flex-shrink:0}.sort-btn{border:1px solid var(--rule)!important;margin-left:2px}.sort-btn.sort-active{background:var(--navy)!important;color:var(--white)!important;border-color:var(--navy)!important}.view-toggle{display:flex;align-items:center;gap:4px;margin-left:auto;flex-shrink:0}.vtab{padding:5px 11px;border-radius:6px;border:1px solid var(--rule);background:transparent;font-family:'Montserrat',sans-serif;font-size:12px;font-weight:600;color:var(--text-secondary);cursor:pointer;line-height:1;transition:all .15s ease}.vtab.active,.vtab:hover{background:var(--navy);color:var(--white);border-color:var(--navy)}.list-view{display:none;width:100%;border:1px solid var(--rule);border-radius:12px;overflow:hidden;background:var(--white)}.list-view.visible{display:block}.list-header{display:grid;grid-template-columns:36px 2fr 1fr 1fr 1fr 1fr 110px;gap:0;background:var(--navy);padding:0}.list-header-cell{font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);padding:10px 14px;cursor:pointer;user-select:none;display:flex;align-items:center;gap:5px;transition:color .15s ease}.list-header-cell:hover{color:rgba(255,255,255,.9)}.list-header-cell.sort-asc,.list-header-cell.sort-desc{color:#fff}.list-header-cell .sort-arrow{font-size:9px;opacity:.5;transition:opacity .15s ease;flex-shrink:0}.list-header-cell.sort-asc .sort-arrow,.list-header-cell.sort-desc .sort-arrow{opacity:1}.list-header-cell-noclick{cursor:default!important}.list-header-cell-noclick:hover{color:rgba(255,255,255,.55)!important}.list-row{display:grid;grid-template-columns:36px 2fr 1fr 1fr 1fr 1fr 110px;gap:0;border-top:1px solid var(--rule);align-items:center;transition:background .12s ease;animation:fadeUp .3s ease both}.list-row:hover{background:#F0F5FF}.list-row.hidden{display:none}.list-cell{padding:10px 14px;font-size:12px;font-weight:500;color:var(--charcoal);overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.list-cell-logo{padding:8px 6px 8px 10px;display:flex;align-items:center;justify-content:center}.list-logo{width:22px;height:22px;object-fit:contain;border-radius:4px}.list-name{font-weight:700;color:var(--navy);font-size:13px}.list-name a{color:var(--reach-blue);text-decoration:none;font-size:11px;font-weight:500;margin-left:7px;opacity:.7}.list-name a:hover{opacity:1;text-decoration:underline}.list-badge{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.04em;padding:2px 7px;border-radius:4px;white-space:nowrap}.list-status{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:10px;display:inline-block}@media(max-width:768px){.site-header{padding:0 16px}.hero{padding:32px 16px 28px}.region-tabs,.main{padding:0 16px}.main{padding:24px 16px 60px}.cards-grid{grid-template-columns:1fr}.hero-title{font-size:24px}.site-footer{padding:14px 16px;flex-direction:column;gap:6px;text-align:center}}"""

JS = r"""
var cf='all', sn=false, cv='card';
var listSortCol=null, listSortDir=1;

function blr(){
  var a=Array.from(document.querySelectorAll('.card'));
  var c=document.getElementById('list-rows');
  c.innerHTML='';
  a.forEach(function(card){
    var tags=card.getAttribute('data-tags')||'';
    var date=card.getAttribute('data-date')||'';
    var n=card.querySelector('.card-name'), name=n?n.textContent:'';
    var w=card.querySelector('.card-website'), ws=w?w.href:'', dm=w?w.textContent.replace('\u2197 ',''):'';
    var li=card.querySelector('.card-logo'), logo=li?li.src:'';
    var tg=card.querySelectorAll('.tag'), cat=tg[0]?tg[0].textContent:'', stg=tg[1]?tg[1].textContent:'';
    var sp=card.querySelector('.status-pill'), st=sp?sp.textContent:'', sb=sp?sp.style.background:'#FFF9C4';
    var tb=card.querySelector('.badge-core')||card.querySelector('.badge-adjacent'), tt=tb?tb.textContent:'';
    var tbg=tb&&tb.classList.contains('badge-core')?'#EBF2FF':'#F0FDF4';
    var tc=tb&&tb.classList.contains('badge-core')?'#1B5BA7':'#166534';
    var rg=tags.split(' ')[0]||'';
    var row=document.createElement('div');
    row.className='list-row';
    row.setAttribute('data-tags',tags);
    row.setAttribute('data-date',date);
    row.setAttribute('data-name',name.toLowerCase());
    row.setAttribute('data-region',rg.toLowerCase());
    row.setAttribute('data-category',cat.toLowerCase());
    row.setAttribute('data-stage',stg.toLowerCase());
    row.innerHTML=
      '<div class="list-cell list-cell-logo"><img src="'+logo+'" class="list-logo" onerror="this.style.display=\'none\'"></div>'+
      '<div class="list-cell list-name">'+name+'<a href="'+ws+'" target="_blank">\u2197 '+dm+'</a></div>'+
      '<div class="list-cell"><span class="list-badge" style="background:#F1F5F9;color:#475569">'+cat+'</span></div>'+
      '<div class="list-cell"><span class="list-badge" style="background:#F1F5F9;color:#475569">'+rg+'</span></div>'+
      '<div class="list-cell">'+stg+'</div>'+
      '<div class="list-cell"><span class="list-badge" style="background:'+tbg+';color:'+tc+'">'+tt+'</span></div>'+
      '<div class="list-cell"><span class="list-status" style="background:'+sb+';color:#5A4000">'+st+'</span></div>';
    c.appendChild(row);
  });
}

function sortList(col){
  if(listSortCol===col){
    listSortDir*=-1;
  } else {
    listSortCol=col;
    listSortDir=(col==='date')?-1:1;
  }
  document.querySelectorAll('.list-header-cell[data-col]').forEach(function(h){
    h.classList.remove('sort-asc','sort-desc');
    var arrow=h.querySelector('.sort-arrow');
    if(arrow) arrow.textContent='\u2195';
  });
  var activeHdr=document.querySelector('.list-header-cell[data-col="'+col+'"]');
  if(activeHdr){
    activeHdr.classList.add(listSortDir===1?'sort-asc':'sort-desc');
    var arrow=activeHdr.querySelector('.sort-arrow');
    if(arrow) arrow.textContent=listSortDir===1?'\u2191':'\u2193';
  }
  var container=document.getElementById('list-rows');
  var rows=Array.from(container.querySelectorAll('.list-row'));
  rows.sort(function(a,b){
    var av=a.getAttribute('data-'+col)||'';
    var bv=b.getAttribute('data-'+col)||'';
    return av.localeCompare(bv,undefined,{sensitivity:'base'})*listSortDir;
  });
  rows.forEach(function(r){ container.appendChild(r); });
  applyListFilter();
}

function applyListFilter(){
  var rows=document.querySelectorAll('#list-rows .list-row');
  var vis=0;
  rows.forEach(function(r){
    var show=cf==='all'||r.getAttribute('data-tags').includes(cf);
    r.classList.toggle('hidden',!show);
    if(show) vis++;
  });
  document.getElementById('cc').textContent='Showing '+vis+' of '+rows.length;
}

function sv(v){
  cv=v;
  var sections=document.querySelectorAll('.section-divider,.cards-grid:not(#sw),#sw');
  var l=document.getElementById('list-view');
  document.getElementById('vcb').classList.toggle('active',v==='card');
  document.getElementById('vlb').classList.toggle('active',v==='list');
  if(v==='list'){
    blr();
    if(!listSortCol){ listSortCol='date'; listSortDir=-1; }
    sortList(listSortCol);
    l.classList.add('visible');
    sections.forEach(function(x){ x.style.display='none'; });
  } else {
    l.classList.remove('visible');
    afs();
  }
}

function fc(tag,btn){
  cf=tag;
  document.querySelectorAll('.rtab:not(.sort-btn)').forEach(function(b){ b.classList.remove('active'); });
  btn.classList.add('active');
  if(cv==='list'){ applyListFilter(); } else { afs(); }
}

function ts(btn){
  sn=!sn;
  btn.classList.toggle('sort-active',sn);
  btn.textContent=sn?'\uD83D\uDCC5 Newest First \u2713':'\uD83D\uDCC5 Newest First';
  if(cv==='list'){ applyListFilter(); } else { afs(); }
}

function afs(){
  var main=document.querySelector('.main');
  var all=Array.from(document.querySelectorAll('.card'));
  var vis=0;
  all.forEach(function(c){
    var show=cf==='all'||c.getAttribute('data-tags').includes(cf);
    c.style.display=show?'flex':'none';
    if(show) vis++;
  });
  document.getElementById('cc').textContent='Showing '+vis+' of '+all.length;
  if(sn){
    var vc=all.filter(function(c){ return c.style.display!=='none'; });
    vc.sort(function(a,b){
      var da=a.getAttribute('data-date')||'2000-01-01';
      var db=b.getAttribute('data-date')||'2000-01-01';
      return db.localeCompare(da);
    });
    var sw=document.getElementById('sw');
    if(!sw){ sw=document.createElement('div'); sw.id='sw'; sw.className='cards-grid'; sw.style.marginTop='20px'; }
    sw.innerHTML='';
    vc.forEach(function(c){ sw.appendChild(c.cloneNode(true)); });
    document.querySelectorAll('.section-divider,.cards-grid:not(#sw)').forEach(function(x){ x.style.display='none'; });
    var ex=document.getElementById('sw');
    if(ex) ex.remove();
    main.appendChild(sw);
  } else {
    var sw=document.getElementById('sw');
    if(sw) sw.remove();
    document.querySelectorAll('.section-divider,.cards-grid').forEach(function(x){ x.style.display=''; });
    all.forEach(function(c){
      var show=cf==='all'||c.getAttribute('data-tags').includes(cf);
      c.style.display=show?'flex':'none';
    });
  }
}
"""

def build_html(companies):
    by_region = {r[0]: [] for r in REGION_ORDER}
    for c in companies:
        r = get_prop(c, "Region", "US")
        by_region.get(r, by_region.setdefault(r, [])).append(c)
    total = len(companies)
    regions_used = sum(1 for r in REGION_ORDER if by_region.get(r[0]))
    cats = set(get_prop(c, "Category", "PropTech") for c in companies)
    try:
        dt = datetime.strptime(DATE_LABEL, "%B %d, %Y")
        short = dt.strftime("%b %-d")
    except Exception:
        short = DATE_LABEL[:6]
    sections = ""
    for rk, rl in REGION_ORDER:
        rc = by_region.get(rk, [])
        if not rc:
            continue
        cards = "\n".join(build_card(c) for c in rc)
        sections += (
            '\n  <div class="section-divider">'
            '<div class="section-divider-label">' + rl + '</div>'
            '<div class="section-divider-line"></div></div>'
            '\n  <div class="cards-grid">\n' + cards + '\n  </div>'
        )
    logo_src = "data:image/png;base64," + SCV_LOGO if SCV_LOGO else ""

    # Sortable list header — columns: logo (no sort), Company, Category, Region, Stage, Type (no sort), Date Added
    list_header = (
        '<div class="list-header">'
        '<div class="list-header-cell list-header-cell-noclick"></div>'
        '<div class="list-header-cell" data-col="name" onclick="sortList(\'name\')">Company <span class="sort-arrow">&#8597;</span></div>'
        '<div class="list-header-cell" data-col="category" onclick="sortList(\'category\')">Category <span class="sort-arrow">&#8597;</span></div>'
        '<div class="list-header-cell" data-col="region" onclick="sortList(\'region\')">Region <span class="sort-arrow">&#8597;</span></div>'
        '<div class="list-header-cell" data-col="stage" onclick="sortList(\'stage\')">Stage <span class="sort-arrow">&#8597;</span></div>'
        '<div class="list-header-cell list-header-cell-noclick">Type</div>'
        '<div class="list-header-cell" data-col="date" onclick="sortList(\'date\')">Date Added <span class="sort-arrow">&#8595;</span></div>'
        '</div>'
    )

    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>REACH Daily Radar \u2014 ' + DATE_LABEL + '</title>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;900&display=swap" rel="stylesheet">\n'
        '<style>' + CSS + '</style>\n</head>\n<body>\n'
        '<header class="site-header">\n  <div class="logo-block">\n'
        '    <img src="' + logo_src + '" alt="Second Century Ventures" class="scv-logo">\n'
        '    <div class="logo-divider"></div>\n'
        '    <div class="logo-subtitle">Daily Radar<span>Second Century Ventures</span></div>\n'
        '  </div>\n  <div class="header-meta">\n'
        '    <div class="header-date">' + DATE_LABEL + '</div>\n'
        '    <div class="header-pill">' + str(total) + ' Companies</div>\n'
        '  </div>\n</header>\n'
        '<div class="hero">\n'
        '  <div class="hero-label">Global Startup Intelligence \u00b7 Powered by REACH</div>\n'
        '  <h1 class="hero-title">Today\u2019s Radar <span>\u2014 Emerging Companies to Watch</span></h1>\n'
        '  <p class="hero-sub">Curated daily from global proptech publications, YC, Crunchbase, Inman, TechCrunch, and regional feeds. Sourced from Notion \u00b7 Duplicate-protected \u00b7 Updated every morning.</p>\n'
        '  <div class="hero-stats">\n'
        '    <div class="hero-stat"><div class="hero-stat-num">' + str(total) + '</div><div class="hero-stat-label">Companies Tracked</div></div>\n'
        '    <div class="hero-stat"><div class="hero-stat-num">' + str(regions_used) + '</div><div class="hero-stat-label">Regions Covered</div></div>\n'
        '    <div class="hero-stat"><div class="hero-stat-num">' + str(len(cats)) + '</div><div class="hero-stat-label">Categories</div></div>\n'
        '    <div class="hero-stat"><div class="hero-stat-num">' + short + '</div><div class="hero-stat-label">Last Updated</div></div>\n'
        '  </div>\n</div>\n'
        '<div class="region-tabs">\n'
        '  <button class="rtab active" onclick="fc(\'all\',this)">&#127760; All</button>\n'
        '  <button class="rtab" onclick="fc(\'US\',this)">&#127482;&#127480; US</button>\n'
        '  <button class="rtab" onclick="fc(\'LatAm\',this)">&#127758; LatAm</button>\n'
        '  <button class="rtab" onclick="fc(\'Europe\',this)">&#127468;&#127463; Europe</button>\n'
        '  <button class="rtab" onclick="fc(\'MENA\',this)">&#127462;&#127466; MENA</button>\n'
        '  <button class="rtab" onclick="fc(\'APAC\',this)">&#127471; APAC</button>\n'
        '  <button class="rtab" onclick="fc(\'Core\',this)">Core</button>\n'
        '  <button class="rtab" onclick="fc(\'Adjacent\',this)">Adjacent</button>\n'
        '  <button class="rtab" onclick="fc(\'AI\',this)">AI</button>\n'
        '  <button class="rtab" onclick="fc(\'FinTech\',this)">FinTech</button>\n'
        '  <button class="rtab" onclick="fc(\'PropTech\',this)">PropTech</button>\n'
        '  <div class="tabs-divider"></div>\n'
        '  <button class="rtab sort-btn" id="sort-btn" onclick="ts(this)">&#128197; Newest First</button>\n'
        '  <div class="tabs-divider"></div>\n'
        '  <div class="view-toggle">\n'
        '    <button class="vtab active" id="vcb" onclick="sv(\'card\')">&#8862; Cards</button>\n'
        '    <button class="vtab" id="vlb" onclick="sv(\'list\')">&#9776; List</button>\n'
        '  </div>\n</div>\n'
        '<main class="main">\n'
        '  <div class="section-header"><div class="section-title">&#9889; All Companies \u00b7 REACH Daily Radar</div>'
        '<div class="section-count" id="cc">Showing ' + str(total) + ' of ' + str(total) + '</div></div>\n'
        '  <div class="list-view" id="list-view">\n'
        '    ' + list_header + '\n'
        '    <div id="list-rows"></div>\n  </div>\n'
        + sections +
        '\n</main>\n'
        '<footer class="site-footer">\n'
        '  <div class="footer-tagline">Accelerating Real Estate \u00b7 REACH Daily Radar</div>\n'
        '  <div class="footer-brand">Second Century Ventures \u00b7 \u00a9 2026</div>\n'
        '</footer>\n<script>' + JS + '</script>\n</body>\n</html>'
    )
    return html

print("Fetching from Notion...")
companies = fetch_all()
print("Fetched " + str(len(companies)) + " companies")
html = build_html(companies)
html = html.encode("utf-8", "replace").decode("utf-8")
with open("index.html", "w", encoding="utf-8", errors="replace") as f:
    f.write(html)
print("Done: " + str(len(html)) + " bytes, " + str(len(companies)) + " companies")

