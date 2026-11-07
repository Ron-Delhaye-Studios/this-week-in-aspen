#!/usr/bin/env python3
"""Apply Brand Standards v1.0 to every static page without replacing editorial copy.

Run after any legacy content generator. data/events.json is the single event input;
calendar/map JSON files are generated compatibility exports, never edited inputs.
"""
import argparse
from datetime import datetime
import html
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from week_scope import coming_up, this_week, week_bounds, available_filters, is_free, DESCRIPTION as WEEK_DESCRIPTION

ROOT = Path(__file__).resolve().parent
TZ = ZoneInfo('America/Denver')
URL = 'https://thegoldenhour.guide/'
HALLOWEEN = {'aspens-darkside-ghost-tour', 'spooktacular-creepy-crafts', 'ute-cemetery-tour',
             'murder-at-the-rattlesnake-saloon', 'ghosts-of-aspens-past', 'coco-and-breezy',
             'halloween-bash-ft-chaparelle', 'shrek-themed-halloween-party'}
NAV = [('index.html','Latest'), ('events/','Events'), ('upcoming/','This Week'),
       ('calendar/','Calendar'), ('map/','Map'), ('picks/','Top Picks'),
       ('activities/','Activities'), ('editions/','Archive'), ('sources/','How we verify')]
# Footer-only guide links: the footer is the canonical guide-discovery
# surface. These render ONLY in the footer (footer_navigation), spliced in
# immediately after Top Picks; they never join NAV / the header nav.
FOOTER_EXTRA = [('happy-hour/', 'Happy Hour', None),
                ('off-season/', 'Off Season', 'off-season')]

# Seasonal footer links (WO#12): season key -> data file whose "windows"
# config stamps a data-windows attribute on the footer anchor;
# assets/gh-theme.js hides seasonal anchors outside every window.
SEASON_FILES = {'off-season': 'off-season/off-season.json'}


def season_windows_attr(season):
    rel = SEASON_FILES.get(season or '')
    if not rel:
        return ''
    try:
        cfg = json.loads((ROOT / rel).read_text(encoding='utf-8'))
        wins = ','.join(f"{w['start']}..{w['end']}" for w in cfg.get('windows', []))
        return f' data-windows="{wins}"' if wins else ''
    except Exception:
        return ''



# WO#16 — homepage concept completion (concept v3.1, below-hero sections).
# The masthead shipped in WO#15; these are the concept's remaining homepage
# sections: This-week list, Explore photo mosaic, Coming-up band, Verify
# steps, giant footer wordmark. All copy below is the concept's own words;
# event rows and band items are generated from data/events.json at build
# time. Imagery is licensed stock only (see the WO#16 MANIFEST); Ron's
# photography never appears on this site.
EXPLORE_TILES = [
    ('upcoming/', 'assets/img/tile-upcoming-live-concert.jpg', 'Browse', 'This Week',
     'Verified events this week, soonest first.',
     'A live band on stage under stage lights, crowd silhouettes in front', 'gh-tile-big'),
    ('map/', 'assets/img/tile-map-aspen-downtown.jpg', 'Wander', 'Map',
     'Every event, placed across Colorado.',
     "Downtown Aspen's historic blocks with the ski slopes behind", 'gh-tile-wide'),
    ('calendar/', 'assets/img/tile-calendar-autumn-gold.jpg', 'Plan', 'Calendar',
     'The month at a glance.',
     'Red Maroon-group peaks above a sea of golden aspens', ''),
    ('picks/', 'assets/img/tile-picks-cafe.jpg', 'The Concierge', 'Top Picks',
     'Local staples, scored and verified.',
     'A quiet café table set by a window in morning light', ''),
    ('activities/', 'assets/img/tile-activities-maroon-bells.jpg', 'Do', 'Activities',
     'Guides to playing here — the high country, on foot, on water, and soon, on snow.',
     'Maroon Bells over Maroon Lake in fall color, reflected in still water', 'gh-tile-full'),
]
LEAD_IMAGE = ('assets/img/lead-ute-cemetery.jpg',
              'The brick entrance sign of Ute Cemetery, Aspen, among bare autumn aspens')
VERIFY_STEPS = [
    ('Checked at the source',
     "Every event is checked against the venue's own page or a trusted local source before it reaches you."),
    ('Aggregators never make the cut',
     "A listing scraped from somewhere else isn't proof. Alone, it never gets published."),
    ('When sources disagree, we hold',
     'If two sources give different times, the pick waits until one is authoritative.'),
]
CAT_LABELS = {'music': 'Music', 'arts': 'Art', 'outdoors': 'Outdoors', 'family': 'Family',
              'comedy': 'Comedy', 'dining': 'Dining', 'dance': 'Dance', 'speakers': 'Speakers'}

def _wo19_summary(event, limit=140):
    """A complete short source sentence, or an existing category/venue fact line."""
    text=' '.join((event.get('blurb') or '').split())
    first=re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])',text,maxsplit=1)[0]
    if first and len(first)<=limit and not first.endswith(('…','...')):
        return first
    return CAT_LABELS.get(event['category'],event['category'].title())+' · '+event['venue'].split(',')[0]


