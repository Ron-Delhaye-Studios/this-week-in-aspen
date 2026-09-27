# Batch 1 — Trust Repair

Fresh branch from current main. No direct-main writes.

- Clean visitor-facing metadata so empty values do not display as raw data.
- Fix repeated audience-prefix wording at one source of truth.
- Rebuild /editions/ on the shared Golden Hour shell: theme, nav, footer, typography, active state.
- Unify Top Picks naming across nav, heading, and supporting copy.
- Rewrite /sources/ for visitors: keep the trust narrative and useful source names; remove internal implementation notes.
- Improve first-paint placeholder copy without fabricating data.
- Preserve event IDs, URLs, anchors, source links, and Map/Upcoming deep links.

Before PR, inspect every touched route and verify navigation, deep links, sources, and visitor-facing metadata. Return branch, commits, changed files, checks, PR, and blockers through BUS. Do not start Batch 2 until Batch 1 is reviewable.