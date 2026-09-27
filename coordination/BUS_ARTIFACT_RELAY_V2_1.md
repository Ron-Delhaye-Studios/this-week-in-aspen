# QPW BUS Artifact Relay v2.1

## Purpose
Move large payloads reliably without forcing oversized BUS rows or MASTER INDY to courier content.

## Pattern
1. Put the full payload in a durable artifact store.
2. Prefer a versioned GitHub branch/file for code, design, specs, and review packets.
3. BUS carries only a compact manifest:
   - artifact_id
   - repo / branch
   - artifact paths
   - short summary
   - requested action
   - requires_reply
4. Recipient reads artifacts, ACKs the manifest, and returns work through the same pattern.
5. Large replies become new artifacts; BUS carries references, not duplicated bodies.

## Why
- smaller BUS messages are more reliable
- artifacts are versioned and reviewable
- code/specs stay close to implementation history
- avoids giant raw-SQL payloads
- supports branch/PR evidence
- MASTER INDY stays out of courier duty

## Rules
- MESSAGE != TRANSPORT.
- BUS = routing, state, thread, ACK, handoff.
- Artifact store = full payload.
- One manifest = one intent.
- Branch/PR for implementation; no direct-main writes unless explicitly approved.
- Never publish sensitive/private material to a public repo. Use a private/approved store for sensitive payloads.
- Include artifact version and branch/ref.
- Recipient verifies artifact availability before acting.
- If one transport fails, preserve message semantics and switch transport.

## Golden Hour proof
Artifact bundle: GH-REVIEW-20260927-V1
Manifest: BUS-20260927-HEPHAESTUS-LUNA-GHREVIEW-ARTIFACT-0001
This is the first production use of the pattern.
