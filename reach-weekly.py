#!/usr/bin/env python3
"""
REACH Daily Radar — Weekly Automation Script
Runs Thursday 2am UTC: Searches Tier 1+2 sources, deduplicates, writes to Notion, posts summary
"""

import re
import os
import json
import sys
import requests
import anthropic
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

DISCOVERIES_FILE = "reach-discoveries.md"
BASELINE_FILE = "reach-baseline.json"
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_DATABASE_ID = "135c09f5319d41bfa9a92089ee4ac5e6"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# =============================================================================
# NORMALIZATION FUNCTIONS
# =============================================================================

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
    url = url.split('/')[0]  # Extract root domain only
    url = re.sub(r'[\s\-_.]+', '', url)
    url = re.sub(r'\.(ai|io|com|app|co|tech|org|net|re|xyz|ca|uk|au)$', '', url)
    return url.strip()

# =============================================================================
# LOAD BASELINE & PORTFOLIO EXCLUSIONS
# =============================================================================

# Hardcoded portfolio set — failsafe in case reach-baseline.json has no portfolio key
PORTFOLIO_HARDCODED = {
    normalize_name(n) for n in [
        # 2013-2026 REACH/SCV portfolio — normalized
        "bombbomb","lumentus","planwise","reach150social","treater","updater","workface",
        "backatyoumedia","deductr","desktime","fundwell","goby","sendhub","smartzip","wevideo",
        "assetavenue","august","boostup","guardllama","loopandtie","notarycam","pro","termscout",
        "sindeo","truststamp","flipt","valoancaptain","energydatametrics","homeselfe",
        "realscout","floorplanonline","homediary","zenergyst",
        "centriq","housecanary","immoviewer","notarize","occly","pearlcertification",
        "relola","trustedmail","adwerx",
        "activepipe","boxbrownie","connectnow","glide","hurdlr","quigler","realkey","zavvie",
        "amarki","curbio","evocalize","kleard","propy","ratemyagent","reconsortia","sdninc",
        "coeo","lulafit","cresimple","biproxi","trove","twofold",
        "kangaroo","ylopo","earnnest","punchlist","modus","realx","transactly","cartofront",
        "dealius","dealiuscapital","epr2","leasera","obierisk","occupier","pearchef","realtimerisksolutions",
        "igloohome","uxtrata","pam","sorted","really","ubipark",
        "brokerassist","clik","clikaiai","parkbench","setter","keyliving","locallogic",
        "honestdoor","rentmoola",
        "aryeo","feather","knock","landis","milestones","plunk","k4connect","super",
        "cove","groundbreaker","landintelligence","lexmarkets","otso","parafin",
        "prodeal","remarkably","valcre",
        "boompower","buildapps","appwell","openn","propic","soho","archix","superdraft",
        "mayordomo","myroffice","radweb","inventorybase","underthedoormat","hammock","sprift","offr",
        "courted","fractional","inspectify","leadpops","perchwell","place","reggora","revive",
        "cretelligent","matrixrentalsolutions","arxcity","stratafolio","bline",
        "leaseup","spackle","stake","whoseyourlandlord",
        "realestatedoc","homelive","futurerent","hipla","roomme","settleeasy","clairco",
        "urbanimmersive","loft47","perch","smartalto","rise","roomvu","rentalbeast",
        "opennegotiation","watrix","simplicity",
        "houzen","safe2","searchsmartly","edozo","mokki","blockdox","cleverly",
        "propertydealsinsight","monspire","residently","fyma",
        "flock","highnote","plusplatform","prisidio","realgrader","summer","tongo",
        "apmhelp","bluestreakiot","dwellwellanalytics","fortress","rockport","workandmother",
        "marketbuy","liz","norx","properti","sensorglobal","realtimeconveyancer",
        "quantproperty","listassist","tapi",
        "productivecall","sustainablepg","frontrunner","iguard","singlekey","soulrooms",
        "koggi","alohome","propmeteus","kippstorage","ambana","beleta","ai360","kolonus",
        "grandbequest","hococo","tweaq","verv","crowd2live","bisly","goyuno",
        "chirpyest","finaloffer","kukun","notable","purlin","scout","trackxi","unlock",
        "acretrader","incentifind","infinityy","premisehq","prophia","rensair","withco",
        "arcanite","erinliving","milkchocolate","leesy","flkitover","agentprofitplanner",
        "squarebysquare","gxe","thdr",
        "collegium","proptexx","propra","maket","infinitecreator","proximahq","iluminai",
        "lendai","buzzztech","centeraya","leancon","accuraiser","reli","mytower","arkdesignai",
        "alterhome","cuid","hippobuild","mica","neo","propi","viventa","wbuild",
        "susyhouse","buildingpassport","jmi","builtapi","zonifero","propalt","infersens",
        "pitch59","foyer","guesthouse","pixlmob","theqwikfix","tether",
        "1031specialists","breatheev","caltana","connexus","forty5park","packsmith",
        "predictap","rekalibrate",
        "unio","propertycredit","scaleapp","handl","aivot","foundat",
        "releaserent","upfront","stelor","voiceflip","reitium","bidmii","sharesfr","rocketplan",
        "homemade","smarthoist","housetable","elphi","robochute","boomrealestch",
        "villatracker","atom",
        "crezes","alpaca","omnimls","passwork","gohaus","docublock","polibit","propio",
        "carrot","prospectorpro","watergate","squareplan","casapay","hybr","factored","husmus",
        "parkbooker","crayons","recrutre","zapiio","arosoftware",
        "repliers","cedar","neobanc","credivera",
        "asano","rewa","watad","fixit","coraly","holox","takeem",
    ]
}

