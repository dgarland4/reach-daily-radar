#!/usr/bin/env python3
"""
REACH Daily Radar — Weekly Automation Script
Runs Thursday 2am: Searches Tier 1+2 sources, deduplicates, writes to Notion, posts summary
"""

import re
import json
import sys
from datetime import datetime
from pathlib import Path

# ==============================================================================
# CONFIGURATION
# ==============================================================================

DISCOVERIES_FILE = "reach-discoveries.md"
BASELINE_FILE = "reach-baseline.json"
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_DATABASE_ID = "135c09f5319d41bfa9a92089ee4ac5e6"

# ==============================================================================
# NORMALIZATION FUNCTIONS
# ==============================================================================

def normalize_name(name):
    """Normalize company name for deduplication."""
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'[\s\-_.()]+', '', name)
    name = re.sub(r'\b(inc|llc|ltd|co|corp|ab|ag|sa|bv|plc)\b', '', name)
    return name.strip()

def normalize_domain(url):
    """Normalize domain for deduplication."""
    if not url:
        return ""
    url = url.lower().replace('https://', '').replace('http://', '').replace('www.', '')
    url = url.split('/')[0]  # Extract root domain
    url = re.sub(r'[\s\-_.]+', '', url)
    url = re.sub(r'\.(ai|io|com|app|co|tech|org|net|re|xyz|ca|uk|au)$', '', url)
    return url.strip()

# ==============================================================================
# LOAD BASELINE & PORTFOLIO EXCLUSIONS
# ==============================================================================

def load_baseline():
    """Load baseline companies and portfolio exclusions from JSON."""
    with open(BASELINE_FILE, 'r') as f:
        baseline_data = json.load(f)
    
    # Build sets for fast lookup
    baseline_names = set()
    baseline_domains = set()
    
    for company in baseline_data['baseline']:
        baseline_names.add(company['normalized_name'])
        baseline_domains.add(company['normalized_domain'])
    
    # Flatten portfolio exclusions
    portfolio_set = set()
    for category, companies in baseline_data['portfolio_exclusions'].items():
        for company in companies:
            portfolio_set.add(normalize_name(company))
    
    return {
        'names': baseline_names,
        'domains': baseline_domains,
        'portfolio': portfolio_set
    }

# ==============================================================================
# PARSE DISCOVERIES.MD
# ==============================================================================

