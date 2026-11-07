"""Keep the approved composition live as its editorial window expires."""
def apply(doc,path,root):
    if path.relative_to(root).as_posix()!='index.html':return
    if not doc.select_one('script[src$="gh-calendar-sync.js"]'):
        doc.head.append(doc.new_tag('script',src='assets/gh-calendar-sync.js'))
    if not doc.select_one('script[src$="gh-home-live.js"]'):
        doc.head.append(doc.new_tag('script',src='assets/gh-home-live.js',defer=''))

    # The current calendar belongs to the runtime adapter, never a baked edition.
    section=doc.select_one('.gh-week')
    if section:
        for key in list(section.attrs):
            if key.startswith('data-ed-') or key in ('data-window-end','data-horizon'):del section[key]
        for node in section.select('.gh-sec-meta'):node.clear()
        lead=section.select_one('.gh-lead')
        if lead:
            lead['hidden']=''
            for node in lead.select('img,.gh-lead-image-link'):node.decompose()
            for node in lead.select('h3,.gh-lead-k,.gh-lead-body>p:not(.gh-lead-k)'):node.clear()
            lead.attrs.pop('data-starts',None)
            link=lead.select_one('a.gh-btn-solid')
            if link:link['href']='upcoming/'
        rows=section.select_one('.gh-rows')
        if rows:
            rows.clear();notice=doc.new_tag('p',attrs={'class':'gh-list-empty','role':'status'});notice.string='Finding what’s on…';rows.append(notice)
        filters=section.select_one('.gh-filters')
        if filters:filters.clear();filters['hidden']=''
