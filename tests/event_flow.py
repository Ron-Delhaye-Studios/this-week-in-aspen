"""Event summaries lead to a real on-site page with supplied media and metadata."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from build_event_details import slug, description, safe_url

class EventFlowTests(unittest.TestCase):
    def test_every_synced_event_has_a_canonical_detail_with_matching_schema(self):
        rows=json.loads((ROOT/'calendar/calendar-sync.json').read_text())['events']
        for event in rows:
            with self.subTest(event=event['id']):
                path=ROOT/'events'/slug(event['id'])/'index.html'
                doc=BeautifulSoup(path.read_text(),'html.parser')
                self.assertEqual(doc.select_one('.gh-sync-detail h1').text,event['title'])
                self.assertEqual(doc.select_one('link[rel=canonical]')['href'],'https://thegoldenhour.guide/events/'+slug(event['id'])+'/')
                ld=json.loads(doc.select_one('#gh-sync-event').string)
                self.assertEqual(ld['startDate'],event['start']);self.assertEqual(ld['name'],event['title'])
                self.assertEqual(bool(doc.select('.gh-sync-media')),bool(event.get('image') and event.get('verified')))
                for image in doc.select('.gh-sync-media img'):self.assertTrue((path.parent/image['src']).is_file())
                self.assertFalse(doc.select('meta[name=robots][content*=noindex]'))
    def test_no_fake_source_links_or_internal_editorial_metadata(self):
        text,url=description('AURELIAN EVENT\nMASTER ID: abc\nWhat: A local evening.\nOfficial: https://venue.example/event')
        self.assertEqual(text,'A local evening.');self.assertEqual(url,'https://venue.example/event')
        self.assertEqual(safe_url('javascript:alert(1)'),'');self.assertEqual(safe_url('https://user:pass@venue.example'),'')
        self.assertEqual(description('See https://unlabelled.example/background')[1],'')
    def test_homepage_shell_contains_no_baked_event_or_edition(self):
        doc=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser');section=doc.select_one('.gh-week')
        self.assertFalse([key for key in section.attrs if key.startswith('data-ed-') or key=='data-window-end'])
        self.assertFalse(section.select('.gh-row'));self.assertTrue(section.select_one('.gh-lead').has_attr('hidden'))
        self.assertEqual(section.select_one('.gh-sec-meta').text,'')
        upcoming=BeautifulSoup((ROOT/'upcoming/index.html').read_text(),'html.parser')
        self.assertEqual(upcoming.select_one('.gh-week-range').text,'')
        self.assertFalse(upcoming.select('.gh-event-card'))
        for page in (doc,upcoming):self.assertEqual(len(page.select('script[src$="gh-calendar-sync.js"]')),1)
    def test_all_event_detail_routes_are_in_sitemap(self):
        import xml.etree.ElementTree as ET
        urls={node.text for node in ET.parse(ROOT/'sitemap.xml').getroot().iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
        for event in json.loads((ROOT/'calendar/calendar-sync.json').read_text())['events']:
            self.assertIn('https://thegoldenhour.guide/events/'+slug(event['id'])+'/',urls)
    def test_feed_bytes_are_unchanged(self):
        expected='8bbda96bbc3a78cc0131b0304f8b22c24188c2d0f12ca6004adf9fbf51efe734'
        self.assertEqual(hashlib.sha256((ROOT/'calendar/calendar-sync.json').read_bytes()).hexdigest(),expected)

if __name__=='__main__':unittest.main()