def load_baseline():
    """Load baseline companies and portfolio exclusions from JSON."""
    with open(BASELINE_FILE, 'r') as f:
        baseline_data = json.load(f)

    baseline_names = set()
    baseline_domains = set()

    for company in baseline_data['baseline']:
        baseline_names.add(company['normalized_name'])
        baseline_domains.add(company['normalized_domain'])

    # Build portfolio set: from JSON if present, else use hardcoded fallback
    portfolio_set = set()
  2 if 'portfolio' in baseline_data:
        for cohort_companies in baseline_data['portfolio'].values():
            for name in cohort_companies:
                portfolio_set.add(normalize_name(name))

    # Merge with hardcoded set for full coverage
    portfolio_set = portfolio_set | PORTFOLIO_HARDCODED

    return {
        'names': baseline_names,
        'domains': baseline_domains,
        'portfolio': portfolio_set
    }

# =============================================================================
# PARSE DISCOVERIES.MD
# =============================================================================

def read_discoveries_md():
    """Read existing discoveries from markdown file. Parses '- Name | URL' lines only."""
    if not Path(DISCOVERIES_FILE).exists():
        return []

    companies = []
    with open(DISCOVERIES_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            # Match format: "- Company Name | https://website.com"
            match = re.match(r'^-\s+([^|]+)\s+\|\s+(https?://\S+)', line)
            if match:
                companies.append({
                    'name': match.group(1).strip(),
                    'website': match.group(2).strip()
                })

    return companies

# =============================================================================
# SEARCH WEB (TIER 1 + TIER 2) via Claude SDK web_search
# =============================================================================

def search_source(client, source, query):
    """Search a single source using Claude with web_search_20260209 tool."""
    try:
        messages = [{
            "role": "user",
            "content": (
                f"Search for new proptech and real estate technology startups announced or funded "
                f"in the past 7 days. Use this query: \"{query}\"\n\n"
                f"Focus on content from: {source}\n\n"
                f"For each company you find, extract the company name and website URL.\n\n"
                f"Return ONLY a valid JSON array in this exact format:\n"
                f'[{{"name": "Company Name", "website": "https://example.com", "source": "{source}"}}]\n\n'
                f"Rules:\n"
                f"- Include only real companies with verifiable websites\n"
                f"- Do not include companies you are uncertain about\n"
                f"- If no companies found, return: []\n"
                f"- Return ONLY the JSON array, no other text"
            )
        }]

        # Agentic loop: Claude may call web_search multiple times before final answer
        for _ in range(8):
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2048,
                tools=[
                    {"type": "web_search_20260209", "name": "web_search"},
                ],
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                # Extract final text response
                for block in response.content:
                    if hasattr(block, 'text'):
                        text = block.text.strip()
                        # Find JSON array anywhere in the response
                        match = re.search(r'\[.*?\]', text, re.DOTALL)
                        if match:
                            try:
                                return json.loads(match.group())
                            except json.JSONDecodeError:
                                pass
                return []

            elif response.stop_reason == "tool_use":
                # Claude is using web_search — extend conversation and continue
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if hasattr(block, 'type') and block.type == "tool_use":
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": ""  # Server-side tool: Anthropic provides results
                        })
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
            else:
                break

    except Exception as e:
        print(f"  ⚠️  Error searching {source}: {e}")

    return []


