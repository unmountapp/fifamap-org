#!/usr/bin/env python3
"""
FIFAMap Weekly Article Publisher — GitHub Actions Version
Runs every Monday at 9AM PDT via GitHub Actions (FREE — no credits needed).
Reads system/article-schedule.json → injects next article into index.html.
GitHub Actions commits and pushes automatically after this script runs.
"""
import json, re, datetime, os, subprocess, sys

SCHEDULE_PATH = 'system/article-schedule.json'
INDEX_PATH    = 'index.html'

def log(msg):
    print(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] {msg}", flush=True)

def check_breaking_news():
    """Check for FIFA-specific crisis-level breaking news only"""
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://www.fifa.com/en/news',
            headers={'User-Agent': 'FifaMapBot/1.0 (+https://fifamap.org)'}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read().decode('utf-8', errors='ignore').lower()
        crisis = ['world cup cancelled','world cup postponed','world cup 2026 cancelled',
                  'stadium evacuated','match abandoned','host city removed','venue changed emergency']
        return [p for p in crisis if p in content]
    except Exception as e:
        log(f"News check skipped: {e}")
        return []

def main():
    log("=== FIFAMap Weekly Article Publisher (GitHub Actions) ===")

    if not os.path.exists(SCHEDULE_PATH):
        log(f"Schedule not found at {SCHEDULE_PATH} — nothing to publish")
        sys.exit(0)

    with open(SCHEDULE_PATH, 'r', encoding='utf-8') as f:
        schedule = json.load(f)

    articles = schedule.get('articles', [])
    idx      = schedule.get('next_article_index', 0)

    if idx >= len(articles):
        log("All articles published. Schedule complete.")
        print("::notice title=FIFAMap Publisher::All scheduled articles have been published.")
        sys.exit(0)

    article = articles[idx]
    today   = datetime.datetime.utcnow().strftime('%B %-d, %Y')
    article['date'] = today
    log(f"Publishing article {idx+1}/{len(articles)}: {article['title']}")

    # Breaking news check
    breaking = check_breaking_news()
    if breaking:
        log(f"Breaking news detected: {breaking}")
        note = (f'<div style="background:rgba(230,57,70,.12);border:2px solid rgba(230,57,70,.4);'
                f'border-radius:.7rem;padding:1rem;margin-bottom:1.25rem"><strong>⚠️ Update '
                f'({today}):</strong> Major FIFA developments are emerging. Check '
                f'<a href="https://fifa.com" target="_blank">fifa.com</a> for the latest. '
                f'This article will be updated shortly.</div>')
        article['content'] = note + article['content']
        print(f"::warning title=Breaking News::Crisis detected: {breaking}")

    # Load and update index.html
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    if 'var ARTICLES = [' not in html:
        log("ERROR: ARTICLES array not found in index.html — aborting")
        sys.exit(1)

    article_json = json.dumps(article, ensure_ascii=False)
    updated_html = html.replace('var ARTICLES = [', f'var ARTICLES = [\n{article_json},', 1)

    # Validate JS syntax using Node.js (pre-installed on GitHub Actions ubuntu-latest)
    scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', updated_html, re.DOTALL)
    if scripts:
        main_js = max(scripts, key=len)
        with open('/tmp/check.js', 'w') as f:
            f.write(main_js)
        result = subprocess.run(['node', '--check', '/tmp/check.js'], capture_output=True, text=True)
        if result.returncode != 0:
            log(f"JS SYNTAX ERROR — aborting publish: {result.stderr[:200]}")
            sys.exit(1)
        log("✅ JavaScript syntax valid")

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(updated_html)
    log(f"✅ index.html updated")

    # Update schedule tracking
    schedule['next_article_index'] = idx + 1
    schedule['last_published']      = today
    schedule['last_article_title']  = article['title']
    with open(SCHEDULE_PATH, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    remaining = len(articles) - idx - 1
    log(f"✅ Done! Articles remaining: {remaining}")
    if remaining > 0:
        log(f"   Next Monday: '{articles[idx+1]['title']}'")

    print(f"::notice title=Article Published::'{article['title']}' published on {today}. {remaining} articles remaining.")

if __name__ == '__main__':
    main()
