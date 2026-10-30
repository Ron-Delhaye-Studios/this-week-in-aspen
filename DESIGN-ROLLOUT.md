# Golden Hour design rollout — WO8

Version 1.0, 2026-10-30. Implements the written 0016 work order and 0017 Brand Standards v1.0 (keeper: LUNA). Payload SHA-256: `cd24cba5055e0512d4a2eeb15cabc55025e32567fd7d6f066589e2c0fea85656`.

Retrieval entry point: [0000-INDEX.md](https://drive.google.com/file/d/1FE3VhfK4d6G5x1Ty96rWuQZJhNNV6eD9/view), in the shared Golden Hour folder. It provides payload, protocol, BUS, repository, and host addresses. The two JPGs in that ZIP show Cloudflare setup screens, so visual matching against the approved Muse v3.1 concept remains for LUNA to verify with the correct reference. Those screenshots are not shipped as site imagery.

## Build and content contract

```sh
pip install -r requirements-design.txt
python build_design.py
python build_design.py --check
```

Run this build after any legacy page generator. `assets/gh-theme.css` and `assets/gh-theme.js` own the shared masthead, palette, controls, date, weather, and PWA registration. Existing editorial text and source links stay on the static pages. Page layout CSS is retained with its legacy text and background colors replaced by shared tokens. Every HTML page, including archives, templates, and internal/noindex pages, receives the design. Press stays noindex and absent from public navigation.

`data/events.json` is the sole canonical input for the hub, Upcoming, calendar, map and homepage rotation. It reconciles the existing calendar and map feeds by immutable occurrence UUID, preserving the eight Halloween route slugs and the three ghost-tour occurrences. Calendar and map read this input directly; their old JSON locations are generated compatibility exports. The build checks dates, IDs, routes and media; CI fails if compatibility exports diverge. Feed ingestion must update this input and run the build. Do not update the compatibility files independently.

The Events hub and Upcoming use the same Denver-date cutoff (today or later) and chronological order. Their JSON-LD uses the identical set and ordering. The runtime hides expired occurrences and removes their structured data, including across month/year boundaries. Older event detail URLs and archives remain accessible. `--as-of YYYY-MM-DD` supports deterministic checks without altering event dates.

Missing promo imagery stays absent; no unrelated image or new photography is substituted. Existing official event media carries image cards. LUNA reviews the generated wordmark icons and the pages before approval.

## One-change seasonal removal

Change `"skin": "halloween"` to `"skin": null` in `design-config.json`, then run the build. The optional assets supply the garland, wordmark pumpkin, maroon hero color, and greeting. The base system is complete without these assets. Existing Halloween event/edition copy is editorial content and remains in its original context.

## Themes, weather and phone installation

WO8-R1 / Brand Standards A1 (2026-10-30): first visits default to light regardless of device preference. An explicit toggle choice is stored in localStorage and wins across navigation and later visits; storage denial falls back to in-memory state for the current page. Invalid stored preferences fall back to light. Weather uses Open-Meteo current temperature and WMO condition at Aspen's coordinates, in Fahrenheit, every 30 minutes. A failed refresh shows the previous reading with its observation date and Denver time; without a reading it says weather unavailable. It never invents a reading.

Relative manifests, icons, assets and service-worker scope support both the GitHub project path and the Cloudflare root path. The light and dark manifests share one app ID and specify their matching colors; the runtime chooses the current scheme. Both use standalone display and brand-only 192/512 PNG icons plus the 180 PNG Apple icon. Cache `golden-hour-v4` precaches the shell and shared design assets; WO8-R1 advances it from v3 so returning phones receive the new default. Live data and pages use network-first; successful stale fallback never replaces a real 404/410.

## Publication and acceptance

One PR targets main. LUNA verifies the work-order checklist, and MASTER INDY alone merges. CI success, merge, GitHub Pages deployment, and Cloudflare deployment are separate facts. After merge, record the GitHub Pages build/run result and a fresh Cloudflare deployment, then verify both public hosts, including live weather and phone Add to Home Screen. Local Chromium emulation cannot certify installation on a physical iPhone.
