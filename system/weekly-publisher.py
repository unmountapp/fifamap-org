#!/usr/bin/env python3
"""
FIFAMap.org Weekly Article Publisher
Runs every Monday at 9 AM PDT (16:00 UTC)
Full schedule: April 13, 2026 → August 9, 2026 (17 articles)
Includes: auto-rewrite capability for breaking tournament news
"""
import json, base64, urllib.request, os, re, datetime, subprocess

REPO = 'unmountapp/fifamap-org'
SCHEDULE_PATH = '/home/user/workspace/fifamap-article-schedule.json'

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
        'User-Agent': 'fifamap-publisher/1.0'
    }
    req = urllib.request.Request(
        f"https://{host}/api/v3/{path}",
        data=json.dumps(data).encode() if data else None,
        method=method, headers=hdrs
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        txt = r.read()
        return json.loads(txt) if txt else {}

def check_for_breaking_news(article):
    """
    Check if major World Cup news happened that would require
    rewriting the scheduled article. Returns rewritten article or original.
    """
    try:
        import urllib.request as ur
        # Search for major recent World Cup news
        query = "FIFA+World+Cup+2026+news+today"
        req = ur.Request(
            f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with ur.urlopen(req, timeout=10) as r:
            content = r.read().decode('utf-8', errors='ignore')
        
        # Check for major events: stadium issues, cancellations, etc.
        # Only flag if BOTH a severity word AND a FIFA/World Cup word appear together
        severity_words = [
            'world cup cancelled', 'world cup postponed', 'world cup relocated',
            'fifa suspended', 'stadium evacuated', 'match abandoned',
            'world cup 2026 cancelled', 'host city removed', 'venue changed'
        ]
        content_lower = content.lower()
        found = [kw for kw in severity_words if kw in content_lower]
        
        if found:
            log(f"⚠️  Breaking news detected: {found} — flagging for review")
            # Add a breaking news note to the article
            note = f'<div style="background:rgba(230,57,70,.12);border:2px solid rgba(230,57,70,.4);border-radius:.7rem;padding:1rem;margin-bottom:1.25rem"><strong>⚠️ Update — {datetime.datetime.now(datetime.timezone.utc).strftime("%B %-d, %Y")}:</strong> Breaking developments related to this topic are emerging. Check official sources and FIFA.com for the latest updates. This article will be updated shortly.</div>'
            article['content'] = note + article['content']
            article['title'] = '🔴 ' + article['title']
            log("  Article flagged with breaking news banner")
        else:
            log("No breaking news detected — publishing as scheduled")
    except Exception as e:
        log(f"News check skipped: {e}")
    
    return article

def inject_article_into_site(article, current_html):
    """Inject article into the ARTICLES JS array in index.html"""
    article_json = json.dumps(article, ensure_ascii=False)
    
    if 'var ARTICLES = [' in current_html:
        updated = current_html.replace(
            'var ARTICLES = [',
            f'var ARTICLES = [\n{article_json},',
            1
        )
        return updated
    else:
        log("ERROR: ARTICLES array not found in index.html")
        return None

def validate_js(html):
    """Check that the JS in the HTML is still valid after injection"""
    scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', html, re.DOTALL)
    if not scripts:
        return False, "No scripts found"
    main_js = max(scripts, key=len)
    with open('/tmp/pub_check.js', 'w') as f:
        f.write(main_js)
    result = subprocess.run(['node', '--check', '/tmp/pub_check.js'],
                            capture_output=True, text=True)
    return result.returncode == 0, result.stderr[:200]

def main():
    log("=" * 55)
    log("FIFAMap.org Weekly Article Publisher")
    log("=" * 55)

    # Load schedule
    if not os.path.exists(SCHEDULE_PATH):
        log(f"ERROR: Schedule not found at {SCHEDULE_PATH}")
        return None

    with open(SCHEDULE_PATH, 'r', encoding='utf-8') as f:
        schedule = json.load(f)

    articles = schedule.get('articles', [])
    idx      = schedule.get('next_article_index', 0)

    if idx >= len(articles):
        log(f"All {len(articles)} scheduled articles published. Schedule complete.")
        return {"status": "complete", "total_published": len(articles)}

    article = articles[idx]
    log(f"Article {idx + 1}/{len(articles)}: {article['title']}")
    log(f"Scheduled date: {article['date']}")

    # Update date to today's actual date
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime('%B %-d, %Y')
    article['date'] = today_str

    # Check for breaking news and potentially update article
    article = check_for_breaking_news(article)

    # Fetch current index.html from GitHub
    log("Fetching index.html from GitHub...")
    file_info = github_api(f'repos/{REPO}/contents/index.html')
    current_html = base64.b64decode(
        file_info['content'].replace('\n', '')
    ).decode('utf-8')
    current_sha  = file_info['sha']
    log(f"Got index.html: {len(current_html):,} bytes | SHA: {current_sha[:8]}")

    # Inject article
    updated_html = inject_article_into_site(article, current_html)
    if not updated_html:
        log("FAILED: Could not inject article")
        return None

    # Validate JS syntax
    log("Validating JavaScript syntax...")
    valid, err = validate_js(updated_html)
    if not valid:
        log(f"SYNTAX ERROR — aborting push: {err}")
        return None
    log("✅ JavaScript syntax valid")

    # Push to GitHub
    log("Pushing to GitHub...")
    new_b64 = base64.b64encode(updated_html.encode('utf-8')).decode('ascii')
    result  = github_api(
        f'repos/{REPO}/contents/index.html',
        method='PUT',
        data={
            "message": f"Auto-publish: {article['title']} ({today_str})",
            "content": new_b64,
            "sha": current_sha
        }
    )
    commit = result.get('commit', {}).get('sha', 'unknown')[:10]
    log(f"✅ Pushed! Commit: {commit}")
    log(f"✅ LIVE: {article['title']}")
    log(f"✅ URL: https://fifamap.org (Guides tab)")

    # Update schedule
    schedule['next_article_index'] = idx + 1
    schedule['last_published']      = today_str
    schedule['last_article_title']  = article['title']
    schedule['last_commit']         = commit
    with open(SCHEDULE_PATH, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)
    log("✅ Schedule updated")

    remaining = len(articles) - idx - 1
    log(f"\n📅 Articles remaining in queue: {remaining}")
    if remaining > 0:
        next_a = articles[idx + 1]
        log(f"   Next: '{next_a['title']}' on {next_a['date']}")
    else:
        log("   This was the final scheduled article (Aug 9, 2026)")

    return {
        'title': article['title'],
        'commit': commit,
        'date': today_str,
        'articles_remaining': remaining,
        'next_article': articles[idx + 1]['title'] if remaining > 0 else 'None'
    }

if __name__ == '__main__':
    result = main()
    if result:
        if result.get('status') == 'complete':
            print(f"\n✅ All articles published. Schedule complete.")
        else:
            print(f"\n✅ Published: '{result['title']}'")
            print(f"   Commit: {result['commit']}")
            print(f"   Remaining: {result['articles_remaining']} articles")
            if result['next_article'] != 'None':
                print(f"   Next up: '{result['next_article']}'")