def search_tier1_tier2():
    """Search Tier 1 + Tier 2 proptech sources for the past 7 days."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    sources = [
        # Tier 1 — every run
        ("TechCrunch",          "proptech real estate startup funded 2026"),
        ("Y Combinator",        "YC proptech real estate 2026"),
        ("Crunchbase",          "real estate proptech funding 2026"),
        ("Inman",               "proptech AI real estate startup 2026"),
        ("PropTechBuzz",        "proptech startup funding news 2026"),
        ("Commercial Observer", "proptech CRE startup funding 2026"),
        # Tier 2
        ("Wamda",               "MENA proptech real estate startup 2026"),
        ("Fintechnews ME",      "proptech real estate Middle East 2026"),
        ("VentureBeat",         "proptech real estate AI startup 2026"),
        ("Fifth Wall",          "proptech portfolio investment 2026"),
    ]

    discovered = []
    for source, query in sources:
        print(f"  🔍 Searching {source}...")
        results = search_source(client, source, query)
        if results:
            print(f"     ✅ Found {len(results)} mention(s)")
            discovered.extend(results)
        else:
            print(f"     — No new companies found")

    return discovered

# =============================================================================
# DEDUPLICATION LOGIC
# =============================================================================

def dedup_discoveries(new_discoveries, baseline, existing_in_md):
    """
    Three-layer deduplication:
    1. Portfolio exclusion (hardcoded + JSON)
    2. Baseline companies (77 originals in reach-baseline.json)
    3. Existing in reach-discoveries.md
    """
    net_new = []
    skipped = {'portfolio': [], 'baseline': [], 'existing_md': []}
    seen_this_run = set()  # prevent within-run duplicates

    for discovery in new_discoveries:
        name = discovery.get('name', '').strip()
        website = discovery.get('website', '').strip()
        if not name:
            continue

        norm_name = normalize_name(name)
        norm_domain = normalize_domain(website)

        # Skip blank normalizations
        if not norm_name:
            continue

        # Within-run dedup
        run_key = norm_name or norm_domain
        if run_key in seen_this_run:
            continue

        # Layer 1: Portfolio exclusion
        if norm_name in baseline['portfolio']:
            skipped['portfolio'].append(f"{name} (REACH/SCV portfolio)")
            continue

        # Layer 2: Baseline check (77 companies)
        if norm_name in baseline['names'] or (norm_domain and norm_domain in baseline['domains']):
            skipped['baseline'].append(name)
            continue

        # Layer 3: Existing in discoveries.md
        is_duplicate = False
        for existing in existing_in_md:
            if (normalize_name(existing['name']) == norm_name or
                    (norm_domain and normalize_domain(existing['website']) == norm_domain)):
                skipped['existing_md'].append(name)
                is_duplicate = True
                break

        if not is_duplicate:
            net_new.append(discovery)
            seen_this_run.add(run_key)

    return net_new, skipped

# =============================================================================
# WRITE TO NOTION
# =============================================================================

def write_to_notion(companies):
    """Write deduplicated companies to Notion database via REST API."""
    if not companies:
        print("  ✅ No net-new companies to write")
        return 0

    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    written = 0
    for company in companies:
        name    = company.get('name', '').strip()
        website = company.get('website', '').strip()
        source  = company.get('source', 'REACH Daily Radar').strip()

        if not name:
            continue

        payload = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Company Name": {
                    "title": [{"text": {"content": name}}]
                },
                "Website": {
                    "url": website if website.startswith('http') else None
                },
                "Status": {
                    "select": {"name": "New"}
                },
                "Source": {
                    "rich_text": [{"text": {"content": source}}]
                },
                "Date Added": {
                    "date": {"start": datetime.now().strftime("%Y-%m-%d")}
                },
                "Type": {
                    "select": {"name": "Core"}
                },
                "Stage / Round": {
                    "select": {"name": "Unknown"}
                }
            }
        }

        try:
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                written += 1
                print(f"  ✅ Written to Notion: {name}")
            else:
                print(f"  ❌ Failed: {name} — HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"  ❌ Error writing {name}: {e}")

    return written

# =============================================================================
# APPEND TO DISCOVERIES.MD
# =============================================================================

def append_to_discoveries(net_new):
    """Append net-new companies to reach-discoveries.md."""
    if not net_new:
        return

    with open(DISCOVERIES_FILE, 'a') as f:
        f.write(f"\n### Week of {datetime.now().strftime('%B %d, %Y')}\n\n")
        for company in net_new:
            website = company.get('website', '#')
            source  = company.get('source', 'REACH Daily Radar')
            f.write(f"- {company['name']} | {website} | {source}\n")

# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================

def main():
    """
    Weekly workflow:
    1. Load baseline + portfolio exclusions
    2. Read existing discoveries
    3. Search Tier 1 + Tier 2 sources (past 7 days)
    4. Deduplicate (3 layers)
    5. Write to Notion
    6. Append to discoveries.md
    7. Print summary
    """
    print("🤖 REACH Daily Radar — Weekly Automation")
    print(f"🕐 {datetime.now().strftime('%A, %B %d, %Y at %H:%M UTC')}\n")

    # Step 1
    print("📊 Loading baseline...")
    baseline = load_baseline()
    print(f"   ✅ {len(baseline['names'])} baseline companies, {len(baseline['portfolio'])} portfolio exclusions\n")

    # Step 2
    print("📂 Reading existing discoveries...")
    existing = read_discoveries_md()
    print(f"   ✅ {len(existing)} companies in discoveries.md\n")

    # Step 3
    print("🔍 Searching Tier 1 + Tier 2 sources (past 7 days)...")
    new_discoveries = search_tier1_tier2()
    print(f"   ✅ {len(new_discoveries)} total mentions found\n")

    # Step 4
    print("✂️  Deduplicating (3 layers)...")
    net_new, skipped = dedup_discoveries(new_discoveries, baseline, existing)
    print(f"   🚫 Portfolio matches skipped:  {len(skipped['portfolio'])}")
    print(f"   🚫 Baseline matches skipped:   {len(skipped['baseline'])}")
    print(f"   🚫 Already in .md skipped:     {len(skipped['existing_md'])}")
    print(f"   ✅ Net-new candidates:          {len(net_new)}\n")

    # Step 5
    print("📝 Writing to Notion...")
    written = write_to_notion(net_new)
    print(f"   ✅ {written} companies written\n")

    # Step 6
    print("📋 Updating reach-discoveries.md...")
    append_to_discoveries(net_new)
    print(f"   ✅ {len(net_new)} entries appended\n")

    # Step 7
    print("=" * 60)
    print("🌟  REACH Daily Radar — Weekly Summary")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"🔎 Sources searched:              10")
    print(f"🌐 Total mentions found:          {len(new_discoveries)}")
    print(f"🚫 PortFolio companies skipped:   {len(skipped['portfolio'])}")
    print(f"🚫 DB duplicates skipped:         {len(skipped['baseline']) + len(skipped['existing_md'])}")
    print(f"✅ Net-new added to Notion:        {written}")
    print(f"📊 Estimated DB total:            {len(baseline['names']) + written}")
    print(f"\n📍 Live at: https://dgarland4.github.io/reach-daily-radar")
    print("=" * 60)


if __name__ == "__main__":
    main()
