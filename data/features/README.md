# Engine places and feature packets

No production place registry or town editorial packet has been supplied in this
branch. Without those inputs the builder creates no place routes or discovery.
LUNA owns registry, source integration and copy; Ron's merge is the publication gate.

`data/places.json` is an engine-exported array of records. Each requires `slug`,
`name`, `valley: {slug, name}`, sourced `character`, `source_url`, `last_checked`,
`verification: CONFIRMED-2026`, and `ready: true` to publish an honest skeleton.
The engine may also supply coordinates and source sets. Templates contain no town
list. Existing explicit event place_key/town_key/town fields match registry keys
or exact registry names; venues and coordinates never imply a town.

LUNA supplies `data/features/<place>.json` when coverage supports a full feature:
`town_key` (registry slug), exact `town`, `department`, `edition`, `lede`,
`editorial_by`, `source_url`, `last_checked`, `verification: CONFIRMED-2026`,
`ready: true`; three to six ordered `entries` (section STAY / PLAY / EAT, name,
description, source_url, last_checked, verification); `highlight_event_id`,
`highlight_last_checked`; exactly two `photos` (file, alt, caption, credit,
license_url, source_url, place_key, last_checked, verification).

The highlight references the ONE canonical `data/events.json` feed. No copied
local calendar and no confidence promotion. Source integration stays a separate
PR. All dates and permission evidence must be supplied and reviewed, never invented.
An invalid ready packet fails the entire place build before writing any documents.

Review fixtures belong under `tests/fixtures/`, with `review_fixture: true`. Render:

```
python build_features.py --preview tests/fixtures/feature-basalt-review.json \
  --output /tmp/gh-feature-review --as-of 2026-11-01
```

The preview must be outside the published checkout; it is labeled and noindex.
Its Aspen sample images are explicitly marked as layout samples, not Basalt.
Production rejects the fixture, wrong-town photography, Ron photography, missing
credit/permission/source evidence, future check dates, and unverified highlights.
A ready flag is a content-completeness flag, never owner merge authorization.
