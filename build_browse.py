"""Build the browse layer for The Golden Hour: Upcoming + Calendar pages.

- upcoming/: all matching rows grouped by week, each with a copy button
- calendar/: Sep/Oct/Nov/Dec 2026 month grids with event dots + per-day listings
--status controls which rows render (draft for preview, approved for publish).
"""
import argparse
import calendar as calmod
import datetime as dt
import html
import json
import os
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import live_layer
import theme  # noqa: E402 — shared live-layer contract (window + anchors)

DENVER = ZoneInfo("America/Denver")


def to_denver(iso):
    d = dt.datetime.fromisoformat(iso)
    if d.tzinfo is None:
        d = d.replace(tzinfo=DENVER)
    return d.astimezone(DENVER)
ALLOWED = ("ypfhcqeispdunewubxjm.supabase.co",)
CRED = "custom.supabase"
API = "https://ypfhcqeispdunewubxjm.supabase.co/rest/v1"
TABLE = "aspen_events"
SELECT_COLS = ("id,title,venue,starts_at,category,price_info,"
               "age_policy,url,blurb,fit_note,status")

CSS = theme.CORE_CSS + """
  h2.when{font-family:var(--serif);font-size:1.5rem;margin:2.6rem 0 1rem}
  .ev{border:1px solid var(--hair);background:#fff;padding:1.2rem 1.2rem 1rem;margin:0 0 1rem;position:relative}
  .ev .cat{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 .3rem}
  .ev h3{font-family:var(--serif);font-size:1.25rem;margin:0 0 .25rem}
  .ev-when{display:flex;align-items:baseline;flex-wrap:wrap;gap:.2rem .8rem;margin:0 0 .35rem;padding-bottom:.4rem;border-bottom:2px solid var(--accent)}
  .ev-date{font-family:var(--serif);font-weight:700;font-size:1.15rem;color:var(--accent)}
  .ev-time{font-size:.78rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase}
  .ev-rel{margin-left:auto;font-size:.68rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
  .ev .meta{font-size:.88rem;color:var(--muted);margin:.15rem 0}
  .ev .blurb{margin:.6rem 0;font-size:.95rem}
  .ev .fit{font-size:.85rem;color:var(--muted);font-style:italic;margin:.3rem 0 .8rem}
  .copybtn{border:1px solid var(--accent);background:#fff;color:var(--ink);padding:.38rem .75rem;font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;cursor:pointer;flex:none}
  .copybtn.done{background:var(--accent);color:#fff}
  .cardfoot{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-top:1.3rem}
  .elink{font-size:.86rem;color:var(--accent);text-decoration:none;font-weight:600}
  .elink:hover{text-decoration:underline}
  .ev .ph{display:block;width:calc(100% + 2.4rem);max-width:none;margin:-1.2rem -1.2rem .9rem;aspect-ratio:16/9;object-fit:cover;background:#efe9dd}
  .month{margin:2.5rem 0}
  .month h2{font-family:var(--serif);font-size:1.6rem;margin:0 0 .8rem}
  table.cal{width:100%;border-collapse:collapse;font-size:.85rem}
  table.cal th{font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:.4rem;font-weight:600}
  table.cal td{border:1px solid var(--hair);height:3.2rem;width:14.28%;vertical-align:top;padding:.3rem;text-align:left}
  table.cal td .d{font-weight:600}
  table.cal td.has{background:#fff;cursor:default}
  table.cal td .dots{color:var(--accent);letter-spacing:2px;font-size:.8rem}
  table.cal td.dim{color:#c9c2b4;background:transparent}
  .daylist h3{font-family:var(--serif);font-size:1.15rem;margin:1.8rem 0 .6rem}
  .empty{color:var(--muted);font-style:italic}
"""

JS = """
<script>
document.addEventListener('click', function(e){
  var b = e.target.closest('.copybtn'); if(!b) return;
  var txt = b.getAttribute('data-copy');
  function done(){ b.textContent = 'Copied ✓'; b.classList.add('done');
    setTimeout(function(){ b.textContent = 'Copy details'; b.classList.remove('done'); }, 1600); }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(txt).then(done, function(){ fallback(); });
  } else { fallback(); }
  function fallback(){
    var ta = document.createElement('textarea'); ta.value = txt;
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch(_){}
    document.body.removeChild(ta); done();
  }
});
/* Relative day labels ("Today", "Tomorrow", "In N days") — computed live so
   static pages never go stale. */
(function(){
  var now = new Date();
  var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  document.querySelectorAll('[data-starts]').forEach(function(el){
    var d = new Date(el.getAttribute('data-starts'));
    if (isNaN(d.getTime())) return;
    var dd = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    var diff = Math.round((dd - today) / 864e5);
    var label = diff < 0 ? null
      : diff === 0 ? 'Today'
      : diff === 1 ? 'Tomorrow'
      : 'In ' + diff + ' days';
    if (label) el.textContent = label;
  });
})();
</script>
"""