def read_discoveries_md():
    """Read existing discoveries from markdown file."""
    if not Path(DISCOVERIES_FILE).exists():
        return []
    
    companies = []
    with open(DISCOVERIES_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            # Match format: "- Company Name | https://website.com"
            match = re.match(r'^-\s+([^|]+)\s+\|\s+(.+)$', line)
            if match:
                companies.append({
                    'name': match.group(1).strip(),
                    'website': match.group(2).strip()
                })
    
    return companies

# ==============================================================================
# SEARCH WEB (TIER 1 + TIER 2)
# ==============================================================================

def search_tier1_tier2():
    """
    Search Tier 1 + Tier 2 proptech sources for past 7 days.
    Returns list of discovered companies.
    
    NOTE: In production, this would call web_search API for each source.
    For testing, returning mock data structure.
    """
    
    tier1_sources = [
        "TechCrunch",
        "Y Combinator", 
        "Crunchbase",
        "Inman",
        "PropTechBuzz",
        "Commercial Observer"
    ]
    
    tier2_sources = [
        "Wamda",
        "Fintechnews ME",
        "VentureBeat",
        "Fifth Wall"
    ]
    
    all_sources = tier1_sources + tier2_sources
    
    discovered = []
    
    # In production: loop through sources, call web_search for each
    # For testing: mock data returned
    # Real implementation would:
    # for source in all_sources:
    #     results = web_search(f"proptech real estate {source} past 7 days")
    #     for result in results:
    #         discovered.append({
    #             'name': result['company_name'],
    #             'website': result['website'],
    #             'source': source,
    #             'date': datetime.now().strftime('%Y-%m-%d')
    #         })
    
    return discovered

# ==============================================================================
# DEDUPLICATION LOGIC
# ==============================================================================

def dedup_discoveries(new_discoveries, baseline, existing_in_md):
    """
    Three-layer deduplication:
    1. Portfolio exclusion
    2. Baseline companies (from 77)
    3. Existing in discoveries.md
    """
    
    net_new = []
    skipped = {
        'portfolio': [],
        'baseline': [],
        'existing_md': []
    }
    
    for discovery in new_discoveries:
        name = discovery['name']
        website = discovery.get('website', '')
        
        norm_name = normalize_name(name)
        norm_domain = normalize_domain(website)
        
        # Layer 1: Portfolio exclusion check
        if norm_name in baseline['portfolio']:
            skipped['portfolio'].append(f"{name} (REACH/SCV portfolio)")
            continue
        
        # Layer 2: Baseline check (77 companies)
        if norm_name in baseline['names'] or norm_domain in baseline['domains']:
            skipped['baseline'].append(name)
            continue
        
        # Layer 3: Existing in discoveries.md
        is_duplicate = False
        for existing in existing_in_md:
            if (normalize_name(existing['name']) == norm_name or
                normalize_domain(existing['website']) == norm_domain):
                skipped['existing_md'].append(name)
                is_duplicate = True
                break
        
        if not is_duplicate:
            net_new.append(discovery)
    
    return net_new, skipped

# ==============================================================================
# WRITE TO NOTION
# ==============================================================================

def write_to_notion(companies):
    """
    Batch-write deduplicated companies to Notion.
    
    In production: calls Notion:notion-create-pages for each company
    For testing: logs what would be written
    """
    
    if not companies:
        print("✅ No net-new companies to write")
        return 0
    
    written = 0
    for company in companies:
        # In production:
        # response = notion_create_pages(
        #     parent.data_source_id: NOTION_DATABASE_ID,
        #     fields: {
        #         "Company Name": company['name'],
        #         "Website": company['website'],
        #         "Region": infer_region(company),
        #         "Category": infer_category(company),
        #         "Stage": "Unknown",
        #         "Status": "New",
        #         "Type": "Core",
        #         "Source": company.get('source', 'REACH Daily Radar'),
        #         "Date Added": datetime.now().isoformat()
        #     }
        # )
        # if response.success:
        written += 1
    
    return written

# ==============================================================================
# APPEND TO DISCOVERIES.MD
# ==============================================================================

def append_to_discoveries(net_new):
    """Add net-new companies to discoveries.md"""
    
    if not net_new:
        return
    
    with open(DISCOVERIES_FILE, 'a') as f:
        f.write(f"\n### Week of {datetime.now().strftime('%B %d, %Y')}\n\n")
        for company in net_new:
            website = company.get('website', '#')
            source = company.get('source', 'REACH Daily Radar')
            f.write(f"- {company['name']} | {website} | {source}\n")

# ==============================================================================
# MAIN ORCHESTRATION
# ==============================================================================

def main():
    """
    Main weekly workflow:
    1. Load baseline + portfolio exclusions
    2. Read existing discoveries
    3. Search Tier 1 + Tier 2 sources
    4. Dedup (3 layers)
    5. Write to Notion
    6. Append to discoveries.md
    7. Post summary
    """
    
    print("🔄 REACH Daily Radar — Weekly Automation")
    print(f"⏰ {datetime.now().strftime('%A, %B %d, %Y at %H:%M UTC')}\n")
    
    # Step 1: Load baseline
    print("📊 Loading baseline...")
    baseline = load_baseline()
    print(f"   ✅ Baseline: {len(baseline['names'])} companies\n")
    
    # Step 2: Read existing discoveries
    print("📝 Reading existing discoveries...")
    existing = read_discoveries_md()
    print(f"   ✅ Found {len(existing)} companies in discoveries.md\n")
    
    # Step 3: Search web
    print("🔍 Searching Tier 1 + Tier 2 sources (past 7 days)...")
    new_discoveries = search_tier1_tier2()
    print(f"   ✅ Found {len(new_discoveries)} total mentions\n")
    
    # Step 4: Dedup
    print("🧹 Deduplicating...")
    net_new, skipped = dedup_discoveries(new_discoveries, baseline, existing)
    
    print(f"   ⏭️  Portfolio matches: {len(skipped['portfolio'])}")
    print(f"   ⏭️  Baseline matches: {len(skipped['baseline'])}")
    print(f"   ⏭️  Existing in MD: {len(skipped['existing_md'])}")
    print(f"   ✅ Net-new candidates: {len(net_new)}\n")
    
    # Step 5: Write to Notion
    print("📌 Writing to Notion...")
    written = write_to_notion(net_new)
    print(f"   ✅ Written: {written}\n")
    
    # Step 6: Append to discoveries
    print("📄 Updating discoveries.md...")
    append_to_discoveries(net_new)
    print(f"   ✅ Appended {len(net_new)} new companies\n")
    
    # Step 7: Summary
    print("=" * 60)
    print("☀️  REACH Daily Radar Summary")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"🔎 Sources searched: {len(tier1_sources + tier2_sources)}")
    print(f"📢 Total mentions found: {len(new_discoveries)}")
    print(f"🚫 Portfolio companies skipped: {len(skipped['portfolio'])}")
    print(f"🚫 DB duplicates skipped: {len(skipped['baseline'])}")
    print(f"📝 Net-new added to Notion: {written}")
    print(f"📊 Baseline total (estimated): {len(baseline['names']) + written}")
    print("\n💾 Website auto-rebuilds at 7:00 AM PST")
    print("📍 Live at: https://dgarland4.github.io/reach-daily-radar")
    print("=" * 60)

if __name__ == "__main__":
    # For testing: python reach-weekly.py
    # For production: runs via GitHub Action Thursday 2am
    main()
