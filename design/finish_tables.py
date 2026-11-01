"""Semantic table records on phones, source wording preserved."""
def apply(doc,path,root):
    if path.relative_to(root).as_posix() not in ('desk/index.html','sources/index.html'):return
    for table in doc.select('table.desk,table.src'):
        rows=table.find_all('tr')
        if not rows:continue
        headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['td','th'],recursive=False)]
        for h in rows[0].find_all('th'):h['scope']='col'
        if not table.thead:
            head=doc.new_tag('thead');head.append(rows[0].extract());table.insert(0,head)
        if not table.tbody:
            body=doc.new_tag('tbody')
            for row in table.find_all('tr',recursive=False):body.append(row.extract())
            table.append(body)
        table['role']='table'
        for row in table.tbody.find_all('tr',recursive=False):
            row['role']='row'
            for i,cell in enumerate(row.find_all(['td','th'],recursive=False)):
                cell['role']='cell';cell['data-label']=headers[i]
