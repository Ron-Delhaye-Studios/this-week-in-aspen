"""Keep the approved composition live as its editorial window expires."""
def apply(doc,path,root):
    if path.relative_to(root).as_posix()!='index.html':return
    if not doc.select_one('script[src$="gh-home-live.js"]'):
        doc.head.append(doc.new_tag('script',src='assets/gh-home-live.js',defer=''))
