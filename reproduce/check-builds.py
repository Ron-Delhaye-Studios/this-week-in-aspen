import subprocess,tempfile,tarfile,io,hashlib,json,os
from pathlib import Path
results=[]
for family in ['chrome','tables','events','collections','guides','map','404']:
 root=Path('/workspace/this-week-in-aspen' if family=='chrome' else '/workspace/wo19-'+family)
 with tempfile.TemporaryDirectory(prefix='wo19-build-') as temp:
  p=Path(temp);data=subprocess.check_output(['git','archive','HEAD'],cwd=root)
  with tarfile.open(fileobj=io.BytesIO(data)) as archive:archive.extractall(p,filter='data')
  env={**os.environ,'PYTHONPATH':'/tmp/site-qa'}
  def cmd(*args):
   r=subprocess.run(args,cwd=p,env=env,text=True,capture_output=True)
   assert r.returncode==0,(family,args,r.stdout[-1000:],r.stderr[-1200:])
   return r.stdout.strip()
  first=cmd('python','build_design.py','--as-of','2026-11-01')
  before={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*.html')}
  cmd('python','build_design.py','--as-of','2026-11-01')
  after={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*.html')}
  assert before==after,(family,'non-idempotent build',[name for name in before if before[name]!=after[name]])
  guard=cmd('python','tests/wo19_static.py')
  result={'family':family,'source':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'build':first,'guards':guard,'idempotent':True}
  results.append(result);print(json.dumps(result),flush=True)
Path('/workspace/wo19-evidence/build-results.json').write_text(json.dumps(results,indent=2)+'\n')
