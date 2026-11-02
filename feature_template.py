"""Magazine destination features: one shared calendar, explicit content evidence."""
from datetime import date, datetime
from html import escape as esc
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from week_scope import DENVER, is_verified, this_week

SITE = 'https://thegoldenhour.guide/'
def load_places(root):
    """Engine-owned registry; absent registry creates no public place pages."""
    path=root/'data/places.json'
    if not path.exists():return {}
    rows=json.loads(path.read_text())
    if not isinstance(rows,list):raise ValueError('Place registry must be a list of records')
    places={}
    for row in rows:
        key=row.get('slug','')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',key) or key in places:raise ValueError('Invalid/duplicate place slug')
        if not row.get('name') or not row.get('character'):raise ValueError('Registry needs name and sourced character line')
        area=row.get('valley',{})
        if not area.get('name') or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',area.get('slug','')):raise ValueError('Registry needs valley name and slug')
        places[key]=row
    return places


def town_key(event,places=None):
    """Only explicit registry keys/names; never infer location from a venue."""
    declared=event.get('place_key') or event.get('town_key') or event.get('town')
    return {p['name']:key for key,p in (places or {}).items()}.get(declared,declared)


def public_url(value):
    parsed=urlparse(value or '')
    return parsed.scheme in ('http','https') and bool(parsed.netloc) and parsed.hostname not in ('example.com','example.org','localhost','127.0.0.1')


def check_source(record,day,preview=False):
    if not public_url(record.get('source_url')) and not preview:
        raise ValueError('A real source URL is required')
    checked=date.fromisoformat(record.get('last_checked',''))
    if checked>day:raise ValueError('Last-checked date cannot be in the future')
    if not preview and record.get('verification')!='CONFIRMED-2026':
        raise ValueError('Unverified editorial material cannot publish')


def validate(feature,rows,root,day,preview=False):
    key=feature.get('town_key');places=load_places(root)
    if key not in places or feature.get('town')!=places[key]['name']:raise ValueError('Unknown registry place or mismatched name')
    if not preview and (feature.get('review_fixture') or feature.get('ready') is not True):
        raise ValueError('Review fixtures and incomplete packets cannot publish')
    if not feature.get('edition'):raise ValueError('Feature edition is required')
    if not feature.get('lede') or not feature.get('editorial_by'):raise ValueError('A sourced editorial lede and editor are required')
    check_source(feature,day,preview)
    entries=feature.get('entries',[])
    if not 1<=len(entries)<=6:raise ValueError('Curate one to six ordered stops')
    groups=[e.get('section') for e in entries]
    if list(dict.fromkeys(groups))!=['STAY','PLAY','EAT'] or groups!=sorted(groups,key=lambda g:['STAY','PLAY','EAT'].index(g) if g in ['STAY','PLAY','EAT'] else 99):raise ValueError('Entries must follow STAY / PLAY / EAT')
    for entry in entries:
        if not entry.get('name') or not entry.get('description'):raise ValueError('Every stop needs a name and short description')
        check_source(entry,day,preview)
    selected=[e for e in rows if e['id']==feature.get('highlight_event_id')]
    if len(selected)!=1:raise ValueError('The one seasonal highlight must reference one canonical event ID')
    highlight=selected[0]
    if town_key(highlight,places)!=key or not is_verified(highlight):raise ValueError('Highlight town/verification does not match the feature')
    if not public_url(highlight.get('url')) and not preview:raise ValueError('Highlight needs its canonical source URL')
    if not preview and not feature.get('highlight_last_checked'):raise ValueError('Highlight needs a last-checked date')
    if date.fromisoformat(feature['highlight_last_checked'])>day:raise ValueError('Highlight last-checked date cannot be in the future')
    if not datetime.fromisoformat(highlight['starts_at']).tzinfo:raise ValueError('Highlight time needs a timezone')
    if datetime.fromisoformat(highlight['starts_at']).astimezone(DENVER).date()<day:raise ValueError('Seasonal highlight has expired')
    if len(feature.get('photos',[]))!=2:raise ValueError('A wide and a tall local photo are required')
    for photo in feature['photos']:
        local=(root/photo['file']).resolve()
        if not local.is_relative_to((root/'assets').resolve() if preview else root.resolve()) or not local.is_file():raise ValueError('Photo must be an existing local asset')
        if local.suffix.lower() not in ('.jpg','.jpeg','.png','.webp'):raise ValueError('Photo must be a supported raster image')
        if not photo.get('alt') or not photo.get('credit') or not photo.get('license_url'):raise ValueError('Photo alt, credit and license/permission evidence are required')
        if re.search(r'ron\s*delhaye',photo['credit']+photo['file'],re.I):raise ValueError('Ron photography is excluded from Golden Hour')
        if not preview:
            if photo.get('place_key')!=key:raise ValueError('Feature photography must belong to this town')
            if not public_url(photo['license_url']):raise ValueError('Photo license/permission URL must be inspectable')
            check_source(photo,day)
    return highlight