def _wo16_edition(doc):
    """Edition (range, title, standfirst, href) for the This-week lead.

    First build reads the legacy .hero block; rebuilds read the data
    attributes the WO#16 section stamps on itself, so decorate() stays
    idempotent over its own output.
    """
    hero = doc.select_one('.hero')
    if hero is not None:
        rng = hero.select_one('.ed-range')
        title = hero.find('h3')
        paras = [p for p in hero.find_all('p') if 'ed-range' not in (p.get('class') or [])]
        btn = hero.select_one('a.btn')
        return {'range': rng.get_text(' ', strip=True) if rng else '',
                'title': title.get_text(' ', strip=True) if title else '',
                'standfirst': paras[0].get_text(' ', strip=True) if paras else '',
                'href': btn.get('href') if btn else 'events/'}
    sec = doc.select_one('.gh-week')
    if sec is not None:
        return {'range': sec.get('data-ed-range', ''), 'title': sec.get('data-ed-title', ''),
                'standfirst': sec.get('data-ed-standfirst', ''), 'href': sec.get('data-ed-href', 'events/'), 'live': sec.get('data-ed-live')=='true'}
    return {'range': '', 'title': '', 'standfirst': '', 'href': 'events/'}


def _wo16_window(ed, day):
    """Edition window [start, end] parsed from the .ed-range text.

    Falls back to the build week (day .. day+6) when unparseable.
    """
    m = re.search(r'(?:\w+,\s*)?(\w+)\s+(\d{1,2})\s*[–—-]\s*(?:\w+,\s*)?(\w+)\s+(\d{1,2}),\s*(\d{4})', ed.get('range', ''))
    if m:
        try:
            start = datetime.strptime(f'{m.group(1)} {m.group(2)} {m.group(5)}', '%B %d %Y').date()
            end = datetime.strptime(f'{m.group(3)} {m.group(4)} {m.group(5)}', '%B %d %Y').date()
            return start, end
        except ValueError:
            pass
    return day, day.fromordinal(day.toordinal() + 6)

def homepage_sections(rows, day, ed, prefix):
    """Current edition panel, approved Explore mosaic and verification steps.

    This Week stays strict; an empty homepage week becomes an explicitly
    labeled next-five calendar view without changing the edition window.
    """
    esc = html.escape
    start, end = week_bounds(day)
    current, horizon = coming_up(rows, day)
    heading = 'Next on the <em>Calendar</em>' if horizon else 'Coming <em>up</em>'
    lead = current[0] if current else None
    live = True
    ed = {'range': f'{start:%A, %B %d} – {end:%A, %B %d, %Y}',
          'title': lead['title'] if lead else 'This Week',
          'standfirst': _wo19_summary(lead) if lead else 'Explore the valley with the guide.',
          'href': prefix+'events/'+lead['slug']+'/' if lead else prefix+'calendar/'}
    lead_image = (lead['image'],lead['title']) if lead and lead.get('image') else None
    lead_class = ' gh-event-lead'
    in_week, seen = [], set()
    for event in current:
        if event['slug'] not in seen:
            seen.add(event['slug'])
            in_week.append(event)
        if len(in_week) == 5:
            break
    filters = ''.join(f'<button type="button" data-filter="{key}" aria-pressed="{str(key == "all").lower()}"' + (' class="on"' if key == 'all' else '') + f'>{label}</button>' for key,label in available_filters(current))
    row_html = ''
    for e in in_week:
        d = datetime.fromisoformat(e['starts_at']).astimezone(TZ)
        row_html += (
            f'<a class="gh-row" data-starts="{esc(e["starts_at"])}" data-free="{int(is_free(e))}" data-cat="{esc(e["category"])}" href="{prefix}events/{esc(e["slug"])}/">'
            f'<span class="gh-row-date"><span class="dow">{d:%a}</span>'
            f'<span class="num">{d:%d}</span><span class="mon">{d:%b}</span></span>'
            f'<span class="gh-row-info"><h4>{esc(e["title"])}</h4>'
            f'<p>{esc(_wo19_summary(e, 110))}</p></span>'
            f'<span class="gh-row-tag">{esc(CAT_LABELS.get(e["category"], e["category"].title()))}</span>'
            '<span class="gh-row-go" aria-hidden="true">→</span></a>')
    if not row_html:
        row_html='<p class="gh-list-empty">Explore <a href="'+prefix+'picks/">Top Picks</a> or plan with <a href="'+prefix+'activities/">Activities</a>.</p>'
    display_range = 'Next five verified happenings' if horizon and current else 'Explore the valley' if horizon else ed['range']
    short_range = 'Next on the Calendar' if horizon else f'{start:%a %b %d} — {end:%a %b %d}'
    week = (
        f'<section class="gh-week" aria-label="{'Next on the Calendar' if horizon else 'Coming up'}" data-ed-range="{esc(ed["range"], quote=True)}" '
        f'data-ed-title="{esc(ed["title"], quote=True)}" data-ed-standfirst="{esc(ed["standfirst"], quote=True)}" '
        f'data-ed-href="{esc(ed["href"], quote=True)}" data-ed-live="{str(bool(live)).lower()}" data-window-end="{end.isoformat()}" data-horizon="{str(horizon).lower()}">'
        f'<div class="gh-sec-head"><h2>{heading}</h2>'
        f'<div class="gh-week-tools"><span class="gh-sec-meta">{esc(display_range)}</span>'
        f'<div class="gh-filters" role="group" aria-label="Filter coming events"{' hidden' if not current else ''}>{filters}</div></div></div>'
        '<div class="gh-week-grid">'
        f'<article class="gh-lead{lead_class}" data-starts="{esc(lead["starts_at"]) if lead else ""}"' + (' hidden' if not lead else '') + '>' + (f'<img src="{prefix}{lead_image[0]}" alt="{esc(lead_image[1])}" loading="lazy" decoding="async">' if lead_image else '') +
        f'<div class="gh-lead-body"><p class="gh-lead-k">{esc(short_range)}</p>'
        f'<h3>{esc(ed["title"])}</h3><p>{esc(ed["standfirst"])}</p>'
        f'<a class="gh-btn-solid" href="{esc(ed["href"])}">See what\'s on <span class="arr" aria-hidden="true">→</span></a>'
        '</div></article>'
        f'<div class="gh-rows">{row_html}</div></div>'
        '</section>')
    tiles = ''.join(
        f'<a class="gh-tile {cls}" href="{prefix}{href}"><img src="{prefix}{img}" alt="{esc(alt)}" loading="lazy" decoding="async">'
        '<span class="gh-tile-shade"></span><span class="gh-tile-arr" aria-hidden="true">→</span>'
        f'<span class="gh-tile-txt"><span class="gh-tile-lab">{esc(lab)}</span>'
        f'<span class="gh-tile-bot"><h3>{esc(name)}</h3><p>{esc(blurb)}</p></span></span></a>'
        for href, img, lab, name, blurb, alt, cls in EXPLORE_TILES)
    explore = (
        '<section class="gh-explore" aria-label="Explore the live guide">'
        '<div class="gh-sec-head"><h2>Explore the <em>live guide</em></h2>'
        '<span class="gh-sec-meta">Every verified event · Five ways in</span></div>'
        f'<div class="gh-mosaic">{tiles}</div></section>')
    # Later dates belong on Calendar/Events, not a second future-week list.
    band = ''
    steps = ''.join(
        f'<div class="gh-step"><span class="gh-step-n">{i:02d}</span>'
        f'<div><h3>{esc(h)}</h3><p>{esc(p)}</p></div></div>'
        for i, (h, p) in enumerate(VERIFY_STEPS, 1))
    verify = (
        '<section class="gh-verify" aria-label="How we verify">'
        '<div class="gh-sec-head"><h2>How we <em>verify</em></h2>'
        f'<a class="gh-btn-line" href="{prefix}sources/">See our sources <span class="arr" aria-hidden="true">→</span></a></div>'
        f'<div class="gh-verify-grid">{steps}</div></section>')
    return week + explore + band + verify


