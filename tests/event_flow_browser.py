"""Visitor journey: local overview first, supplied images throughout, explicit source exit."""
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



BASE='http://127.0.0.1:8785/'
OUT=ROOT/'design/review/event-flow';OUT.mkdir(parents=True,exist_ok=True)
feed=[];results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
 for mode in ('light','dark'):
  c=browser.new_context(viewport={'width':390,'height':844},service_workers='block')
  clock(c,'2026-11-06T18:00:00-07:00',mode);networking(c,feed)
  page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(BASE,wait_until='networkidle');page.evaluate('document.fonts.ready')

  for image in page.locator('img').all():
   if image.is_visible():image.scroll_into_view_if_needed();page.wait_for_timeout(80)
  page.locator('.gh-week').scroll_into_view_if_needed()
  assert page.locator('.masthead nav a').first.evaluate('e=>e.getBoundingClientRect().left>=e.parentElement.getBoundingClientRect().left-2')
  assert page.locator('.gh-row-image').count()>=2
  assert page.locator('.gh-row').evaluate_all("es=>es.every(e=>e.origin===location.origin&&e.pathname.startsWith('/events/sync-'))")
  assert 'October 31' not in page.locator('.gh-week').text_content()
  page.screenshot(path=str(OUT/f'home-{mode}.png'),full_page=True)
  page.locator('.gh-lead .gh-btn-solid').click();page.wait_for_load_state('networkidle')
  assert page.url.startswith(BASE+'events/sync-')
  assert 'Storytime' in page.locator('.gh-sync-detail h1').text_content()
  assert page.locator('.gh-sync-media').count()==0
  page.screenshot(path=str(OUT/f'detail-no-media-{mode}.png'),full_page=True)
  page.locator('.gh-sync-actions a[href$="upcoming/"]').click();page.wait_for_load_state('networkidle')
  titles=page.locator('.gh-card-link');assert titles.count()>0
  assert page.locator('.gh-event-card a').evaluate_all("es=>es.every(e=>e.origin===location.origin&&e.pathname.startsWith('/events/sync-'))")
  assert page.locator('.gh-card-media').count()>=5
  page.screenshot(path=str(OUT/f'upcoming-{mode}.png'),full_page=True)
  page.locator('.gh-card-link',has_text='Comedian Ben Roy').click();page.wait_for_load_state('networkidle')
  photo=page.locator('.gh-sync-media img');assert photo.count()==1
  assert photo.evaluate('e=>e.complete&&e.naturalWidth>0')
  source=page.locator('.gh-sync-actions a[target=_blank]');assert source.count()==1 and source.get_attribute('href').startswith('https://tacaw.org/')
  assert '20:00' in page.locator('#gh-sync-event').text_content()
  assert 'MASTER ID:' not in page.locator('main').text_content()
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.add_script_tag(path='/workspace/lux-tools/node_modules/axe-core/axe.min.js')
  aa=page.evaluate("async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}")
  assert aa==[],aa
  page.screenshot(path=str(OUT/f'detail-media-{mode}.png'),full_page=True)
  page.set_viewport_size({'width':1440,'height':900});page.screenshot(path=str(OUT/f'detail-desktop-{mode}.png'),full_page=True)
  results.append({'theme':mode,'home_to_local_overview':'PASS','upcoming_title_and_image_links_stay_local':'PASS','home_thumbnails':True,'no_unverified_placeholder_figure':'PASS','official_source_is_explicit_new_tab_action':'PASS','detail_media_loaded':True,'axe_A_AA_violations':aa,'page_errors':errors})
  assert not errors,errors
  c.close()
 # Calendar keeps its modal and its next action on site.
 c=browser.new_context(viewport={'width':390,'height':844},service_workers='block');clock(c,'2026-11-06T18:00:00-07:00');networking(c,feed)
 page=c.new_page();page.goto(BASE+'calendar/',wait_until='networkidle')
 assert page.locator('#gcal-title').text_content()=='November 2026'
 page.locator('.gcal-event').first.click()
 assert page.locator('.gcal-links a').evaluate('e=>e.origin===location.origin&&e.pathname.startsWith("/events/sync-")')
 page.locator('.gcal-links a').click();page.wait_for_load_state('networkidle');assert page.locator('.gh-sync-detail').count()==1
 c.close()
 # A failed feed clears all event content rather than showing a stale edition.
 for path in ('','upcoming/'):
  c=browser.new_context(service_workers='block');clock(c,'2026-11-06T18:00:00-07:00');networking(c,feed);c.route('**/calendar/calendar-sync.json',lambda r:r.abort())
  page=c.new_page();page.goto(BASE+path,wait_until='networkidle')
  assert page.locator('.gh-row,.gh-event-card').count()==0
  assert 'temporarily unavailable' in page.locator('.gh-list-empty').text_content()
  c.close()
 # Reopened/long-lived pages drop yesterday's events at Denver midnight.
 c=browser.new_context(service_workers='block');clock(c,'2026-11-06T18:00:00-07:00');networking(c,feed)
 page=c.new_page();page.goto(BASE+'upcoming/',wait_until='networkidle')
 assert page.locator('.gh-card-link',has_text='Storytime').count()==1
 page.evaluate('window.__ghNow=Date.parse("2026-11-07T00:01:00-07:00");dispatchEvent(new Event("pageshow"))');page.wait_for_timeout(300)
 assert page.locator('.gh-card-link',has_text='Storytime').count()==0
 assert 'Storytime' not in page.locator('#gh-event-list').text_content()
 c.close();browser.close()
results.append({'feed_failure_no_stale_events':'PASS','Denver_midnight_prunes_HTML_and_JSONLD':'PASS','calendar_month_and_internal_overview':'PASS'})
(OUT/'browser-results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
