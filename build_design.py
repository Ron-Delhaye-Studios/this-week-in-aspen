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

ROOT = Path(__file__).resolve().parent
TZ = ZoneInfo('America/Denver')
URL = 'https://ron-delhaye-studios.github.io/this-week-in-aspen/'
HALLOWEEN = {'aspens-darkside-ghost-tour', 'spooktacular-creepy-crafts', 'ute-cemetery-tour',
             'murder-at-the-rattlesnake-saloon', 'ghosts-of-aspens-past', 'coco-and-breezy',
             'halloween-bash-ft-chaparelle', 'shrek-themed-halloween-party'}
NAV = [('index.html','Latest'), ('events/','Events'), ('upcoming/','Upcoming'),
       ('calendar/','Calendar'), ('map/','Map'), ('picks/','Top Picks'),
       ('activities/','Activities'), ('editions/','Archive'), ('sources/','How we verify')]


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


def decorate(path, skin):
    text = path.read_text()
    # Absolute project paths break the Cloudflare root deployment.
    prefix = '../' * len(path.relative_to(ROOT).parts[:-1])
    text = re.sub(r'''(?<=["'])/this-week-in-aspen/''', prefix, text)
    text = re.sub(r'\s*[·&;\s]*An Ad Astra Media publication\.', '', text, flags=re.I)
    text = re.sub(r'Ad Astra', '', text, flags=re.I)
    doc = soup(text)
    if not doc.head or not doc.body:
        raise ValueError(f'Incomplete HTML document: {path}')
    doc.body['class'] = list(dict.fromkeys(doc.body.get('class', []) + ['gh-site']))
    for tag in doc.select('[data-gh-design], .gh-top, .gh-footer'):
        tag.decompose()
    # Remove old registrations and head resources; a single shared runtime owns PWA.
    for tag in list(doc.head.find_all('script')):
        if 'serviceWorker' in tag.get_text(): tag.decompose()
    for tag in list(doc.head.select('link[rel="manifest"], link[rel="apple-touch-icon"], meta[name="theme-color"]')):
        tag.decompose()
    for tag in doc.find_all('script', src=True):
        if tag['src'] in {prefix+'assets/gh-theme.js',prefix+'assets/gh-halloween.js'}: tag.decompose()
    for tag in doc.find_all('link', href=True):
        if 'fonts.googleapis.com/css' in tag['href']:
            tag['href'] = 'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,900&family=Inter:wght@400;500;600;700&display=swap'
    for tag in doc.find_all('style'):
        tag.string = clean_css(tag.get_text())
    for tag in doc.select('[style]'):
        tag['style'] = clean_css(tag['style'])
    current = path.relative_to(ROOT).as_posix().replace('index.html','') or 'index.html'
    masthead = doc.select_one('header.masthead')
    if masthead:
        # Keep edition datelines and descriptive copy, outside the wordmark.
        retained = [t.extract() for t in list(masthead.children)
                    if getattr(t,'name',None) and not (set(t.get('class',[])) & {'brand','kicker','rule-double','site-nav','gh-top'})]
    else:
        retained = []
        masthead = doc.new_tag('header', attrs={'class':'masthead'})
        (doc.select_one('.page') or doc.body).insert(0,masthead)
    masthead.clear()
    masthead.append(fragment('<div class="gh-top"><time class="gh-date">Aspen, Colorado</time>'
        '<span class="gh-weather" role="status">Aspen · Loading weather…</span>'
        '<button class="gh-theme-toggle" type="button" aria-label="Dark theme" aria-pressed="false">Theme</button></div>'
        '<p class="kicker">FROM ASPEN AND BEYOND</p>'
        f'<p class="brand"><a href="{prefix}index.html" aria-label="The Golden Hour — home">THE GOLDEN <em>HOUR</em></a></p>'
        + navigation(prefix,current)))
    for tag in reversed(retained): masthead.insert_after(tag)
    if not doc.find('h1'):
        masthead.select_one('.brand').name = 'h1'
    for footer in doc.find_all('footer'): footer.decompose()
    doc.body.append(fragment('<footer class="gh-footer">' + navigation(prefix,current) +
        '<p>Every event verified against official sources before publication. Details may change — please confirm with the venue.</p>'
        '<p>© 2026 The Golden Hour · From Aspen and Beyond.</p></footer>'))
    if path.relative_to(ROOT).parts[0] in ('press','desk','stats'):
        robots = doc.find('meta', attrs={'name':'robots'})
        if not robots: robots = doc.new_tag('meta',attrs={'name':'robots'});doc.head.append(robots)
        robots['content'] = 'noindex, nofollow'
    resources = f'''<meta data-gh-design name="theme-color" content="#faf4e8">
<meta data-gh-design name="mobile-web-app-capable" content="yes">
<meta data-gh-design name="apple-mobile-web-app-capable" content="yes">
<meta data-gh-design name="apple-mobile-web-app-title" content="Golden Hour">
<link data-gh-design rel="manifest" href="{prefix}manifest.json">
<link data-gh-design rel="apple-touch-icon" href="{prefix}icons/apple-touch-icon.png">
<link data-gh-design rel="stylesheet" href="{prefix}assets/gh-theme.css">
<script data-gh-design src="{prefix}assets/gh-theme.js"></script>'''
    if skin == 'halloween':
        resources += f'<link data-gh-design rel="stylesheet" href="{prefix}assets/gh-halloween.css"><script data-gh-design defer src="{prefix}assets/gh-halloween.js"></script>'
    doc.head.append(fragment(resources))
    path.write_text('\n'.join(line.rstrip() for line in str(doc).splitlines()).rstrip() + '\n')


