"""Generate internal event pages from the canonical public calendar export."""
import html
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SITE = 'https://thegoldenhour.guide/'

def slug(event_id):
    return 'sync-' + re.sub(r'[^a-zA-Z0-9_-]', '-', event_id)

def safe_url(value):
    return value if urlparse(value or '').scheme in ('https', 'http') else ''

def build(root=ROOT):
    data = json.loads((root/'calendar/calendar-sync.json').read_text(encoding='utf-8'))
    shell = (root/'upcoming/index.html').read_text(encoding='utf-8')
    mast = re.search(r'<header class="masthead">.*?</header>', shell, re.S).group()
    foot = re.search(r'<footer class="gh-footer">.*?</footer>', shell, re.S).group()
    # Detail pages are one level deeper than the collection shell.
    mast = mast.replace('../', '../../')
    foot = foot.replace('../', '../../')
    seen = set()
    for e in data['events']:
        key = slug(e['id'])
        if key in seen:
            raise ValueError('Duplicate route: '+key)
        seen.add(key)
        esc = lambda v: html.escape(str(v or ''), quote=True)
        title = esc(e['title'])
        text = re.sub(r'<[^>]+>', ' ', e.get('description', ''))
        url = safe_url(e.get('url'))
        if not url:
            urls = re.findall(r'https?://[^\s<>"\)]+', text)
            url = safe_url(urls[0]) if urls else ''
        image = safe_url(e.get('image')) or (('../../'+e['image']) if e.get('image','').startswith('calendar/media/') else '')
        def stamp(value):
            d = datetime.fromisoformat(value)
            return d.astimezone(ZoneInfo('America/Denver')).strftime('%b %d, %Y · %I:%M %p MT') if d.tzinfo else d.strftime('%b %d, %Y')
        when = esc(stamp(e['start'])) + (' — '+esc(stamp(e['end'])) if e.get('end') else '')
        end = datetime.fromisoformat(e.get('end') or e['start'])
        today = datetime.now(ZoneInfo('America/Denver'))
        past = end < today if end.tzinfo else end.date() < today.date()
        content = '<p><a href="../../upcoming/">This Week</a> / Event details</p><h1>'+title+'</h1>'
        if past:
            content += '<p><strong>Past event</strong> · Historical listing. See This Week for current plans.</p>'
        if image:
            content += '<img style="width:100%;max-height:520px;object-fit:contain" src="'+esc(image)+'" alt="'+title+'"/>'
        content += '<dl><dt>Date and time</dt><dd>'+when+'</dd><dt>Venue</dt><dd>'+esc(e.get('venue') or 'Confirm with venue')+'</dd></dl>'
        content += '<p>Dates are shown as supplied by the calendar source. For date-only listings, confirm opening or performance times with the venue.</p>'
        content += '<div style="max-width:70ch;white-space:pre-line">'+esc(text)+'</div>'
        if url:
            content += '<p><a href="'+esc(url)+'" rel="noopener">Venue details &amp; booking ↗</a></p>'
        content += '<p>Calendar updated '+esc(data.get('exported_at'))+'. Details may change.</p><p><a href="../../calendar/">Explore the calendar</a> · <a href="../../picks/">Local favorites</a></p>'
        page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+' — The Golden Hour</title><meta name="description" content="'+esc(text[:150] or e['title'])+'"><link rel="canonical" href="'+SITE+'events/'+key+'/"><link rel="stylesheet" href="../../assets/gh-theme.css"><link rel="stylesheet" href="../../assets/gh-chrome.css"><script src="../../assets/gh-theme.js" defer></script></head><body class="gh-site" data-page="events/detail"><div class="page">'+mast+'<main>'+content+'</main></div>'+foot+'</body></html>'
        target = root/'events'/key/'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding='utf-8')
    return len(seen)

if __name__ == '__main__':
    print('Generated', build(), 'internal event pages')
