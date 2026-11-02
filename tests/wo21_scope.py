"""WO21: temporal/verification boundaries and static publication invariants."""
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build_design as build
from week_scope import this_week, week_bounds, available_filters
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]


def event(id, starts, category='music', **extra):
    return dict(id=id,title=id,starts_at=starts,category=category,venue='Test venue',slug=id,url='https://example.com/'+id,price_info='',**extra)


class ScopeTests(unittest.TestCase):
    def test_saturday_friday_and_year_boundary(self):
        self.assertEqual(week_bounds(date(2026,11,1)),(date(2026,10,31),date(2026,11,6)))
        self.assertEqual(week_bounds(date(2027,1,1)),(date(2026,12,26),date(2027,1,1)))
        self.assertEqual(week_bounds(date(2026,11,7)),(date(2026,11,7),date(2026,11,13)))

    def test_denver_dst_midnight_and_end_exclusive(self):
        rows=[event('next-week','2026-11-07T00:00:00-07:00'),event('fri-late','2026-11-06T23:59:00-07:00'),
              event('prior-local-day','2026-11-01T05:30:00+00:00'),event('sun-early','2026-11-01T06:30:00+00:00'),
              event('first-one-am','2026-11-01T07:30:00+00:00'),event('second-one-am','2026-11-01T08:30:00+00:00')]
        self.assertEqual([e['id'] for e in this_week(rows,date(2026,11,1))],['sun-early','first-one-am','second-one-am','fri-late'])

    def test_explicit_unverified_rows_do_not_inherit_legacy_feed_trust(self):
        rows=[event('legacy','2026-11-03T12:00:00-07:00')]
        for flag in [{'verified':False},{'verified':None},{'status':'draft'},{'status':None},{'confidence':'PROVISIONAL'},{'confidence':None}]:
            row=event('held','2026-11-03T12:00:00-07:00');row.update(flag);rows.append(row)
        self.assertEqual([e['id'] for e in this_week(rows,date(2026,11,1))],['legacy'])

    def test_chips_are_compact_set_and_only_nonempty_categories(self):
        outdoor=event('walk','2026-11-03T12:00:00-07:00','outdoors')
        self.assertEqual(available_filters([outdoor]),[('all','All')])
        outdoor['price_info']='Free'
        self.assertEqual(available_filters([outdoor]),[('all','All'),('free','Free')])
        self.assertEqual(available_filters([]),[])

    def test_server_html_and_schema_have_same_week_scope(self):
        rows=[event('this-week','2026-11-03T12:00:00-07:00'),event('future','2026-11-14T12:00:00-07:00')]
        original=deepcopy(rows)
        with TemporaryDirectory() as directory,patch.object(build,'ROOT',Path(directory)):
            for folder in ['events','upcoming']: (Path(directory)/folder).mkdir()
            build.build_lists(rows,date(2026,11,1))
            doc=BeautifulSoup((Path(directory)/'upcoming/index.html').read_text(),'html.parser')
            self.assertEqual(doc.h1.text,'This Week')
            self.assertEqual([c['data-slug'] for c in doc.select('.gh-event-card')],['this-week'])
            self.assertEqual([x['item']['name'] for x in json.loads(doc.select_one('#gh-event-list').string)['itemListElement']],['this-week'])
            self.assertEqual(doc.select_one('link[rel="canonical"]')['href'],'https://thegoldenhour.guide/upcoming/')
            events=BeautifulSoup((Path(directory)/'events/index.html').read_text(),'html.parser')
            self.assertEqual(len(events.select('.gh-event-card')),2)
        self.assertEqual(rows,original)

    def test_empty_week_does_not_promote_a_future_edition(self):
        rows=[event('nov-14','2026-11-14T12:00:00-07:00')]
        doc=BeautifulSoup(build.homepage_sections(rows,date(2026,11,1),{},''),'html.parser')
        week=doc.select_one('.gh-week')
        self.assertEqual(week['data-window-end'],'2026-11-06')
        self.assertFalse(week.select('.gh-row'))
        self.assertTrue(week.select_one('.gh-filters').has_attr('hidden'))
        self.assertTrue(week.select_one('.gh-lead').has_attr('hidden'))
        self.assertIn('Calendar',week.get_text())

    def test_canonical_bytes_and_generated_navigation(self):
        expected='115afb6b6e0b23111faae3998b47e85df994f93c7ccdbaaf3b00c311888b02ae'
        for name in ['data/events.json','calendar/events.json','map/events.json']:
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
        for path in ROOT.rglob('*.html'):
            if '.git' in path.parts:continue
            doc=BeautifulSoup(path.read_text(),'html.parser')
            for link in doc.select('nav a[href$="upcoming/"]'):
                self.assertEqual(link.get_text(strip=True),'This Week',str(path))


if __name__=='__main__':unittest.main(verbosity=2)
