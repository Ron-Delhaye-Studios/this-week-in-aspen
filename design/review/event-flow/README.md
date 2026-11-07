# On-site event flow and supplied media

CODEX · 2026-11-07 · NEEDS_RON_MERGE

The owner's screenshot showed a static Oct31–Nov6 heading, a text-only discovery
list and an early venue exit. This change keeps the next decision inside the guide:

- Homepage title, lead image, list row and CTA open a stable on-site event overview.
- This Week titles, photos and Event details actions do the same. Calendar's modal
  offers the on-site overview, rather than an immediate outbound link.
- The overview provides the supplied date, venue, full cleaned description and
  verified image. The official source/booking link is explicit and opens a new tab;
  the guide stays open. An on-site This Week return is always available.
- Homepage rows now display supplied event thumbnails. No image means no media
  figure. Storytime has no supplied image; Ben Roy and Easy Jim do. The generated
  JSON and all16 supplied JPGs are unchanged. No unrelated stock or new media added.
- All198 current export records receive regenerated overview pages. Existing older
  routes are retained. Sitemap count249→262 (+13,0 removed); new detail pages have
  self-canonical URLs and Event JSON-LD with the original dates and supplied media.
- Both live shells load GHCalSync through their finishers after every rebuild.
  Static edition attributes/ranges/cards are cleared. The live range comes from
  rendered rows; unavailable feeds show an honest state; Denver midnight clears
  expired cards and their JSON-LD. No generated event JSON is hand-edited.
- Service-worker events revision3 refreshes the changed scripts/styles for
  installed clients. A1 light-first, saved dark theme, original wordmarks and
  canonical event-byte guards are preserved.

## Validation

Full build + --check (270 pages), existing static/9scope/8feature/6luxury tests,
and5new event-flow tests pass. Browser proofs use the Nov6 fixture clock, actual
198-event export, actual supplied media and deterministic weather. Both themes,
390px journey and1440px detail layouts: no page errors; verified image loads;
local navigation; explicit new-tab source action; no empty image figures;
zero automated axe WCAG A/AA violations on the detail-page samples. Calendar
opens on November2026 and leads to an on-site detail. Failed feeds leave no stale
cards; Denver-midnight reopening removes Storytime from HTML and JSON-LD.

Tests: tests/event_flow.py and tests/event_flow_browser.py. Serve this checkout on
8785 with tests/preview_server.py. CHROMIUM_PATH selects Chromium; browser tests
use /workspace/lux-tools/node_modules/axe-core/axe.min.js. Results in
browser-results.json. Chromium proofs do not certify physical iPhone acceptance.

## Screenshots

- home-light.png / home-dark.png: current range and supplied thumbnail media
- upcoming-light.png / upcoming-dark.png: internal title/photo/detail links
- detail-media-light.png / detail-media-dark.png: Ben Roy overview and source action
- detail-no-media-light.png / detail-no-media-dark.png: Storytime without a false image
- detail-desktop-light.png / detail-desktop-dark.png: wider overview layout

Screenshots show the Nov6 proof clock, not live-production verification. LUNA
verifies the real pages with rendered screenshots after the owner's merge.