NAV_LINKS = theme.NAV_ITEMS
nav_html = theme.nav_html
foot_html = theme.footer


def supa_get(params):
    url = API + "/" + TABLE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED)
    return read_json_response(urllib.request.urlopen(req, timeout=30))


def fetch(statuses):
    today = dt.date.today().isoformat()
    rows = supa_get({
        "status": f"in.({','.join(statuses)})",
        "starts_at": f"gte.{today}T00:00:00-07:00",
        "select": SELECT_COLS,
        "order": "starts_at.asc",
        "limit": "200",
    })
    return rows if isinstance(rows, list) else []


def fmt_dt(starts_at):
    d = to_denver(starts_at)
    day = d.strftime("%a %b %d").replace(" 0", " ")
    t = d.strftime("%-I:%M %p").replace(":00 ", " ")
    return day, t


def clean_str(v):
    """Visitor-facing text sanitizer: literal 'None'/'null' strings from the
    data layer render as missing, never as the word None."""
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() in ("none", "null", "nan", "n/a", "-"):
        return None
    return s


def sanitize_row(r):
    """Batch 1 trust repair at the render layer: no raw nulls, no internal
    brand names, visitor-safe copy. Runs on every row before any builder."""
    for k in ("title", "venue", "price_info", "age_policy", "url",
              "blurb", "fit_note", "category"):
        v = r.get(k)
        if isinstance(v, str):
            v = clean_str(v)
            if v:
                v = (v.replace("AURELIAN Desk", "Concierge Desk")
                      .replace("AURELIAN", "Concierge"))
            r[k] = v
    return r


def fit_label(note):
    """'For: For the…' -> 'For the…'. Notes that already open with 'For'
    render as-is; others get the 'For:' prefix."""
    if note.lower().startswith("for "):
        return note
    return f"For: {note}"


def copy_text(r):
    day, t = fmt_dt(r["starts_at"])
    lines = [f"{r['title']} — {r['venue']}", f"{day} · {t}"]
    meta = " · ".join(x for x in (r.get("price_info"), r.get("age_policy")) if x)
    if meta:
        lines.append(meta)
    if r.get("url"):
        lines.append(r["url"])
    if r.get("blurb"):
        lines.append(r["blurb"])
    return "\n".join(lines)


def event_card(r, root):
    day, t = fmt_dt(r["starts_at"])
    day_label = day.replace(" ", ", ", 1)
    cat = html.escape(r.get("category") or "event")
    meta = " · ".join(x for x in (r.get("price_info"), r.get("age_policy")) if x)
    img = (f'<img class="ph" src="{root}assets/browse/{html.escape(r["image"])}" '
           f'alt="{html.escape(r["title"])}" loading="lazy">' if r.get("image") else "")
    elink = (f'<a class="elink" href="{html.escape(r["url"], quote=True)}" '
             f'target="_blank" rel="noopener">Official event page ↗</a>' if r.get("url") else "")
    maplink = (f'<a class="elink" href="{live_layer.map_url(r["id"], root)}">View on map ↗</a>'
               if r.get("id") else "")
    return f"""  <div class="ev" id="{live_layer.anchor(r['id'])}">
    {img}
    <p class="cat">{cat}</p>
    <h3>{html.escape(r['title'])}</h3>
    <div class="ev-when">
      <span class="ev-date">{html.escape(day_label)}</span>
      <span class="ev-time">{html.escape(t)}</span>
      <span class="ev-rel" data-starts="{html.escape(r['starts_at'], quote=True)}"></span>
    </div>
    <p class="meta">{html.escape(r['venue'])}</p>
    {f'<p class="meta">{html.escape(meta)}</p>' if meta else ''}
    <p class="blurb">{html.escape(r.get('blurb') or '')}</p>
    {f'<p class="fit">{html.escape(fit_label(r["fit_note"]))}</p>' if r.get('fit_note') else ''}
    <div class="cardfoot">
      {elink}
      {maplink}
      <button class="copybtn" data-copy="{html.escape(copy_text(r), quote=True)}">Copy details</button>
    </div>
  </div>"""


def week_start(d):
    # Saturday-start weeks, matching edition_week convention
    return d - dt.timedelta(days=(d.weekday() + 2) % 7)


