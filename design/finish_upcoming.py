"""Keep the cached This Week page inside the same Denver edition window."""
def apply(doc,path,root):
    if path.relative_to(root).as_posix() != 'upcoming/index.html':
        return
    if not doc.select_one('script[src$="gh-this-week.js"]'):
        doc.head.append(doc.new_tag('script', src='../assets/gh-this-week.js', defer=''))
