# The Golden Hour

An insider's pocket guide to Aspen and the Roaring Fork Valley, for concierges and travelers.

Read [AGENTS.md](AGENTS.md) and [CUSTODY.md](CUSTODY.md) before work. Production is [thegoldenhour.guide](https://thegoldenhour.guide); the [Pages mirror](https://ron-delhaye-studios.github.io/this-week-in-aspen/) must also work under its project prefix. MASTER INDY's merge is the only publication gate.

## Build and check

Use Python 3.12. Keep virtual environments and review worktrees outside the checkout: the existing builder discovers HTML recursively.

```sh
python -m pip install -r requirements-design.txt
python build_design.py
python build_design.py --check
python tests/wo19_static.py
python tests/wo21_scope.py
python tests/wo20_features.py
python tests/luxury_scope.py
python tests/event_flow.py
git diff --check
```

On Windows, install `tzdata` for IANA time zones. `--as-of YYYY-MM-DD` on the builder selects a reproducible Denver fixture date. A build rewrites generated output; run it in the relevant branch and inspect the diff.

Browser QA dependencies are in `requirements-qa.txt`; scripts currently expect `CHROMIUM_PATH` or `/usr/bin/chromium`. They provide local evidence only. Do not certify production or physical-phone installation from emulation.

## Content and generation

Current runtime listings consume LUNA's two-calendar AURELIAN export, `calendar/calendar-sync.json`, through `assets/gh-calendar-sync.js`. Never access Personal or Ritz-Carlton calendars. Do not hand-edit generated exports. The older `data/events.json`, `calendar/events.json` and `map/events.json` remain legacy compatibility feeds; preserve their invariants until consumers migrate explicitly.

`build_design.py` composes the shared design; `design/finish_*.py` maintain page families; `build_event_details.py` generates stable overview routes. Change behavior there and in shared renderers, then regenerate, rather than editing individual output pages. See [DESIGN-ROLLOUT.md](DESIGN-ROLLOUT.md) for historical implementation context; its original canonical-feed statement predates the current sync adapter.

## Review and release

One sprint, one branch, one PR. Record base/head, payload references, changed files and relevant test evidence. CODEX never merges or deploys. After MASTER INDY merges, LUNA inspects real rendered pages, images and link journeys on both hosts and records evidence in custody. Merged, deployed and verified live are separate states.
