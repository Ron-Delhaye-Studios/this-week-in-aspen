# Accuracy and bands — implementation evidence

Base: main `23ef449b07ddc31effcd15a1cc39afe33432a055`. No event-source export, legacy canonical feed, score or supplied image changes.

## Behavior
- Shared Denver calendar-day cutoff and stable day/band/time/ID ordering. Ongoing records stay eligible through their end day. Day-cell ordering uses band/time when an ongoing record began earlier.
- Verified public AURELIAN sources only; routine worship/regular-class/standing-hours defense at render and intake. Seasonal specials remain eligible. No numeric scoring.
- Events, homepage, This Week, Calendar and Map consume the current adapter; Calendar and Map refresh on minute/resume/pageshow and fail honestly. Missing coordinates produce an explicit map limitation. No invented geocodes.
- Current export remains legacy-unbanded. Renderer accepts supplied bands but never invents them. `validate_calendar.py --require-bands` rejects incomplete future payloads. LUNA's corrected and fully banded payload is still required separately.
- Current overview language switches to Past event after its Denver end day, including on an open page. Existing routes remain.
- Source methodology lives in llms.txt and /agents/. Guest copy uses the short trust line. Agent index added to sitemap.
- Existing rolling-window and immutable-canonical tests retained. Compatibility output uses LF on Windows as on Linux.

## Validation
Executed on Windows with Python 3.12, pinned design dependencies and tzdata, using UTF-8 mode:

```
python build_design.py
python build_design.py --check
python tests/wo19_static.py
python tests/wo21_scope.py
python tests/wo20_features.py
python tests/luxury_scope.py
python tests/event_flow.py
python tests/calendar_intake.py
node tests/event_policy.cjs
git diff --check
```

271-page build/check and static guards PASS; 9 scope, 8 feature, 6 luxury, 5 event-flow and 3 intake tests PASS. Node assertions cover Denver/DST/all-day boundaries, bands, sources, verification, media paths, project-prefixed links, failed/malformed feeds and retry. Script syntax checks PASS. No tests skipped or suppressed.

## Remaining acceptance — not merge-ready
Browser control is disabled in this session. No visual screenshots, installed-phone acceptance or live journey are claimed. LUNA must render the preview at 390px and desktop in both themes, verify filters and current-month Calendar, simulate midnight/resume/failure, and inspect the map's honest empty state. Inspect source overview links and the new agent/source surfaces. Supply the fully banded export in its own data PR; current legacy records must not be treated as already curated.

After MASTER INDY merges, LUNA checks both real hosts with screenshots seen and links followed. Deploy checks alone do not close this gate.
