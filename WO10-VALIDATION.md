# WO10 design fixes — validation and handoff

Source: 0018 visual review and 0019 work order, ZIP SHA-256 `2ec05914687cf818fc58f34daaf89de36b14858b862066d6af7896968fb3c305`. Base: main at `bb77e735ae3971cdc378b3a2ff3c59893effbe9d`, including the separately merged light-default rider. Evidence labels below distinguish local observations from production acceptance.

## All 12 fix groups

| Group | Repair | Verification |
|---|---|---|
| 1. Calendar | Empty markers replaced by titled event buttons: at most three per date and a labelled “+N more.” Desktop keeps the month grid; phones get a dated monthly event list with empty days omitted. Month heading renders before data arrives. | OBSERVED_LOCAL: title buttons, eight-event Oct 31 agenda, next/Today, dialog opening, Escape, focus restoration and focus trap passed. |
| 2. Sources | Desktop tables become labelled Source / Reliability / Notes cards on phones. Headers and words do not break mid-word. | OBSERVED_LOCAL: 390px and 1440px screenshots, labelled cells, normal word-breaking, no page overflow. Source text/links retained. |
| 3. 404 | Real `404.html`, branded error message, recovery links and noindex. Its asset base supports the GitHub project path and root/custom-domain hosting, including nested missing URLs. | OBSERVED_LOCAL: actual HTTP 404 responses with working shared CSS and recovery URLs on both path layouts. Production routing remains post-merge. |
| 4. Artwork | Official images are shown full-frame with `object-fit: contain`; homepage collage uses aligned frames with no rotated/staggered offsets. Event heroes and modal/popup imagery retain the whole frame. | OBSERVED_LOCAL: before/after home, Digable Planets, Events and Upcoming screenshots. No image files changed. |
| 5. Top Picks | Shared card frame, body and type hierarchy. Missing photos use a designed category/name/score header; score has its own spacing. Failed remote photos also fall back to this treatment. | OBSERVED_LOCAL: eleven picks render; no lone-letter placeholders. Existing scores, descriptions, addresses and credits retained. |
| 6. Events / Upcoming | Both render the same card markup and six filters. Artwork stays visible above a solid AA caption surface, replacing the near-black overlay. Full booking fields/blurb remain available in Details & booking; official-source and copy actions use the shared control system. | OBSERVED_LOCAL: identical card markup, 22 occurrences in order, category filters, details and clipboard action passed on both pages. All eight required Halloween routes retained. |
| 7. Map | Added Map heading; uniform range/category grids; actual legend swatches; 44px zoom controls; resize/font-ready invalidation; explicit cluster anchors and no transient initial cluster animation. | OBSERVED_LOCAL: non-overlapping visible markers, equal filter widths, and loaded real OSM tiles covering both map edges after 390 → 1440 → 390 resize. |
| 8. Header / footer | Date/weather form one context group beside the theme control; wordmark has no emoji. Shared navigation has deliberate wrapping and 44px links; footer keeps all nine discovery links. Halloween is confined to its removable homepage banner. | OBSERVED_LOCAL: controls stay inside the strip, full wordmark, all footer links, no internal-page seasonal banner. A1 theme choice behavior retained. |
| 9. Event details | “Listing source checked” badge has inverse AA colors. Field verification caveat is explicit; existing unverified prices/ages are retained. Values have room inside the details box; return links have clear hit areas. | OBSERVED_LOCAL: Digable Planets detail in both themes/widths, badge/note/field wording and full-frame artwork. |
| 10. Counts | Press's upcoming count derives from the canonical dataset and Denver build-date cutoff. Existing map, calendar and picks counters already derive from data and remain intact. | OBSERVED_LOCAL: press count matches both generated lists (22 at Oct 30); no hand-entered event count. |
| 11. Archive / Activities | Archive heading aligns with navigation; its existing edition becomes a dated card with its original arrival line. Golf becomes a featured typographic guide with its existing content/link. | OBSERVED_LOCAL: one real archived edition, one real golf guide, no invented editions or activities. |
| 12. Details | Homepage THEN entries use a hanging indent; tagline uses readable normal text; calendar legend/targets are legible; Top Picks map has an unobscured place label above markers. | OBSERVED_LOCAL: screenshots and geometry checks. Legacy template card padding and Shoulder Season page width also repaired after the all-page audit exposed overlaps. |

The “no scrim” choice in group 6 is intentional: copy sits on a solid surface below the complete artwork, so no text needs to cover or darken poster lettering. Missing-image cards have full designed type headers, not empty media fields.