def soup(text):
    return BeautifulSoup(text, 'html.parser')


def fragment(text):
    return soup(text)


def clean_css(css):
    """Keep page layout, replace legacy colors with audited shared theme tokens."""
    css = re.sub(r'(?<![-\w])color\s*:[^;}]+', 'color:var(--ink)', css, flags=re.I)
    css = re.sub(r'(?<![-\w])background(?:-color)?\s*:[^;}]+', 'background:var(--surface)', css, flags=re.I)
    css = re.sub(r'(?<![-\w])opacity\s*:[^;}]+', 'opacity:1', css, flags=re.I)
    # Legacy :root declarations otherwise fight the shared palette.
    return re.sub(r':root\s*\{[^}]+\}', '', css)


def navigation(prefix, current):
    return '<nav class="site-nav" aria-label="Sections">' + ''.join(
        f'<a href="{prefix}{path}"' + (' aria-current="page"' if path == current else '') + f'>{label}</a>'
        for path, label in NAV) + '</nav>'


def footer_navigation(prefix, current):
    """Footer nav: NAV plus the FOOTER_EXTRA guide links after Top Picks."""
    items = []
    for path, label in NAV:
        items.append((path, label, None))
        if path == 'picks/':
            items.extend(FOOTER_EXTRA)
    return '<nav class="site-nav" aria-label="Sections">' + ''.join(
        f'<a href="{prefix}{path}"' + (' aria-current="page"' if path == current else '') + season_windows_attr(season) + f'>{label}</a>'
        for path, label, season in items) + '</nav>'


