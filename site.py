#!/usr/bin/env python3
"""Build 'The Golden Hour' media website.

Generates from sources.json + verification.json + editions/:
  index.html            homepage — brand, latest edition, archive
  sources/index.html    public source registry ("How we verify")
  desk/index.html       internal research & verification desk (noindex, not linked publicly)

Usage: python3 site.py
"""
import datetime as dt
import html
import json
import os
import re

import theme

HERE = os.path.dirname(os.path.abspath(__file__))
EDITIONS = os.path.join(HERE, "editions")

CONTACT = "Ron Delhaye, Jr. · (970) 925-0000 · Ron.Delhaye@RitzCarlton.com"

PWA_HEAD = """<link rel="manifest" href="/this-week-in-aspen/manifest.json">
<meta name="theme-color" content="#0a1628">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Golden Hour">
<link rel="apple-touch-icon" href="/this-week-in-aspen/icons/apple-touch-icon.png">
<script>
if ("serviceWorker" in navigator) {{
  window.addEventListener("load", function () {{
    navigator.serviceWorker.register("/this-week-in-aspen/sw.js", {{ scope: "/this-week-in-aspen/" }});
  }});
}
</script>"""

def head_html(title, extra_head="", seo_desc=None, seo_path=""):
    seo = theme.seo_head(title, seo_desc, seo_path) if seo_desc else ""
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
            '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + extra_head + PWA_HEAD + "<title>" + html.escape(title) + "</title>\n" + seo
            + theme.FONT_LINKS + "\n<style>\n" + theme.CORE_CSS + EXTRA_CSS + "\n</style>\n</head>\n"
            '<body>\n<div class="page">\n')


EXTRA_CSS = """
  .hero{border:1px solid var(--hair);padding:1.6rem 1.4rem;margin-top:1rem;background:#fff}
  .hero .ed-range{font-size:.75rem;letter-spacing:.18em;text-transform:uppercase;color:var(--accent)}
  .hero h3{font-family:var(--serif);font-size:1.6rem;margin:.4rem 0 .4rem}
  .hero p{color:var(--muted);margin:.4rem 0 1rem}
  ul.archive{list-style:none;padding:0;margin:1rem 0}
  ul.archive li{padding:.7rem 0;border-bottom:1px solid var(--hair)}
  ul.archive a{color:var(--ink);text-decoration-color:var(--accent);text-underline-offset:3px}
  ul.archive .when{display:block;font-size:.8rem;color:var(--muted)}
  .method{border-left:2px solid var(--accent);padding:.4rem 0 .4rem 1rem;color:var(--muted);
          font-style:italic;margin:1.2rem 0}
  .pagetitle h2{font-family:var(--serif);font-weight:600;font-size:2rem;margin:.2rem 0 .4rem}
  .rubric{counter-reset:step;list-style:none;padding:0;margin:1.2rem 0}
  .rubric li{counter-increment:step;position:relative;padding:.7rem 0 .7rem 2.6rem;border-bottom:1px solid var(--hair)}
  .rubric li::before{content:counter(step);position:absolute;left:0;top:.65rem;width:1.7rem;height:1.7rem;
    border:1.5px solid var(--accent);color:var(--accent);border-radius:50%;
    display:flex;align-items:center;justify-content:center;font-size:.8rem;font-weight:700}
  .rubric li b{display:block;font-size:.95rem}
  .rubric li span{color:var(--muted);font-size:.9rem}
  .pick{border:1px solid var(--hair);background:#fff;padding:1.2rem;margin:0 0 1rem}
  .pick .cat{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 .3rem}
  .pick h3{font-family:var(--serif);font-size:1.3rem;margin:0 0 .25rem}
  .pick .score{display:inline-block;border:1.5px solid var(--gold);color:var(--ink);font-weight:700;
    font-size:.85rem;padding:.15rem .6rem;border-radius:999px;margin-left:.5rem;vertical-align:middle}
  .pick .why{margin:.5rem 0;font-size:.95rem}
  .pick .src{font-size:.82rem;color:var(--muted);margin:.2rem 0}
  table.src{width:100%;border-collapse:collapse;margin:1.2rem 0;font-size:.92rem}
  table.src th{text-align:left;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;
               color:var(--muted);border-bottom:1px solid var(--accent);padding:.5rem .4rem}
  table.src td{border-bottom:1px solid var(--hair);padding:.6rem .4rem;vertical-align:top}
  table.src a{color:var(--ink);text-decoration-color:var(--accent);text-underline-offset:2px}
  .rel-highest,.rel-high,.rel-medium,.rel-low{display:inline-block;padding:.28rem .8rem;border-radius:999px;
               font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
               border:1.5px solid;white-space:nowrap}
  .rel-highest{color:#1b5e20;border-color:#2e7d32;background:#e8f5e9}
  .rel-high{color:#33691e;border-color:#558b2f;background:#f1f8e9}
  .rel-medium{color:#7a5c14;border-color:#b89b3e;background:#fdf6e3}
  .rel-low{color:#8f2d2d;border-color:#c05757;background:#fbeeee}
  table.desk{width:100%;border-collapse:collapse;margin:1.2rem 0;font-size:.86rem}
  table.desk th{text-align:left;font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;
                color:var(--muted);border-bottom:1px solid var(--accent);padding:.5rem .35rem}
  table.desk td{border-bottom:1px solid var(--hair);padding:.55rem .35rem;vertical-align:top}
  .pill{display:inline-block;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;
        border:1px solid;padding:.15rem .55rem;border-radius:2px;white-space:nowrap}
  .st-verified-official{border-color:#2e7d32;color:#2e7d32}
  .st-verified-secondary{border-color:#33691e;color:#33691e}
  .st-needs-check{border-color:#8f7134;color:#8f7134}
  .st-time-conflict{border-color:#b3261e;color:#b3261e}
  .st-replaced{border-color:#6e675c;color:#6e675c}
  .flag{border:1px solid var(--ink);font-size:.68rem;padding:.1rem .4rem;white-space:nowrap}
  @media print{ nav.site-nav, .btn {display:none} }
"""


