"""theme.py — the Golden Hour's single source of design truth.

Every public page (homepage, upcoming, calendar, map, picks, sources) draws
its palette, type, nav, masthead, and footer from here. Change it once,
rebuild, and the whole site moves together.

Doctrine: restraint. One serif, one sans, one paper, two brand colors
(navy = identity/interactive, gold = today/urgent). Category and time are
carried by typography and labels, never by a rainbow.
"""

import html as _html

SITE_URL = "https://ron-delhaye-studios.github.io/this-week-in-aspen"


def seo_head(title, description, path=""):
    """SEO head block: meta description, canonical, Open Graph, Twitter card.

    Additive only — emits head tags, never touches visible markup or CSS.
    path is the page path relative to the site root, e.g. "upcoming/".
    """
    url = SITE_URL + "/" + path.lstrip("/")
    t = _html.escape(title, quote=True)
    d = _html.escape(description, quote=True)
    return (
        f'<meta name="description" content="{d}">\n'
        f'<link rel="canonical" href="{url}">\n'
        f'<meta property="og:title" content="{t}">\n'
        f'<meta property="og:description" content="{d}">\n'
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:url" content="{url}">\n'
        '<meta property="og:site_name" content="The Golden Hour">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{t}">\n'
        f'<meta name="twitter:description" content="{d}">\n'
        '<meta name="theme-color" content="#103D60">\n'
    )

def analytics_tags(root=""):
    """Analytics skeleton snippet. Additive head tags only — no visible markup.

    root is the relative prefix back to the site root ("" / "../" / "../../"),
    since the site is served from a subdirectory and root-absolute asset paths
    would break. Emits the config first (holds the anon key), then the beacon.
    Until a real anon key is pasted into analytics-config.js, the beacon
    silently does nothing.
    """
    return (
        f'<script src="{root}assets/js/analytics-config.js"></script>\n'
        f'<script defer src="{root}assets/js/analytics.js"></script>\n'
    )


FONT_LINKS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500;1,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">"""

SERIF = '"Cormorant Garamond",Didot,"Bodoni MT",Georgia,"Times New Roman",serif'
SANS = 'Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif'

# Canonical palette
PAPER = "#fdfcf8"
INK = "#1d1a16"
MUTED = "#6e675c"
FAINT = "#a39a8b"
HAIR = "#e4ded1"
ACCENT = "#103d60"   # navy — identity, links, interactive
GOLD = "#b98a1d"     # gold — today / urgent, used sparingly

CSS_VARS = (
    ":root{--paper:%s;--ink:%s;--muted:%s;--faint:%s;--hair:%s;"
    "--accent:%s;--gold:%s;--serif:%s;--sans:%s}"
    % (PAPER, INK, MUTED, FAINT, HAIR, ACCENT, GOLD, SERIF, SANS)
)

# (href, label, key) — same items, same order, on every page.
NAV_ITEMS = [
    ("index.html", "Latest", "latest"),
    ("upcoming/", "Upcoming", "upcoming"),
    ("calendar/", "Calendar", "calendar"),
    ("map/", "Map", "map"),
    ("picks/", "Top Picks", "picks"),
    ("editions/", "Archive", "archive"),
    ("sources/", "How we verify", "verify"),
]


def nav_html(root, active=None):
    items = []
    for href, label, key in NAV_ITEMS:
        mark = ' class="active" aria-current="page"' if key == active else ""
        items.append(f'    <a href="{root}{href}"{mark}>{label}</a>')
    return (
        '  <nav class="site-nav" aria-label="Sections">\n'
        + "\n".join(items)
        + "\n  </nav>\n"
    )


def masthead(root, active=None, tagline=None):
    tag = tagline or (
        "A weekly field guide to what's on — music, art, and high-country "
        "happenings, verified before publication."
    )
    return (
        '  <header class="masthead">\n'
        '    <p class="kicker">From Aspen and Beyond</p>\n'
        '    <h1 class="brand">The Golden Hour</h1>\n'
        '    <hr class="rule-double">\n'
        f'    <p class="tagline">{tag}</p>\n'
        + nav_html(root, active)
        + "  </header>\n"
    )


def footer(root):
    links = " · ".join(
        f'<a href="{root}{href}">{label}</a>' for href, label, _ in NAV_ITEMS
    )
    return (
        '  <footer class="colophon">\n'
        "    <p>Every event verified against official sources before "
        "publication. Details may change — please confirm with the venue.</p>\n"
        f'    <p class="foot-links">{links}</p>\n'
        "    <p>© 2026 The Golden Hour · An Ad Astra Media publication.</p>\n"

        "  </footer>\n"
    )


# Shared core CSS: page frame, masthead, nav, footer, buttons, sections.
# Page-specific CSS extends this; nothing here is overridden elsewhere.
CORE_CSS = (
    CSS_VARS
    + """
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
       font-size:16px;line-height:1.65;-webkit-font-smoothing:antialiased}
  .page{max-width:46rem;margin:0 auto;padding:2.5rem 1.25rem 3rem}
  .masthead{text-align:center;margin-bottom:2rem}
  .kicker{font-size:.72rem;letter-spacing:.22em;text-transform:uppercase;color:var(--accent);margin:0 0 .8rem}
  .brand{font-family:var(--serif);font-weight:600;font-size:clamp(2.2rem,7vw,3.4rem);margin:0 0 .6rem;letter-spacing:.02em}
  .rule-double{border:0;border-top:1px solid var(--accent);border-bottom:1px solid var(--accent);height:5px;padding:1px 0;margin:1.2rem 0}
  .tagline{color:var(--muted);font-style:italic;margin:0;max-width:34rem;margin-left:auto;margin-right:auto}
  nav.site-nav{display:flex;gap:1.4rem;justify-content:center;flex-wrap:wrap;margin:1.6rem 0 0;
               font-size:.85rem;letter-spacing:.08em;text-transform:uppercase}
  nav.site-nav a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--accent);padding-bottom:2px}
  nav.site-nav a.active{font-weight:700;border-bottom:3px solid var(--accent)}
  h2.section{font-family:var(--serif);font-weight:600;font-size:1.7rem;margin:2.8rem 0 .8rem}
  .lede{color:var(--muted);font-size:1.02rem;max-width:36rem}
  .btn{display:inline-block;border:1px solid var(--accent);color:var(--ink);padding:.6rem 1.3rem;
       text-decoration:none;font-size:.85rem;letter-spacing:.1em;text-transform:uppercase;background:transparent}
  .btn:hover{background:var(--accent);color:#fff}
  .colophon{margin-top:3.5rem;padding-top:1.5rem;border-top:1px solid var(--hair);
            font-size:.8rem;color:var(--muted);text-align:center}
  .colophon .foot-links a{color:var(--ink);text-decoration-color:var(--accent);text-underline-offset:2px}
  .explore{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:.9rem;margin:1.4rem 0}
  .explore a{display:block;border:1px solid var(--hair);background:#fff;padding:1.1rem 1rem;text-decoration:none;color:var(--ink)}
  .explore a:hover{border-color:var(--accent)}
  .explore .ek{font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin:0 0 .3rem}
  .explore h3{font-family:var(--serif);font-size:1.2rem;margin:0 0 .25rem;font-weight:600}
  .explore p{font-size:.85rem;color:var(--muted);margin:0}
"""
)
