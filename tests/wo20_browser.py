"""Labeled private layout proofs; no real town editorial content is asserted."""
import json
import os
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).parent))
import datetime as dt
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
REMOTE={}
def timestamp(value):return int(dt.datetime.fromisoformat(value).timestamp()*1000)


def clock(context,when,theme=None):
    context.add_init_script('''window.__ghNow = %d;
      const NativeDate=Date;window.Date=class extends NativeDate{
        constructor(...args){super(...(args.length?args:[window.__ghNow]))}
        static now(){return window.__ghNow}
      };'''%timestamp(when))
    if theme:context.add_init_script('localStorage.setItem("gh-theme",'+json.dumps(theme)+')')


def networking(context,feed):
    def handle(route):
        url=route.request.url
        if '/data/events.json' in url:return route.fulfill(json=feed)
        if 'api.open-meteo.com' in url:return route.fulfill(json={'current':{'temperature_2m':45,'weather_code':2,'time':'2026-11-01T18:00'}})
        if 'fonts.googleapis.com' in url or 'fonts.gstatic.com' in url:
            try:
                if url not in REMOTE:
                    with urllib.request.urlopen(url,timeout=15) as response:REMOTE[url]=(response.read(),response.headers.get('Content-Type'))
                data,kind=REMOTE[url];return route.fulfill(body=data,content_type=kind)
            except Exception:return route.abort()
        if url.startswith(BASE):return route.continue_()
        return route.abort()
    context.route('**/*',handle)



BASE='http://127.0.0.1:8783/'

OUT=ROOT/'design/review/wo20';OUT.mkdir(parents=True,exist_ok=True)
feed=json.loads((ROOT/'tests/fixtures/feature-events-review.json').read_text())
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
    for width in (390,1440):
        for theme in ('light','dark'):
            context=browser.new_context(viewport={'width':width,'height':844},device_scale_factor=1)
            clock(context,'2026-11-01T18:00:00-07:00',theme);networking(context,feed)
            page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(BASE+'valley/basalt/',wait_until='networkidle');page.evaluate('document.fonts.ready')
            page.locator('.gh-feature-photos').scroll_into_view_if_needed();page.wait_for_timeout(300);page.evaluate('scrollTo(0,0)')
            state=page.evaluate('''()=>({overflow:document.documentElement.scrollWidth>innerWidth,broken:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),columns:getComputedStyle(document.querySelector('.gh-feature-body')).gridTemplateColumns,weekly:[...document.querySelectorAll('.gh-feature-week li')].map(e=>e.textContent),theme:document.documentElement.dataset.theme})''')
            assert not state['overflow'] and not state['broken'] and not errors,(state,errors)
            assert len(state['weekly'])==1,state
            assert 'Sample' in state['weekly'][0]
            page.screenshot(path=str(OUT/f'feature-{width}-{theme}.png'),full_page=True)
            # Runtime rollover removes previous-week sample data, including schema.
            page.evaluate('window.__ghNow=Date.parse("2026-11-08T18:00:00-07:00");dispatchEvent(new Event("pageshow"))');page.wait_for_timeout(200)
            assert page.locator('.gh-feature-week li:not([hidden])').count()==0
            assert json.loads(page.locator('#feature-week-events').text_content())['itemListElement']==[]
            results.append({'width':width,'theme':theme,**state,'page_errors':errors,'rollover':'PASS'})
            context.close()
    browser.close()
(OUT/'browser-results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
