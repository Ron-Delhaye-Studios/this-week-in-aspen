"""Publication boundaries and registry-driven feature behavior (no feed edits)."""
import copy
from datetime import date
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from feature_template import validate, render, render_skeleton, load_places, feature_links
from build_features import build_ready
from design.finish_features import apply

class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'data/features').mkdir(parents=True)
        self.day=date(2026,11,1)
        self.feature=json.loads((ROOT/'tests/fixtures/feature-basalt-review.json').read_text())
        self.rows=json.loads((ROOT/'tests/fixtures/feature-events-review.json').read_text())
        self.place=json.loads((ROOT/'tests/fixtures/places-review.json').read_text())[0]
        self.place.update(ready=True,review_fixture=False,source_url='https://www.basalt.net/',last_checked='2026-11-01',verification='CONFIRMED-2026')
        self.write_registry([self.place])
        self.feature.update(ready=True,review_fixture=False)
        for record in [self.feature,*self.feature['entries'],*self.feature['photos']]:
            record.update(source_url='https://www.basalt.net/',verification='CONFIRMED-2026')
        for photo in self.feature['photos']:
            photo['place_key']='basalt'
            target=self.root/photo['file'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/photo['file'],target)
        self.rows[1]['url']='https://www.basalt.net/'
        # These facts are synthetic test evidence only; never a publishable packet.
    def write_registry(self,rows):(self.root/'data/places.json').write_text(json.dumps(rows))
    def test_registry_drives_arbitrary_place(self):
        p=dict(self.place,slug='test-place',name='Test Place');self.write_registry([p])
        self.assertIn('test-place',load_places(self.root))
        doc=BeautifulSoup(render_skeleton(p,[],self.root,self.day),'html.parser')
        self.assertEqual(doc.h1.text,'Destination: Test Place')
        self.assertEqual(len(json.loads(doc.select_one('#feature-breadcrumbs').string)['itemListElement']),4)
        self.assertEqual(doc.select_one('link[rel=canonical]')['href'],'https://thegoldenhour.guide/valley/test-place/')
        self.assertNotIn('gh-feature-photos',str(doc))
    def test_render_order_and_single_highlight(self):
        doc=BeautifulSoup(render(self.feature,self.rows,self.root,self.day),'html.parser')
        self.assertEqual(len(doc.select('.gh-feature-callout')),1)
        self.assertEqual([x.text for x in doc.select('.gh-feature-stop .gh-feature-kicker')],['STAY','PLAY','EAT'])
        self.assertIn('By CODEX',doc.select_one('.gh-feature-byline').text)
        html=str(doc);self.assertLess(html.index('gh-feature-entries'),html.index('gh-feature-callout'));self.assertLess(html.index('gh-feature-callout'),html.index('gh-feature-photos'))
        self.assertEqual(len(doc.select('.gh-feature-week li')),1)
        self.assertIn('Sample',doc.select_one('.gh-feature-week li').text)
    def test_fixture_and_bad_evidence_rejected(self):
        mutations=[lambda f:f.update(review_fixture=True),lambda f:f.update(ready=False),lambda f:f.update(source_url='https://example.com'),lambda f:f.update(last_checked='2027-01-01'),lambda f:f['entries'][0].update(verification='DRAFT'),lambda f:f['entries'][0].update(section='EAT'),lambda f:f.update(highlight_event_id='absent'),lambda f:f['photos'][0].update(place_key='aspen'),lambda f:f['photos'][0].update(credit='Ron Delhaye'),lambda f:f['photos'][0].update(license_url=''),lambda f:f['photos'][0].update(file='../outside.jpg')]
        for mutate in mutations:
            f=copy.deepcopy(self.feature);mutate(f)
            with self.subTest(f=f),self.assertRaises(ValueError):validate(f,self.rows,self.root,self.day)
    def test_highlight_explicit_town_and_verification(self):
        for patch in [{'place_key':'carbondale'},{'verified':False},{'starts_at':'2026-12-05T17:00:00'},{'starts_at':'2025-12-05T17:00:00-07:00'}]:
            rows=copy.deepcopy(self.rows);rows[1].update(patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError):validate(self.feature,rows,self.root,self.day)
    def test_empty_registry_and_atomic_bad_packet(self):
        (self.root/'data/places.json').unlink();self.assertEqual(build_ready(self.root,self.rows,self.day),[])
        self.write_registry([self.place]);bad=dict(self.feature,source_url='https://example.com')
        (self.root/'data/features/bad.json').write_text(json.dumps(bad))
        with self.assertRaises(ValueError):build_ready(self.root,self.rows,self.day)
        self.assertFalse((self.root/'valley').exists())
    def test_skeleton_discovery_idempotent_and_feed_untouched(self):
        feed=self.root/'data/events.json';feed.write_text(json.dumps(self.rows));before=feed.read_bytes()
        (self.root/'sitemap.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://thegoldenhour.guide/</loc></url></urlset>')
        paths=build_ready(self.root,self.rows,self.day)
        self.assertIn('https://thegoldenhour.guide/valley/basalt/',(self.root/'sitemap.xml').read_text())
        self.assertEqual(len(paths),3);self.assertEqual(feature_links(self.root),[('basalt','Basalt')]);self.assertEqual(feed.read_bytes(),before)
        doc=BeautifulSoup('<html><head></head><body><nav class="gh-nav">Existing</nav><div class="page"></div><footer class="gh-footer"></footer></body></html>','html.parser')
        apply(doc,self.root/'index.html',self.root);apply(doc,self.root/'index.html',self.root)
        self.assertEqual(len(doc.select('.gh-valley-discovery')),1)
        self.assertEqual(doc.select_one('.gh-nav').text,'Existing')
    def test_event_breadcrumbs_and_schema_are_idempotent(self):
        (self.root/'data/events.json').write_text(json.dumps(self.rows));build_ready(self.root,self.rows,self.day)
        doc=BeautifulSoup('<html><head></head><body><h1>Sample weekly event</h1></body></html>','html.parser')
        path=self.root/'events'/self.rows[0]['slug']/'index.html'
        apply(doc,path,self.root);apply(doc,path,self.root)
        self.assertEqual(len(doc.select('.gh-feature-breadcrumbs')),1)
        self.assertEqual(len(json.loads(doc.select_one('#feature-breadcrumbs').string)['itemListElement']),5)
        self.assertEqual(len(doc.select('#feature-canonical-event')),1)
        self.assertEqual(len(doc.select('link[href$="gh-page-valley.css"]')),1)

    def test_duplicate_registry_rejected(self):
        self.write_registry([self.place,self.place])
        with self.assertRaises(ValueError):load_places(self.root)

if __name__=='__main__':unittest.main()