## Evidence and regression checks

- OBSERVED_LOCAL: 48 screenshot/contrast combinations — 12 page groups × 390/1440px × light/dark. Zero horizontal page overflows, zero runtime errors, zero reported contrast violations and zero incomplete contrast checks in that settled viewport pass.
- OBSERVED_LOCAL: a separate 136-combination scan covers all 68 HTML pages in light/dark. Zero reported contrast violations. Six map-only review flags occurred during dynamic layout/for the non-text zoom glyph; the settled viewport pass and marker/tile/control checks cover those cases. This is not a claim that axe alone certifies WCAG.
- OBSERVED_LOCAL: browser interaction suite passes all four viewport/theme combinations under BOTH project-path and root hosting. Calendar selection/dialog keyboard flow, list/filter/copy behavior, source layout, picks, Map, nested 404s, press count/placeholder, Archive and Activities are exercised.
- OBSERVED_LOCAL: cache v4 is removed on v5 activation; 404 is precached; a visited hub reloads offline under both hosting layouts. Service-worker policy still preserves genuine network 404s.
- OBSERVED_LOCAL: all local HTML links/assets resolve; JSON-LD parses; repeat builds stabilize; JavaScript syntax and diff-whitespace checks pass.
- MOCKED_WEATHER: deterministic Open-Meteo responses make the screenshots repeatable. These screenshots do not certify a fresh live reading. The production weather endpoint and failure logic are unchanged.
- OBSERVED_PUBLIC_RESPONSES: Leaflet, map tiles and existing remote pick photos are loaded through their public URLs, with a local response cache for repeatability. No new imagery is introduced.

The shared Drive evidence ZIP contains a local HTML screenshot index, before/after images, raw scan results, functional results and source hashes. Its link and hash are recorded in the PR and master index `0000-INDEX.md`.

Evidence download: [WO10 visual evidence](https://drive.google.com/file/d/12VDOpiRsrQkjf_pbL0OEBO3RP54EqakF/view). Read `index.html` after extracting the ZIP; the final source manifest identifies the captured implementation.

## Hard guards

`data/events.json`, `calendar/events.json`, and `map/events.json` remain byte-identical to base (SHA-256 `115afb6b6e0b23111faae3998b47e85df994f93c7ccdbaaf3b00c311888b02ae`). `picks/picks.json` is also unchanged. No event facts, image files, photography credits, prices or age policies are rewritten.

The press placeholder element is identical to base and deliberately remains BLOCKED on MASTER INDY, as 0019 requires. Existing drafts and field-verification qualifiers are not converted into factual claims. Personal sign-off text remains absent from site HTML. Press remains unlisted/noindex. Halloween removal still requires only `skin: null` plus a rebuild; its removal is a separate work order. The light-default/localStorage logic from WO8-R1 is not duplicated or changed.

## Publish Standard — seven checks

1. WORKS: local end-to-end interactions pass, beyond the static build.
2. PHONE-FIRST: observed at an emulated 390px phone viewport, plus 1440px desktop; physical-phone acceptance belongs to LUNA's live pass.
3. VERIFIED LIVE: PENDING after MASTER INDY's merge and successful deployment on both hosts. Local screenshots and PR checks do not replace it.
4. NO PLACEHOLDERS: no new placeholders. Press email stays BLOCKED and unchanged under the explicit WO10 guard; no full pass is claimed for this gate.
5. DETAILS SWEEP: layout, copy preservation, dates/counts, artwork framing and verification qualifiers checked. Existing image bytes are unchanged; LUNA rechecks their live presentation.
6. FINDABLE: introduced error page has title/description/noindex. Previously generated historical event routes gain missing metadata/structured data and four missing sitemap entries. Public pages have a share image; the existing unclipped app-brand tile replaces the cropped legacy share graphic reference. Existing event imagery is preserved.
7. PROUD TEST: LUNA and MASTER INDY make the final visual judgment. This PR supplies the review evidence and does not claim publication approval.

## Reproduce

```sh
pip install -r requirements-design.txt -r requirements-qa.txt
python build_design.py
python build_design.py --check
python tests/preview_server.py --port 8781 --prefix /this-week-in-aspen/
# In another terminal, with Chromium installed:
CHROMIUM_PATH=/usr/bin/chromium python tests/wo10_browser.py
```

For root hosting, serve with `python tests/preview_server.py --port 8790` and run the browser suite with `BASE_URL=http://127.0.0.1:8790/`. Browser checks were run locally before the PR; existing CI verifies the static design/feed contract. Do not merge or deploy from these preview commands.
