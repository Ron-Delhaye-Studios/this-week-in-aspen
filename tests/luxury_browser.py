"""Phone/desktop luxury-pass acceptance; Chromium is not physical iOS."""
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
feed=json.loads((ROOT/'data/events.json').read_text())
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
 for width in (390,1440):
  for theme in ('light','dark'):
   c=browser.new_context(viewport={'width':width,'height':844},device_scale_factor=1)
   clock(c,'2026-11-01T18:00:00-07:00',theme);networking(c,feed)
   page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(BASE,wait_until='networkidle');page.evaluate('document.fonts.ready')
   
   for image in page.locator('img').all():
    image.scroll_into_view_if_needed();page.wait_for_timeout(80)
   page.evaluate('scrollTo(0,0)')
   nav=page.locator('.masthead nav')
   state=page.evaluate("""()=>({overflow:document.documentElement.scrollWidth>innerWidth,broken:[...document.images].filter(i=>!i.complete&&i.loading!=='lazy'||i.complete&&!i.naturalWidth).map(i=>i.src),navRows:new Set([...document.querySelectorAll('.masthead nav a')].map(a=>Math.round(a.getBoundingClientRect().y))).size,navScroll:document.querySelector('.masthead nav').scrollWidth>document.querySelector('.masthead nav').clientWidth,duplicate:document.querySelectorAll('.gh-top-loc').length,tabular:getComputedStyle(document.querySelector('.gh-date')).fontVariantNumeric,background:getComputedStyle(document.querySelector('.gh-top')).backgroundColor,body:getComputedStyle(document.body).backgroundColor,heading:document.querySelector('.gh-week h2').textContent,rows:document.querySelectorAll('.gh-row:not([hidden])').length,credits:document.querySelector('.gh-credits').textContent,theme:document.documentElement.dataset.theme})""")
   assert not state['overflow'] and not state['broken'] and not errors,(state,errors)
   assert state['duplicate']==0 and state['tabular']=='tabular-nums',state
   assert state['rows']==5 and 'Next on the Calendar'==state['heading']
   assert 'Lorie Shaull' in state['credits'] and 'Jeffrey Beall' not in state['credits']
   if theme=='light':assert state['background']==state['body']
   if width==390:
    assert state['navRows']==1 and state['navScroll'],state
    nav.locator('a').last.focus();assert page.evaluate("document.querySelector('.masthead nav').scrollLeft>0")
    nav.locator('a').first.focus();page.locator('.gh-theme-toggle').focus();nav.evaluate('(e)=>e.scrollLeft=0')
   page.add_script_tag(path=os.environ.get('AXE_PATH','/workspace/lux-tools/node_modules/axe-core/axe.min.js'))
   aa=page.evaluate("async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});return r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))}")
   state['axe_violations']=aa
   assert aa==[],aa
   page.screenshot(path=str(OUT/f'home-{width}-{theme}.png'),full_page=True)
   # Live cover swap, credit deduplication and hidden-plate removal.
   page.locator('.gh-cover-frame img').evaluate("e=>e.src='assets/img/lead-ute-cemetery.jpg'")
   page.wait_for_function("document.querySelector('.gh-credits').textContent.includes('Jeffrey Beall')&&!document.querySelector('.gh-credits').textContent.includes('Lorie Shaull')")
   assert 'Jeffrey Beall' in page.locator('.gh-cover-credit').text_content()
   page.locator('.gh-cover-frame').evaluate('e=>e.hidden=true');page.wait_for_function("!document.querySelector('.gh-credits').textContent.includes('Jeffrey Beall')")
   # Advance beyond all feed events: positive guide actions, no invented listings.
   page.evaluate('window.__ghNow=Date.parse("2027-02-01T18:00:00-07:00");dispatchEvent(new Event("pageshow"))');page.wait_for_timeout(200)
   assert page.locator('.gh-row:not([hidden])').count()==0
   assert 'Top Picks' in page.locator('.gh-week .gh-list-empty').text_content()
   assert 'No verified' not in page.locator('.gh-week').text_content()
   results.append({'width':width,'mode':theme,**state,'page_errors':errors,'credit_swap':'PASS','exhausted_feed':'PASS'})
   c.close()
 # Fresh device preferring dark must still default to warm paper; stored choice persists.
 c=browser.new_context(viewport={'width':390,'height':844},color_scheme='dark',service_workers='block')
 clock(c,'2026-11-01T18:00:00-07:00');networking(c,feed);page=c.new_page();page.goto(BASE,wait_until='networkidle')
 assert page.evaluate('document.documentElement.dataset.theme')=='light'
 page.locator('.gh-theme-toggle').click();page.reload(wait_until='networkidle');assert page.evaluate('document.documentElement.dataset.theme')=='dark'
 page.goto(BASE+'upcoming/',wait_until='networkidle');assert page.locator('h1').text_content()=='This Week';assert page.locator('.gh-event-card:not([hidden])').count()==0
 assert page.locator('.masthead nav').evaluate("e=>new Set([...e.children].map(a=>a.getBoundingClientRect().y)).size")==1
 c.close()
 # Offline server fallback retains its labeled horizon, then prunes expired rows.
 c=browser.new_context(viewport={'width':390,'height':844},service_workers='block')
 clock(c,'2026-11-01T18:00:00-07:00');networking(c,feed);c.route('**/data/events.json',lambda route:route.abort())
 page=c.new_page();page.goto(BASE,wait_until='networkidle');assert page.locator('.gh-row:not([hidden])').count()==5
 page.evaluate('window.__ghNow=Date.parse("2026-11-15T18:00:00-07:00");dispatchEvent(new Event("pageshow"))');page.wait_for_timeout(150)
 assert page.locator('.gh-row:not([hidden])').count()==4
 assert page.locator('.gh-week h2').text_content()=='Next on the Calendar'
 c.close()
 results.append({'fresh_OS_dark_defaults_light':'PASS','manual_dark_persists':'PASS','This_Week_stays_strict':'PASS','offline_horizon_pruning':'PASS','inner_mobile_nav':'PASS'})
 browser.close()
(OUT/'browser-results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