def json_ld(value,id):
    return '<script id="'+id+'" type="application/ld+json">'+json.dumps(value,ensure_ascii=False).replace('</','<\\/')+'</script>'


def event_schema(event):
    return {'@context':'https://schema.org','@type':'Event','name':event['title'],'startDate':event['starts_at'],
            'url':SITE+'events/'+event['slug']+'/', 'location':{'@type':'Place','name':event['venue']}}


def breadcrumb_schema(key,places):
    place=places[key];area=place['valley']
    return {'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[
        {'@type':'ListItem','position':1,'name':'Home','item':SITE},
        {'@type':'ListItem','position':2,'name':'Places','item':SITE+'places/'},
        {'@type':'ListItem','position':3,'name':area['name'],'item':SITE+'places/'+area['slug']+'/'},
        {'@type':'ListItem','position':4,'name':place['name'],'item':SITE+'valley/'+key+'/'}]}


ORNAMENT='<svg class="gh-feature-mountain" viewBox="0 0 150 56" aria-hidden="true" focusable="false"><path d="M3 46 35 14 49 29 72 4 102 39 117 23 147 46 M25 24 35 14 40 29 M59 19 72 4 79 24 87 20 M108 33 117 23 123 37" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/></svg>'


def render(feature,rows,root,day,preview=False):
    highlight=validate(feature,rows,root,day,preview)
    key=feature['town_key'];town=feature['town'];places=load_places(root);area=places[key]['valley']
    weekly=this_week([e for e in rows if town_key(e,places)==key],day)
    breadcrumb='<nav class="gh-feature-breadcrumbs" aria-label="Breadcrumb"><ol><li><a href="../../index.html">Home</a></li><li><a href="../../places/">Places</a></li><li><a href="../../places/'+esc(area['slug'])+'/">'+esc(area['name'])+'</a></li><li aria-current="page">'+esc(town)+'</li></ol></nav>'
    back='<nav class="gh-feature-return" aria-label="Back to the guide"><a href="../../upcoming/">This Week</a><a href="../../calendar/">Calendar</a><a href="../../desk/">Concierge</a></nav>'
    entries=''.join('<article class="gh-feature-stop"><p class="gh-feature-kicker">'+esc(e['section'])+'</p><h2><em>'+esc(e['name'])+'</em></h2><p>'+esc(e['description'])+'</p><p class="gh-feature-source"><a href="'+esc(e['source_url'],quote=True)+'" rel="noopener">Source</a> · Checked <time datetime="'+e['last_checked']+'">'+e['last_checked']+'</time></p></article>' for e in feature['entries'])
    when=datetime.fromisoformat(highlight['starts_at']).astimezone(DENVER)
    callout='<aside class="gh-feature-callout" aria-labelledby="feature-callout-title"><p class="gh-feature-kicker">One for the season</p><h2 id="feature-callout-title">'+esc(highlight['title'])+'</h2><p><time datetime="'+esc(highlight['starts_at'],quote=True)+'">'+when.strftime('%a, %b %d · %I:%M %p')+' MT</time><br>'+esc(highlight['venue'])+'</p><p class="gh-feature-source">Source checked <time datetime="'+feature['highlight_last_checked']+'">'+feature['highlight_last_checked']+'</time></p><a href="'+esc(highlight['url'],quote=True)+'" rel="noopener">Official details →</a></aside>'
    photos=''.join('<figure><img src="../../'+esc(p['file'],quote=True)+'" alt="'+esc(p['alt'],quote=True)+'" loading="lazy"/><figcaption>'+esc(p.get('caption',''))+' · '+esc(p['credit'])+' · <a href="'+esc(p['source_url'],quote=True)+'">Source</a> · <a href="'+esc(p['license_url'],quote=True)+'" rel="license">License / permission</a></figcaption></figure>' for p in feature['photos'])
    week_items=''.join('<li data-starts="'+esc(e['starts_at'],quote=True)+'"><time datetime="'+esc(e['starts_at'],quote=True)+'">'+datetime.fromisoformat(e['starts_at']).astimezone(DENVER).strftime('%a, %b %d · %I:%M %p')+' MT</time><a href="../../events/'+esc(e['slug'],quote=True)+'/">'+esc(e['title'])+'</a></li>' for e in weekly)
    empty='<p class="gh-feature-week-empty"'+(' hidden' if weekly else '')+'>No verified listings this week. <a href="../../calendar/">Calendar</a> · <a href="../../events/">Events</a></p>'
    proof='<p class="gh-feature-proof">Layout proof · sample content, not a published Basalt guide.</p>' if preview else ''
    body='<div class="page">'+breadcrumb+back+'<main class="gh-feature" data-feature-town="'+key+'">'+proof+'<header class="gh-feature-head"><p class="gh-feature-kicker">'+esc(feature.get('department','Around the Valley'))+'</p>'+ORNAMENT+'<h1>Destination: <span>'+esc(town)+'</span></h1><p class="gh-feature-byline">By '+esc(feature['editorial_by'])+'</p><p class="gh-feature-lede"><em><strong>Why we love it:</strong> '+esc(feature['lede'])+'</em></p></header><div class="gh-feature-body"><section class="gh-feature-entries" aria-label="Curated stops">'+entries+'</section>'+callout+'</div><section class="gh-feature-week" data-town-key="'+key+'" data-town-name="'+esc(town,quote=True)+'"><h2>This week in '+esc(town)+'</h2><ol>'+week_items+'</ol>'+empty+'</section><div class="gh-feature-photos">'+photos+'</div><div class="gh-feature-folio" role="contentinfo">The Golden Hour · '+esc(feature['edition'])+' · Sources checked '+feature['last_checked']+'</div></main></div>'
    structured=json_ld(breadcrumb_schema(key,places),'feature-breadcrumbs')+json_ld(event_schema(highlight),'feature-highlight')+json_ld({'@context':'https://schema.org','@type':'ItemList','name':'This week in '+town,'itemListElement':[{'@type':'ListItem','position':i+1,'item':event_schema(e)} for i,e in enumerate(weekly)]},'feature-week-events')
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/><title>Destination: '+esc(town)+' — The Golden Hour</title><meta name="description" content="'+esc(feature['lede'],quote=True)+'"/><link rel="canonical" href="'+SITE+'valley/'+key+'/"/>'+('<meta name="robots" content="noindex,nofollow"/>' if preview else '')+structured+'</head><body>'+body+'</body></html>'


