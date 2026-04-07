#!/usr/bin/env python3
"""
FIFAMap.org Reddit Accuracy Monitor
Runs every 6 hours — searches Reddit, FIFA official sources, and
news for corrections/complaints about fifamap.org content.
Flags issues and saves them for Harry's review.
"""
import urllib.request, json, os, datetime, re

LOG_PATH = '/home/user/workspace/cron_tracking/reddit-monitor/issues.json'
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log(msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print(f"[{ts}] {msg}")

def web_search(query):
    """Search via DuckDuckGo HTML (no API key needed)"""
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        log(f"Search error: {e}")
        return ""

import urllib.parse

def search_reddit_mentions():
    """Search web for Reddit discussions mentioning fifamap or WC2026 transport issues"""
    queries = [
        "fifamap.org reddit site:reddit.com",
        "\"world cup 2026\" transport wrong inaccurate reddit",
        "world cup 2026 sofi stadium metro bus site:reddit.com",
        "world cup 2026 AT&T stadium transit site:reddit.com",
        "world cup 2026 metlife NJ transit site:reddit.com",
    ]
    
    all_issues = []
    for query in queries:
        try:
            log(f"Searching: {query[:60]}")
            content = web_search(query)
            
            # Look for accuracy-related keywords
            issue_keywords = [
                'wrong', 'incorrect', 'inaccurate', 'not true', 'misinformation',
                'actually', 'correction', 'error', 'mistake', 'false',
                'update', 'changed', 'confirmed', 'official'
            ]
            
            content_lower = content.lower()
            found_issues = [kw for kw in issue_keywords if kw in content_lower]
            
            if found_issues:
                # Extract relevant snippets
                for kw in found_issues[:2]:
                    idx = content_lower.find(kw)
                    if idx > 0:
                        snippet = content[max(0,idx-100):idx+200].strip()
                        # Clean HTML
                        snippet = re.sub(r'<[^>]+>', ' ', snippet)
                        snippet = re.sub(r'\s+', ' ', snippet).strip()
                        if len(snippet) > 50:
                            all_issues.append({
                                'query': query,
                                'keyword': kw,
                                'snippet': snippet[:300],
                                'found_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
                            })
        except Exception as e:
            log(f"Query failed: {e}")
    
    return all_issues

def check_official_sources():
    """Check official transport sources for any updates"""
    sources = [
        ('LA Metro World Cup', 'https://www.metro.net/riding/world-cup/'),
        ('NJ Transit FIFA', 'https://www.njtransit.com/fifa'),
        ('FIFA Official', 'https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026'),
    ]
    
    updates = []
    for name, url in sources:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                content = r.read().decode('utf-8', errors='ignore')
            
            update_keywords = ['updated', 'new', 'announced', 'confirmed', 'change', 'revised']
            content_lower = content.lower()
            found = [kw for kw in update_keywords if kw in content_lower]
            
            if found:
                updates.append({
                    'source': name,
                    'url': url,
                    'keywords_found': found[:3],
                    'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
                })
                log(f"  Update detected at {name}: {found[:3]}")
        except Exception as e:
            log(f"  {name} check failed: {e}")
    
    return updates

def load_existing_issues():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            return json.load(f)
    return {"issues": [], "last_checked": None, "total_checks": 0}

def save_issues(data):
    with open(LOG_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    log("=== FIFAMap Reddit Accuracy Monitor ===")
    
    existing = load_existing_issues()
    existing['total_checks'] = existing.get('total_checks', 0) + 1
    existing['last_checked'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    log("Searching Reddit and web for accuracy issues...")
    reddit_issues = search_reddit_mentions()
    
    log("Checking official transport sources for updates...")
    official_updates = check_official_sources()
    
    # Deduplicate against existing issues
    existing_snippets = {i.get('snippet', '')[:50] for i in existing.get('issues', [])}
    new_issues = [i for i in reddit_issues if i.get('snippet', '')[:50] not in existing_snippets]
    
    if new_issues:
        existing['issues'].extend(new_issues)
        save_issues(existing)
        
        summary = f"Found {len(new_issues)} new accuracy issue(s) mentioned online:\n\n"
        for issue in new_issues[:3]:
            summary += f"• Keyword: '{issue['keyword']}'\n  Context: {issue['snippet'][:150]}...\n\n"
        summary += "Review at: /home/user/workspace/cron_tracking/reddit-monitor/issues.json\n"
        summary += "Harry can ask Computer to fix any confirmed inaccuracies on fifamap.org."
        
        log(f"NEW ISSUES: {len(new_issues)}")
        return {"new_issues": len(new_issues), "summary": summary, "should_notify": True}
    
    if official_updates:
        save_issues(existing)
        summary = f"Official source updates detected: {[u['source'] for u in official_updates]}"
        log(summary)
        return {"official_updates": len(official_updates), "summary": summary, "should_notify": True}
    
    save_issues(existing)
    log(f"No new issues found. Total checks: {existing['total_checks']}")
    return {"new_issues": 0, "should_notify": False}

if __name__ == '__main__':
    result = main()
    print(f"\nResult: {result}")
