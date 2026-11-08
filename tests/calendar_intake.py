"""Intake rejects missing bands, duplicates and routine records without rewriting data."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validate_calendar import validate


class IntakeTests(unittest.TestCase):
    def row(self, **extra):
        return dict(id='id', title='Concert', source='aurelian-local', verified=True, start='2026-11-08T19:00:00-07:00',end='2026-11-08T21:00:00-07:00', **extra)

    def test_requires_upstream_band(self):
        with self.assertRaisesRegex(ValueError,'band'):validate({'events':[self.row()]},True)
        self.assertEqual(validate({'events':[self.row(band='FEATURED')]},True),1)

    def test_no_duplicates_or_unapproved_sources(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):validate({'events':[self.row(),self.row()]})
        row=self.row();row['source']='personal'
        with self.assertRaisesRegex(ValueError,'source'):validate({'events':[row]})

    def test_routine_exclusion_retains_seasonal_special(self):
        row=self.row();row['title']='Sunday Worship — Church'
        with self.assertRaisesRegex(ValueError,'routine'):validate({'events':[row]})
        row['title']='Christmas Sunday Worship — Church'
        self.assertEqual(validate({'events':[row]}),1)


if __name__=='__main__':unittest.main()
