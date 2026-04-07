#!/usr/bin/env python3
"""
FIFAMap Quarterly Platform Manager — GitHub Actions Version
Runs Jan 1, Apr 1, Jul 1, Oct 1. Checks FIFA.com for new announcements.
Detects when a new tournament research phase should begin.
Outputs GitHub Actions annotations for any actions needed.
"""
import json, datetime, os, urllib.request, sys

REGISTRY_PATH = 'system/tournament-registry.json'

def log(msg):
    print(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] {msg}", flush=True)

def web_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'FifaMapBot/1.0 (+https://fifamap.org)'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8', errors='ignore')

def main():
    log("=== FIFAMap Quarterly Platform Check (GitHub Actions) ===")
    today = datetime.date.today()
    log(f"Date: {today}")

    if not os.path.exists(REGISTRY_PATH):
        log("Registry not found — skipping check")
        sys.exit(0)

    with open(REGISTRY_PATH) as f:
        registry = json.load(f)

    actions_needed = []

    # 1. Check if current tournament has ended
    current = registry.get('current_tournament', {})
    if current:
        end_date = datetime.date.fromisoformat(current['end'])
        if today > end_date:
            msg = f"TOURNAMENT_ENDED: {current['name']} ended {end_date}"
            log(f"⚠️  {msg}")
            actions_needed.append(msg)
            print(f"::warning title=Tournament Ended::{current['name']} has ended. Update site to transition to next tournament.")

    # 2. Check upcoming tournaments for research phase
    for t in registry.get('upcoming_tournaments', []):
        if t.get('status') not in ('upcoming',):
            continue

        research_date    = datetime.date.fromisoformat(t.get('research_start_date', '2099-01-01'))
        site_launch_date = datetime.date.fromisoformat(t.get('site_launch_date', '2099-01-01'))
        tournament_start = datetime.date.fromisoformat(t['start'])
        days_to_start    = (tournament_start - today).days

        if today >= research_date and today < site_launch_date:
            msg = f"RESEARCH_PHASE_ACTIVE: {t['name']} — host countries: {', '.join(t['host_countries'])}"
            log(f"🔬 {msg}")
            actions_needed.append(msg)
            print(f"::warning title=Research Phase Active::{t['name']} research phase has begun. Run tournament rebuild workflow.")

        elif today >= site_launch_date and today < tournament_start:
            msg = f"SITE_LAUNCH_DUE: {t['name']} — site should be live now ({days_to_start} days to tournament)"
            log(f"🚀 {msg}")
            actions_needed.append(msg)
            print(f"::error title=Site Launch Overdue::{t['name']} site launch date has passed. Tournament in {days_to_start} days!")

        elif days_to_start <= 365 and today < research_date:
            log(f"📅 {t['name']} in {days_to_start} days — research starts {research_date}")

    # 3. Check FIFA.com for new tournament announcements
    try:
        content = web_get('https://www.fifa.com/en/tournaments').lower()
        new_phrases = [
            'host nation confirmed', 'appointed as host', 'bid awarded',
            'new tournament', 'hosting rights awarded', 'will host'
        ]
        found = [p for p in new_phrases if p in content]
        if found:
            msg = f"FIFA_ANNOUNCEMENT: Possible new tournament on FIFA.com — phrases: {found[:3]}"
            log(f"📢 {msg}")
            actions_needed.append(msg)
            print(f"::notice title=FIFA.com Update::New content detected on FIFA.com: {found[:3]}. Manual review recommended.")
    except Exception as e:
        log(f"FIFA.com check skipped: {e}")

    # Update last check date
    registry['last_platform_check'] = today.isoformat()
    registry['last_platform_actions'] = actions_needed
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)

    log(f"\nSummary: {len(actions_needed)} action(s) needed")
    if not actions_needed:
        log("✅ All good — no actions needed this quarter.")
        print("::notice title=Platform Check::All good — no actions needed this quarter.")

if __name__ == '__main__':
    main()
