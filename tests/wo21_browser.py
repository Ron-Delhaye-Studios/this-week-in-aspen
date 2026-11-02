"""WO21 phone/desktop, cached-week and actual installed Chromium PWA checks.

Run with CHROMIUM_PATH pointing to current Chrome. Installed-app proof needs
DISPLAY (a real/Xvfb display); this is not a physical iPhone acceptance test.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys
import tempfile
import urllib.request
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('BASE_URL','http://127.0.0.1:8781/')
OUT=ROOT/'design/review/wo21'
OUT.mkdir(parents=True,exist_ok=True)
CHROME=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium')
CANONICAL=json.loads((ROOT/'data/events.json').read_text())
RESULTS=[]
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


def safe_area(context,page):
    session=context.new_cdp_session(page)
    session.send('Emulation.setSafeAreaInsetsOverride',{'insets':{'top':47,'bottom':34,'left':0,'right':0}})
    return session


def styles(page):
    return page.evaluate('''()=>{
      const css=e=>getComputedStyle(e),b=document.body,top=document.querySelector('.gh-topbar');
      return {body:css(b).backgroundColor,bar:css(top).backgroundColor,
        inner:css(document.querySelector('.gh-topbar-in')).backgroundColor,
        weather:css(document.querySelector('.gh-weather')).backgroundColor,
        button:css(document.querySelector('.gh-theme-toggle')).backgroundColor,
        inset:css(top).paddingTop,scrim:getComputedStyle(b,'::before').backgroundColor,
        blur:getComputedStyle(b,'::before').backdropFilter,
        scrimHeight:getComputedStyle(b,'::before').height,
        nativeStatus:document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]').content,
        theme:document.documentElement.dataset.theme};
    }''')


def light_band(page):
    colors=styles(page)
    assert all(colors[k]=='rgb(250, 244, 232)' for k in ['body','bar','inner','weather','button','scrim']),colors
    assert colors['blur']=='none' and colors['nativeStatus']=='default',colors
    assert colors['inset']=='47px' and colors['scrimHeight']=='47px',colors
    assert page.locator('.gh-date').bounding_box()['y']>=47
    return colors


def load(page,path=''):
    page.goto(BASE+path,wait_until='domcontentloaded')
    page.locator('.gh-theme-toggle').wait_for()
    page.evaluate('document.fonts.ready')


def fixture(id,start,category='music',price='',**extra):
    return dict(id=id,title=id,slug=id,starts_at=start,category=category,price_info=price,venue='QA venue',url='https://example.com/'+id,blurb='Test fixture for temporal scoping.',**extra)


with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    for width in [320,390,1440]:
        context=browser.new_context(viewport={'width':width,'height':844},service_workers='block',color_scheme='dark')
        clock(context,'2026-11-01T18:00:00+00:00');networking(context,CANONICAL)
        page=context.new_page();safe_area(context,page);load(page)
        assert page.evaluate('document.documentElement.dataset.theme')=='light'
        light_band(page)
        if width==390:page.screenshot(path=str(OUT/'top-light-browser-safe-area-simulated.png'))
        page.locator('.gh-theme-toggle').click()
        dark=styles(page);assert dark['bar']=='rgb(13, 27, 36)' and dark['scrim']=='rgba(13, 27, 36, 0.82)' and dark['nativeStatus']=='black-translucent',dark
        page.locator('.gh-theme-toggle').click();light_band(page)
        page.evaluate('scrollTo(0,600)');light=styles(page);assert light['scrim']=='rgb(250, 244, 232)' and light['blur']=='none'
        load(page,'upcoming/');assert page.locator('h1').inner_text()=='This Week'
        page.wait_for_function("document.querySelector('.gh-week-range').textContent.includes('Nov 06')")
        assert page.locator('.gh-event-card:visible').count()==0
        assert page.locator('.gh-filters').is_hidden()
        assert page.locator('link[rel="canonical"]').get_attribute('href')=='https://thegoldenhour.guide/upcoming/'
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        if width==390:
            page.locator('h1').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'this-week-current-empty.png'))
        RESULTS.append({'mode':'browser','width':width,'light_band':'pass','dark_band':'unchanged','empty_current_week':'pass'})
        context.close()
    # Ordinary browser tab: native zero safe-area inset, no emulated status strip.
    context=browser.new_context(viewport={'width':390,'height':844},service_workers='block',color_scheme='dark')
    clock(context,'2026-11-01T18:00:00+00:00');networking(context,CANONICAL)
    page=context.new_page();load(page)
    ordinary=styles(page)
    assert ordinary['theme']=='light' and ordinary['inset']=='0px',ordinary
    assert all(ordinary[k]=='rgb(250, 244, 232)' for k in ['body','bar','inner','weather','button','scrim']),ordinary
    page.screenshot(path=str(OUT/'top-light-browser-native-zero-inset.png'))
    RESULTS.append({'mode':'ordinary_browser_tab','width':390,'native_safe_area':'0px','light_default_with_dark_OS':'pass','light_band':'pass'})
    context.close()
    # Deterministic fixture covers all four chips and explicit unverified cases.
    feed=[fixture('week-music','2026-11-03T19:00:00-07:00'),fixture('week-art','2026-11-04T17:00:00-07:00','arts'),fixture('week-free','2026-11-05T12:00:00-07:00','outdoors','Free'),fixture('later-event','2026-11-14T12:00:00-07:00'),fixture('past-event','2026-10-31T12:00:00-06:00'),fixture('held-draft','2026-11-03T12:00:00-07:00',status='draft'),fixture('held-provisional','2026-11-03T12:00:00-07:00',confidence='PROVISIONAL')]
    for width in [320,390,1440]:
        context=browser.new_context(viewport={'width':width,'height':844},service_workers='block')
        clock(context,'2026-11-01T18:00:00+00:00');networking(context,feed)
        page=context.new_page();safe_area(context,page);load(page,'upcoming/')
        page.wait_for_function("document.querySelectorAll('.gh-event-card').length===3")
        assert page.locator('.gh-event-card').evaluate_all('els=>els.map(e=>e.dataset.slug)')==['week-music','week-art','week-free']
        assert page.locator('.gh-filters button').all_text_contents()==['All','Music','Art','Free']
        boxes=page.locator('.gh-filters button').evaluate_all('els=>els.map(e=>{const r=e.getBoundingClientRect();return {y:r.y,h:r.height,w:r.width}})')
        assert max(b['y'] for b in boxes)-min(b['y'] for b in boxes)<1 and all(b['h']>=44 and b['w']<120 for b in boxes),boxes
        page.locator('[data-filter="arts"]').click();assert page.locator('.gh-event-card:visible').count()==1
        assert page.locator('.gh-event-card:visible').get_attribute('data-slug')=='week-art'
        page.locator('[data-filter="free"]').click();assert page.locator('.gh-event-card:visible').get_attribute('data-slug')=='week-free'
        page.locator('[data-filter="all"]').click()
        ld=json.loads(page.locator('#gh-event-list').text_content());assert [x['item']['name'] for x in ld['itemListElement']]==['week-music','week-art','week-free']
        if width==390:
            page.evaluate("scrollTo(0,document.querySelector('h1').getBoundingClientRect().top+scrollY-60)");page.screenshot(path=str(OUT/'this-week-four-chips-FIXTURE.png'))
        page.route('**/data/events.json',lambda route:route.abort())
        page.evaluate('window.__ghNow='+str(timestamp('2026-11-07T18:00:00+00:00'))+';dispatchEvent(new Event("pageshow"))')
        assert page.locator('.gh-event-card:visible').count()==0
        assert page.locator('.gh-filters').is_hidden()
        assert json.loads(page.locator('#gh-event-list').text_content())['itemListElement']==[]
        RESULTS.append({'mode':'fixture','width':width,'compact_chips':'pass','verification_and_week_scope':'pass','cached_rollover_feed_offline':'pass'})
        context.close()
    # Actual canonical feed in a populated reference week (clock only is changed).
    context=browser.new_context(viewport={'width':390,'height':844},service_workers='block')
    clock(context,'2026-11-14T18:00:00+00:00');networking(context,CANONICAL)
    page=context.new_page();safe_area(context,page);load(page)
    page.wait_for_selector('.gh-week .gh-row')
    page.evaluate("scrollTo(0,document.querySelector('.gh-week').getBoundingClientRect().top+scrollY-60)")
    page.screenshot(path=str(OUT/'coming-up-populated-reference-week.png'))
    assert page.locator('.gh-week .gh-filters').evaluate('e=>getComputedStyle(e).paddingTop')=='0px'
    gap=page.evaluate("document.querySelector('.gh-week .gh-filters').getBoundingClientRect().top-document.querySelector('.gh-week .gh-sec-meta').getBoundingClientRect().bottom")
    assert gap<24,gap
    load(page,'upcoming/');page.wait_for_selector('.gh-event-card')
    assert page.locator('.gh-filters button').all_text_contents()==['All','Music']
    page.evaluate("scrollTo(0,document.querySelector('h1').getBoundingClientRect().top+scrollY-60)")
    page.screenshot(path=str(OUT/'this-week-populated-reference-week.png'))
    RESULTS.append({'mode':'canonical_reference_week','as_of':'2026-11-14','heading_to_chips_gap':gap,'zero_count_art_free_chips_hidden':True})
    context.close();browser.close()
    # Install and launch a real headful Chromium PWA in a disposable profile.
    if not os.environ.get('DISPLAY'):raise RuntimeError('DISPLAY required for the installed-app proof; do not call a headless tab an installed app.')
    with tempfile.TemporaryDirectory(prefix='wo21-pwa-') as profile:
        context=p.chromium.launch_persistent_context(profile,executable_path=CHROME,headless=False,args=['--no-sandbox'],viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        clock(context,'2026-11-01T18:00:00+00:00');networking(context,CANONICAL)
        tab=context.pages[0];load(tab);session=safe_area(context,tab)
        session.send('PWA.install',{'manifestId':BASE,'installUrlOrBundleUrl':BASE})
        session.send('PWA.changeAppUserSettings',{'manifestId':BASE,'displayMode':'standalone'})
        with context.expect_page() as opened:launch=session.send('PWA.launch',{'manifestId':BASE})
        app=opened.value;app.wait_for_url(BASE);app.set_viewport_size({'width':390,'height':844});safe_area(context,app)
        app.locator('.gh-topbar').wait_for();app.evaluate('document.fonts.ready')
        app.wait_for_function("matchMedia('(display-mode: standalone)').matches")
        light_band(app)
        app.screenshot(path=str(OUT/'top-light-INSTALLED-CHROMIUM-simulated-safe-area.png'))
        app.locator('.gh-theme-toggle').click();assert styles(app)['bar']=='rgb(13, 27, 36)'
        app.locator('.gh-theme-toggle').click();light_band(app)
        RESULTS.append({'mode':'actual_installed_chromium_PWA','viewport':[390,844],'display_mode':'standalone','safe_area':'CDP simulated 47px; not physical iOS','launch_target':launch['targetId'],'light_band':'pass','dark_mode':'pass'})
        session.send('PWA.uninstall',{'manifestId':BASE});context.close()
(OUT/'browser-results.json').write_text(json.dumps(RESULTS,indent=2)+'\n')
print(json.dumps(RESULTS,indent=2))
