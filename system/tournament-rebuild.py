#!/usr/bin/env python3
"""
FIFAMap.org — Tournament Site Rebuilder
=========================================
Called when a new tournament research phase begins.
Does a full internet research sweep of all host cities,
then rebuilds the entire site with the new tournament's data.

Usage: python3 fifamap-tournament-rebuild.py --tournament wwc2027
"""

import json, os, sys, datetime, subprocess, base64, urllib.request

REGISTRY_PATH = '/home/user/workspace/fifamap-tournament-registry.json'
WORKSPACE = '/home/user/workspace'

def log(msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print(f"[{ts}] {msg}")

def research_city(city, country, tournament_name):
    """Research a single host city for a new tournament"""
    log(f"Researching: {city}, {country} for {tournament_name}")
    
    # This function generates the search queries to pass to wide_research
    queries = [
        f"{city} {tournament_name} stadium transport official",
        f"{city} {tournament_name} fan zone locations dates",  
        f"{city} {country} top attractions tourists 2027",
        f"{city} best restaurants dining visitors",
        f"how to get to {city} stadium transit guide",
    ]
    
    return {
        'city': city,
        'country': country,
        'queries': queries,
        'status': 'queued'
    }

def build_wwc2027_site():
    """
    Full rebuild pipeline for FIFA Women's World Cup 2027 Brazil
    Called automatically from Oct 1, 2026 onwards
    """
    log("=== REBUILDING FIFAMAP.ORG FOR WOMEN'S WORLD CUP 2027 ===")
    
    # Step 1: Research all 10 Brazilian host cities
    cities = [
        ('São Paulo', 'Brazil', 'Estádio do Morumbi or Arena Corinthians'),
        ('Rio de Janeiro', 'Brazil', 'Estádio do Maracanã'),
        ('Belo Horizonte', 'Brazil', 'Estádio Mineirão'),
        ('Salvador', 'Brazil', 'Arena Fonte Nova'),
        ('Porto Alegre', 'Brazil', 'Estádio Beira-Rio'),
        ('Manaus', 'Brazil', 'Arena da Amazônia'),
        ('Curitiba', 'Brazil', 'Estádio Couto Pereira or Arena da Baixada'),
        ('Brasília', 'Brazil', 'Estádio Nacional Mané Garrincha'),
        ('Recife', 'Brazil', 'Arena Pernambuco'),
        ('Fortaleza', 'Brazil', 'Estádio Castelão'),
    ]
    
    city_research_queries = []
    for city, country, stadium in cities:
        city_research_queries.append(research_city(city, country, "Women's World Cup 2027"))
    
    # Step 2: Define the new language priorities for Brazil tournament
    # Portuguese becomes PRIMARY, Spanish secondary
    language_updates = {
        'primary': 'pt',
        'languages': ['pt', 'es', 'en', 'fr', 'ar', 'de', 'ja', 'zh'],
        'note': "WWC2027 is in Brazil — Portuguese is PRIMARY language, Spanish secondary"
    }
    
    # Step 3: Update hero section
    hero_update = {
        'title2': 'FIFA Women\'s World Cup 2027™',
        'badge': 'Official Host Country · Brazil · July–August 2027',
        'sub': '10 host cities across Brazil. Plan your ultimate trip — free.',
        'countdown_target': '2027-07-01T16:00:00-03:00',
        'countdown_note': 'Until the Tournament Opener · Brazil · July 1, 2027'
    }
    
    # Step 4: New article schedule (18 weeks before tournament)
    article_schedule = [
        {'week': 1, 'title': 'FIFA Women\'s World Cup 2027 Brazil: Complete Visitor\'s Guide', 'city': 'All Cities'},
        {'week': 2, 'title': 'São Paulo WWC2027: The Heart of Brazil for Women\'s Football', 'city': 'São Paulo'},
        {'week': 3, 'title': 'Rio de Janeiro WWC2027: Maracanã, Beaches and Carnival Spirit', 'city': 'Rio de Janeiro'},
        {'week': 4, 'title': 'Transport Guide: Getting to Every WWC2027 Stadium in Brazil', 'city': 'All Cities'},
        {'week': 5, 'title': 'Brazil Travel Safety Guide for WWC2027 Visitors', 'city': 'All Cities'},
        {'week': 6, 'title': 'Belo Horizonte WWC2027: Mineirão Stadium and Minas Gerais', 'city': 'Belo Horizonte'},
        {'week': 7, 'title': 'Brazilian Food Guide: What to Eat at WWC2027', 'city': 'All Cities'},
        {'week': 8, 'title': 'Salvador WWC2027: Afro-Brazilian Culture and Arena Fonte Nova', 'city': 'Salvador'},
        {'week': 9, 'title': 'Budget Travel in Brazil for WWC2027: How to Do it Cheap', 'city': 'All Cities'},
        {'week': 10, 'title': 'Visa Requirements for WWC2027 Brazil: Country-by-Country Guide', 'city': 'All Cities'},
        {'week': 11, 'title': 'Brasília WWC2027: The Modern Capital and Mané Garrincha Stadium', 'city': 'Brasília'},
        {'week': 12, 'title': 'Fan Zones Guide: Watch WWC2027 for Free Across Brazil', 'city': 'All Cities'},
        {'week': 13, 'title': 'Recife & Fortaleza WWC2027: Northeast Brazil Beach Cities', 'city': 'Northeast Brazil'},
        {'week': 14, 'title': 'WWC2027 Match Day Guide: What Every First-Timer Must Know', 'city': 'All Cities'},
        {'week': 15, 'title': 'Porto Alegre WWC2027: Southern Brazil and Beira-Rio Stadium', 'city': 'Porto Alegre'},
        {'week': 16, 'title': 'The WWC2027 Knockout Stage: Which Cities Host What?', 'city': 'All Cities'},
        {'week': 17, 'title': 'Amazon Adventure: Manaus WWC2027 and the Rainforest', 'city': 'Manaus'},
        {'week': 18, 'title': 'WWC2027 Final Preview: Everything About the Rio Showdown', 'city': 'Rio de Janeiro'},
    ]
    
    return {
        'tournament': 'FIFA Women\'s World Cup 2027',
        'cities': cities,
        'languages': language_updates,
        'hero': hero_update,
        'articles': article_schedule,
        'rebuild_status': 'blueprint_ready'
    }

def build_wc2030_site():
    """Blueprint for FIFA World Cup 2030 (Spain/Portugal/Morocco + South America)"""
    log("=== BLUEPRINT: WORLD CUP 2030 ===")
    return {
        'tournament': 'FIFA World Cup 2030',
        'host_countries': ['Spain', 'Portugal', 'Morocco', 'Argentina', 'Uruguay', 'Paraguay'],
        'primary_languages': ['es', 'pt', 'fr', 'ar', 'en', 'de', 'ja', 'zh'],
        'key_cities': {
            'Spain': ['Madrid', 'Barcelona', 'Seville', 'Bilbao', 'Valencia', 'Zaragoza', 'Málaga'],
            'Portugal': ['Lisbon', 'Porto', 'Braga'],
            'Morocco': ['Casablanca', 'Rabat', 'Marrakech', 'Tangier', 'Agadir', 'Fez'],
            'South_America': ['Buenos Aires (Argentina)', 'Montevideo (Uruguay)', 'Asunción (Paraguay)']
        },
        'special_notes': 'WC Centenary (100 years). Final likely at Bernabéu Madrid or Grand Stade Hassan II Casablanca (115,000 capacity). 6 countries = biggest logistical challenge in World Cup history.',
        'rebuild_status': 'scheduled_for_2029'
    }

if __name__ == '__main__':
    tournament_id = sys.argv[2] if len(sys.argv) > 2 else 'wwc2027'
    
    if tournament_id == 'wwc2027':
        result = build_wwc2027_site()
    elif tournament_id == 'wc2030':
        result = build_wc2030_site()
    else:
        print(f"Unknown tournament: {tournament_id}")
        sys.exit(1)
    
    # Save blueprint
    blueprint_path = f'{WORKSPACE}/fifamap-blueprint-{tournament_id}.json'
    with open(blueprint_path, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    log(f"Blueprint saved: {blueprint_path}")
    print(f"\n✅ {result['tournament']} blueprint ready")
    print(f"   Cities: {len(result.get('cities', result.get('key_cities', {})))}")
    print(f"   Articles planned: {len(result.get('articles', []))}")
