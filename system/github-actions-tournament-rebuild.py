#!/usr/bin/env python3
"""
FIFAMap Tournament Rebuilder — GitHub Actions Version
Triggered Oct 1 annually. In Oct 2026: launches WWC2027 Brazil preview.
In Oct 2029: launches WC2030 Spain/Portugal/Morocco preview.
Researches host cities from official sources, updates index.html.
"""
import json, datetime, os, sys, re, urllib.request, urllib.parse

REGISTRY_PATH = 'system/tournament-registry.json'
INDEX_PATH    = 'index.html'

def log(msg):
    print(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] {msg}", flush=True)

def web_search(query):
    """Search for official info about a city/tournament"""
    try:
        encoded = urllib.parse.quote_plus(query)
        req = urllib.request.Request(
            f"https://html.duckduckgo.com/html/?q={encoded}",
            headers={'User-Agent': 'Mozilla/5.0 FifaMapBot/1.0 (+https://fifamap.org)'}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        log(f"Search failed for '{query}': {e}")
        return ""

def research_city(city, country, tournament):
    """Research key facts about a host city for a tournament"""
    log(f"  Researching: {city}, {country}...")
    content = web_search(f"{city} {tournament} stadium transport official 2027")
    # Extract relevant snippets (simplified — in real use this feeds into site data)
    snippets = []
    for line in content.split('\n'):
        line = re.sub(r'<[^>]+>', ' ', line).strip()
        if len(line) > 50 and any(w in line.lower() for w in ['stadium', 'transport', 'metro', 'train', 'bus', city.lower()]):
            snippets.append(line[:200])
    return snippets[:3]

def add_tournament_preview(html, tournament_data):
    """Add a 'Coming Next on FIFAMap.org' section to the site"""
    today_str = datetime.date.today().strftime('%B %-d, %Y')
    name      = tournament_data['name']
    emoji     = tournament_data['emoji']
    badge     = tournament_data['badge']
    sub       = tournament_data['sub']
    cities    = tournament_data['cities']
    note      = tournament_data['countdown_note']

    city_pills = "".join(
        f'<span style="padding:.3rem .7rem;background:var(--navy3);border:1px solid var(--border);'
        f'border-radius:.4rem;font-size:.72rem">{c}</span>'
        for c in cities[:6]
    )
    if len(cities) > 6:
        city_pills += (f'<span style="padding:.3rem .7rem;background:var(--navy3);border:1px solid '
                       f'var(--border);border-radius:.4rem;font-size:.72rem">+{len(cities)-6} more</span>')

    preview = f"""
<!-- NEXT TOURNAMENT PREVIEW — auto-added {today_str} -->
<div id="next-tournament" style="background:linear-gradient(135deg,rgba(0,150,50,.08),rgba(0,100,200,.06));border-top:3px solid #22c55e;padding:2.5rem 0;margin-top:2rem">
  <div class="container" style="text-align:center">
    <div style="font-size:3rem;margin-bottom:.5rem">{emoji}</div>
    <div style="font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem">Coming Next on FIFAMap.org</div>
    <h2 style="font-size:1.4rem;font-weight:800;margin-bottom:.4rem">{name}</h2>
    <p style="color:var(--muted);font-size:.82rem;margin-bottom:.75rem">{badge}</p>
    <p style="color:var(--muted);font-size:.8rem;max-width:450px;margin:0 auto 1.25rem">{sub}</p>
    <div style="display:flex;flex-wrap:wrap;gap:.4rem;justify-content:center;margin-bottom:1rem">
      {city_pills}
    </div>
    <p style="font-size:.72rem;color:var(--muted)">{note}</p>
  </div>
</div>
"""

    # Remove any existing preview section first
    html = re.sub(r'<!-- NEXT TOURNAMENT PREVIEW.*?</div>\s*</div>\s*</div>', '', html, flags=re.DOTALL)

    # Insert before footer
    if '<footer' in html:
        return html.replace('<footer', preview + '\n<footer', 1)
    else:
        return html.replace('</body>', preview + '\n</body>')

def main():
    today = datetime.date.today()
    year  = today.year
    tournament_env = os.environ.get('TOURNAMENT', 'auto')

    log(f"=== Tournament Rebuilder — {today} (year={year}, tournament={tournament_env}) ===")

    # Determine which tournament to build for
    if year == 2026 or tournament_env == 'wwc2027':
        log("Building preview: FIFA Women's World Cup 2027 — Brazil")
        tournament_data = {
            "name": "FIFA Women's World Cup 2027\u2122",
            "emoji": "\U0001f1e7\U0001f1f7",
            "badge": "Official Host Country \u00b7 Brazil \u00b7 July\u2013August 2027",
            "sub": "10 host cities across Brazil. The first Women's World Cup in South America. Plan your trip \u2014 free.",
            "countdown_note": "Until the WWC2027 Opener \u00b7 Brazil \u00b7 July 1, 2027",
            "cities": ["S\u00e3o Paulo","Rio de Janeiro","Belo Horizonte","Salvador",
                       "Porto Alegre","Manaus","Curitiba","Bras\u00edlia","Recife","Fortaleza"]
        }

        # Research cities (light touch — full research happens via separate workflow)
        log("Researching host cities...")
        research_results = {}
        for city in tournament_data['cities'][:3]:  # Research first 3 as sample
            results = research_city(city, 'Brazil', "Women's World Cup 2027")
            research_results[city] = results
            log(f"  {city}: {len(results)} facts found")

        # Save research
        with open('system/wwc2027-city-research.json', 'w', encoding='utf-8') as f:
            json.dump(research_results, f, ensure_ascii=False, indent=2)
        log("✅ City research saved to system/wwc2027-city-research.json")

    elif year >= 2029 or tournament_env == 'wc2030':
        log("Building preview: FIFA World Cup 2030 — Spain/Portugal/Morocco")
        tournament_data = {
            "name": "FIFA World Cup 2030\u2122",
            "emoji": "\U0001f30d",
            "badge": "Spain \u00b7 Portugal \u00b7 Morocco \u00b7 + South America \u00b7 The Centenary World Cup",
            "sub": "6 host countries. 100 years of the World Cup. The biggest tournament ever. Plan your trip \u2014 free.",
            "countdown_note": "Until the WC2030 Opener \u00b7 2030",
            "cities": ["Madrid","Barcelona","Lisbon","Porto","Casablanca",
                       "Rabat","Marrakech","Seville","Buenos Aires","Montevideo"]
        }
    else:
        log(f"No rebuild needed for {year}. Tournament env: {tournament_env}")
        print(f"::notice title=No Rebuild Needed::Year {year} — no tournament rebuild triggered.")
        sys.exit(0)

    # Update index.html with preview
    if not os.path.exists(INDEX_PATH):
        log(f"ERROR: {INDEX_PATH} not found")
        sys.exit(1)

    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    updated_html = add_tournament_preview(html, tournament_data)

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(updated_html)

    log(f"✅ index.html updated with {tournament_data['name']} preview")
    print(f"::notice title=Tournament Preview Added::{tournament_data['name']} preview section added to fifamap.org")

if __name__ == '__main__':
    main()
