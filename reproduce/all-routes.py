import asyncio,json,subprocess
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path('/workspace/wo19-combined');routes=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*.html') if '.git' not in p.parts]
async def main():
 results=[];jobs=asyncio.Queue()
 for route in routes:
  for theme in ['light','dark']:jobs.put_nowait((route,theme))
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  async def worker():
   while not jobs.empty():
    route,theme=jobs.get_nowait();c=await b.new_context(viewport={'width':390,'height':844},service_workers='block',reduced_motion='reduce')
    await c.add_init_script(f"localStorage.setItem('gh-theme','{theme}')")
    await c.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json={'current':{'time':'2026-11-01T15:00','temperature_2m':38,'weather_code':0}}))
    page=await c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await page.goto('http://127.0.0.1:8326/'+route,wait_until='domcontentloaded');await page.wait_for_timeout(100)
    await page.add_script_tag(path='/tmp/site-axe/node_modules/axe-core/axe.min.js')
    violations=await page.evaluate("async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}")
    overflow=await page.evaluate('document.documentElement.scrollWidth>innerWidth')
    results.append({'route':route,'theme':theme,'overflow':overflow,'issues':violations,'errors':errors})
    if violations or overflow or errors:print(json.dumps(results[-1]),flush=True)
    await c.close();jobs.task_done()
  await asyncio.gather(*(worker() for _ in range(3)));await b.close()
 source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 Path('/workspace/wo19-evidence/all-routes.json').write_text(json.dumps({'source':source,'width':390,'results':results},indent=2)+'\n')
 print('Scanned',len(results),'route/theme cases; failures:',sum(bool(x['issues'] or x['overflow'] or x['errors']) for x in results),flush=True)
asyncio.run(main())
