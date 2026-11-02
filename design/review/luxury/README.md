# Golden Hour luxury pass — review record

CODEX · 2026-11-02 · NEEDS_RON_MERGE

Source: [0043](https://docs.google.com/document/d/1mjYFiNFtmNzi2fP6CyQ4NEizFVp7R7lH6FWg4tPGZv0/edit), read in full. Brand Standards0017 read from the indexed WO8 package; Amendment A1 supersedes its original device-theme default. WO19 PRs14–22 were all owner-merged before this branch. Base main: efb00c2 (also includes merged WO21, Search Console slot and WO20 foundation).

## Result

- Removes the duplicate location label; date/weather/theme hooks retain their role. Dates, times, calendar numbers and temperatures use tabular numerals. Phone topbar keeps the date/weather left and theme action right.
- All existing header destinations remain in one momentum-scrolling mobile rail. The rail starts at Latest and keyboard focus reaches How we verify. Focus removes the edge fade. Desktop and footer navigation keep their existing arrangement.
- Homepage uses the current week when it has verified listings. Otherwise it shows up to five unique future verified events, soonest first, labeled **Next on the Calendar**. Edition dates and /upcoming/ remain strictly current-week. An exhausted feed offers Top Picks and Activities; it invents no listings. Offline views preserve the explicitly labeled server horizon and prune expired rows.
- CC metadata comes from data/image-credits.json, transcribed from the existing approved cover and homepage credits. The builder and browser match actual image paths, deduplicate credits, and remove hidden/absent plate credits. Cover swaps update both caption and footer. Existing event promo captions and feature-local credits keep their own provenance. New CC plates must be registered before publication.
- New shared presentation CSS is loaded on all70 existing pages; legacy regeneration adds it automatically in the correct stylesheet order. A service-worker revision carries the new assets to installed clients.

## Guard evidence

1. **A1:** fresh browser preferring dark defaults to warm paper; explicit dark choice survives reload. Light status band matches body. Existing safe-area backgrounds remain.
2. **Media:** no new photographs; no Ron photography or studio credit. Existing approved plates only.
3. **Canonical data:** all three event JSON files retain SHA256 `115afb6b6e0b23111faae3998b47e85df994f93c7ccdbaaf3b00c311888b02ae`.
4. **Public brand:** name/tagline/wordmark, footer-only guide discovery and forbidden-signoff/internal-name guards retained. No navigation redesign or invented elevation claims.
5. **Legibility:** automated axe WCAG2 A/AA + WCAG2.1 A/AA: zero violations on the homepage at390/1440, light/dark. Caption colors use text-grade tokens; no reduced-opacity text. The audit exposed an inherited theme-button accessible-name mismatch; its name now matches the visible action.

## Validation

- Six new horizon/attribution tests; eight week-scope and eight feature tests passed.
- Full design build + --check and existing70-page static guards passed.
- Browser: no horizontal overflow, broken images or JS errors; single mobile nav row and keyboard reach verified; cover-credit swap/hidden-image cleanup and exhausted-feed actions passed.
- Offline fallback pruning, fresh light default, stored dark choice and inner-page nav checks passed.
- [Machine results](browser-results.json); [phone light](home-390-light.png), [phone dark](home-390-dark.png), [desktop light](home-1440-light.png), [desktop dark](home-1440-dark.png).

Chromium checks do not certify physical iOS acceptance. The inherited cover paragraph still references Halloween despite merged WO19; this PR's four requested changes do not rewrite that editorial copy. The separate engine-first data integration is also unchanged.

## Reproduce browser proofs

Install Playwright, Chromium and axe-core outside the checkout. Serve with
`python tests/preview_server.py --port 8784`. Run `tests/luxury_browser.py` with
`CHROMIUM_PATH` and `AXE_PATH` pointing to those local installations. Browser tests
use a fixed Denver date and deterministic weather; event data comes from the
unchanged publication feed.

## Owner optimization follow-up

Added after the owner's request to contribute branding and UX improvements:

- The same approved footer wordmark now fits320/390/430/1440px with normal and
  italic Playfair900 loaded. Text-range geometry catches clipping that page
  overflow and automated accessibility checks missed. See brand-geometry.json
  and footer-320/390-light/dark.png.
- Unchanged event data no longer replaces the This Week card/chip DOM on minute,
  pageshow or visibility refresh. Open booking details, copy feedback and keyboard
  focus survive. Filter changes update selected state without replacing cards.
- The homepage also retains its unchanged lead image and rows; changing a filter
  preserves the chip focus and avoids recreating an identical lead image.
- Denver date rollover still removes expired records from HTML and JSON-LD.
  Both-theme browser proofs: live-state-results.json; reproduce with
  tests/live_state_browser.py against the local8784 preview server.
- Cache revision luxury:2 carries these fixes. Canonical event bytes remain unchanged.