# Nav, masthead, footer: single-sourced from theme.py


def load_json(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


def edition_weeks():
    weeks = []
    if os.path.isdir(EDITIONS):
        for name in os.listdir(EDITIONS):
            d = os.path.join(EDITIONS, name, "index.html")
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", name) and os.path.isfile(d):
                weeks.append(name)
    weeks.sort(reverse=True)
    return weeks


def edition_label(week):
    sat = dt.date.fromisoformat(week)
    end = sat + dt.timedelta(days=7)
    return (f"{sat.strftime('%A')}, {sat.strftime('%B')} {sat.day} – "
            f"{end.strftime('%A')}, {end.strftime('%B')} {end.day}, {end.year}")


def build_homepage(weeks):
    body = [head_html("The Golden Hour", seo_desc="The Golden Hour is a weekly field guide to what's on in Aspen and beyond — music, art, and high-country happenings, verified before publication.", seo_path="")]
    body.append(theme.masthead("", "latest"))
    if weeks:
        latest = weeks[0]
        body.append('  <h2 class="section">This week</h2>')
        body.append('  <div class="hero">')
        body.append(f'    <p class="ed-range">{html.escape(edition_label(latest))}</p>')
        body.append('    <h3>The current edition</h3>')
        body.append('    <p>Eight days of curated picks — arriving Saturday through departure Saturday — each one verified against official sources.</p>')
        body.append(f'    <a class="btn" href="editions/{latest}/">Read the edition</a>')
        body.append('  </div>')
    body.append('  <h2 class="section">Explore the live guide</h2>')
    body.append('  <p class="lede">The guide never sleeps: every verified event, four ways in — always current, always sourced.</p>')
    body.append('  <div class="explore">')
    for href, kicker, title, blurb in [
        ("upcoming/", "Browse", "Upcoming", "Every verified event, soonest first."),
        ("calendar/", "Plan", "Calendar", "The month at a glance, Google-style."),
        ("map/", "Wander", "Map", "Every event placed on Colorado."),
        ("picks/", "The Concierge", "Top Picks", "Local staples, scored and verified."),
    ]:
        body.append(f'    <a href="{href}"><p class="ek">{kicker}</p><h3>{title}</h3><p>{blurb}</p></a>')
    body.append('  </div>')
    if len(weeks) > 1:
        body.append('  <h2 class="section">Past editions</h2>')
        body.append('  <ul class="archive">')
        for w in weeks[1:]:
            body.append(f'    <li><a href="editions/{w}/">{html.escape(edition_label(w))}</a>'
                        f'<span class="when">Published for arrivals {w}</span></li>')
        body.append('  </ul>')
    body.append('  <h2 class="section">How we verify</h2>')
    body.append('  <p class="method">Every event is checked against the venue\'s own page or a trusted local source before it reaches you. Aggregator listings alone never make the cut — and when two sources disagree on a time, we hold the pick until one is authoritative.</p>')
    body.append('  <p><a class="btn" href="sources/">See our sources</a></p>')
    body.append(theme.footer(""))
    return "\n".join(body)


def build_sources_page(sources):
    by_cat = {}
    for s in sources:
        by_cat.setdefault(s["category"], []).append(s)
    cat_titles = {
        "venue-official": "Venue & organizer pages",
        "venue-social": "Venue social channels",
        "local-news": "Local news",
        "regional": "Regional & Colorado coverage",
        "tourism-official": "Tourism & town calendars",
        "aggregator": "Aggregators (fallback only)",
    }
    body = [head_html("How we verify — The Golden Hour", seo_desc="How The Golden Hour verifies every event against official sources before publication.", seo_path="sources/")]
    body.append(theme.masthead("../", "verify"))
    body.append('  <h2 class="section">How we verify</h2>')
    body.append('  <p class="method">Each week\'s picks are researched against the sources below. '
                'Venue and organizer pages are ground truth. Local papers surface announcements and last-minute additions. '
                'Aggregators are a fallback — never the sole source for a published time or ticket link.</p>')
    for cat, items in by_cat.items():
        body.append(f'  <h2 class="section">{html.escape(cat_titles.get(cat, cat))}</h2>')
        body.append('  <table class="src"><tr><th>Source</th><th>Reliability</th><th>Notes</th></tr>')
        for s in items:
            rel = html.escape(s["reliability"])
            rel_class = "rel-" + s["reliability"].replace("-", "")
            name = html.escape(s["name"])
            cell = (f'<a href="{html.escape(s["url"], quote=True)}">{name}</a>'
                    if s.get("url") else name)
            body.append('    <tr>'
                        f'<td>{cell}</td>'
                        f'<td><span class="{rel_class}">{rel}</span></td>'
                        f'<td>{html.escape(s["notes"])}<br><span style="color:var(--faint);font-size:.8rem">Timeliness: {html.escape(s.get("timeliness",""))}</span></td>'
                        '</tr>')
        body.append('  </table>')
    body.append(theme.footer("../"))
    return "\n".join(body)


STATUS_LABELS = {
    "verified-official": "Verified — official",
    "verified-secondary": "Verified — secondary",
    "needs-check": "Needs check",
    "time-conflict": "Time conflict",
    "replaced": "Replaced",
}


def build_desk(verification):
    ev = verification.get("events", {})
    extra = '<meta name="robots" content="noindex,nofollow">'
    body = [head_html("Research desk — internal", extra_head=extra, seo_desc="Internal research desk for The Golden Hour editors.", seo_path="desk/")]
    body.append('  <header class="masthead">')
    body.append('    <p class="kicker">Internal — not for publication</p>')
    body.append('    <h1 class="brand" style="font-size:2.2rem">Research desk</h1>')
    body.append('    <hr class="rule-double">')
    body.append('    <p class="tagline">Verification state for every event in the current edition. '
                'Nothing ships with a conflict or an unchecked aggregator link.</p>')
    body.append('  </header>')
    counts = {}
    for v in ev.values():
        counts[v.get("status", "?")] = counts.get(v.get("status", "?"), 0) + 1
    body.append('  <p style="font-size:.85rem;color:var(--muted)">'
                + " · ".join(f'{html.escape(STATUS_LABELS.get(k, k))}: {n}' for k, n in sorted(counts.items()))
                + '</p>')
    body.append('  <table class="desk"><tr><th>Event</th><th>Status</th><th>Checked</th><th>Notes</th></tr>')
    for eid, v in ev.items():
        st = v.get("status", "?")
        body.append('    <tr>'
                    f'<td><span style="color:var(--faint);font-size:.75rem">{html.escape(eid[:8])}</span><br>{html.escape(eid)}</td>'
                    f'<td><span class="pill st-{html.escape(st)}">{html.escape(STATUS_LABELS.get(st, st))}</span>'
                    + (f'<br><span class="flag" style="color:#b3261e;border-color:#b3261e">{html.escape(v["issue"])}</span>' if v.get("issue") else '')
                    + '</td>'
                    f'<td style="font-size:.78rem">{html.escape(", ".join(v.get("sources_checked", [])))}</td>'
                    f'<td style="font-size:.82rem">{html.escape(v.get("notes", ""))}</td>'
                    '</tr>')
    body.append('  </table>')
    body.append('  <p style="font-size:.85rem;color:var(--muted)">Update <code>verification.json</code> and rerun <code>python3 site.py</code> to refresh this page.</p>')
    body.append(theme.footer("../"))
    return "\n".join(body)


def build_picks():
    """Top Picks — skeleton. Picks render from picks/picks.json;
    empty array = honest 'in curation' state, never fabricated entries."""
    js = """
<script>
(function(){
  function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){
    return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
  fetch("picks.json").then(function(r){return r.json();}).then(function(d){
    var picks=d.picks||[];
    var host=document.getElementById("pick-list");
    if(!picks.length){
      host.innerHTML='<p class="lede" style="font-style:italic">The first staples are being scored now — check back soon. Nothing here is published until it earns its place.</p>';
      return;
    }
    host.innerHTML=picks.map(function(p){
      return '<article class="pick"><p class="cat">'+esc(p.category)+'</p>'+
        '<h3>'+esc(p.name)+'<span class="score">'+esc(p.score)+' / 10</span></h3>'+
        '<p class="why">'+esc(p.why)+'</p>'+
        '<p class="src">'+esc(p.sources)+' · Verified '+esc(p.verified)+'</p></article>';
    }).join("");
  }).catch(function(){
    document.getElementById("pick-list").innerHTML='<p class="lede">Could not load picks.</p>';
  });
})();
</script>"""
    body = [head_html("Top Picks — The Golden Hour", seo_desc="Local staples and concierge-tested picks around Aspen, scored and verified.", seo_path="picks/")]
    body.append(theme.masthead("../", "picks"))
    body.append('  <div class="pagetitle"><p class="kicker">The Concierge</p>')
    body.append('  <h2>Top Picks</h2></div>')
    body.append('  <p class="lede">The places Aspen locals actually go — restaurants, bars, trails, shops, services. '
                'Each one is scored, sourced, and verified before it appears here. No ads, no pay-to-play, no filler.</p>')
    body.append('  <h2 class="section">How a pick earns its place</h2>')
    body.append('  <ol class="rubric">')
    for title, desc in [
        ("Public reputation", "Google and Yelp ratings weighted by review volume — a 4.9 from 40 reviews does not outrank a 4.7 from 4,000."),
        ("Staying power", "Years in business. A decade of winters survived counts more than a season of hype."),
        ("Local corroboration", "Concierge desks, bartenders, and longtime locals are asked what they actually recommend — off the record."),
        ("On-the-ground check", "Hours, prices, and the experience itself are verified in person before publication."),
        ("The dealbreakers", "Tourist traps, pay-to-play placements, and anything that can't be verified are cut — loudly if necessary."),
    ]:
        body.append(f'    <li><b>{title}</b><span>{desc}</span></li>')
    body.append('  </ol>')
    body.append('  <h2 class="section">The picks</h2>')
    body.append('  <div id="pick-list"><p class="lede">Loading…</p></div>')
    body.append(theme.footer("../"))
    body.append(js)
    return "\n".join(body)


def build_editions(weeks):
    """Archive index on the shared theme shell — was an unstyled orphan."""
    body = [head_html("Archive — The Golden Hour", seo_desc="Past weekly editions of The Golden Hour field guide.", seo_path="editions/")]
    body.append(theme.masthead("../", "archive"))
    body.append('  <h2 class="section">Past editions</h2>')
    body.append('  <p class="lede">Every weekly edition, frozen as published — '
                'a snapshot of what was on, as it was curated.</p>')
    if weeks:
        body.append('  <ul class="archive">')
        for w in weeks:
            body.append(f'    <li><a href="{html.escape(w)}/">{html.escape(edition_label(w))}</a>'
                        f'<span class="when">Published for arrivals {html.escape(w)}</span></li>')
        body.append('  </ul>')
    else:
        body.append('  <p class="lede" style="font-style:italic">No archived editions yet — check back soon.</p>')
    body.append(theme.footer("../"))
    body.append("</div>\n</body>\n</html>")
    return "\n".join(body)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", path)


def main():
    reg = load_json("sources.json")
    ver = load_json("verification.json")
    weeks = edition_weeks()
    write(os.path.join(HERE, "index.html"), build_homepage(weeks))
    write(os.path.join(HERE, "sources", "index.html"),
          build_sources_page(reg.get("sources", [])))
    write(os.path.join(HERE, "picks", "index.html"), build_picks())
    write(os.path.join(HERE, "editions", "index.html"), build_editions(weeks))
    stub = os.path.join(HERE, "picks", "picks.json")
    if not os.path.exists(stub):
        with open(stub, "w", encoding="utf-8") as f:
            json.dump({
                "_note": "Top Picks data. Append pick objects; the page renders them. Empty = honest curation state.",
                "_schema": {"name": "str", "category": "Eat|Drink|Outdoors|Arts & Culture|Services",
                            "score": "number 0-10", "why": "one line", "sources": "e.g. Google 4.8 (2.1k) · Yelp 4.5",
                            "verified": "YYYY-MM-DD"},
                "rubric_version": "v1",
                "picks": []
            }, f, ensure_ascii=False, indent=2)
        print("wrote", stub)
    write(os.path.join(HERE, "desk", "index.html"), build_desk(ver))


if __name__ == "__main__":
    main()
