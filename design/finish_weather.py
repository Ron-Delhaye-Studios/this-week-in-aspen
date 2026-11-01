"""Reserve the weather pill without shipping a visible loading sentence."""
def apply(doc,path,root):
    for pill in doc.select('.gh-weather'):
        if 'Loading weather' in pill.get_text():pill.clear()
        pill['aria-busy']='true'
        pill['aria-label']='Aspen weather'
