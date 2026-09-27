# Golden Hour — North Star + Review Rubric

**From:** HEPHAESTUS  
**To:** LUNA  
**Authority:** MASTER INDY  
**Status:** execution authorized in versioned batches.

## North Star
The Golden Hour should feel like a **quiet, editorial, high-trust field guide — the friend who actually checked**. It must be useful first, elegant second, and never generic luxury minimalism. Mobile is primary. Reduce cognitive load, foreground **time / date / place**, and make trust visible without exposing internal operations.

## Master design-review rubric
Review and build against:
1. **Five-second first impression** — what is this, who is it for, what can I do, what dominates, and should it?
2. **Visual hierarchy + typography** — coherent scale; time/date/place scan immediately; phone readability.
3. **Color + material** — restrained palette, meaningful color semantics, WCAG AA for meaningful text.
4. **Spacing + rhythm** — consistent scale; calm emptiness vs broken emptiness.
5. **Navigation + IA** — core destinations one tap away; consistent order/state; honest labels.
6. **Interaction + motion** — controls look interactive; purposeful restraint; 44pt minimum touch targets.
7. **Mobile first** — review around 390x844 before desktop; no squeezed-desktop behavior.
8. **Content + trust** — official sources, verification, dates, photos, honest empty states; no internal leakage.
9. **Brand coherence** — every page should feel like one product.
10. **Cut list** — remove at least five things that do not earn their place.

Every criticism gets a concrete remedy. End with the three highest-leverage changes.

## HEPHAESTUS critique / additions
I agree with your major calls: compact utility masthead, 44px touch targets, Archive repair, calendar coherence, source-page cleanup, null/For-prefix fixes, stronger time hierarchy, restrained motion.

Four guardrails:
- **Do not sterilize the product.** Keep local/editorial character and a sense of place.
- **Protect interfaces:** `ev-<uuid>`, `map/?event=<uuid>`, popup Event-details -> `upcoming/#ev-<uuid>`, official-source links, rolling event-window behavior.
- **Shared shell drift is architectural.** Move gradually toward one shared source of truth; no risky big-bang refactor.
- **Freshness is trust.** PWA/service-worker behavior must not silently serve stale event data.
