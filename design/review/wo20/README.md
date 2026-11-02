# WO20 — magazine blend / registry template foundation

CODEX · 2026-11-02 · NEEDS_RON_MERGE

This PR delivers the reusable build, not completed town reporting. No production
registry or sourced town packet is present; no new place pages publish from this
branch. LUNA has been asked on BUS for the engine registry and Basalt packet.

Owner sources read: 0040 (one calendar), 0048 (Destination model and both photos),
0049 (Road Trip blend), 0050 (roundup, filed for hiking later), 0051 (registry and
searchable breadcrumbs). The owner source controls mobile reading order.

The feature supplies kicker, original line mountain ornament, serif headline,
byline, italic lede, STAY / PLAY / EAT prose entries, one canonical seasonal event,
weekly feed subset, credited wide/tall imagery, and edition/source folio. No
magazine prose, images, bylines or traced ornament are copied into the website.

Registry records drive pages, valley hubs, four-level visible/JSON-LD breadcrumbs,
canonical URLs and sitemap additions. Thin places get a character line and verified
events, without fabricated stops or filler photos. Full feature packets replace
that skeleton after validation. Matching event pages receive a fifth breadcrumb.
Footer discovery remains; homepage/Events use the previously authorized Down the
Valley strip. Main navigation is untouched. No intelligent navigation design is added.

Canonical event files remain byte-identical. The template consumes existing explicit
place keys; the engine/source integration is a separate PR. Missing or unverified
content cannot be silently promoted. The registry import contract is documented
in data/features/README.md and will be adapted to LUNA's supplied engine export.

## Review images

All four screenshots are **layout proofs with sample text**, not publishable Basalt
coverage. The banner and image captions say so. The existing licensed Aspen-area
images demonstrate geometry only; production rejects them for Basalt. The sample
events exist only under tests/fixtures and the external preview directory.

- [390px light](feature-390-light.png)
- [390px dark](feature-390-dark.png)
- [1440px light](feature-1440-light.png)
- [1440px dark](feature-1440-dark.png)

## Validation

- 8 publication/registry/schema tests; 8 existing week-scope tests passed.
- Existing 70-page static guards and full design build + --check passed.
- Browser checks at 390/1440, light/dark: zero broken images, no overflow, no JS
  errors; town-only weekly sample and next-week removal (HTML + JSON-LD) passed.
- Browser results are in browser-results.json. These are Chromium layout checks,
  not physical installed-iPhone acceptance of WO21.
- No automated WCAG conformance claim is made by these checks.

Required next inputs: ready sourced registry records; LUNA's sourced Basalt lede,
byline and STAY/PLAY/EAT prose; canonical town-keyed event/highlight records from
the separate engine integration; two town-local credited licensed/promo images.
Owner merge remains the gate. No merge or deployment by CODEX.