def build_upcoming(rows, root):
    body = [f"""<div class="page">
  <header class="masthead">
    <p class="kicker">From Aspen and Beyond</p>
    <h1 class="brand">The Golden Hour</h1>
    <hr class="rule-double">
  </header>
  <h2 class="when" style="margin-top:0">Upcoming</h2>
  <p class="empty">{live_layer.window_label()}</p>"""]
    if not rows:
        body.append('  <p class="empty">New picks are being curated — check back soon.</p>')
    else:
        by_week = {}
        for r in rows:
            d = to_denver(r["starts_at"]).date()
            by_week.setdefault(week_start(d), []).append(r)
        for ws in sorted(by_week):
            we = ws + dt.timedelta(days=6)
            label = (f"{ws.strftime('%B')} {ws.day} – {we.strftime('%B')} {we.day}, {we.year}"
                     .replace(" 0", " "))
            body.append(f'  <h2 class="when">{html.escape(label)}</h2>')
            body.extend(event_card(r, root) for r in by_week[ws])
    body.append("</div>")
    return wrap("Upcoming — The Golden Hour", "\n".join(body), root, active="upcoming")


GCAL_CSS = """
<style>
.gcal-toolbar{display:flex;align-items:center;gap:.6rem;margin:1rem 0;flex-wrap:wrap}
.gcal-title{font-size:1.5rem;margin:0 .4rem 0 0;font-family:var(--serif);font-weight:600;color:var(--accent)}
.gcal-btn{border:1px solid var(--hair);background:#fff;border-radius:999px;padding:.45rem .95rem;
  font-size:.9rem;cursor:pointer;color:var(--accent);font-family:var(--sans)}
.gcal-btn:hover:not(:disabled){background:#f0f4f8}
.gcal-btn:disabled{opacity:.35;cursor:default}
.gcal-btn.nav{width:2.4rem;padding:.45rem 0;text-align:center;font-size:1.05rem;line-height:1}
.gcal-dow{display:grid;grid-template-columns:repeat(7,1fr);margin-top:.4rem}
.gcal-dow span{text-align:center;font-size:.72rem;letter-spacing:.08em;color:#8a94a6;padding:.4rem 0;text-transform:uppercase}
.gcal-grid{display:grid;grid-template-columns:repeat(7,1fr);border-top:1px solid #e2e6ec;border-left:1px solid #e2e6ec}
.gcal-day{min-height:104px;border-right:1px solid #e2e6ec;border-bottom:1px solid #e2e6ec;
  padding:4px 5px;overflow:hidden;background:#fff}
.gcal-day.dim{background:#fafbfc;color:#9aa3b2}
.gcal-daynum{font-size:.8rem;font-weight:600;width:1.7rem;height:1.7rem;display:flex;
  align-items:center;justify-content:center;border-radius:50%;margin-bottom:2px}
.gcal-daynum.today{background:var(--accent);color:#fff}
.gcal-chip{display:block;width:100%;text-align:left;border:0;border-radius:4px;
  font-size:.74rem;line-height:1.35;padding:.18rem .45rem;margin:2px 0;cursor:pointer;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gcal-chip .ct{font-weight:700;margin-right:.25rem}
.gcal-chip.istoday{box-shadow:inset 3px 0 0 var(--gold)}
.gcal-more{background:none;border:0;color:#5f6b7a;font-size:.74rem;cursor:pointer;padding:.15rem .45rem}
.gcal-more:hover{text-decoration:underline}
.gcal-overlay{position:fixed;inset:0;background:rgba(16,61,96,.45);display:flex;
  align-items:center;justify-content:center;z-index:60;padding:1rem}
.gcal-modal-card{background:#fff;border-radius:12px;max-width:430px;width:100%;max-height:88vh;
  overflow:auto;position:relative;box-shadow:0 12px 40px rgba(0,0,0,.25)}
.gcal-x{position:absolute;top:.4rem;right:.7rem;border:0;background:none;font-size:1.6rem;
  cursor:pointer;color:#5f6b7a;z-index:2}
.gcal-photo{width:100%;height:190px;object-fit:cover;display:block;border-radius:12px 12px 0 0}
.gcal-modal-body{padding:1.1rem 1.2rem 1.3rem}
.gcal-modal-body h3{margin:.4rem 0 .5rem;font-size:1.35rem;font-family:var(--serif);font-weight:600;color:var(--accent)}
.gcal-cat{display:inline-block;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;
  padding:.2rem .6rem;border-radius:999px;margin:0}
.gcal-when{margin:.2rem 0;font-size:.95rem}
.gcal-rel{color:#0b8043;font-weight:700}
.gcal-venue{font-weight:600;margin:.2rem 0}
.gcal-meta{color:#5f6b7a;font-size:.88rem;margin:.2rem 0}
.gcal-blurb{margin:.6rem 0;line-height:1.5}
.gcal-fit{font-style:italic;color:#5f6b7a;font-size:.9rem}
.gcal-links{display:flex;flex-wrap:wrap;gap:.4rem 1rem;margin-top:.8rem}
.gcal-links a{color:var(--accent);font-weight:600;font-size:.9rem}
@media (max-width:640px){
  .gcal-day{min-height:76px;padding:3px}
  .gcal-chip{font-size:.66rem}
  .gcal-title{font-size:1.2rem}
}
</style>
"""