def decorate(path, skin, rows, day):
    text = path.read_text()
    # Absolute project paths break the Cloudflare root deployment.
    prefix = '../' * len(path.relative_to(ROOT).parts[:-1])
    if path.name != '404.html':
        text = re.sub(r'''(?<=["'])/this-week-in-aspen/''', prefix, text)
    text = re.sub(r'\s*[·&;\s]*An Ad Astra Media publication\.', '', text, flags=re.I)
    text = re.sub(r'Ad Astra', '', text, flags=re.I)
    doc = soup(text)
    if not doc.head or not doc.body:
        raise ValueError(f'Incomplete HTML document: {path}')
    doc.body['class'] = list(dict.fromkeys(doc.body.get('class', []) + ['gh-site']))
    doc.body['data-page'] = path.relative_to(ROOT).as_posix()
    for tag in doc.select('[data-gh-design], .gh-top, .gh-footer'):
        tag.decompose()
    # Remove old registrations and head resources; a single shared runtime owns PWA.
    for tag in list(doc.head.find_all('script')):
        if 'serviceWorker' in tag.get_text(): tag.decompose()
    for tag in list(doc.head.select('link[rel="manifest"], link[rel="apple-touch-icon"], meta[name="theme-color"], meta[name="apple-mobile-web-app-status-bar-style"]')):
        tag.decompose()
    for tag in doc.find_all('script', src=True):
        if tag['src'] in {prefix+'assets/gh-theme.js',prefix+'assets/gh-halloween.js'}: tag.decompose()
    for tag in doc.find_all('link', href=True):
        if 'fonts.googleapis.com/css' in tag['href']:
            tag['href'] = 'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,900&family=Inter:wght@400;500;600;700&display=swap'
    if not any('fonts.googleapis.com/css' in tag.get('href','') for tag in doc.find_all('link')):
        doc.head.append(doc.new_tag('link',rel='stylesheet',href='https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,900&family=Inter:wght@400;500;600;700&display=swap'))
    for tag in doc.find_all('style'):
        tag.string = clean_css(tag.get_text())
    for tag in doc.select('[style]'):
        tag['style'] = clean_css(tag['style'])
    current = path.relative_to(ROOT).as_posix().replace('index.html','') or 'index.html'
    home_tagline = None
    if current == 'index.html':
        # WO#15: the homepage tagline moves into the concept mast-sub row;
        # lift it out before the masthead rebuild discards shell children.
        tagline_tag = doc.select_one('.tagline')
        if tagline_tag is not None: home_tagline = tagline_tag.extract()
    masthead = doc.select_one('header.masthead')
    if masthead:
        # Keep edition datelines and descriptive copy, outside the wordmark.
        retained = [t.extract() for t in list(masthead.children)
                    if getattr(t,'name',None) and not (set(t.get('class',[])) & {'brand','kicker','rule-double','site-nav','gh-top','gh-mast-sub'})]
    else:
        retained = []
        masthead = doc.new_tag('header', attrs={'class':'masthead'})
        (doc.select_one('.page') or doc.body).insert(0,masthead)
    masthead.clear()
    if current == 'index.html':
        # WO#15 — homepage concept masthead (approved concept v3.1): the top
        # strip leaves the masthead so it bleeds full width as a dark band;
        # eyebrow rules, giant two-line wordmark, tagline + pill-nav row.
        # gh-theme.js hooks (.gh-date/.gh-weather/.gh-theme-toggle) unchanged.
        topbar = fragment('<div class="gh-top gh-topbar"><div class="gh-topbar-in">'
            '<span class="gh-top-left"><time class="gh-date">Aspen, Colorado</time>'
            '<span class="gh-weather" role="status">Aspen · Loading weather…</span></span>'
            '<span class="gh-top-center" aria-hidden="true"></span>'
            '<span class="gh-top-right">'
            '<button class="gh-theme-toggle" type="button" aria-label="Dark theme" aria-pressed="false">Theme</button></span></div></div>')
        doc.body.insert(0, topbar.select_one('.gh-topbar').extract())
        masthead.append(fragment('<p class="kicker gh-eyebrow"><span class="rule double"></span>'
            '<span class="gh-kicker-text">FROM ASPEN AND BEYOND</span><span class="rule double"></span></p>'
            f'<p class="brand"><a href="{prefix}index.html" aria-label="The Golden Hour — home">'
            '<span class="l1">THE GOLDEN</span> <span class="l2"><em>HOUR</em></span></a></p>'))
        masthead.append(fragment('<div class="gh-mast-sub"></div>'))
    else:
        masthead.append(fragment('<div class="gh-top"><div class="gh-context"><time class="gh-date">Aspen, Colorado</time>'
            '<span class="gh-weather" role="status">Aspen · Loading weather…</span></div>'
            '<button class="gh-theme-toggle" type="button" aria-label="Dark theme" aria-pressed="false">Theme</button></div>'
            '<p class="kicker">FROM ASPEN AND BEYOND</p>'
            f'<p class="brand"><a href="{prefix}index.html" aria-label="The Golden Hour — home">THE GOLDEN <em>HOUR</em></a></p>'
            + navigation(prefix,current)))
    for tag in reversed(retained): masthead.insert_after(tag)
    if current == 'index.html':
        sub = masthead.select_one('.gh-mast-sub')
        if home_tagline is None:
            home_tagline = fragment('<p class="tagline">A weekly field guide to what&rsquo;s on &mdash; music, art, and high-country happenings, verified before publication.</p>').select_one('.tagline').extract()
        sub.insert(0, home_tagline)
        sub.append(fragment(navigation(prefix, current)).select_one('nav').extract())
    if current == 'index.html':
        # WO#16: below-hero homepage sections are builder-generated from
        # the concept (This week / Explore mosaic / Coming-up band /
        # Verify). Editorial inputs (edition range, title, standfirst)
        # are extracted before the legacy blocks are replaced.
        page_div = next((d for d in doc.select('.page')
                         if d.select_one('.hero, .gh-week')), None)
        if page_div is not None:
            ed = _wo16_edition(doc)
            block = fragment(homepage_sections(rows, day, ed, prefix))
            page_div.clear()
            for child in list(block.contents):
                page_div.append(child.extract() if hasattr(child, 'extract') else child)
    if not doc.find('h1'):
        masthead.select_one('.brand').name = 'h1'
    refine_page(doc, path, rows, day)
    for footer in doc.find_all('footer'): footer.decompose()
    foot_head = ''
    if current == 'index.html':
        # WO#16: the concept's giant footer wordmark + meta line, homepage
        # only; the shared footer shell (nav, verification line) is kept.
        foot_head = ('<p class="gh-foot-word">THE GOLDEN <em>HOUR</em></p>'
                     '<p class="gh-foot-meta"><span>From Aspen and Beyond</span>'
                     '<span class="gh-gold">Verified before publication</span></p>')
    doc.body.append(fragment('<footer class="gh-footer">' + foot_head + footer_navigation(prefix,current) +
        '<p>Every event verified against official sources before publication. Details may change — please confirm with the venue.</p>'
        '<p>© 2026 The Golden Hour · From Aspen and Beyond.</p></footer>'))
    if current == 'index.html':
        assert doc.select_one('.gh-foot-word'), 'WO#16: footer wordmark missing'
    if path.relative_to(ROOT).parts[0] in ('press','desk','stats'):
        robots = doc.find('meta', attrs={'name':'robots'})
        if not robots: robots = doc.new_tag('meta',attrs={'name':'robots'});doc.head.append(robots)
        robots['content'] = 'noindex, nofollow'
    resources = f'''<meta data-gh-design name="theme-color" content="#faf4e8">
<meta data-gh-design name="apple-mobile-web-app-status-bar-style" content="default">
<meta data-gh-design name="mobile-web-app-capable" content="yes">
<meta data-gh-design name="apple-mobile-web-app-capable" content="yes">
<meta data-gh-design name="apple-mobile-web-app-title" content="Golden Hour">
<link data-gh-design rel="manifest" href="{prefix}manifest.json">
<link data-gh-design rel="apple-touch-icon" href="{prefix}icons/apple-touch-icon.png">
<link data-gh-design rel="stylesheet" href="{prefix}assets/gh-theme.css">
<script data-gh-design src="{prefix}assets/gh-theme.js"></script>'''
    if current in ('index.html','upcoming/'):
        resources = resources.replace(f'<script data-gh-design src="{prefix}assets/gh-theme.js">',f'<script data-gh-design src="{prefix}assets/gh-week.js"></script><script data-gh-design src="{prefix}assets/gh-theme.js">')
    if current == 'index.html':
        resources += f'<link data-gh-design rel="stylesheet" href="{prefix}assets/gh-home.css">'
    if skin == 'halloween':
        resources += f'<link data-gh-design rel="stylesheet" href="{prefix}assets/gh-halloween.css"><script data-gh-design defer src="{prefix}assets/gh-halloween.js"></script>'
    doc.head.append(fragment(resources))
    from design.chrome import finish as finish_chrome
    finish_chrome(doc, path, ROOT)
    path.write_text('\n'.join(line.rstrip() for line in str(doc).splitlines()).rstrip() + '\n')


