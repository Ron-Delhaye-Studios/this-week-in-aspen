"""Validate staged AURELIAN payloads without changing export bytes."""
import argparse
import json
from datetime import datetime
from pathlib import Path
import re

SOURCES = {'aurelian-local', 'aurelian-regional'}


def validate(data, require_bands=False):
    seen = set()
    for event in data['events']:
        key = event['id']
        if key in seen:
            raise ValueError('Duplicate event ID: ' + key)
        seen.add(key)
        if event['source'] not in SOURCES or event.get('verified') is not True:
            raise ValueError('Unapproved source or verification: ' + key)
        for field in ('start', 'end'):
            datetime.fromisoformat(event.get(field) or event['start'])
        if require_bands and event.get('band') not in ('FEATURED', 'LISTED'):
            raise ValueError('Missing or invalid intake band: ' + key)
        if 'band' in event and event['band'] not in ('FEATURED', 'LISTED'):
            raise ValueError('Invalid intake band: ' + key)
        title = event['title']
        seasonal = re.search(r'christmas|holiday|festival|candlelight|lessons\s*(?:and|&)\s*carols', title, re.I)
        routine = re.search(r'^(?:Sunday\s+(?:Mass|Worship)|(?:Daily|Weekly|Regular|Routine)\s+(?:Worship|Mass|Service|Class)|Standing hours)\b', title, re.I)
        if event.get('event_kind') in ('routine-worship', 'regular-class', 'standing-hours') or (routine and not seasonal):
            raise ValueError('Excluded routine record: ' + key)
    return len(seen)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--require-bands', action='store_true')
    args = parser.parse_args()
    print('Validated', validate(json.loads(args.path.read_text(encoding='utf-8')), args.require_bands), 'records')
