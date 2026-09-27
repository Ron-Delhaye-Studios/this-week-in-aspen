# Batch 2 — Mobile Shell + Interaction

Start after Batch 1 is reviewable. Fresh branch from then-current `main`.

1. **Compact utility masthead**
   - /calendar/ and /map/: smaller brand, tighter vertical spacing, shared shell, page title below.
   - Homepage keeps the full editorial masthead.

2. **Mobile navigation**
   - <=640px: one horizontally scrolling row.
   - No 2–3 row wrap.
   - >=44px tap height.
   - Preserve order and active state.

3. **Touch targets**
   Bring to >=44px without visual bulk:
   - calendar arrows
   - calendar chips
   - overflow affordance ("1 more")
   - map filters
   - card actions

4. **Calendar -> list**
   - Add **View as list ->** linking to Upcoming.

5. **Reconcile PR #1 correctly**
   - Rebase onto current main.
   - Keep useful mobile CSS only.
   - Preserve approved visible markers: **20px normal / 24px today**.
   - Add a **44x44 transparent hit area** around markers; do not shrink the visible dots.
   - Remove dead `.gh-dot-core` CSS if not wired.
   - Verify/remove `#controls2` if the element does not exist.

6. **Mobile verification**
   - Target ~390x844 or nearest reliable emulation.
   - If exact viewport unavailable, document that limitation.
   - Verify no horizontal overflow, broken wrapping, or unusable control density.