def refine_page(doc, path, rows, day):
    """Presentation repairs; never changes the canonical event records."""
    route = path.relative_to(ROOT).as_posix()
    robots=doc.find('meta',attrs={'name':'robots'})
    if not (robots and 'noindex' in robots.get('content','')):
        title=doc.title.get_text() if doc.title else 'The Golden Hour'
        description=doc.find('meta',attrs={'name':'description'})
        for prop,value in [('og:title',title),('og:description',description.get('content','') if description else '')]:
            if value and not doc.find('meta',attrs={'property':prop}):doc.head.append(doc.new_tag('meta',attrs={'property':prop,'content':value}))
        image=doc.find('meta',attrs={'property':'og:image'})
        if not image:
            doc.head.append(doc.new_tag('meta',attrs={'property':'og:image','content':URL+'icons/icon-512.png'}))
        elif image.get('content','').endswith('/assets/img/og-events.jpg'):
            image['content']=URL+'icons/icon-512.png'
        twitter=doc.find('meta',attrs={'name':'twitter:image'})
        if twitter and twitter.get('content','').endswith('/assets/img/og-events.jpg'):twitter['content']=URL+'icons/icon-512.png'
    if route == 'shoulder-season/index.html' and not doc.select_one('main.page'):
        content=doc.new_tag('main',attrs={'class':'page'})
        for tag in list(doc.body.children):
            if getattr(tag,'name',None) and tag.name!='header' and tag.name!='footer':content.append(tag.extract())
        doc.body.append(content)
    if route == '404.html' and not doc.find('meta',attrs={'name':'description'}):
        doc.head.append(doc.new_tag('meta',attrs={'name':'description','content':'This page could not be found. Return to The Golden Hour guide to Aspen events and activities.'}))
    for image in doc.select('img'):
        image['class'] = list(dict.fromkeys(image.get('class', []) + ['gh-artwork']))
    for table in doc.select('table.src'):
        headers = [th.get_text(' ',strip=True) for th in table.select('tr:first-child th')]
        if not table.thead:
            head = doc.new_tag('thead'); head.append(table.find('tr').extract());table.insert(0,head)
        if not table.tbody:
            body = doc.new_tag('tbody')
            for row in list(table.find_all('tr',recursive=False)):body.append(row.extract())
            table.append(body)
        table['role']='table'
        for row in table.select('tbody tr'):
            row['role']='row'
            for i,cell in enumerate(row.find_all(['td','th'],recursive=False)):
                cell['data-label']=headers[i];cell['role']='cell'
    if route == 'calendar/index.html':
        title=doc.select_one('#gcal-title')
        title.string=day.strftime('%B %Y')
        legend=doc.select_one('.gcal-legend')
        if legend:
            for span in legend.select('span'):
                span['data-category']=span.get_text(strip=True).lower()
        if not doc.select_one('.gcal-mobile-note'):
            doc.select_one('.gcal-grid').insert_before(fragment('<p class="gcal-mobile-note">Select a date or event for details.</p>'))
    if route == 'map/index.html':
        if not doc.select_one('.gh-map-heading'):
            doc.select_one('.masthead').insert_after(fragment('<div class="page gh-map-heading"><h1>Map</h1></div>'))
        legend=doc.select_one('.legend')
        if legend:
            for span,key in zip(legend.find_all('span',recursive=False),['today','week','month','later']):
                span['data-range-key']=key
    if route.startswith('events/') and route!='events/index.html':
        event=next((e for e in rows if route=='events/'+e['slug']+'/index.html'),None)
        if event:
            description=event.get('blurb') or event['title']+' — '+event['venue']
            if not doc.find('meta',attrs={'name':'description'}):doc.head.append(doc.new_tag('meta',attrs={'name':'description','content':description}))
            if not doc.find('link',rel='canonical'):doc.head.append(doc.new_tag('link',rel='canonical',href=URL+'events/'+event['slug']+'/'))
            if not doc.find('script',type='application/ld+json'):
                ld={'@context':'https://schema.org','@type':'Event','name':event['title'],'startDate':event['starts_at'],'url':URL+'events/'+event['slug']+'/','description':description,'location':{'@type':'Place','name':event['venue']}}
                tag=doc.new_tag('script',type='application/ld+json');tag.string=json.dumps(ld,ensure_ascii=False).replace('</','<\\/');doc.head.append(tag)
            for prop,value in [('og:title',event['title']+' — The Golden Hour'),('og:description',description),('og:image',URL+(event.get('image') or 'icons/icon-512.png'))]:
                if not doc.find('meta',attrs={'property':prop}):doc.head.append(doc.new_tag('meta',attrs={'property':prop,'content':value}))
        badge=doc.select_one('.vbadge')
        if badge:
            badge.string='Listing source checked'
            if not doc.select_one('.gh-field-note'):
                badge.insert_after(fragment('<p class="gh-field-note">Price and age details may remain unverified. Confirm these fields with the venue when booking.</p>'))
    if route == 'index.html':
        # WO#15 guards: the concept cover and pill nav are homepage structure,
        # not decoration — a build that loses them must fail here, not ship.
        assert doc.select_one('.gh-cover-frame img'), 'WO#15: homepage cover missing'
        assert doc.select_one('.gh-topbar'), 'WO#15: homepage top strip missing'
        assert doc.select_one('.gh-mast-sub nav.site-nav'), 'WO#15: homepage pill nav missing'
        # WO#16 guards: the concept's below-hero sections are homepage
        # structure — a build that loses them must fail here, not ship.
        assert len(doc.select('.gh-tile')) == 5, 'WO#16: Explore mosaic must carry five tiles'
        assert not doc.select_one('.gh-band') or len(doc.select('.gh-band-item')) >= 3, 'WO#16: Coming-up band items missing'
        assert len(doc.select('.gh-step')) == 3, 'WO#16: Verify steps missing'
        assert doc.select_one('.gh-week .gh-row,.gh-week .gh-list-empty'), 'WO#16: This-week rows missing'
    if route == 'press/index.html':
        total=sum(datetime.fromisoformat(e['starts_at']).astimezone(TZ).date()>=day for e in rows)
        for paragraph in doc.select('.card p'):
            if 'verified events' in paragraph.get_text() or paragraph.select_one('[data-upcoming-count]'):
                paragraph.clear();paragraph.append(fragment(f'<span data-upcoming-count="">{total}</span> verified upcoming events with dates, times, available artwork, and official event links.'))
    if route == 'editions/index.html':
        doc.title.string='Archive — The Golden Hour'
        for meta in doc.select('meta[property="og:title"],meta[name="twitter:title"]'):meta['content']='Archive — The Golden Hour'
        for heading in doc.find_all(['h1','h2']):
            if heading.get_text(strip=True)=='Past editions':heading.string='Archive'
        archive=doc.select_one('ul.archive')
        if archive:
            grid=doc.new_tag('div',attrs={'class':'gh-archive-grid'})
            for entry in archive.find_all('li',recursive=False):
                link=entry.find('a');arrival=entry.select_one('.when')
                article=doc.new_tag('article',attrs={'class':'gh-card gh-typographic'})
                article.append(fragment('<p class="gh-card-kicker">Weekly edition</p>'))
                heading=doc.new_tag('h3');heading.append(link.extract());article.append(heading)
                if arrival:article.append(arrival.extract())
                grid.append(article)
            archive.replace_with(grid)