def build_calendar(rows, root):
    # Google-style month view: shell page + events.json rendered client-side.
    outdir = os.path.join(HERE, "calendar")
    os.makedirs(outdir, exist_ok=True)
    data = []
    for r in rows:
        data.append({
            "id": r.get("id"),
            "title": r.get("title"),
            "starts_at": r.get("starts_at"),
            "venue": r.get("venue"),
            "category": r.get("category"),
            "image": ("assets/browse/" + r["image"]) if r.get("image") else None,
            "url": r.get("url"),
            "blurb": r.get("blurb"),
            "price_info": r.get("price_info"),
            "age_policy": r.get("age_policy"),
            "fit_note": r.get("fit_note"),
        })
    with open(os.path.join(outdir, "events.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    body = f"""<div class="page">
  <header class="masthead">
    <p class="kicker">From Aspen and Beyond</p>
    <h1 class="brand">The Golden Hour</h1>
    <hr class="rule-double">
  </header>
  <h2 class="when" style="margin-top:0">Calendar</h2>
{GCAL_CSS}
  <div class="gcal-toolbar">
    <button class="gcal-btn" id="gcal-today">Today</button>
    <button class="gcal-btn nav" id="gcal-prev" aria-label="Previous month">&#8249;</button>
    <button class="gcal-btn nav" id="gcal-next" aria-label="Next month">&#8250;</button>
    <h3 class="gcal-title" id="gcal-title"></h3>
  </div>
  <div class="gcal-dow"><span>Sun</span><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span></div>
  <div class="gcal-grid" id="gcal-grid"><p class="empty">Loading events…</p></div>
  <p class="empty" style="margin-top:1rem">Tap an event for details, photos, and links.</p>
</div>
<script src="calendar.js"></script>"""
    return wrap("Calendar — The Golden Hour", body, root, active="calendar")


SEO_FOR_PAGE = {
    "upcoming": ("Every verified upcoming event in Aspen and the high country, soonest first.", "upcoming/"),
    "calendar": ("The month at a glance \u2014 every verified Aspen-area event on a Google-style calendar.", "calendar/"),
}


def wrap(title, inner, root, active=None):
    seo_desc, seo_path = SEO_FOR_PAGE.get(active, ("", ""))
    seo = theme.seo_head(title, seo_desc, seo_path) if seo_desc else ""
    analytics = theme.analytics_tags(root)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
{seo}{analytics}{theme.FONT_LINKS}
<style>{CSS}</style>
</head>
<body>
{inner}
{foot_html(root)}
{JS}
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", default="approved")
    args = ap.parse_args()
    statuses = [s.strip() for s in args.status.split(",")]
    rows = fetch(statuses)
    # Batch 1 trust repair: sanitize every row at the render layer before
    # any builder sees it (null-string cleanup, brand voice, visitor copy).
    rows = [sanitize_row(r) for r in rows]
    # Rolling live window: the live layer (Upcoming/Calendar/Map) shows only
    # events inside live_layer's window. Policy lives in live_layer.py.
    rows = [r for r in rows if live_layer.in_window(r.get("starts_at"))]
    print(f"live window: {len(rows)} events in range", file=sys.stderr)
    # attach browse photos: assets/browse/manifest.json maps event id -> filename
    try:
        with open(os.path.join(HERE, "assets", "browse", "manifest.json"), encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        manifest = {}
    for r in rows:
        fn = manifest.get(r["id"])
        if fn:
            r["image"] = fn
    # inject nav after masthead header: rebuild pages with nav included
    for name, builder, active in (("upcoming", build_upcoming, "upcoming"), ("calendar", build_calendar, "calendar")):
        outdir = os.path.join(HERE, name)
        os.makedirs(outdir, exist_ok=True)
        page = builder(rows, "../")
        # insert nav before closing of masthead header
        page = page.replace("</header>", nav_html("../", active) + "\n</header>", 1)
        with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        print("wrote", os.path.join(outdir, "index.html"), f"({len(rows)} rows)")


if __name__ == "__main__":
    main()
