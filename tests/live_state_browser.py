"""Unchanged refresh must preserve interaction; Denver rollover still prunes."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
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



BASE='http://127.0.0.1:8784/'
OUT=ROOT/'design/review/luxury';OUT.mkdir(parents=True,exist_ok=True)
original=json.loads((ROOT/'data/events.json').read_text())[0]
feed=[dict(original,id='qa-music',slug='qa-music',title='QA music',category='music',price_info='Free',starts_at='2026-11-03T18:00:00-07:00'),dict(original,id='qa-art',slug='qa-art',title='QA art',category='arts',starts_at='2026-11-04T18:00:00-07:00')]
results=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
 for theme in ('light','dark'):
  c=b.new_context(viewport={'width':390,'height':844},service_workers='block');clock(c,'2026-11-01T18:00:00-07:00',theme);networking(c,feed)
  c.add_init_script("window.__minute=[];const nativeInterval=window.setInterval;window.setInterval=(fn,ms,...args)=>{if(ms===60000)window.__minute.push(fn);return nativeInterval(fn,ms,...args)}")
  page=c.new_page();page.goto(BASE+'upcoming/',wait_until='networkidle')
  page.locator('.gh-card-details summary').first.click();page.locator('.gh-copy').first.focus()
  page.evaluate("window.__details=document.querySelector('.gh-card-details');window.__focus=document.activeElement;dispatchEvent(new Event('pageshow'));document.dispatchEvent(new Event('visibilitychange'));window.__minute.forEach(fn=>fn())")
  page.wait_for_timeout(150)
  assert page.evaluate("window.__details===document.querySelector('.gh-card-details')&&window.__details.open&&window.__focus===document.activeElement")
  chip=page.locator('button[data-filter=music]');chip.focus();chip.click();assert page.locator('.gh-event-card:not([hidden])').count()==1
  assert page.evaluate("document.activeElement.dataset.filter==='music'")
  assert page.locator('.gh-card-details').first.get_attribute('open') is not None
  page.evaluate('window.__ghNow=Date.parse("2026-11-08T18:00:00-07:00");dispatchEvent(new Event("pageshow"))');page.wait_for_timeout(150)
  assert page.locator('.gh-event-card:not([hidden])').count()==0
  assert json.loads(page.locator('#gh-event-list').text_content())['itemListElement']==[]
  page.evaluate('window.__ghNow=Date.parse("2026-11-01T18:00:00-07:00")');page.goto(BASE,wait_until='networkidle')
  page.locator('.gh-filters button[data-filter=music]').focus()
  page.evaluate("window.__lead=document.querySelector('.gh-lead img');window.__row=document.querySelector('.gh-row');window.__focus=document.activeElement;dispatchEvent(new Event('pageshow'));window.__minute.forEach(fn=>fn())")
  page.wait_for_timeout(150)
  assert page.evaluate("window.__lead===document.querySelector('.gh-lead img')&&window.__row===document.querySelector('.gh-row')&&window.__focus===document.activeElement")
  page.locator('.gh-filters button[data-filter=music]').click();assert page.locator('.gh-row:not([hidden])').count()==1
  assert page.evaluate("window.__lead===document.querySelector('.gh-lead img')&&document.activeElement.dataset.filter==='music'")
  results.append({'theme':theme,'details_and_focus_after_minute_pageshow_visibility':'PASS','filter_focus_and_details_preserved':'PASS','rollover_prunes_HTML_and_JSONLD':'PASS','unchanged_home_lead_and_rows_retained':'PASS','home_filter_focus':'PASS'})
  c.close()
 b.close()
(OUT/'live-state-results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
