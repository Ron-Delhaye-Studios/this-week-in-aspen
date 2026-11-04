"""Presentation-only edition window; never rewrites the canonical event feed."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

DENVER = ZoneInfo('America/Denver')
FILTERS = [('all', 'All'), ('music', 'Music'), ('arts', 'Art'), ('free', 'Free')]
DESCRIPTION = 'Every verified event this week in Aspen and the high country, soonest first.'


def week_bounds(day):
    # Rolling discovery window, including today and the following six days.
    return day, day + timedelta(days=6)


def is_verified(event):
    # This legacy publication feed omits verification flags. Explicit draft,
    # provisional or unverified additions must never inherit that legacy trust.
    return (event.get('verified', True) is True
            and event.get('status', 'approved') in ('approved', 'verified', 'published')
            and event.get('confidence', 'CONFIRMED-2026') in ('CONFIRMED-2026', 'CONFIRMED', 'verified'))


def is_free(event):
    import re
    return bool(re.search(r'\bfree\b|^\$?0(?:\D|$)', event.get('price_info') or '', re.I))


def this_week(rows, day):
    start, end = week_bounds(day)
    return sorted((event for event in rows if is_verified(event)
                   and max(start, day) <= datetime.fromisoformat(event['starts_at']).astimezone(DENVER).date() <= end),
                  key=lambda event: datetime.fromisoformat(event['starts_at']))


def available_filters(rows):
    return [(key, label) for key, label in FILTERS if rows and
            (key == 'all' or any(is_free(e) if key == 'free' else e['category'] == key for e in rows))]


def coming_up(rows, day):
    """Keep the weekly edition; explicitly label a forward-calendar fallback."""
    weekly=this_week(rows,day)
    if weekly:return weekly,False
    future=sorted((e for e in rows if is_verified(e) and datetime.fromisoformat(e['starts_at']).astimezone(DENVER).date()>=day),key=lambda e:datetime.fromisoformat(e['starts_at']))
    seen=set();chosen=[]
    for event in future:
        if event['slug'] in seen:continue
        seen.add(event['slug']);chosen.append(event)
        if len(chosen)==5:break
    return chosen,True
