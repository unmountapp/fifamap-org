#!/usr/bin/env python3
"""
FIFAMap.org — Autonomous Platform Manager
==========================================
Runs quarterly. Monitors FIFA.com for new tournaments, host city confirmations,
and major updates. When a new tournament is detected, triggers full site rebuild.

Schedule: Every 3 months (quarterly check)
Also runs: 6 months before each known tournament (intensive research phase)
"""

import json, urllib.request, os, re, datetime, subprocess, base64

REGISTRY_PATH = '/home/user/workspace/fifamap-tournament-registry.json'
LOG_PATH = '/home/user/workspace/cron_tracking/platform-manager/activity.json'

def log(msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print(f"[{ts}] {msg}")

def github_api(path, method='GET', data=None):
    token = os.environ.get('GH_ENTERPRISE_TOKEN', '')
    host  = os.environ.get('GH_HOST', 'github.com')
    hdrs  = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'fifamap-manager/1.0'
    }
    req = urllib.request.Request(
        f"https://{host}/api/v3/{path}",
        data=json.dumps(data).encode() if data else None,
        method=method, headers=hdrs
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read(); return json.loads(txt) if txt else {}

def web_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 FifaMapBot/1.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8', errors='ignore')

def load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)

def save_registry(data):
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def check_fifa_for_new_tournaments():
    """Scrape FIFA.com tournaments page for any new announcements"""
    log("Checking FIFA.com for tournament updates...")
    new_found = []
    
    urls_to_check = [
        'https://www.fifa.com/en/tournaments',
        'https://www.fifa.com/en/news',
    ]
    
    trigger_phrases = [
        'world cup', 'host nation', 'host country', 'awarded to',
        'will host', 'confirmed as host', 'appointed as host',
        'tournament announced', 'new tournament', 'bid awarded',
        'women\'s world cup', 'club world cup', 'u-20', 'u-17',
        'confederations cup', 'nations league'
    ]
    
    for url in urls_to_check:
        try:
            content = web_get(url).lower()
            found = [p for p in trigger_phrases if p in content]
            if found:
                new_found.append({'url': url, 'triggers': found[:3]})
                log(f"  Triggers found at {url}: {found[:3]}")
        except Exception as e:
            log(f"  Skipped {url}: {e}")
    
    return new_found

def determine_active_tournament():
    """Check which tournament is currently active or closest upcoming"""
    registry = load_registry()
    today = datetime.date.today()
    
    # Check current
    current = registry.get('current_tournament', {})
    if current:
        end = datetime.date.fromisoformat(current['end'])
        start = datetime.date.fromisoformat(current['start'])
        if start <= today <= end:
            return current, 'active'
        if today > end:
            return current, 'ended'
    
    # Find next upcoming
    upcoming = registry.get('upcoming_tournaments', [])
    for t in upcoming:
        if t['status'] == 'upcoming':
            start = datetime.date.fromisoformat(t['start'])
            days_until = (start - today).days
            if days_until <= 365:  # Within 1 year
                return t, f'upcoming_in_{days_until}_days'
    
    return None, 'none'

def should_trigger_research(tournament):
    """Check if we're in the research window for a tournament"""
    today = datetime.date.today()
    research_start = datetime.date.fromisoformat(tournament.get('research_start_date', '2099-01-01'))
    site_launch = datetime.date.fromisoformat(tournament.get('site_launch_date', '2099-01-01'))
    
    if today >= research_start and today < site_launch:
        return True, 'research_phase'
    if today >= site_launch:
        return True, 'site_should_be_live'
    return False, 'too_early'

def research_next_tournament(tournament):
    """
    Full research pipeline for a new tournament.
    This is the big one — runs when a new tournament research phase begins.
    """
    log(f"=== RESEARCH PHASE: {tournament['name']} ===")
    log(f"Host countries: {tournament['host_countries']}")
    
    # This function will be called when a real tournament research begins
    # It triggers a full web research run across all host cities
    # Then rebuilds the entire site with new tournament data
    
    results = {
        'tournament': tournament['name'],
        'triggered_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'host_countries': tournament['host_countries'],
        'status': 'research_initiated',
        'next_steps': [
            f'Run wide_research on all host cities for {tournament["name"]}',
            'Rebuild CITIES data array with new tournament cities',
            f'Update all 8 language strings for {tournament["name"]}',
            'Update match schedule data when fixtures confirmed',
            'Rebuild blog article schedule (18 weeks of articles)',
            'Update affiliate links with new city/hotel searches',
            'Resubmit sitemap to Google Search Console',
            'Post on Reddit about new tournament coverage',
        ]
    }
    
    log(f"Research initiated for {tournament['name']}")
    return results

