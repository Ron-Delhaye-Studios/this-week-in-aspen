import argparse,asyncio,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
from playwright.async_api import async_playwright
parser=argparse.ArgumentParser();parser.add_argument('family');parser.add_argument('--port',default='8311');parser.add_argument('--routes',required=True);parser.add_argument('--root',default='/workspace/this-week-in-aspen');args=parser.parse_args()
async def main():
 out=Path('/workspace/wo19-evidence')/args.family;out.mkdir(parents=True,exist_ok=True);results=[]
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for width in [390,1440]:
   for theme in ['light','dark']:
    c=await b.new_context(viewport={'width':width,'height':1000 if width==1440 else 844},service_workers='block',reduced_motion='reduce')
    await c.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json={'current':{'time':'2026-11-01T15:00','temperature_2m':38,'weather_code':0}}))
    await c.add_init_script(f"localStorage.setItem('gh-theme','{theme}')")
    for item in json.loads(args.routes):
     route,selector=item if isinstance(item,list) else (item,None)
     page=await c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     await page.clock.install(time=datetime(2026,11,1,15,tzinfo=timezone.utc))
     response=await page.goto(f'http://127.0.0.1:{args.port}/'+route,wait_until='domcontentloaded');await page.wait_for_timeout(500)
     await page.evaluate('document.fonts.ready')
     if selector:
      await page.locator(selector).first.evaluate("el=>el.scrollIntoView({block:'start'})")
      await page.wait_for_timeout(700)
     await page.add_script_tag(path='/tmp/site-axe/node_modules/axe-core/axe.min.js')
     issues=await page.evaluate("async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))}")
     name=(route.strip('/').replace('/','-') or 'home')+f'-{width}-{theme}.png';await page.screenshot(path=str(out/name))
     results.append({'route':route,'width':width,'theme':theme,'http':response.status,'overflow':await page.evaluate('document.documentElement.scrollWidth>innerWidth'),'issues':issues,'errors':errors,'screenshot':name})
     print(args.family,route,width,theme,'issues='+','.join(i['id'] for i in issues),'errors='+str(errors),flush=True)
     await page.close()
    await c.close()
  await b.close()
 source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=args.root,text=True).strip()
 (out/'results.json').write_text(json.dumps({'source':source,'weather':'MOCKED_WEATHER','clock':'2026-11-01T15:00:00Z','results':results},indent=2)+'\n')
 if any(x['issues'] or x['overflow'] or x['errors'] for x in results):raise SystemExit('Review required; see results.json')
asyncio.run(main())
