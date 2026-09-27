# Batch 3 — Coherence + Accessibility + Systemization

Fresh branch after prior batches settle.

1. **Calendar palette**
   - Reduce Google-rainbow feel.
   - Use a smaller house-derived category palette.
   - Add a visible legend.
   - Keep labels so color is not the only cue.

2. **Map state contrast**
   - Increase distinction between "later" and "past".

3. **Text contrast**
   - Audit meaningful text using `--faint`.
   - Target WCAG AA for real copy.

4. **Event-card hierarchy**
   - Make time/date scan faster.
   - Reserve gold for meaningful **today** emphasis.
   - Do not overpower the title.

5. **Shared design system**
   - Audit duplicated CSS / shell markup.
   - No risky full refactor.
   - Propose the smallest migration path toward a single theme/source of truth, then migrate incrementally.

6. **Freshness / PWA**
   - Audit service-worker/cache behavior.
   - Implement a safer strategy only if verified.
   - Stale event content must not be silently preferred.

7. **Regression pass**
   - /, /upcoming/, /calendar/, /map/, /picks/, /editions/, /sources/

## Execution + versioning rules
- Branch + PR only. Never push direct to `main`.
- Rebase/sync from current main before touching a moving surface.
- No overlapping writes with HEPHAESTUS without BUS sync.
- Preserve protected anchors/deep links and official-source trust model.
- Verify after each batch; never claim completion without evidence.
- If you see a better idea, say **"I have a better idea"** and explain user benefit, architectural benefit, tradeoff, and reversibility.
- MASTER INDY is not the courier. Use BUS for status, blockers, evidence, and handoffs.

## Deliverable format per batch
1. What changed
2. Why
3. Files changed
4. Commit(s)
5. PR
6. Verification
7. Risks / blockers
8. Next recommended action

## Immediate ask
Please ACK this artifact bundle, **start Batch 1 now**, and return your active branch/files through BUS so HEPHAESTUS avoids conflicts.

**AD ASTRA**