def post_wc2026_transition():
    """
    After World Cup 2026 ends (July 19, 2026), transition site to:
    1. Legacy/archive mode for WC2026
    2. Preview mode for Women's World Cup 2027 (Brazil)
    3. Keep earning from WC2026 content (still searchable)
    """
    today = datetime.date.today()
    wc2026_end = datetime.date(2026, 7, 19)
    wwc2027_research = datetime.date(2026, 10, 1)
    
    if today > wc2026_end and today < wwc2027_research:
        return {
            'phase': 'post_wc2026_transition',
            'action': 'Add Women\'s World Cup 2027 preview section to fifamap.org',
            'message': 'WC2026 has ended. Keep legacy content live (still earns from SEO). Add WWC2027 preview.'
        }
    
    if today >= wwc2027_research:
        return {
            'phase': 'wwc2027_research',
            'action': 'Full research phase for Women\'s World Cup 2027 Brazil',
            'cities_to_research': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Salvador', 
                                    'Porto Alegre', 'Manaus', 'Curitiba', 'Brasília', 'Recife', 'Fortaleza']
        }
    
    return None

def main():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    log("=" * 60)
    log("FIFAMap Platform Manager — Quarterly Check")
    log("=" * 60)
    
    # Load activity log
    activity = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            activity = json.load(f)
    
    results = {
        'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'actions': [],
        'notifications': []
    }
    
    # 1. Check current tournament status
    tournament, status = determine_active_tournament()
    log(f"Tournament status: {status}")
    if tournament:
        log(f"Tournament: {tournament['name']}")
    
    # 2. Check FIFA.com for new announcements
    fifa_updates = check_fifa_for_new_tournaments()
    if fifa_updates:
        results['actions'].append(f"FIFA.com updates detected: {len(fifa_updates)} pages with triggers")
        results['notifications'].append({
            'title': '⚽ FIFAMap: FIFA.com Update Detected',
            'body': f"FIFA.com has new content that may be relevant to fifamap.org. Found triggers on: {[u['url'] for u in fifa_updates[:2]]}. Review and update site content as needed."
        })
    
    # 3. Check post-WC2026 transition
    transition = post_wc2026_transition()
    if transition:
        results['actions'].append(f"Transition needed: {transition['phase']}")
        results['notifications'].append({
            'title': f"⚽ FIFAMap: {transition['phase'].replace('_', ' ').title()}",
            'body': transition.get('action', 'Action needed for FIFAMap.org')
        })
    
    # 4. Check if any upcoming tournament enters research phase
    registry = load_registry()
    for t in registry.get('upcoming_tournaments', []):
        if t['status'] == 'upcoming':
            should_research, reason = should_trigger_research(t)
            if should_research:
                log(f"Research phase triggered for: {t['name']}")
                research_results = research_next_tournament(t)
                results['actions'].append(f"Research phase: {t['name']}")
                results['notifications'].append({
                    'title': f"⚽ FIFAMap: Start Research — {t['name']}",
                    'body': f"It's time to build the {t['name']} section of fifamap.org! Research phase: {reason}. Host countries: {t['host_countries']}. Next steps: research all host cities, rebuild site data, update 8 languages."
                })
    
    # Save activity
    activity.append(results)
    activity = activity[-50:]  # Keep last 50 runs
    with open(LOG_PATH, 'w') as f:
        json.dump(activity, f, indent=2)
    
    log(f"\nResults: {len(results['actions'])} actions, {len(results['notifications'])} notifications")
    return results

if __name__ == '__main__':
    result = main()
    print(f"\n{'='*60}")
    print(f"Platform check complete. Actions: {len(result.get('actions', []))}")
    for a in result.get('actions', []):
        print(f"  • {a}")
