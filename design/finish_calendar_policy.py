"""Apply shared runtime policy after legacy builders; never alter source exports."""
from bs4 import BeautifulSoup

TRUST = 'Checked at the source · refreshed daily · validated when published.'


def apply(doc, path, root):
    route = path.relative_to(root).as_posix()
    prefix = '../' * (len(path.relative_to(root).parts)-1)
    if route in ('events/index.html', 'map/index.html'):
        if not doc.select_one('script[src$="gh-calendar-sync.js"]'):
            doc.head.append(doc.new_tag('script', src=prefix+'assets/gh-calendar-sync.js'))
    if route == 'map/index.html':
        for control in doc.select('[data-range="past"]'):
            control.decompose()
    if route == 'events/index.html':
        grid = doc.select_one('.gh-event-grid')
        if grid:
            grid.clear()
            grid['data-gh-scope'] = 'all'
        schema = doc.select_one('#gh-event-list')
        if schema:
            schema.string = '{"@context":"https://schema.org","@type":"ItemList","itemListElement":[]}'
        if not doc.select_one('.gh-list-empty') and grid:
            state = doc.new_tag('p', attrs={'class':'gh-list-empty','role':'status'})
            state.string = 'Finding what’s on…'
            grid.insert_after(state)
        if not doc.select_one('script[src$="gh-this-week.js"]'):
            doc.head.append(doc.new_tag('script', src=prefix+'assets/gh-this-week.js', defer=''))
    policy = prefix+'assets/gh-event-policy.js'
    if doc.select_one('.gh-sync-detail') and not doc.select_one('script[src$="gh-event-detail-live.js"]'):
        doc.head.append(doc.new_tag('script', src=prefix+'assets/gh-event-detail-live.js', defer=''))
    # Adapter can be inserted by a later finisher. Policy always executes first.
    needs_policy = route in ('index.html','upcoming/index.html','events/index.html','calendar/index.html','map/index.html') or doc.select_one('.gh-sync-detail')
    if needs_policy and not doc.find('script', src=policy):
        doc.head.insert(0, doc.new_tag('script', src=policy))
    if not needs_policy:
        for script in doc.select('script[src$="gh-event-policy.js"]'):
            script.decompose()
    for section in doc.select('.gh-verify'):
        short = doc.new_tag('p', attrs={'class':'gh-trust-line'})
        short.string = TRUST
        section.replace_with(short)
    foot = doc.select_one('.gh-footer')
    if foot:
        for span in foot.select('.gh-foot-meta span'):
            if span.get_text(strip=True) == 'Verified before publication':
                span.decompose()
        for paragraph in foot.find_all('p', recursive=False):
            if 'Every event verified against official sources' in paragraph.get_text():
                paragraph.string = TRUST
    if route == 'sources/index.html':
        if doc.title:
            doc.title.string = 'About the guide — The Golden Hour'
        main = doc.select_one('main') or doc.select_one('.page')
        if main:
            # Source methodology belongs in the agent documents, not guest copy.
            body = BeautifulSoup('<main class="page"><h1>About the guide</h1><p>'+TRUST+'</p><p>Explore Aspen and the Roaring Fork Valley.</p><p><a href="../upcoming/">See what’s on this week →</a></p></main>', 'html.parser').main
            mast = main.select_one('header.masthead')
            if mast:
                body.insert(0, mast.extract())
            main.replace_with(body)
    for anchor in doc.select('a[href$="sources/"]'):
        if anchor.get_text(strip=True) == 'How we verify':
            anchor.string = 'About the guide'
