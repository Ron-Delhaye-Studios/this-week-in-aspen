#!/usr/bin/env python3
"""Build evidence-complete town features; preview fixtures stay outside the site."""
import argparse
from datetime import datetime
import json
from pathlib import Path

from feature_template import DENVER, SITE, load_ready, render, load_places, render_skeleton

ROOT=Path(__file__).resolve().parent


def hub(features,preview=False,title='Places',route='places/'):
    from html import escape
    links=''.join('<li><a href="/valley/'+f['town_key']+'/">Destination: '+escape(f['town'])+'</a></li>' for f in features)
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/><title>'+escape(title)+' — The Golden Hour</title><link rel="canonical" href="'+SITE+route+'"/>'+('<meta name="robots" content="noindex,nofollow"/>' if preview else '')+'</head><body><div class="page"><main class="gh-feature"><p class="gh-feature-kicker">Around the Valley</p><h1>'+escape(title)+'</h1><ul>'+links+'</ul><p><a href="/upcoming/">This Week</a> · <a href="/calendar/">Calendar</a> · <a href="/desk/">Concierge</a></p></main></div></body></html>'


def build_ready(root,rows,day):
    ready=load_ready(root);places=load_places(root)
    documents={}
    for key,place in places.items():
        if place.get('ready') is True:documents[root/'valley'/key/'index.html']=render_skeleton(place,rows,root,day)
    for _,feature in ready:
        if feature['town_key'] not in places or places[feature['town_key']].get('ready') is not True:raise ValueError('Feature requires ready engine place')
        documents[root/'valley'/feature['town_key']/'index.html']=render(feature,rows,root,day)
    if documents:
        all_places=[{'town_key':k,'town':p['name']} for k,p in places.items() if p.get('ready') is True]
        documents[root/'places/index.html']=hub(all_places)
        for area in {p['valley']['slug'] for p in places.values() if p.get('ready') is True}:
            subset=[{'town_key':k,'town':p['name']} for k,p in places.items() if p.get('ready') is True and p['valley']['slug']==area]
            area_name=next(p['valley']['name'] for p in places.values() if p['valley']['slug']==area)
            documents[root/'places'/area/'index.html']=hub(subset,title=area_name,route='places/'+area+'/')
    for path,html in documents.items():path.parent.mkdir(parents=True,exist_ok=True);path.write_text(html+'\n')
    if documents and (root/'sitemap.xml').is_file():
        import xml.etree.ElementTree as ET
        namespace='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',namespace)
        tree=ET.parse(root/'sitemap.xml');urlset=tree.getroot()
        existing={node.text for node in urlset.iter('{'+namespace+'}loc')}
        for path in documents:
            url=SITE+path.relative_to(root).as_posix().removesuffix('index.html')
            if url not in existing:
                node=ET.SubElement(urlset,'{'+namespace+'}url');ET.SubElement(node,'{'+namespace+'}loc').text=url
        tree.write(root/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    return list(documents)


def preview(file,output,day):
    import build_design as design
    feature=json.loads(file.read_text())
    if output.resolve().is_relative_to(ROOT):raise ValueError('Review fixtures must render outside the published checkout')
    output.mkdir(parents=True,exist_ok=True)
    for name in ['assets','icons','design','off-season']:
        link=output/name
        if not link.exists():link.symlink_to(ROOT/name,target_is_directory=True)
    rows=json.loads((ROOT/'tests/fixtures/feature-events-review.json').read_text())
    (output/'data').mkdir(exist_ok=True)
    (output/'data/events.json').write_text(json.dumps(rows))
    (output/'data/places.json').write_text((ROOT/'tests/fixtures/places-review.json').read_text())
    documents={output/'valley'/feature['town_key']/'index.html':render(feature,rows,output,day,preview=True),output/'places/index.html':hub([feature],True),output/'places/roaring-fork/index.html':hub([feature],True,'Roaring Fork Valley','places/roaring-fork/')}
    previous=design.ROOT
    try:
        design.ROOT=output
        for path,html in documents.items():
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(html+'\n');design.decorate(path,None,rows,day)
    finally:design.ROOT=previous
    return list(documents)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--as-of',default=datetime.now(DENVER).date().isoformat())
    args=parser.parse_args();day=datetime.fromisoformat(args.as_of).date()
    if args.preview:
        if not args.output:parser.error('--preview requires an output directory outside the checkout')
        paths=preview(args.preview,args.output,day)
    else:paths=build_ready(ROOT,json.loads((ROOT/'data/events.json').read_text()),day)
    print(f'{len(paths)} feature documents built; no canonical event files changed.')


if __name__=='__main__':main()
