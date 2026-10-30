"""WO10 browser regression pass. See WO10-VALIDATION.md for server setup.

BASE_URL selects the served site; WO10_HTTP_CACHE optionally reuses genuine
public CDN/tile responses. Weather is a deterministic fixture, not live proof.
"""
import hashlib
import json
import os
from pathlib import Path
import urllib.request

from playwright.sync_api import sync_playwright

BASE = os.environ.get('BASE_URL', 'http://127.0.0.1:8781/this-week-in-aspen/')
CACHE = Path(os.environ.get('WO10_HTTP_CACHE', '/tmp/wo10-http'))
CACHE.mkdir(parents=True,exist_ok=True)
RESULTS = []


def network(route):
    url = route.request.url
    if url.startswith(BASE.split('/this-week-in-aspen/')[0]):
        return route.continue_()
    if route.request.method!='GET':return route.abort()
    if 'api.open-meteo.com' in url:
        return route.fulfill(json={'current':{'time':'2026-10-30T18:00','temperature_2m':58.2,'weather_code':0}})
    key = CACHE/hashlib.sha256(url.encode()).hexdigest()
    try:
        if key.with_suffix('.fail').exists():return route.abort()
        if not key.exists():
            with urllib.request.urlopen(url,timeout=8) as response:
                key.write_bytes(response.read());key.with_suffix('.type').write_text(response.headers.get('Content-Type','application/octet-stream'))
        route.fulfill(body=key.read_bytes(),content_type=key.with_suffix('.type').read_text(),headers={'Access-Control-Allow-Origin':'*'})
    except Exception:
        route.abort()


def load(page,path):
    page.goto(BASE+path,wait_until='domcontentloaded')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),path
    strip=page.locator('.gh-top').bounding_box();toggle=page.locator('.gh-theme-toggle').bounding_box()
    assert toggle['y']>=strip['y'] and toggle['y']+toggle['height']<=strip['y']+strip['height']+1
    assert page.locator('.masthead .brand').inner_text()=='THE GOLDEN HOUR'
    assert page.locator('.gh-footer nav a').count()==9