def events():
    rows = json.loads((ROOT/'data/events.json').read_text())
    assert len({e['id'] for e in rows}) == len(rows), 'Duplicate event IDs'
    assert HALLOWEEN <= {e['slug'] for e in rows}, 'Missing required Halloween IDs'
    for e in rows:
        assert datetime.fromisoformat(e['starts_at']).tzinfo, f"Timezone missing: {e['id']}"
        assert e['slug'] and re.fullmatch('[a-z0-9-]+',e['slug'])
        if e.get('image'): assert (ROOT/e['image']).is_file(), f"Missing event media: {e['image']}"
    return sorted(rows,key=lambda e:datetime.fromisoformat(e['starts_at']))


def document(title,body,ld=None,route=None):
    structured = '<script id="gh-event-list" type="application/ld+json">' + json.dumps(ld,ensure_ascii=False).replace('</','<\\/') + '</script>' if ld else ''
    route = route or title.lower() + '/'
    description = WEEK_DESCRIPTION if route == 'upcoming/' else 'Every verified upcoming event in Aspen and the high country, soonest first.'
    seo = (f'<meta name="description" content="{description}"><link rel="canonical" href="{URL}{route}">' if title in ('Events','Upcoming','This Week') else '')
    analytics = '<script src="../assets/js/analytics-config.js"></script><script defer src="../assets/js/analytics.js"></script>' if title in ('Events','Upcoming','This Week') else ''
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{html.escape(title)} — The Golden Hour</title>{seo}{structured}{analytics}</head><body><div class="page">{body}</div></body></html>'


