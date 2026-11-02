"""Credit the registered CC plates actually present, including a changing lead."""
import json
from html import escape
from urllib.parse import urljoin, urlparse, unquote


def credit_html(record):
    return escape(record['title'])+' — '+escape(record['author'])+', <a href="'+escape(record['license_url'],quote=True)+'" rel="license">'+escape(record['license'])+'</a>'


def apply(doc,path,root):
    registry=json.loads((root/'data/image-credits.json').read_text()) if (root/'data/image-credits.json').exists() else []
    if not registry:return
    from bs4 import BeautifulSoup
    for node in doc.select('.gh-footer .gh-credits,#gh-credit-map'):node.decompose()
    route=path.relative_to(root).as_posix();prefix='../'*(len(path.relative_to(root).parts)-1)
    def key(image):
        url=urlparse(urljoin('https://thegoldenhour.guide/'+route,image.get('src','')))
        return unquote(url.path).removeprefix('/this-week-in-aspen').lstrip('/') if url.hostname=='thegoldenhour.guide' else ''
    rendered={key(image) for image in doc.select('img[src]') if not image.has_attr('hidden') and not image.find_parent(attrs={'hidden':True})}
    matched=[record for record in registry if record['file'] in rendered]
    if not matched and route!='index.html':
        for node in doc.select('script[src$="gh-image-credits.js"]'):node.decompose()
        return
    footer=doc.select_one('.gh-footer')
    if footer and matched:
        node=doc.new_tag('p',attrs={'class':'gh-credits'});node.append(BeautifulSoup('Image credits: '+' · '.join(credit_html(record) for record in matched),'html.parser'))
        footer.append(node)
    cover=doc.select_one('.gh-cover-frame img')
    caption=doc.select_one('.gh-cover-credit')
    if caption and cover:
        record=next((r for r in registry if r['file']==key(cover)),None)
        caption.clear()
        if record:
            caption.append(BeautifulSoup('Cover: '+credit_html(record)+('. '+escape(record['note']) if record.get('note') else ''),'html.parser'))
    script=doc.new_tag('script',id='gh-credit-map',type='application/json');script.string=json.dumps(registry,ensure_ascii=False).replace('</','<\\/');doc.head.append(script)
    if not doc.select_one('script[src$="gh-image-credits.js"]'):doc.head.append(doc.new_tag('script',src=prefix+'assets/gh-image-credits.js',defer=''))
