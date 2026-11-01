import asyncio,json,subprocess,tempfile,tarfile,io,os
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
root=Path('/workspace/wo19-homepage');checks=[]
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for date in ['2026-11-01T15:00:00+00:00','2026-11-21T15:00:00+00:00']:
   c=await b.new_context(viewport={'width':390,'height':844},service_workers='block',color_scheme='dark')
   await c.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json={'current':{'time':'2026-11-01T15:00','temperature_2m':38,'weather_code':0}}))
   page=await c.new_page();await page.clock.install(time=datetime.fromisoformat(date))
   response=await page.goto('http://127.0.0.1:8328/',wait_until='networkidle')
   assert 'Loading weather' not in await response.text()
   assert await page.get_attribute('html','data-theme')=='light'
   title=await page.locator('.gh-lead h3').inner_text();assert title!='Halloween in Aspen'
   assert not any('…' in x for x in await page.locator('.gh-row-info p,.gh-band-item p').all_inner_texts())
   for row in await page.locator('.gh-row').evaluate_all('els=>els.map(el=>el.querySelector("h4").textContent)'):assert row
   await page.locator('.gh-theme-toggle').click();assert await page.get_attribute('html','data-theme')=='dark'
   await c.close();checks.append({'date':date,'title':title,'default_theme':'light','summaries':'complete source sentences or category/venue facts'})
  c=await b.new_context(service_workers='block');page=await c.new_page();await page.clock.install(time=datetime.fromisoformat('2026-11-21T15:00:00+00:00'))
  await c.route('**/data/events.json',lambda r:r.abort())
  await page.goto('http://127.0.0.1:8328/',wait_until='networkidle');assert not await page.locator('.gh-week-grid').is_visible();assert await page.locator('[data-gh-recovery]').inner_text()=='Events';await c.close()
  checks.append({'offline_stale_feed':'expired edition hidden; Events recovery remains'})
  await b.close()
 # Full source generation must still stabilize and preserve canonical bytes.
 with tempfile.TemporaryDirectory(prefix='wo19-home-build-') as temp:
  data=subprocess.check_output(['git','archive','HEAD'],cwd=root)
  with tarfile.open(fileobj=io.BytesIO(data)) as z:z.extractall(temp,filter='data')
  env={**os.environ,'PYTHONPATH':'/tmp/site-qa'}
  for i in range(2):
   subprocess.run(['python','build_design.py','--as-of','2026-11-01'],cwd=temp,env=env,check=True,capture_output=True)
   current={str(p.relative_to(temp)):p.read_bytes() for p in Path(temp).rglob('*.html')}
   if i:assert current==previous
   previous=current
  subprocess.run(['python','tests/wo19_static.py'],cwd=temp,env=env,check=True)
 checks.append({'full_build':'repeat stable; 70-page guard and canonical hashes pass'})
 Path('/workspace/wo19-evidence/homepage/functional.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
asyncio.run(main())