def load_ready(root):
    ready=[];seen=set()
    for path in sorted((root/'data/features').glob('*.json')):
        feature=json.loads(path.read_text())
        if feature.get('ready') is not True:continue
        key=feature['town_key']
        if key in seen:raise ValueError('Duplicate feature place')
        seen.add(key);ready.append((path,feature))
    return ready


def feature_links(root):
    return [(key,p['name']) for key,p in load_places(root).items() if p.get('ready') is True and (root/'valley'/key/'index.html').is_file()]


def render_skeleton(place,rows,root,day):
    """An honest, sourced registry entry; no invented stops or photo fillers."""
    if place.get('ready') is not True or place.get('review_fixture'):raise ValueError('Registry record is not ready')
    check_source(place,day)
    places=load_places(root);key=place['slug'];name=place['name']
    weekly=this_week([e for e in rows if town_key(e,places)==key],day)
    crumbs=breadcrumb_schema(key,places)
    trail=''.join('<li>'+('<span aria-current="page">'+esc(x['name'])+'</span>' if x['position']==4 else '<a href="'+esc(x['item'],quote=True)+'">'+esc(x['name'])+'</a>')+'</li>' for x in crumbs['itemListElement'])
    items=''.join('<li data-starts="'+esc(e['starts_at'],quote=True)+'"><time datetime="'+esc(e['starts_at'],quote=True)+'">'+datetime.fromisoformat(e['starts_at']).astimezone(DENVER).strftime('%a, %b %d · %I:%M %p')+' MT</time><a href="../../events/'+esc(e['slug'],quote=True)+'/">'+esc(e['title'])+'</a></li>' for e in weekly)
    body='<div class="page"><nav class="gh-feature-breadcrumbs" aria-label="Breadcrumb"><ol>'+trail+'</ol></nav><main class="gh-feature"><header class="gh-feature-head"><p class="gh-feature-kicker">Around the Valley</p>'+ORNAMENT+'<h1>Destination: '+esc(name)+'</h1><p class="gh-feature-lede">'+esc(place['character'])+'</p></header><section class="gh-feature-week" data-town-key="'+key+'" data-town-name="'+esc(name,quote=True)+'"><h2>This week in '+esc(name)+'</h2><ol>'+items+'</ol><p class="gh-feature-week-empty"'+(' hidden' if weekly else '')+'>No verified listings this week.</p></section><p>Feature coverage is growing.</p><p class="gh-feature-source"><a href="'+esc(place['source_url'],quote=True)+'">Source</a> · Checked '+place['last_checked']+'</p><nav class="gh-feature-return" aria-label="Back to the guide"><a href="../../upcoming/">This Week</a><a href="../../calendar/">Calendar</a><a href="../../desk/">Concierge</a></nav></main></div>'
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/><title>Destination: '+esc(name)+' — The Golden Hour</title><meta name="description" content="'+esc(place['character'],quote=True)+'"/><link rel="canonical" href="'+SITE+'valley/'+key+'/"/>'+json_ld(crumbs,'feature-breadcrumbs')+json_ld({'@context':'https://schema.org','@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'item':event_schema(e)} for i,e in enumerate(weekly)]},'feature-week-events')+'</head><body>'+body+'</body></html>'