def events():
    rows = json.loads((ROOT/'data/events.json').read_text())
    assert len({e['id'] for e in rows}) == len(rows), 'Duplicate event IDs'
    assert HALLOWEEN <= {e['slug'] for e in rows}, 'Missing required Halloween IDs'
    for e in rows:
        assert datetime.fromisoformat(e['starts_at']).tzinfo, f"Timezone missing: {e['id']}"
        assert e['slug'] and re.fullmatch('[a-z0-9-]+',e['slug'])
        if e.get('image'): assert (ROOT/e['image']).is_file(), f"Missing event media: {e['image']}"
    return sorted(rows,key=lambda e:datetime.fromisoformat(e['starts_at']))


def document(title,body,ld=None):
    structured = '<script id="gh-event-list" type="application/ld+json">' + json.dumps(ld,ensure_ascii=False).replace('</','<\\/') + '</script>' if ld else ''
    route = title.lower() + '/'
    seo = (f'<meta name="description" content="Every verified upcoming event in Aspen and the high country, soonest first."><link rel="canonical" href="{URL}{route}">' if title in ('Events','Upcoming') else '')
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} — The Golden Hour</title>{seo}{structured}</head><body><div class="page">{body}</div></body></html>'


def card(e,detail=False):
    esc = html.escape
    d = datetime.fromisoformat(e['starts_at']).astimezone(TZ)
    image = f'<img src="../{esc(e["image"])}" alt="{esc(e["title"])} — official event imagery" loading="lazy" decoding="async">' if e.get('image') else ''
    copy = f'{e["title"]} — {e["venue"]}\n{d:%a, %b %d · %I:%M %p} MT\n{e.get("blurb") or ""}\n{e["url"]}'
    extra = (f'<p>{esc(e.get("price_info") or "")}</p><p>{esc(e.get("age_policy") or "")}</p>'
             f'<p>{esc(e.get("blurb") or "")}</p><p>{esc(e.get("fit_note") or "")}</p>'
             f'<a href="{esc(e["url"])}" rel="noopener">Official event page ↗</a>'
             f'<button type="button" class="copybtn gh-copy" data-copy="{esc(copy)}">Copy details</button>') if detail else ''
    return (f'<article id="ev-{esc(e["id"])}" class="gh-event-card {"has-media" if image else ""}" data-starts="{esc(e["starts_at"])}" data-slug="{esc(e["slug"])}">'
            f'{image}<time datetime="{esc(e["starts_at"])}">{d:%a, %b %d · %I:%M %p} MT</time>'
            f'<h2><a class="gh-card-link" href="../events/{esc(e["slug"])}/">{esc(e["title"])}</a></h2>'
            f'<p>{esc(e["venue"])}</p>{extra}</article>')


def build_lists(rows,day):
    future = [e for e in rows if datetime.fromisoformat(e['starts_at']).astimezone(TZ).date() >= day]
    ld = {'@context':'https://schema.org','@type':'ItemList','name':'Upcoming events — The Golden Hour',
          'itemListElement':[{'@type':'ListItem','position':i+1,'item':{'@type':'Event','name':e['title'],
            'startDate':e['starts_at'],'url':URL+'events/'+e['slug']+'/'}} for i,e in enumerate(future)]}
    for path,title,detail in [('events/index.html','Events',False),('upcoming/index.html','Upcoming',True)]:
        body = f'<h1>{title}</h1><p class="lede">Every verified upcoming event in Aspen and the high country, soonest first.</p>'
        body += '<div class="gh-event-grid">' + ''.join(card(e,detail) for e in future) + '</div>'
        body += '<p class="gh-list-empty"' + (' hidden' if future else '') + '>No upcoming events listed. Check back soon.</p>'
        (ROOT/path).write_text(document(title,body,ld))
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
        assert [c['id'][3:] for c in doc.select('.gh-event-card')] == expected, f'{name}: stale, missing, or unsorted rows'
        ld=json.loads(doc.select_one('#gh-event-list').string)
        assert [x['item']['startDate'] for x in ld['itemListElement']] == [e['starts_at'] for e in rows if e['id'] in expected], f'{name}: structured data differs from visible events'
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
    print(f'PASS: {count} pages share the design; {len(rows)} canonical occurrences; {len(expected)} today/future occurrences in both lists.')


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
        skin=json.loads((ROOT/'design-config.json').read_text())['skin']
        assert skin in (None,'halloween'), 'Unknown seasonal skin'
        for path in ROOT.rglob('*.html'):
            if '.git' not in path.parts: decorate(path,skin)
    validate(rows,day)


if __name__ == '__main__': main()
