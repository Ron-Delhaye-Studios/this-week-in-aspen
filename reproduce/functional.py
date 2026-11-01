import asyncio,json,re
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright
out=Path('/workspace/wo19-evidence');checks=[]
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  async def context(width=390,date='2026-11-01T15:00:00+00:00',theme=None):
   c=await b.new_context(viewport={'width':width,'height':844},color_scheme='dark',service_workers='block')
   await c.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json={'current':{'time':'2026-11-01T15:00','temperature_2m':38,'weather_code':0}}))
   if theme:await c.add_init_script(f"localStorage.setItem('gh-theme','{theme}')")
   page=await c.new_page();await page.clock.install(time=datetime.fromisoformat(date));return c,page
  c,page=await context()
  async def inset(route):
   r=await route.fetch();text=await r.text();await route.fulfill(response=r,body=re.sub(r'env\(safe-area-inset-top(?:\s*,[^)]+)?\)','37px',text))
  await c.route('**/assets/gh-chrome.css',inset);await c.route('**/assets/gh-home.css',inset)
  for route in ['', 'sources/']:
   await page.goto('http://127.0.0.1:8326/'+route,wait_until='networkidle');assert await page.get_attribute('html','data-theme')=='light'
   box=await page.locator('.gh-topbar-in').bounding_box();assert 36<=box['y']<=38,box
   assert '38°F' in await page.locator('.gh-weather').inner_text()
  await page.locator('.gh-theme-toggle').click();await page.goto('http://127.0.0.1:8326/events/',wait_until='domcontentloaded');assert await page.get_attribute('html','data-theme')=='dark'
  await c.close();checks.append('A1 light landing on dark device, persistent toggle, weather fixture, single synthetic 37px safe inset: home + inner')
  for width in [390,1440]:
   for theme in ['light','dark']:
    c,page=await context(width=width,theme=theme)
    await c.route('**/*',lambda r:r.abort() if r.request.resource_type=='image' else r.continue_())
    await page.goto('http://127.0.0.1:8326/events/',wait_until='networkidle')
    first=page.locator('.gh-event-card:not([hidden])').first;await first.scroll_into_view_if_needed();await page.wait_for_timeout(300)
    assert 'gh-typographic' in await first.get_attribute('class')
    assert await first.locator('.gh-type-media h2').inner_text()
    folder=out/'image-failure';folder.mkdir(exist_ok=True)
    await page.screenshot(path=str(folder/f'events-{width}-{theme}.png'))
    await page.goto('http://127.0.0.1:8326/picks/',wait_until='networkidle');await page.locator('#pick-list .pick').first.scroll_into_view_if_needed();await page.wait_for_timeout(300)
    assert await page.locator('.pick.gh-typographic').count()>0
    await page.screenshot(path=str(folder/f'picks-{width}-{theme}.png'));await c.close()
  checks.append('Failed event and pick photographs retain designed, populated type compositions at both widths/themes')
  c,page=await context(date='2026-10-30T18:00:00+00:00')
  await page.goto('http://127.0.0.1:8326/calendar/',wait_until='networkidle')
  day=page.locator('[data-day="2026-10-31"]');await day.locator('.gcal-morecount').click();assert await page.locator('#gcal-agenda .gcal-arow').count()==8
  event=day.locator('.gcal-event').first;await event.click();assert await page.locator('.gcal-x').evaluate('(el)=>el===document.activeElement')
  await page.keyboard.press('Shift+Tab');assert await page.locator('.gcal-links a').last.evaluate('(el)=>el===document.activeElement')
  await page.keyboard.press('Escape');assert await event.evaluate('(el)=>el===document.activeElement');await c.close()
  checks.append('Calendar: crowded Oct 31 carries eight real events; more/agenda/dialog/focus trap/Escape/return pass')
  c,page=await context(date='2026-12-01T18:00:00+00:00')
  await page.goto('http://127.0.0.1:8326/off-season/',wait_until='networkidle');assert await page.locator('#season-out').is_visible();assert not await page.locator('#season-live').is_visible();await c.close()
  c,page=await context();await c.route('**/happy-hours.json',lambda r:r.fulfill(json={'listings':[]}));await page.goto('http://127.0.0.1:8326/happy-hour/',wait_until='networkidle');assert 'No verified happy hours' in await page.locator('#hh-list').inner_text();await c.close()
  checks.append('Existing out-of-season and empty-guide states remain intact (MOCKED_CLOCK / MOCKED_DATA)')
  c,page=await context()
  for origin in ['http://127.0.0.1:8326/','http://127.0.0.1:8327/this-week-in-aspen/']:
   response=await page.goto(origin+'missing/nested/wo19',wait_until='networkidle');assert response.status==404
   assert await page.locator('.gh-not-found h1').inner_text()=='Page not found'
   assert await page.locator('link[href$="gh-page-404.css"]').evaluate('async el=>(await fetch(el.href)).ok')
   assert await page.locator('.gh-not-found a').evaluate_all('(els,base)=>els.every(el=>el.href.startsWith(base))',origin)
  await c.close();checks.append('Real nested HTTP 404 + resources/recovery links: root and project-prefix hosting')
  c=await b.new_context(viewport={'width':390,'height':844})
  await c.add_init_script("window.realRegister=navigator.serviceWorker.register.bind(navigator.serviceWorker);navigator.serviceWorker.register=()=>Promise.reject(new Error('QA delays registration'));")
  page=await c.new_page();await page.goto('http://127.0.0.1:8326/',wait_until='domcontentloaded')
  await page.evaluate("async()=>{await caches.open('golden-hour-obsolete');await realRegister('/sw.js');await navigator.serviceWorker.ready}")
  await page.wait_for_function('!!navigator.serviceWorker.controller')
  await page.evaluate("async()=>{while((await caches.keys()).includes('golden-hour-obsolete'))await new Promise(r=>setTimeout(r,50))}")
  await page.goto('http://127.0.0.1:8326/events/',wait_until='networkidle');await page.reload(wait_until='networkidle');await c.set_offline(True);await page.reload(wait_until='domcontentloaded');assert await page.locator('.gh-event-grid').count()==1
  assert await page.locator('link[href$="gh-page-events.css"]').evaluate('async el=>(await fetch(el.href)).ok')
  await c.close();checks.append('Combined service worker removes obsolete cache; visited Events and family CSS load offline')
  await b.close()
 (out/'functional-results.json').write_text(json.dumps({'evidence':'OBSERVED_LOCAL','checks':checks,'physical_phone':'UNKNOWN; synthetic inset is not physical iOS proof'},indent=2)+'\n')
 print(json.dumps(checks,indent=2))
asyncio.run(main())