def card(e,detail=False):
    esc = html.escape
    d = datetime.fromisoformat(e['starts_at']).astimezone(TZ)
    image = f'<figure class="gh-card-media"><img src="../{esc(e["image"])}" alt="{esc(e["title"])} — official event imagery" loading="lazy" decoding="async"></figure>' if e.get('image') else ''
    copy = f'{e["title"]} — {e["venue"]}\n{d:%a, %b %d · %I:%M %p} MT\n{e.get("blurb") or ""}\n{e["url"]}'
    extra = (f'<details class="gh-card-details"><summary>Details &amp; booking</summary><dl>'
             f'<div><dt>Price</dt><dd>{esc(e.get("price_info") or "Confirm with venue")}</dd></div>'
             f'<div><dt>Ages</dt><dd>{esc(e.get("age_policy") or "Confirm with venue")}</dd></div></dl>'
             f'<p>{esc(e.get("blurb") or "")}</p><p>{esc(e.get("fit_note") or "")}</p></details>'
             f'<div class="gh-card-actions"><a class="btn" href="{esc(e["url"])}" rel="noopener">Official source ↗</a>'
             f'<button type="button" class="copybtn gh-copy" data-copy="{esc(copy)}">Copy details</button></div>')
    free = '1' if re.search(r'\bfree\b|^\$?0(?:\D|$)',e.get('price_info') or '',re.I) else '0'
    heading = (f'<p class="gh-card-kicker">{esc(e["category"])}</p><time datetime="{esc(e["starts_at"])}">{d:%a, %b %d · %I:%M %p} MT</time>'
               f'<h2><a class="gh-card-link" href="../events/{esc(e["slug"])}/">{esc(e["title"])}</a></h2>')
    media = image if image else f'<header class="gh-type-media">{heading}</header>'
    return (f'<article id="ev-{esc(e["id"])}" class="gh-event-card gh-card {"has-media" if image else "gh-typographic"}" data-starts="{esc(e["starts_at"])}" data-slug="{esc(e["slug"])}" data-cat="{esc(e["category"])}" data-free="{free}">'
            f'{media}<div class="gh-card-body">{heading if image else ""}'
            f'<p class="gh-card-venue">{esc(e["venue"])}</p>{extra}</div></article>')


def build_lists(rows,day):
    future = [e for e in rows if datetime.fromisoformat(e['starts_at']).astimezone(TZ).date() >= day]
    for path,title,detail in [('events/index.html','Events',False),('upcoming/index.html','This Week',True)]:
        weekly = path.startswith('upcoming/')
        selected = this_week(rows,day) if weekly else future
        ld = {'@context':'https://schema.org','@type':'ItemList','name':title+' — The Golden Hour',
              'itemListElement':[{'@type':'ListItem','position':i+1,'item':{'@type':'Event','name':e['title'],
                'startDate':e['starts_at'],'url':URL+'events/'+e['slug']+'/'}} for i,e in enumerate(selected)]}
        body = f'<h1>{title}</h1><p class="lede">{WEEK_DESCRIPTION if weekly else "Every verified upcoming event in Aspen and the high country, soonest first."}</p>'
        if weekly:
            start,end=week_bounds(day)
            body += f'<p class="gh-week-range">{start:%b %d} – {end:%b %d, %Y} · MT</p>'
        chips = available_filters(selected) if weekly else [('all','All'),('weekend','This weekend'),('music','Music'),('arts','Art'),('outdoors','Outdoors'),('free','Free')]
        body += '<div class="gh-filters" role="group" aria-label="Filter events"'+ (' hidden' if weekly and not selected else '') +'>' + ''.join(f'<button type="button" data-filter="{key}" aria-pressed="{str(key == "all").lower()}">{label}</button>' for key,label in chips) + '</div>'
        body += '<div class="gh-event-grid">' + ''.join(card(e,detail) for e in selected) + '</div>'
        empty = 'No verified events this week. <a href="../calendar/">Calendar</a> · <a href="../events/">Events</a>' if weekly else 'No upcoming events listed. Check back soon.'
        body += '<p class="gh-list-empty"' + (' hidden' if selected else '') + '>'+empty+'</p>'
        (ROOT/path).write_text(document(title,body,ld,route=path.replace('index.html','')))
    # Preserve existing individual event editorial pages; create only missing routes.
    for e in rows:
        path = ROOT/'events'/e['slug']/'index.html'
        if path.exists(): continue
        esc=html.escape
        path.parent.mkdir(parents=True,exist_ok=True)
        d=datetime.fromisoformat(e['starts_at']).astimezone(TZ)
        image = f'<figure class="ev-hero"><img src="../../{esc(e["image"])}" alt="{esc(e["title"])} — official event imagery"></figure>' if e.get('image') else ''
        body=f'{image}<h1>{esc(e["title"])}</h1><p>{d:%A, %B %d, %Y · %I:%M %p} MT · {esc(e["venue"])}</p><p>{esc(e.get("blurb") or "")}</p><a class="btn" href="{esc(e["url"])}">Official event page ↗</a>'
        path.write_text(document(e['title'],body))
    return future


