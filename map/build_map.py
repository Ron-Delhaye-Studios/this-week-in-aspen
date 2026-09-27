#!/usr/bin/env python3
"""Build the Golden Hour interactive map layer.

Skeleton-first design: this script is the DATA PIPELINE. It produces:
  map/events.json        — the data feed the map page reads (schema below)
  map/venues.json        — geocode cache: venue string -> {lat, lng, source}
  map/geocode-review.json — venues that could not be geocoded (human review, never silently dropped)
  map/index.html         — the page shell (nav + filters + Leaflet mount)

Events source: Supabase aspen_events, status=approved (same table as Upcoming/Calendar).
Geocoding: Nominatim (free, no key), 1 req/sec, cached forever in venues.json.

events.json schema (one object per event):
  {id, title, venue, lat, lng, starts_at, ends_at, category,
   price_info, age_policy, url, blurb}

Usage:
  python3 build_map.py --limit 6     # skeleton demo: 6 events, quick
  python3 build_map.py                # full import
  python3 build_map.py --shell-only   # rebuild index.html without touching data
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import live_layer  # noqa: E402 — shared live-layer contract (window + anchors)
MAPDIR = HERE  # this file lives in map/
DENVER = ZoneInfo("America/Denver")
API = "https://ypfhcqeispdunewubxjm.supabase.co/rest/v1"
TABLE = "aspen_events"
ALLOWED = ("ypfhcqeispdunewubxjm.supabase.co",)
CRED = "custom.supabase"
VENUES_JSON = os.path.join(MAPDIR, "venues.json")
REVIEW_JSON = os.path.join(MAPDIR, "geocode-review.json")
EVENTS_JSON = os.path.join(MAPDIR, "events.json")

NAV = [
    ("../index.html", "Latest"),
    ("../upcoming/", "Upcoming"),
    ("../calendar/", "Calendar"),
    ("", "Map"),
    ("../picks/", "Top Picks"),
    ("../editions/", "Archive"),
    ("../sources/", "How we verify"),
]


def supa_get(params):
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(API + "/" + TABLE + "?" + qs,
                                 headers={"Accept": "application/json"})
    add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED)
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())


def fetch_approved(limit=None):
    params = {
        "select": "id,title,venue,starts_at,ends_at,category,price_info,age_policy,url,blurb",
        "status": "eq.approved",
        "order": "starts_at.asc",
    }
    if limit:
        params["limit"] = str(limit)
    return supa_get(params)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


STREET_RE = re.compile(
    r"\b\d+\s+(?:[NSEW]\s+)?(?:[A-Za-z0-9.'-]+\s+){1,3}"
    r"(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Blvd|Boulevard|Way|Ln|Lane|Pl|Place|Ct|Court)\b",
    re.IGNORECASE)

# Approximate town centers for vague venues like "Downtown Aspen".
# Used ONLY when no street address resolves; flagged accuracy="town-center".
TOWN_CENTERS = {
    "aspen": (39.1911, -106.8235),
    "snowmass village": (39.2130, -106.9378),
    "snowmass": (39.2130, -106.9378),
    "basalt": (39.3689, -107.0320),
    "carbondale": (39.4022, -107.2112),
    "denver": (39.7392, -104.9903),
    "boulder": (40.0150, -105.2705),
    "vail": (39.6403, -106.3742),
    "telluride": (37.9375, -107.8123),
    "colorado springs": (38.8339, -104.8214),
    "glenwood springs": (39.5505, -107.3248),
}


def town_of(venue):
    v = venue.lower()
    for town in sorted(TOWN_CENTERS, key=len, reverse=True):
        if town in v:
            return town
    return None


def clean_queries(venue):
    """Candidate Nominatim queries, most-specific first. Street addresses
    beat venue names: 'Belly Up Aspen' alone resolves to the WRONG town."""
    v = venue.strip()
    no_paren = re.sub(r"\s*\([^)]*\)", "", v).strip()
    town = town_of(v)
    town_suffix = (town.title() + ", Colorado") if town else "Colorado"
    cands = []
    m = STREET_RE.search(no_paren)
    if m:
        cands.append(f"{m.group(0).strip()}, {town_suffix}, USA")
    cands.append(v + ", Colorado, USA")
    if no_paren != v:
        cands.append(no_paren + ", Colorado, USA")
    name_only = no_paren.split(",")[0].strip()
    if name_only and name_only != no_paren:
        cands.append(name_only + ", Colorado, USA")
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out, town


def sane_result(query, display_name, town):
    """Reject fuzzy matches in the wrong town (e.g. 'Belly Up' -> Eagle County)."""
    if not town:
        return True
    return town in display_name.lower()


def geocode_nominatim(venue):
    """One venue string -> (lat, lng, display_name, query, accuracy) or None."""
    queries, town = clean_queries(venue)
    for q in queries:
        params = urllib.parse.urlencode({"q": q, "format": "json", "limit": "1"})
        req = urllib.request.Request(
            "https://nominatim.openstreetmap.org/search?" + params,
            headers={"User-Agent": "GoldenHourMap/1.0 (contact: golden-hour)"})
        try:
            res = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
        except Exception:
            res = None
        time.sleep(1.05)  # Nominatim politeness, per attempt
        if res and sane_result(q, res[0].get("display_name", ""), town):
            return (float(res[0]["lat"]), float(res[0]["lon"]),
                    res[0].get("display_name", ""), q, "rooftop")
    # last resort: town center, honestly flagged
    if town:
        lat, lng = TOWN_CENTERS[town]
        return lat, lng, town.title() + " (town center)", "town-center-fallback", "town-center"
    return None


def _clean_str(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() in ("none", "null", "nan", "n/a", "-"):
        return None
    return (s.replace("AURELIAN Desk", "Concierge Desk")
             .replace("AURELIAN", "Concierge"))


def build_data(limit=None):
    rows = fetch_approved(limit)
    # Rolling live window — same policy as Upcoming/Calendar (live_layer.py).
    rows = [r for r in rows if live_layer.in_window(r.get("starts_at"))]
    cache = load_json(VENUES_JSON, {})
    review = load_json(REVIEW_JSON, [])
    review_set = {r["venue"] for r in review}
    # browse photos: same manifest the Upcoming/Calendar builders use —
    # assets/browse/manifest.json maps event id -> filename (no DB column needed)
    try:
        with open(os.path.join(os.path.dirname(HERE), "assets", "browse",
                               "manifest.json"), encoding="utf-8") as f:
            photo_manifest = json.load(f)
    except (OSError, ValueError):
        photo_manifest = {}
    events = []
    new_cached = 0
    for r in rows:
        venue = (r.get("venue") or "").strip()
        if not venue:
            continue
        hit = cache.get(venue)
        if hit is None:
            g = geocode_nominatim(venue)
            if g:
                lat, lng, disp, qused, acc = g
                cache[venue] = {"lat": lat, "lng": lng, "source": "nominatim",
                                "query": qused, "accuracy": acc,
                                "display_name": disp}
                new_cached += 1
                hit = cache[venue]
            else:
                if venue not in review_set:
                    review.append({"venue": venue,
                                   "reason": "nominatim-no-result",
                                   "event_id": r["id"], "title": r.get("title")})
                    review_set.add(venue)
                continue  # never place an event at a guessed location
        img = photo_manifest.get(r["id"])
        events.append({
            "id": r["id"], "title": _clean_str(r.get("title")), "venue": venue,
            "lat": hit["lat"], "lng": hit["lng"],
            "accuracy": hit.get("accuracy", "rooftop"),
            "starts_at": r.get("starts_at"), "ends_at": r.get("ends_at"),
            "category": _clean_str(r.get("category")),
            "price_info": _clean_str(r.get("price_info")),
            "age_policy": _clean_str(r.get("age_policy")),
            "url": _clean_str(r.get("url")),
            "blurb": _clean_str(r.get("blurb")),
            "image": f"assets/browse/{img}" if img else None,
        })
    save_json(VENUES_JSON, cache)
    save_json(REVIEW_JSON, review)
    save_json(EVENTS_JSON, events)
    print(f"events: {len(events)} | venues cached: {len(cache)} (+{new_cached} new) | "
          f"needs review: {len(review)}")


PAGE_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Map — The Golden Hour</title>
{seo}
{analytics}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500;1,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<style>
  :root{{--paper:#fdfcf8;--ink:#1d1a16;--muted:#6e675c;--hair:#e4ded1;--accent:#103d60;--gold:#b98a1d;
    --serif:"Cormorant Garamond",Didot,Georgia,serif;--sans:"Inter",-apple-system,"Segoe UI",sans-serif}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.65}}
  .masthead{{text-align:center;padding:2rem 1.25rem 0}}
  .kicker{{font-size:.72rem;letter-spacing:.22em;text-transform:uppercase;color:var(--accent);margin:0 0 .6rem}}
  h1.brand{{font-family:var(--serif);font-weight:600;font-size:clamp(1.8rem,5vw,2.6rem);margin:0 0 .4rem}}
  .tagline{{color:var(--muted);font-style:italic;margin:0 0 1rem}}
  nav.site-nav{{display:flex;gap:1.2rem;justify-content:center;flex-wrap:wrap;font-size:.82rem;letter-spacing:.08em;text-transform:uppercase}}
  nav.site-nav a{{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--accent);padding-bottom:2px}}
  nav.site-nav a.active{{font-weight:700;border-bottom:3px solid var(--accent)}}
  #controls{{max-width:60rem;margin:1.2rem auto 0;padding:0 1.25rem;display:flex;flex-wrap:wrap;gap:.5rem;align-items:center}}
  .chip{{border:1px solid var(--accent);background:#fff;color:var(--ink);padding:.42rem .9rem;font-size:.72rem;
         letter-spacing:.08em;text-transform:uppercase;cursor:pointer;border-radius:999px}}
  .chip[aria-pressed="true"]{{background:var(--accent);color:#fff}}
  .chip.gold[aria-pressed="true"]{{background:var(--gold);border-color:var(--gold)}}
  #catrow{{max-width:60rem;margin:.6rem auto 0;padding:0 1.25rem;display:flex;flex-wrap:wrap;gap:.45rem}}
  #map{{height:min(72vh,640px);max-width:60rem;margin:1rem auto;border:1px solid var(--hair)}}
  #count{{max-width:60rem;margin:.4rem auto 0;padding:0 1.25rem;color:var(--muted);font-size:.85rem}}
  .ev-date{{font-family:var(--serif);font-weight:700;font-size:1.35rem;color:var(--accent);margin:0}}
  .ev-time{{font-size:.75rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase}}
  .ev-rel{{display:inline-block;font-size:.66rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
           background:var(--accent);color:#fff;border-radius:999px;padding:.15rem .6rem;margin-left:.5rem;vertical-align:middle}}
  .ev-rel.soon{{background:var(--gold)}}
  .leaflet-popup-content{{font-family:var(--sans);margin:.8rem 1rem;line-height:1.5}}
  .leaflet-popup-content h3{{font-family:var(--serif);font-size:1.15rem;margin:.3rem 0 .2rem}}
  .leaflet-popup-content .meta{{font-size:.82rem;color:var(--muted);margin:.1rem 0}}
  .leaflet-popup-content a{{color:var(--accent)}}
  .leaflet-popup-content img.ev-photo{{width:100%;height:150px;object-fit:cover;
    border-radius:6px;margin:0 0 .5rem;display:block}}
  footer.colophon{{text-align:center;color:var(--muted);font-size:.85rem;padding:2rem 1.25rem 3rem}}
  footer.colophon a{{color:var(--ink)}}
  .legend{{display:flex;gap:1rem;flex-wrap:wrap;font-size:.78rem;color:var(--muted)}}
  .dot{{display:inline-block;width:.7rem;height:.7rem;border-radius:50%;margin-right:.3rem;vertical-align:baseline}}
</style>
</head>
<body>
<header class="masthead">
  <p class="kicker">The Golden Hour</p>
  <h1 class="brand">Event Map</h1>
  <p class="tagline">Every verified event, placed on Colorado.</p>
  <nav class="site-nav" aria-label="Sections">
{nav}
  </nav>
</header>

<div id="controls" role="group" aria-label="Date range">
  <button class="chip gold" data-range="today" aria-pressed="false">Today</button>
  <button class="chip" data-range="weekend" aria-pressed="false">This weekend</button>
  <button class="chip" data-range="7" aria-pressed="true">Next 7 days</button>
  <button class="chip" data-range="30" aria-pressed="false">Next 30 days</button>
  <button class="chip" data-range="all" aria-pressed="false">All upcoming</button>
  <button class="chip" data-range="past" aria-pressed="false">Include past</button>
</div>
<div id="catrow" role="group" aria-label="Categories"></div>
<div id="count" aria-live="polite"></div>
<div id="map" role="application" aria-label="Colorado event map"></div>
<div id="controls2" style="max-width:60rem;margin:.6rem auto 0;padding:0 1.25rem">
  <div class="legend">
    <span><span class="dot" style="background:#b98a1d"></span>Today</span>
    <span><span class="dot" style="background:#103d60"></span>Within 7 days</span>
    <span><span class="dot" style="background:#7a8ba0"></span>Within 30 days</span>
    <span><span class="dot" style="background:#c9c2b4"></span>Later</span>
  </div>
</div>

<footer class="colophon">
  <p>Every event verified against official sources before publication. Details may change — please confirm with the venue.</p>
  <p><a href="../index.html">Latest</a> · <a href="../upcoming/">Upcoming</a> · <a href="../calendar/">Calendar</a> · <a href="index.html">Map</a> · <a href="../picks/">Top Picks</a> · <a href="../editions/">Archive</a> · <a href="../sources/">How we verify</a></p>
  <p>© 2026 The Golden Hour · An Ad Astra Media publication. Photography by Ron Delhaye Studios.</p>
</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script src="map.js"></script>
</body>
</html>
"""


def build_shell():
    nav = "\n".join(
        f'    <a href="{href}"' + (' class="active" aria-current="page"' if label == "Map" else "") +
        f'>{label}</a>' for href, label in NAV)
    # PAGE_TMPL was authored with doubled braces (format-style); build_shell
    # uses plain replace, so un-double them here — otherwise browsers drop
    # every CSS rule and the page renders unstyled with no visible map.
    import theme as _theme
    seo = _theme.seo_head("Map — The Golden Hour",
        "Every verified Aspen-area event placed on a map of Colorado.", "map/")
    analytics = _theme.analytics_tags("../")
    page = PAGE_TMPL.replace("{nav}", nav).replace("{seo}", seo).replace("{analytics}", analytics).replace("{{", "{").replace("}}", "}")
    with open(os.path.join(MAPDIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote map/index.html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--shell-only", action="store_true")
    args = ap.parse_args()
    os.makedirs(MAPDIR, exist_ok=True)
    if not args.shell_only:
        build_data(args.limit)
    build_shell()


if __name__ == "__main__":
    main()
