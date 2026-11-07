"""Keep the cached This Week page inside the same Denver edition window."""
def apply(doc,path,root):
    if path.relative_to(root).as_posix() != 'upcoming/index.html':
        return
    if not doc.select_one('script[src$="gh-calendar-sync.js"]'):
        doc.head.append(doc.new_tag('script',src='../assets/gh-calendar-sync.js'))
    if not doc.select_one('script[src$="gh-this-week.js"]'):
        doc.head.append(doc.new_tag('script', src='../assets/gh-this-week.js', defer=''))

    # This is a live surface; the shell must not advertise an older edition.
    grid=doc.select_one('.gh-event-grid')
    if grid:grid.clear()
    date=doc.select_one('.gh-week-range')
    if date:date.clear()
    state=doc.select_one('.gh-list-empty')
    if state:state.string='Finding what’s on…';state.attrs.pop('hidden',None)
    schema=doc.select_one('#gh-event-list')
    if schema:schema.string='{"@context":"https://schema.org","@type":"ItemList","itemListElement":[]}'
