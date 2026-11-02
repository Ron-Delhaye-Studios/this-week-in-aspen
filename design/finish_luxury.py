"""Presentation polish shared by the homepage and inner-page shells."""
def apply(doc,path,root):
    prefix='../'*(len(path.relative_to(root).parts)-1)
    href=prefix+'assets/gh-luxury-polish.css'
    for node in doc.select('.gh-top-loc'):node.decompose()
    if not doc.find('link',href=href):
        link=doc.new_tag('link',rel='stylesheet',href=href)
        family=path.relative_to(root).parts[0] if len(path.relative_to(root).parts)>1 else path.stem
        family_css=doc.find('link',href=prefix+'assets/gh-page-'+family+'.css')
        if family_css:family_css.insert_before(link)
        else:doc.head.append(link)
