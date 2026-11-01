"""Compose existing event headings; leave all event fields and data unchanged."""
def apply(doc,path,root):
    route=path.relative_to(root).as_posix()
    if not route.startswith('events/'):return
    if route!='events/index.html' and not doc.select_one('.gh-event-title-block'):
        title=doc.select_one('h1.ev-title')
        if title:
            block=doc.new_tag('header',attrs={'class':'gh-event-title-block'})
            title.insert_before(block)
            kicker=title.find_previous_sibling('p',class_='kicker')
            if kicker:block.append(kicker.extract())
            block.append(title.extract())
    prefix='../'*(len(path.relative_to(root).parts)-1)
    if not doc.select_one('script[src$="gh-event-media.js"]'):
        doc.head.append(doc.new_tag('script',src=prefix+'assets/gh-event-media.js'))
