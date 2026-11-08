/* Development-only pure JS/adapter tests; no production/browser acceptance claim. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const P=require('../assets/gh-event-policy.js');
const event=(id,start,band='LISTED',extra={})=>({id,title:id,start,end:start,band,source:'aurelian-local',verified:true,...extra});
assert.equal(P.day('2026-11-08T06:59:59Z'),'2026-11-07');
assert.equal(P.day('2026-11-08T07:00:00Z'),'2026-11-08');
assert.equal(P.endDay(event('all','2026-11-01','LISTED',{end:'2026-11-03',all_day:true})),'2026-11-02');
assert.equal(P.eligible(event('overnight','2026-11-06T23:00:00-07:00','LISTED',{end:'2026-11-07T01:00:00-07:00'}),'2026-11-07'),true);
assert.equal(P.eligible(event('overnight','2026-11-06T23:00:00-07:00','LISTED',{end:'2026-11-07T01:00:00-07:00'}),'2026-11-08'),false);
assert.equal(P.endDay(event('spring','2026-03-08','LISTED',{end:'2026-03-09',all_day:true})),'2026-03-08');
const rows=[event('early','2026-11-08T09:00:00-07:00'),event('feature','2026-11-08T20:00:00-07:00','FEATURED'),event('previous','2026-11-07T23:00:00-07:00')];
assert.deepEqual(rows.sort(P.compare).map(e=>e.id),['previous','feature','early']);
assert.equal(P.routine({title:'Sunday Mass — St Mary'}),true);
assert.equal(P.routine({title:'Christmas Sunday Mass — St Mary'}),false);
assert.equal(P.routine({title:'Holiday concert'}),false);
assert.equal(P.verified(event('private','2026-11-08', 'LISTED',{source:'personal'})),false);
assert.equal(P.verified(event('null','2026-11-08','LISTED',{verified:null})),false);
async function testAdapter(){
  let calls=0,fail=false,invalid=false;
  const context={Intl,URL,Date,window:{GHEventPolicy:P},document:{currentScript:{src:'https://example.test/this-week-in-aspen/assets/gh-calendar-sync.js'},querySelector:()=>({src:'https://example.test/this-week-in-aspen/assets/gh-calendar-sync.js'})},fetch:async()=>{calls++;if(fail)throw Error('offline');return {ok:true,json:async()=>invalid?{}:{events:[event('feature','2099-11-08T20:00:00-07:00','FEATURED'),event('early','2099-11-08T09:00:00-07:00'),event('mass','2099-11-08','LISTED',{title:'Sunday Mass — routine'}),event('private','2099-11-08','LISTED',{source:'personal'}),event('unverified','2099-11-08','LISTED',{verified:false}),event('expired','2020-01-01')]}}}};
  vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'assets/gh-calendar-sync.js'),'utf8'),context);
  const C=context.window.GHCalSync;
  const data=await C.load();assert.deepEqual(Array.from(data.local,e=>e.id),['feature','early']);
  assert.equal(C.detailUrl(data.local[0]),'https://example.test/this-week-in-aspen/events/sync-feature/');
  assert.equal(C.normalize(event('no-image','2099-11-08','LISTED',{image:'https://stock.test/generic.jpg'})).image,'');
  await C.load();assert.equal(calls,1);
  // A fresh page must fail honestly, and retry after a rejected promise.
  vm.runInContext(fs.readFileSync(path.join(root,'assets/gh-calendar-sync.js'),'utf8'),context);
  fail=true;await assert.rejects(context.window.GHCalSync.load());fail=false;invalid=true;
  await assert.rejects(context.window.GHCalSync.load());invalid=false;
  assert.equal((await context.window.GHCalSync.load()).local.length,2);
}
testAdapter().then(()=>console.log('PASS: lifecycle, bands, source/verification gates, media, path, feed rejection and retry')).catch(e=>{console.error(e);process.exitCode=1});
