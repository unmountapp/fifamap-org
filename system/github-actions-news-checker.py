#!/usr/bin/env python3
"""
FIFAMap Breaking News Checker — GitHub Actions Version
Runs daily June-August during active tournaments.
Checks FIFA.com and BBC Sport for critical World Cup updates.
Outputs GitHub Actions error annotations if crisis detected.
"""
import json, datetime, os, urllib.request, sys

INDEX_PATH = 'index.html'
LOG_PATH   = 'system/news-checker-log.json'

def log(msg):
    print(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] {msg}", flush=True)

def web_get(url):
    req = urllib.request.Request(
        url, headers={'User-Agent': 'FifaMapBot/1.0 (+https://fifamap.org)'}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode('utf-8', errors='ignore').lower()

def main():
    log("=== FIFAMap Breaking News Checker ===")
    today = datetime.date.today().isoformat()

    # Load log
    log_data = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            log_data = json.load(f)
        # Already checked today?
        if log_data and log_data[-1].get('date') == today:
            log("Already checked today — nothing to do")
            sys.exit(0)

    # Crisis-level phrases that actually affect WC2026
    crisis_phrases = [
        'world cup 2026 cancelled', 'world cup cancelled',
        'world cup 2026 postponed', 'world cup postponed',
        'sofi stadium closed', 'metlife stadium closed',
        'att stadium closed', 'mercedes-benz stadium closed',
        'stadium evacuated', 'match abandoned', 'fifa suspends world cup',
        'host city removed from world cup', 'venue changed emergency'
    ]

    # Also check for accuracy-relevant updates (transport, fan zones)
    accuracy_phrases = [
        'metro transport update world cup 2026',
        'sofi stadium transit change',
        'nj transit world cup update',
        'fan festival cancelled',
        'fan zone cancelled world cup'
    ]

    sources = [
        'https://www.fifa.com/en/news',
        'https://www.bbc.com/sport/football/world-cup',
    ]

    crisis_found   = []
    accuracy_found = []

    for url in sources:
        try:
            content = web_get(url)
            crisis_found.extend([p for p in crisis_phrases if p in content])
            accuracy_found.extend([p for p in accuracy_phrases if p in content])
            log(f"  ✅ Checked: {url}")
        except Exception as e:
            log(f"  ⚠️  Failed: {url} — {e}")

    # De-duplicate
    crisis_found   = list(set(crisis_found))
    accuracy_found = list(set(accuracy_found))

    # Log entry
    entry = {
        'date': today,
        'crisis': crisis_found,
        'accuracy_updates': accuracy_found,
        'status': 'crisis' if crisis_found else ('update' if accuracy_found else 'clear')
    }
    log_data.append(entry)
    log_data = log_data[-90:]  # Keep 90 days

    with open(LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)

    # Output results
    if crisis_found:
        log(f"🚨 CRISIS DETECTED: {crisis_found}")
        print(f"::error title=FIFAMap Crisis Alert::Breaking news detected: {crisis_found[:3]}. Immediate review required — site may need emergency updates.")
        # This creates a GitHub Actions error that emails the repo owner
        sys.exit(1)  # Fail the workflow so GitHub notifies the owner by email

    elif accuracy_found:
        log(f"⚠️  Accuracy update detected: {accuracy_found}")
        print(f"::warning title=FIFAMap Accuracy Update::Possible transport/venue update: {accuracy_found[:3]}. Review and update site transport data.")

    else:
        log("✅ Clear — no breaking news. Site content remains accurate.")
        print("::notice title=News Check Clear::No breaking FIFA news detected today.")

if __name__ == '__main__':
    main()
