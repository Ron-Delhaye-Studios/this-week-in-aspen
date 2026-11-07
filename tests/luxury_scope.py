"""Forward horizon and attribution behavior; canonical data remains untouched."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import sys
import unittest
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from week_scope import coming_up, this_week
from build_design import homepage_sections
from design.finish_image_credits import apply

def event(slug,when,**flags):
    return dict(id=slug,slug=slug,title=slug,starts_at=when,category='music',venue='Test venue',url='https://example.com',price_info='',**flags)

class LuxuryTests(unittest.TestCase):
    def test_week_precedes_horizon_without_mutating_input(self):
        rows=[event('later','2026-11-14T12:00:00-07:00'),event('week','2026-11-03T12:00:00-07:00')];before=deepcopy(rows)
        chosen,horizon=coming_up(rows,date(2026,11,1));self.assertFalse(horizon);self.assertEqual([e['slug'] for e in chosen],['week']);self.assertEqual(rows,before)
    def test_horizon_sorted_verified_deduplicated_and_limited(self):
        rows=[event(str(n),f'2026-11-{n:02}T12:00:00-07:00') for n in reversed(range(10,19))]
        rows+=[rows[0],event('draft','2026-11-07T12:00:00-07:00',verified=False),event('past','2026-10-31T23:59:00-06:00')]
        chosen,horizon=coming_up(rows,date(2026,11,1));self.assertTrue(horizon);self.assertEqual([e['slug'] for e in chosen],['10','11','12','13','14']);self.assertEqual(this_week(rows,date(2026,11,1)),[])
    def test_denver_date_not_utc_day_controls_cutoff(self):
        rows=[event('prior','2026-11-01T05:30:00Z'),event('last-local-day','2026-11-08T02:00:00Z')]
        chosen,horizon=coming_up(rows,date(2026,11,1));self.assertFalse(horizon);self.assertEqual([e['slug'] for e in chosen],['last-local-day'])
        beyond=event('future','2026-11-08T07:00:00Z')
        chosen,horizon=coming_up([rows[0],beyond],date(2026,11,1));self.assertTrue(horizon);self.assertEqual([e['slug'] for e in chosen],['future'])
    def test_empty_feed_offers_positive_guide_paths(self):
        doc=BeautifulSoup(homepage_sections([],date(2026,11,1),{},''),'html.parser').select_one('.gh-week')
        self.assertNotIn('No verified',doc.text);self.assertEqual([a['href'] for a in doc.select('.gh-list-empty a')],['picks/','activities/'])
    def test_credits_match_cover_swap_and_remove_old_plate(self):
        doc=BeautifulSoup('<html><head></head><body><figure class="gh-cover-frame"><img src="assets/img/cover-maroon-bells.jpg"></figure><p class="gh-cover-credit">old</p><footer class="gh-footer"><p class="gh-credits">stale</p></footer></body></html>','html.parser')
        apply(doc,ROOT/'index.html',ROOT);self.assertIn('Lorie Shaull',doc.select_one('.gh-credits').text);self.assertNotIn('Jeffrey',doc.select_one('.gh-credits').text)
        doc.img['src']='assets/img/lead-ute-cemetery.jpg';apply(doc,ROOT/'index.html',ROOT);apply(doc,ROOT/'index.html',ROOT)
        self.assertEqual(len(doc.select('.gh-credits')),1);self.assertIn('Jeffrey Beall',doc.select_one('.gh-credits').text);self.assertNotIn('Lorie',doc.select_one('.gh-credits').text)
    def test_hidden_and_unrelated_images_do_not_get_credits(self):
        doc=BeautifulSoup('<html><head></head><body><div hidden><img src="../../assets/img/lead-ute-cemetery.jpg"></div><img src="https://external.test/assets/img/cover-maroon-bells.jpg"><footer class="gh-footer"></footer></body></html>','html.parser')
        apply(doc,ROOT/'events/test/index.html',ROOT);self.assertFalse(doc.select('.gh-credits'))

if __name__=='__main__':unittest.main()
