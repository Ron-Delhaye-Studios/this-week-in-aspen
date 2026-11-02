"""Expose only built, complete features; never add towns to the main menu."""
from feature_template import feature_links, load_places, breadcrumb_schema, event_schema, json_ld, town_key, SITE
import json
from html import escape


def apply(doc,path,root):
    from bs4 import BeautifulSoup
    route=path.relative_to(root).as_posix()
    prefix='../'*(len(path.relative_to(root).parts)-1)
    links=feature_links(root)
    for old in doc.select('.gh-valley-discovery,.gh-valley-footer'):old.decompose()
    if links:
        anchors=''.join('<li><a href="'+prefix+'valley/'+key+'/">'+escape(town)+'</a></li>' for key,town in links)
        if route in ('index.html','events/index.html'):
            section=BeautifulSoup('<section class="gh-valley-discovery"><h2>Down the Valley</h2><ul>'+anchors+'</ul></section>','html.parser').section
            (doc.select_one('.page') or doc.body).append(section)
        footer=doc.select_one('.gh-footer')
        if footer:footer.append(BeautifulSoup('<nav class="gh-valley-footer" aria-label="Down the Valley"><ul>'+anchors+'</ul></nav>','html.parser').nav)
    if links and route in ('index.html','events/index.html'):
        href=prefix+'assets/gh-page-valley.css'
        if not doc.find('link',href=href):doc.head.append(doc.new_tag('link',rel='stylesheet',href=href))
    if links and route.startswith('events/') and route!='events/index.html':
        source=root/'data/events.json'
        rows=json.loads(source.read_text()) if source.exists() else []
        event=next((e for e in rows if route=='events/'+e['slug']+'/index.html' and town_key(e,load_places(root)) in dict(links)),None)
        if event:
            key=town_key(event,load_places(root));town=dict(links)[key]
            href=prefix+'assets/gh-page-valley.css'
            if not doc.find('link',href=href):doc.head.append(doc.new_tag('link',rel='stylesheet',href=href))
            for node in doc.select('.gh-feature-breadcrumbs,#feature-breadcrumbs'):node.decompose()
            crumbs=BeautifulSoup('<nav class="gh-feature-breadcrumbs" aria-label="Breadcrumb"><ol><li><a href="'+prefix+'index.html">Home</a></li><li><a href="'+prefix+'places/">Places</a></li><li><a href="'+prefix+'places/'+load_places(root)[key]['valley']['slug']+'/">'+escape(load_places(root)[key]['valley']['name'])+'</a></li><li><a href="'+prefix+'valley/'+key+'/">'+escape(town)+'</a></li><li aria-current="page">Event</li></ol></nav>','html.parser').nav
            heading=doc.select_one('h1')
            if heading:heading.insert_before(crumbs)
            data=breadcrumb_schema(key,load_places(root))
            data['itemListElement'].append({'@type':'ListItem','position':5,'name':event['title'],'item':SITE+'events/'+event['slug']+'/'})
            doc.head.append(BeautifulSoup(json_ld(data,'feature-breadcrumbs'),'html.parser'))
            has_event=False
            for script in doc.select('script[type="application/ld+json"]'):
                try:
                    if json.loads(script.string or '{}').get('@type')=='Event':has_event=True
                except (ValueError,AttributeError):pass
            if not has_event:doc.head.append(BeautifulSoup(json_ld(event_schema(event),'feature-canonical-event'),'html.parser'))
    if route.startswith('valley/'):

        if not doc.select_one('script[src$="gh-week.js"]'):
            helper=doc.new_tag('script',src=prefix+'assets/gh-week.js')
            theme=doc.select_one('script[src$="gh-theme.js"]')
            if theme:theme.insert_before(helper)
            else:doc.head.append(helper)
        if doc.select_one('.gh-feature-week') and not doc.select_one('script[src$="gh-feature-live.js"]'):
            doc.head.append(doc.new_tag('script',src=prefix+'assets/gh-feature-live.js',defer=''))
