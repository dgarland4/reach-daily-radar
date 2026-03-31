# REACH Daily Radar — Automated Weekly Search & Notion Writes

**Status:** Ready for live testing Thursday 2am UTC

---

## What This Does

**Every Thursday at 2:00 AM UTC:**
1. Searches Tier 1 + Tier 2 proptech sources for past 7 days
2. Deduplicates against 77 baseline companies + REACH/SCV portfolio exclusions
3. Writes net-new companies to your Notion database
4. Posts summary report at 7:00 AM PST (Thursday morning)
5. GitHub Pages auto-rebuilds your dashboard from updated Notion data

**Token cost:** ~60-90k per week (vs ~840k-1.2M with daily approach)

---

## Files Included

```
reach-daily-radar/
├── reach-baseline.json              ← 77 companies + portfolio exclusions (static)
├── reach-discoveries.md             ← Rolling baseline (grows each week)
├── reach-weekly.py                  ← Main automation script
├── .github/workflows/
│   └── weekly-radar.yml             ← GitHub Action (Thursday 2am + 7am summary)
└── README.md                        ← This file
```

---

## Setup Instructions

### Step 1: Add Files to Your Repo

Copy these files to your `reach-daily-radar` repository:
- `reach-baseline.json` → repo root
- `reach-discoveries.md` → repo root  
- `reach-weekly.py` → repo root
- `weekly-radar.yml` → `.github/workflows/`

### Step 2: Add Notion API Token to GitHub Secrets

1. Go to your `reach-daily-radar` repo → **Settings** → **Secrets and variables** → **Actions**
2. Create new secret: `NOTION_API_TOKEN`
3. Paste your Notion API token (you already have this)

The workflow will automatically use this token for Notion writes.

### Step 3: Verify GitHub Pages Rebuild

Make sure your existing `reach-daily-rebuild.yml` is still in `.github/workflows/` and configured to run Friday 7am PST.

The weekly automation will:
1. Write net-new companies to Notion (Thursday 2am)
2. Trigger the existing rebuild action (Friday 7am PST)
3. Website auto-updates with latest data

---

## How It Works

### Thursday 2:00 AM UTC (Wednesday 6pm PT)

```
reach-weekly.py runs:
  ✅ Load 77-company baseline + portfolio exclusions
  ✅ Read past 7 days from Tier 1 sources:
     - TechCrunch
     - Y Combinator
     - Crunchbase
     - Inman
     - PropTechBuzz
     - Commercial Observer
  ✅ Read Tier 2 (rotating):
     - Wamda, Fintechnews ME, VentureBeat, Fifth Wall, Camber Creek, NFX, CRETI
  ✅ Dedup (3 layers):
     1. Portfolio exclusion check (REACH/SCV)
     2. Baseline check (77 companies)
     3. Existing discoveries.md
  ✅ Write net-new to Notion
  ✅ Append to discoveries.md
  ✅ Save summary.txt
```

### Thursday 7:00 AM PST (Friday 3pm UTC)

```
GitHub Action posts:
  📧 Summary issue with:
     - Companies found
     - Duplicates skipped
     - Net-new written
     - Dashboard link
```

### Friday 7:00 AM PST (Auto-rebuild)

```
Your existing GitHub Pages action runs:
  🌐 Fetches latest data from Notion
  🌐 Rebuilds index.html
  🌐 Deploys to https://dgarland4.github.io/reach-daily-radar
```

---

## Testing Before Go-Live

**To test Thursday morning:**

1. **Manual trigger:**
   - Go to repo → **Actions** → **REACH Daily Radar — Weekly Automation**
   - Click **Run workflow** → **Run workflow**

2. **Check the run:**
   - Watch the steps execute
   - Look for `reach-summary.txt` in artifacts
   - Verify commits to `reach-discoveries.md`
   - Check for GitHub issue with summary (posted at simulated 7am)

3. **Verify Notion writes:**
   - Open your Notion database
   - Check for new companies in Status = "New"

4. **If everything works:**
   - You're ready for live Thursday 2am run

---

## What Happens Each Week

**Week 1 (March 30):**
- Baseline: 77 companies
- New companies found: X
- Net-new written: Y
- discoveries.md now has: 77 + Y companies

**Week 2 (April 6):**
- Baseline: 77 + Y companies (from Week 1)
- New companies found: X
- Net-new written: Z
- discoveries.md now has: 77 + Y + Z companies

**Rolling forward:**
- Each week, the baseline automatically expands
- Zero manual deduplication needed
- No chance of duplicates in Notion

---

## Customization

### Change Search Time

Edit `.github/workflows/weekly-radar.yml`:
```yaml
on:
  schedule:
    # Change the cron time here
    # Format: 'minute hour day month weekday'
    - cron: '0 2 * * 4'  # Currently: Thursday 2am UTC
```

### Add More Sources

Edit `reach-weekly.py`, update `tier1_sources` and `tier2_sources` lists:
```python
tier1_sources = [
    "TechCrunch",
    "Y Combinator",
    # Add more here
]
```

### Change Notion Write Fields

Edit `reach-weekly.py`, `write_to_notion()` function:
```python
# Add or modify fields being written to Notion
"Region": infer_region(company),
"Category": infer_category(company),
# etc
```

---

## Monitoring & Alerts

Each Thursday 7am PST, check:
1. **GitHub issues** for summary report
2. **Actions tab** for workflow run status
3. **Notion database** for new companies (Status = "New")
4. **Website** for updated dashboard at 7am PST Friday

---

## Troubleshooting

**Issue: "NOTION_API_TOKEN not found"**
- Go to repo Settings → Secrets → verify token is set correctly
- Re-run workflow (wait 5 min for secrets to propagate)

**Issue: "reach-discoveries.md not updating"**
- Check GitHub Actions run logs
- Verify git config is correct in workflow file
- Ensure GitHub Actions has write permissions

**Issue: "No new companies written"**
- Check that new discoveries were actually found
- Verify Notion API token has write permissions
- Check reach-summary.txt in artifacts

**Issue: "Website not rebuilding"**
- Verify `reach-daily-rebuild.yml` still exists in `.github/workflows/`
- Check that cron schedule is Friday 7am PST
- Manually trigger rebuild action as test

---

## Next Steps

1. **Copy all files to your repo**
2. **Add Notion API token to GitHub Secrets**
3. **Test Thursday morning with manual workflow trigger**
4. **Go live: Thursday 2am UTC regular schedule**

---

**Questions?** Check the GitHub Actions logs or reach out to Claude.

**Live Dashboard:** https://dgarland4.github.io/reach-daily-radar
