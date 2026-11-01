"""Extend the approved homepage shell without regenerating editorial content."""
from pathlib import Path
from bs4 import BeautifulSoup

def apply(doc,path,root):
    route=path.relative_to(root).as_posix()
    if route=='index.html':
        return
    prefix='../'*(len(path.relative_to(root).parts)-1)
    mast=doc.select_one('header.masthead')
    if not mast:return
    # Retain all page-specific masthead children outside the shared wordmark.
    retained=[]
    for child in list(mast.children):
        if getattr(child,'name',None) and not set(child.get('class',[])) & {'gh-top','brand','kicker','rule-double','site-nav','gh-mast-sub'}:
            retained.append(child.extract())
    for old in doc.select('.gh-top'):old.decompose()
    top=BeautifulSoup('<div class="gh-top gh-topbar"><div class="gh-topbar-in"><span class="gh-top-left"><time class="gh-date">Aspen, Colorado</time><span class="gh-weather" role="status">Aspen · Loading weather…</span></span><span class="gh-top-right"><button class="gh-theme-toggle" type="button" aria-label="Dark theme" aria-pressed="false">Theme</button></span></div></div>','html.parser')
    doc.body.insert(0,top.div.extract())
    nav=mast.select_one('nav.site-nav')
    if nav:nav.extract()
    mast.clear()
    head=BeautifulSoup(f'<p class="kicker gh-eyebrow"><span class="rule double"></span><span class="gh-kicker-text">FROM ASPEN AND BEYOND</span><span class="rule double"></span></p><p class="brand"><a href="{prefix}index.html" aria-label="The Golden Hour — home"><span class="l1">THE GOLDEN</span> <span class="l2"><em>HOUR</em></span></a></p><div class="gh-mast-sub"></div>','html.parser')
    for child in list(head.contents):mast.append(child.extract())
    if nav:mast.select_one('.gh-mast-sub').append(nav)
    if not doc.find('h1'):mast.select_one('.brand').name='h1'
    for child in reversed(retained):mast.insert_after(child)
    foot=doc.select_one('.gh-footer')
    if foot:
        from build_design import footer_navigation
        current=route.replace('index.html','') or 'index.html'
        canonical=BeautifulSoup(footer_navigation(prefix,current),'html.parser').nav
        old_nav=foot.select_one('nav')
        if old_nav:old_nav.replace_with(canonical)
        else:foot.insert(0,canonical)
    if foot and not foot.select_one('.gh-foot-word'):
        front=BeautifulSoup('<p class="gh-foot-word">THE GOLDEN <em>HOUR</em></p><p class="gh-foot-meta"><span>From Aspen and Beyond</span><span>Verified before publication</span></p>','html.parser')
        for child in reversed(list(front.contents)):foot.insert(0,child.extract())
    css=doc.select_one('link[href$="gh-chrome.css"]')
    if css:css.extract()
    doc.head.append(css or doc.new_tag('link',rel='stylesheet',href=prefix+'assets/gh-chrome.css'))

def link_family(doc,path,root):
    route=path.relative_to(root)
    family=route.parts[0] if len(route.parts)>1 else route.stem
    asset='assets/gh-page-'+family+'.css'
    if (root/asset).exists():
        href='../'*(len(route.parts)-1)+asset
        css=doc.find('link',href=href)
        if css:css.extract()
        doc.head.append(css or doc.new_tag('link',rel='stylesheet',href=href))

def finish(doc,path,root):
    import importlib
    apply(doc,path,root)
    for module in sorted((root/'design').glob('finish_*.py')):
        importlib.import_module('design.'+module.stem).apply(doc,path,root)
    link_family(doc,path,root)
    # Removed generated head tags must not leave one extra blank node per build.
    for child in list(doc.head.children):
        if not getattr(child, 'name', None) and not str(child).strip():child.extract()

def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--routes', nargs='+', help='Only these route roots; does not regenerate feeds or editorial lists')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    for path in root.rglob('*.html'):
        if '.git' in path.parts:continue
        route=path.relative_to(root).as_posix()
        if route=='index.html':continue
        if args.routes and not any(route==r or route.startswith(r.rstrip('/')+'/') for r in args.routes):continue
        doc=BeautifulSoup(path.read_text(),'html.parser')
        if not doc.body or not doc.head:continue
        finish(doc,path,root)
        path.write_text(str(doc).rstrip()+'\n')
if __name__=='__main__':main()
