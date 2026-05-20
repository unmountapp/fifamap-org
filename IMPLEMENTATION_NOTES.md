# FIFAMap.org — Commercial Upgrade Implementation Notes

## Overview
This update transforms fifamap.org from a travel guide into a decision-making platform for World Cup 2026 fans, travelers, venues, and sponsors.

## What Was Added

### Phase 1 — Homepage Decision Point
- Intent Router: 6 intent cards (Plan My Trip, Where to Stay, Watch Parties, Getting Around, Follow My Team, Explore Cities)
- Featured Partners Block: renders from `data/partners.js` (Booking.com, Viator, Skyscanner)
- Guide Discovery Cards: 6 high-intent cards (Hotels, Transport, Watch Parties, Budget, Family, Fan Zones)
- Updated hero: "Hotels. Matches. Transport. Nightlife. 16 cities. Your trip starts here — free."
- Nightlife added to quick grid and cross-linked throughout

### Phase 2 — Planner Conversion
- Value prop block: "Plan your World Cup trip in minutes"
- Pricing strip: Free (2 messages), Single Trip ($4.99), Tournament Pass ($9.99/mo)
- Free limit changed from 3 to 2 messages
- Soft warning after 1st message: "You have 1 free message left"
- Upgrade modal: "Unlock Your Full World Cup Itinerary"
- Monetizable cross-links below planner: Hotels, Watch Parties, Transport, Tours

### Phase 3 — Partner Data System
- `data/partners.js`: all partner/venue/sponsor data in one editable file
- `renderPartnerCard()` function for reusable partner card rendering
- Sponsor slot registry for all page types

### Phase 4 — Cross-linking
- Guide discovery cards on homepage
- Cross-links: matches → nightlife, dining → nightlife, transport → nightlife + planner
- Every page now links to planner, hotels, and nightlife

### Phase 5 — Nightlife Page (`page-nightlife`)
- City-specific watch party areas with vibe descriptions
- Featured venue listings with badges
- Email capture: "Get Nightlife & Watch Party Updates"
- Venue owner CTA linking to Advertise page
- Data covers LA, NYC, Dallas, Miami, Mexico City, Toronto, Vancouver

### Phase 6 — Structured Partner Data (`data/partners.js`)
- `PARTNERS` array: all inventory with city, category, tier, badge, tags, CTA
- `WATCH_PARTIES` object: nightlife areas per city
- `SPONSOR_SLOTS` object: available inventory per page/city

### Phase 7 — Email Capture (4 pages)
- Homepage, Cities, Nightlife, Advertise
- `handleEmailCapture(context)` stores to localStorage with city/lang/planner usage
- TODO: Wire to Mailchimp/ConvertKit — data at key `fifamap_captures`

### Phase 8 — Advertise Page (`page-advertise`)
- Full pitch page: High-Intent Audience, 16 Cities / 8 Languages, AI Planner Integration
- 7 placement types with pricing
- Lead form: email + company name
- Contact: customercareblackaiser@gmail.com

### Phase 9 — SEO & Internal Linking
- Cross-links from all section pages
- Nightlife and Advertise add keyword-rich content
- Footer expanded with full site navigation

### Phase 10 — Quality Control
- All affiliate integrations preserved (AdSense, Booking.com/Awin, Viator, StubHub, Viagogo, Skyscanner)
- GitHub Pages compatible (static only)
- Mobile responsive CSS for all new components
- Multilingual architecture preserved
- Contact email: customercareblackaiser@gmail.com
- Footer: "Built by Harry" preserved

## Key Configurable Values

| Item | Location |
|------|----------|
| Free message limit | `var FREE_LIMIT = 2;` in index.html |
| Stripe URLs | `STRIPE_TRIP_URL`, `STRIPE_MONTH_URL` in index.html |
| Partner data | `data/partners.js` |
| Email capture | `handleEmailCapture()` in index.html → wire to email service |
| Contact email | `customercareblackaiser@gmail.com` throughout |

## Files Changed
- `index.html` — all UI changes (CSS, HTML, JS) — 925+ lines added
- `data/partners.js` — NEW: structured partner/listing/watchparty data
- `IMPLEMENTATION_NOTES.md` — NEW: this file
