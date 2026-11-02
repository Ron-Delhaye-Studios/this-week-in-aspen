# WO21 — This Week and light-mode top-band repairs

Sources: [0046](https://drive.google.com/file/d/1mpZM9FgvGl9O2aF93edXumeXcHZZtyV_/view) and [0047](https://drive.google.com/file/d/1gsJp5SVU8C8AgIsDopsVsE8uw-_D5TcJ/view), plus the owner's three marked phone screenshots. Base: `90664f8` (owner-merged WO19 chrome). Gate: **NEEDS_RON_MERGE**.

## Result

- In light mode, the root, body, full-width top bar, inner row, weather/toggle surfaces and fixed safe-area scrim use the existing paper token `#faf4e8`. The light scrim is opaque and has no backdrop blur. Dark-mode selectors, colours and safe-area geometry are preserved.
- The homepage weekly filters no longer repeat `safe-area-inset-top` or add their own vertical margins. Existing section/head/card styling stays in place.
- `/upcoming/` remains the route and canonical URL; its heading, document/social metadata, navigation and homepage Explore tile now say **This Week**.
- One row of compact **All · Music · Art · Free** chips replaces the six-button grid on that page. Each retains a 44px hit area. Empty categories are hidden; an entirely empty week hides the row.
- Both weekly surfaces use the existing Saturday–Friday edition convention in **America/Denver**, including DST. They show remaining verified occurrences from today through Friday, sorted by start time. No rollover into a later event's week to fill an empty edition. Explicit unverified/draft/provisional flags are excluded; existing unflagged records retain their publication-feed status.
- Later dates stay on Calendar/Events. The duplicate farther-future homepage event band is omitted. Category chips on the homepage use the same eligible set and can show a category beyond its initial five-row preview.
- Cached pages re-evaluate the Denver day on return/each minute, prune expired/out-of-window records even offline, and refresh from the same canonical feed. A new SW revision precaches the new helpers; its takeover refreshes already-controlled weekly pages so prior cache-first styles do not linger.

## Evidence

**PASS:** seven Python scope tests; nine browser scenarios at 320px, 390px and 1440px; build validation; existing WO19 static guards; JavaScript syntax and whitespace checks. Tests cover the Denver DST rollback, Friday/Saturday and year boundaries, empty weeks, explicit verification flags, single-row chips, nonempty-category filtering, DOM/JSON-LD agreement, offline cached rollover, light-default with a dark OS preference, ordinary zero-inset tabs and simulated 47px safe areas. No horizontal overflow observed in the checked page states.

The three canonical files remain byte-identical:

- `data/events.json`
- `calendar/events.json`
- `map/events.json`

SHA256 for each: `115afb6b6e0b23111faae3998b47e85df994f93c7ccdbaaf3b00c311888b02ae`.

On the actual canonical snapshot, as of **Nov 1 Denver time**, the remaining Oct 31–Nov 6 window has **zero** listings. The empty state is intentional; this PR does not invent/import events or relabel November 14 as this week. Events retains all 11 future occurrences; Calendar retains the complete feed.

## Screenshot interpretation

All screenshots are 390px wide. Weather responses are deterministic QA inputs; they are not a live weather verification.

| File in `design/review/wo21/` | What it proves |
| --- | --- |
| `top-light-browser-native-zero-inset.png` | Ordinary browser, native 0px safe-area inset, light default despite dark OS preference. |
| `top-light-browser-safe-area-simulated.png` | Browser with a CDP-simulated 47px top inset. |
| `top-light-INSTALLED-CHROMIUM-simulated-safe-area.png` | **Actually installed and launched headful Chromium PWA**, disposable profile, `display-mode: standalone` asserted. Phone viewport and 47px safe area are simulated. **This is not a physical iPhone capture.** |
| `coming-up-populated-reference-week.png` | Canonical events, clock fixed to Nov 14 solely to show populated heading/date/chips/card spacing. |
| `this-week-populated-reference-week.png` | Same canonical reference week; Art/Free chips correctly absent when empty. |
| `this-week-current-empty.png` | Actual snapshot's empty current-week treatment. |
| `this-week-four-chips-FIXTURE.png` | Clearly synthetic QA feed exercising all four chips, not published listings. |

**Physical iOS installed-app acceptance remains pending with LUNA.** Headless, headful desktop and simulated safe-area checks do not certify the iPhone status bar. Review this on an installed iPhone before treating Fix 1 as physically accepted. No merge or deployment has been performed by CODEX.

## Reproduce

```sh
pip install -r requirements-design.txt -r requirements-qa.txt
python tests/wo21_scope.py
python tests/preview_server.py --port 8781
# Separate shell; current Chromium + DISPLAY needed for installed-app portion:
DISPLAY=:99 CHROMIUM_PATH=/path/to/current/chrome python tests/wo21_browser.py
python build_design.py --as-of 2026-11-01 --check
python tests/wo19_static.py
```

The browser suite uses the experimental Chromium PWA install/launch and safe-area-override CDP commands. Its temporary app is uninstalled after the proof. The source build's date-scoping check must use the same as-of date as the generated snapshot, or rebuild first for a new date. No new production dependency is added.