def check(page,width,theme):
    load(page,'events/')
    page.wait_for_selector('.gh-event-card')
    cards=page.locator('.gh-event-card').evaluate_all('els=>els.map(e=>e.outerHTML)')
    assert len(cards)==22
    assert page.locator('.gh-filters button').count()==6
    page.locator('[data-filter="outdoors"]').click()
    assert page.locator('[data-slug="digable-planets"]:visible').count()==0
    page.locator('[data-filter="all"]').click()
    page.locator('.gh-card-details').first.locator('summary').click()
    assert page.locator('.gh-card-details').first.locator('dd').count()==2
    load(page,'upcoming/')
    assert page.locator('.gh-event-card').evaluate_all('els=>els.map(e=>e.outerHTML)')==cards
    assert page.locator('.gh-filters button').count()==6
    page.locator('[data-filter="music"]').click()
    assert page.locator('[data-slug="ute-cemetery-tour"]:visible').count()==0
    page.locator('[data-filter="all"]').click()
    page.locator('.gh-copy').first.click()
    page.wait_for_function("document.querySelector('.gh-copy').textContent.includes('Copied')")

    load(page,'calendar/')
    assert page.locator('#gcal-title').inner_text().strip()
    page.wait_for_selector('.gcal-event',state='attached')
    assert page.locator('.gcal-dot').count()==0
    assert page.locator('.gcal-event').evaluate_all('els=>els.every(e=>e.textContent.trim().length>4)')
    assert page.locator('.gcal-day').evaluate_all("els=>els.every(e=>e.querySelectorAll('.gcal-event').length<=3)")
    day=page.locator('[data-day="2026-10-31"]')
    day.locator('.gcal-morecount').click()
    assert page.locator('#gcal-agenda .gcal-arow').count()==8
    event=day.locator('.gcal-event').first
    event.click();page.wait_for_selector('[role="dialog"]')
    assert page.locator('.gcal-x').evaluate('e=>e===document.activeElement')
    page.keyboard.press('Shift+Tab')
    assert page.locator('.gcal-links a').last.evaluate('e=>e===document.activeElement')
    page.keyboard.press('Escape')
    assert page.locator('[role="dialog"]').count()==0
    assert event.evaluate('e=>e===document.activeElement')
    page.locator('#gcal-next').click();assert 'November' in page.locator('#gcal-title').inner_text()
    page.locator('#gcal-today').click();assert page.locator('[data-day="2026-10-30"] .gcal-daynum').get_attribute('aria-pressed')=='true'

    load(page,'sources/')
    assert page.locator('table.src tbody td').evaluate_all("els=>els.every(e=>e.dataset.label&&getComputedStyle(e).wordBreak==='normal'&&getComputedStyle(e).overflowWrap==='normal')")
    if width==390:
        assert page.locator('table.src tbody tr').evaluate_all("els=>els.every(e=>getComputedStyle(e).display==='block'&&e.getBoundingClientRect().width>300)")

    load(page,'events/digable-planets/')
    assert 'Listing source checked' in page.locator('.vbadge').text_content()
    assert 'unverified' in page.locator('.gh-field-note').inner_text()
    assert page.locator('.ev-hero img').evaluate("e=>getComputedStyle(e).objectFit==='contain'")
    load(page,'picks/');page.wait_for_selector('.pick')
    assert page.locator('.pick').count()==11
    assert page.locator('.pick-photo.ph').count()==0
    assert page.locator('.pick.gh-typographic .gh-type-media').evaluate_all("els=>els.every(e=>e.querySelector('h3')&&e.querySelector('.score')&&e.querySelector('.gh-card-kicker'))")
    assert 'Aspen' in page.locator('.gh-map-place').inner_text()
    place=page.locator('.gh-map-place').bounding_box();mp=page.locator('#picks-map').bounding_box()
    assert place['x']>=mp['x'] and place['x']+place['width']<=mp['x']+mp['width']

    load(page,'map/');page.wait_for_selector('#catrow button');page.wait_for_timeout(500)
    assert page.locator('.gh-map-heading h1').inner_text()=='Map'
    widths=page.locator('#controls button').evaluate_all('els=>els.map(e=>e.getBoundingClientRect().width)')
    assert max(widths)-min(widths)<1
    assert page.locator('.leaflet-control-zoom a').evaluate_all('els=>els.every(e=>e.getBoundingClientRect().width>=40&&e.getBoundingClientRect().height>=40)')
    colors=page.locator('.legend .dot').evaluate_all('els=>els.map(e=>getComputedStyle(e).backgroundColor)')
    assert len(set(colors))==4
    markers=page.locator('.leaflet-marker-icon').evaluate_all("els=>els.filter(e=>getComputedStyle(e).opacity==='1').map(e=>{const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,r:r.width/2}})")
    for i,a in enumerate(markers):
        for b in markers[i+1:]:assert ((a['x']-b['x'])**2+(a['y']-b['y'])**2)**.5>=a['r']+b['r']

    response=page.goto(BASE+'missing/nested/wo10',wait_until='domcontentloaded')
    assert response.status==404
    assert page.locator('.gh-not-found h1').inner_text()=='Page not found'
    assert page.locator('link[href$="gh-theme.css"]').evaluate('async e=>(await fetch(e.href)).ok')
    assert page.locator('.gh-not-found a').evaluate_all('(els,base)=>els.every(e=>e.href.startsWith(base))',BASE)
    load(page,'press/')
    assert page.locator('.placeholder').inner_text()=='[press email — to be added]'
    assert page.locator('[data-upcoming-count]').inner_text()=='22'
    assert 'noindex' in page.locator('meta[name="robots"]').get_attribute('content')
    load(page,'editions/');assert page.locator('h2.section').inner_text()=='Archive'
    assert page.locator('.gh-archive-grid article').count()==1
    load(page,'activities/');assert page.locator('.guides a').get_attribute('href')=='golf/'
    RESULTS.append({'width':width,'theme':theme,'functional':'pass'})


def main():
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
        for width in [390,1440]:
            for theme in ['light','dark']:
                context=browser.new_context(viewport={'width':width,'height':900},service_workers='block',permissions=['clipboard-read','clipboard-write'])
                context.route('**/*',network);context.add_init_script(f"localStorage.setItem('gh-theme','{theme}')")
                page=context.new_page();check(page,width,theme);context.close()
        browser.close()
    print(json.dumps(RESULTS,indent=2))


if __name__=='__main__':main()
