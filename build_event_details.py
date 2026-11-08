"""Generate the on-site event overview before a visitor chooses a venue link."""
import html
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SITE = 'https://thegoldenhour.guide/'
DENVER = ZoneInfo('America/Denver')


def slug(event_id):
    return 'sync-' + re.sub(r'[^a-zA-Z0-9_-]', '-', event_id)


def safe_url(value):
    parsed = urlparse(value or '')
    return value if parsed.scheme in ('https', 'http') and parsed.hostname and not parsed.username else ''


def description(raw):
    text = re.sub(r'<\s*br\s*/?\s*>|</p\s*>', '\n', raw or '', flags=re.I)
    text = BeautifulSoup(text, 'html.parser').get_text()
    url = re.search(r'(?im)^\s*(?:source|official(?: url)?):\s*(https?://[^\s<>"\)]+)', text)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or re.match(r'^(?:AURELIAN EVENT$|MASTER ID:|AURELIAN Score:|Trip Type:|(?:Official|Source):\s*https?://)', line, re.I):
            continue
        lines.append(re.sub(r'^(What|Where|Why it matters|Tickets):\s*', '', line, flags=re.I))
    return '\n\n'.join(lines), safe_url(url[1]) if url else ''


def build(root=ROOT, now=None):
    data = json.loads((root/'calendar/calendar-sync.json').read_text(encoding='utf-8'))
    shell = BeautifulSoup((root/'upcoming/index.html').read_text(), 'html.parser')
    mast, foot = shell.select_one('header.masthead'), shell.select_one('footer.gh-footer')
    if mast is None or foot is None:
        raise ValueError('Decorate the collection shell before generating event details')
    mast, foot = str(mast).replace('../', '../../'), str(foot).replace('../', '../../')
    today = (now or datetime.now(DENVER)).astimezone(DENVER).date()
    seen = set()
    for event in data['events']:
        key = slug(event['id'])
        if key in seen:
            raise ValueError('Duplicate route: '+key)
        seen.add(key)
        esc = lambda value: html.escape(str(value or ''), quote=True)
        text, source_url = description(event.get('description'))
        source_url = safe_url(event.get('url')) or source_url
        image = ''
        supplied = event.get('image') or ''
        if event.get('verified') is True and re.fullmatch(r'calendar/media/[a-zA-Z0-9_.-]+\.(?:jpg|jpeg|png|webp)', supplied, re.I):
            if not (root/supplied).is_file():
                raise ValueError('Missing supplied event image: '+supplied)
            image = '../../'+supplied
        def stamp(value):
            day = datetime.fromisoformat(value)
            return day.astimezone(DENVER).strftime('%a, %b %d, %Y · %I:%M %p MT') if day.tzinfo else day.strftime('%a, %b %d, %Y')
        display_end = event.get('end') or event['start']
        if event.get('all_day') and display_end > event['start']:
            display_end = (datetime.fromisoformat(display_end)-timedelta(days=1)).date().isoformat()
        end = datetime.fromisoformat(display_end)
        end_day = end.astimezone(DENVER).date() if end.tzinfo else end.date()
        past = end_day < today
        when = stamp(event['start'])
        if event.get('all_day') and display_end != event['start']:
            when += ' — '+stamp(display_end)
        if event.get('all_day'):
            when += ' · All day'
        title = esc(event['title'])
        page_url = SITE+'events/'+key+'/'
        content = '<nav aria-label="Breadcrumb"><a href="../../index.html">Home</a> / <a href="../../upcoming/">This Week</a> / Event details</nav>'
        content += '<main class="gh-sync-detail" data-end-day="'+end_day.isoformat()+'" data-when="'+esc(when)+'"><p class="gh-card-kicker">'+('Past event' if past else 'Event details')+'</p><h1>'+title+'</h1>'
        if past:
            content += '<p class="gh-sync-past"><strong>This event took place on '+esc(when)+'.</strong> See This Week for current plans.</p>'
        if image:
            content += '<figure class="gh-sync-media"><img src="'+esc(image)+'" alt="'+title+' — official event imagery" decoding="async"/></figure>'
        content += '<dl class="gh-sync-facts"><div><dt>When</dt><dd>'+esc(when)+'</dd></div><div><dt>Where</dt><dd>'+esc(event.get('venue') or 'Confirm with venue')+'</dd></div></dl>'
        if text:
            content += '<div class="gh-sync-story">'+''.join('<p>'+esc(p)+'</p>' for p in text.split('\n\n'))+'</div>'
        if event.get('all_day'):
            content += '<p class="gh-sync-note">For date-only listings, confirm opening or performance times with the venue.</p>'
        content += '<div class="gh-sync-actions">'
        if source_url:
            content += '<a class="gh-btn-solid" href="'+esc(source_url)+'" target="_blank" rel="noopener noreferrer">Official details &amp; booking ↗</a><span class="gh-sync-note">Opens the source in a new tab.</span>'
        content += '<a class="gh-btn-line" href="../../upcoming/">See what’s on this week →</a></div>'
        content += '<p class="gh-sync-note">Calendar updated '+esc(stamp(data['exported_at']) if data.get('exported_at') else 'the latest supplied export')+'. Details may change.</p></main>'
        ld = {'@context':'https://schema.org','@type':'Event','name':event['title'],'startDate':event['start'],'url':page_url,'description':('Past event. ' if past else '')+text}
        if event.get('end'):ld['endDate']=event['end']
        if event.get('venue'):ld['location']={'@type':'Place','name':event['venue']}
        if image:ld['image']=SITE+supplied
        structured = '<script type="application/ld+json" id="gh-sync-event">'+json.dumps(ld,ensure_ascii=False).replace('</','<\\/')+'</script>'
        page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>'+title+' — The Golden Hour</title><meta name="description" content="'+esc(text[:150] or event['title'])+'"><link rel="canonical" href="'+page_url+'"><link rel="stylesheet" href="../../assets/gh-event-detail.css">'+structured+'</head><body class="gh-site"><div class="page">'+mast+content+'</div>'+foot+'</body></html>'
        target = root/'events'/key/'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page,encoding='utf-8')
        from build_design import decorate
        decorate(target,None,[],today)
    sitemap=root/'sitemap.xml'
    if sitemap.is_file():
        import xml.etree.ElementTree as ET
        namespace='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',namespace)
        tree=ET.parse(sitemap);urls=tree.getroot();existing={node.text for node in urls.iter('{'+namespace+'}loc')}
        for key in sorted(seen):
            url=SITE+'events/'+key+'/'
            if url not in existing:
                node=ET.SubElement(urls,'{'+namespace+'}url');ET.SubElement(node,'{'+namespace+'}loc').text=url
        tree.write(sitemap,encoding='utf-8',xml_declaration=True)
    return len(seen)


if __name__ == '__main__':
    print('Generated',build(),'internal event pages')