def validate(rows,day):
    for name in ['calendar/events.json','map/events.json']:
        assert json.loads((ROOT/name).read_text()) == rows, f'Canonical event set diverged: {name}. Run build_design.py after content changes.'
    expected = [e['id'] for e in rows if datetime.fromisoformat(e['starts_at']).astimezone(TZ).date() >= day]
    for name in ['events/index.html','upcoming/index.html']:
        doc=soup((ROOT/name).read_text())
        scoped = [e['id'] for e in this_week(rows,day)] if name.startswith('upcoming/') else expected
        assert [c['id'][3:] for c in doc.select('.gh-event-card')] == scoped, f'{name}: stale, missing, or unsorted rows'
        ld=json.loads(doc.select_one('#gh-event-list').string)
        assert [x['item']['startDate'] for x in ld['itemListElement']] == [e['starts_at'] for e in rows if e['id'] in scoped], f'{name}: structured data differs from visible events'
    count=0
    for path in ROOT.rglob('*.html'):
        if '.git' in path.parts: continue
        doc=soup(path.read_text())
        assert len(doc.select('.gh-top'))==1, f'Missing shared strip: {path}'
        assert len(doc.select('.masthead .brand'))==1, f'Missing wordmark: {path}'
        assert doc.select_one('link[rel="manifest"]'), f'Missing PWA: {path}'
        for image in doc.find_all('img',src=True):
            src=image['src']
            if not re.match(r'^(https?:|data:|//)',src):
                assert (path.parent/src).is_file(), f'Broken local image: {path}: {src}'
        assert not re.search(r'ad\s+astra|photograph(?:y|er)?[^<\n]{0,80}Ron Delhaye',str(doc),re.I), f'Brand lock: {path}'
        count+=1
    print(f'PASS: {count} pages share the design; {len(rows)} canonical occurrences; {len(expected)} today/future occurrences; {len(this_week(rows,day))} remaining this-week occurrences.')


def build_404():
    base_script = '''<script>const projectHost=location.hostname.endsWith('.github.io')||(['127.0.0.1','localhost'].includes(location.hostname)&&location.pathname.startsWith('/this-week-in-aspen/'));const base=document.createElement('base');base.href=projectHost?'/this-week-in-aspen/':'/';document.head.append(base);</script>'''
    content = document('Page not found','<main class="gh-not-found"><p class="gh-card-kicker">404</p><h1>Page not found</h1><p>This address does not lead to a page in the guide. Find your next Aspen moment below.</p><div class="gh-card-actions"><a class="btn" href="index.html">Latest</a><a class="btn" href="events/">Events</a><a class="btn" href="calendar/">Calendar</a></div></main>')
    (ROOT/'404.html').write_text(content.replace('<head>','<head>'+base_script+'<meta name="robots" content="noindex"><meta name="description" content="This page could not be found. Return to The Golden Hour guide to Aspen events and activities.">'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--as-of',help='Denver date, YYYY-MM-DD; defaults to today')
    args=parser.parse_args()
    day=datetime.fromisoformat(args.as_of).date() if args.as_of else datetime.now(TZ).date()
    rows=events()
    if not args.check:
        for name in ['calendar/events.json','map/events.json']:
            (ROOT/name).write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
        build_lists(rows,day)
        from build_features import build_ready
        build_ready(ROOT,rows,day)
        build_404()
        skin=json.loads((ROOT/'design-config.json').read_text())['skin']
        assert skin in (None,'halloween'), 'Unknown seasonal skin'
        for path in ROOT.rglob('*.html'):
            if '.git' not in path.parts: decorate(path,skin,rows,day)
        # The detail generator copies shared chrome from the decorated collection.
        from build_event_details import build as build_event_details
        build_event_details(ROOT, datetime.combine(day, datetime.min.time(), tzinfo=TZ))
    validate(rows,day)


if __name__ == '__main__': main()
