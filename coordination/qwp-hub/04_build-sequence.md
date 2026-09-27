# QPW HUB v0.1 — Build Sequence + Acceptance Tests

## Phase A — Read-only Hub
Build a mobile-first page that reads existing Supabase state:
- recent BUS activity
- coordination tasks
- approval-like items
- network status derived honestly from runtime state

No writes yet.

**Pass:** loads on mobile, useful in under 5 seconds, no secret keys in client.

## Phase B — One Command
Add one command box.
A submitted command becomes one canonical BUS message / task intake event.

**Pass:** submit once -> durable row -> visible in Hub -> LUNA can see it without MASTER INDY relaying.

## Phase C — Team Routing
Add NEXUS routing rules as simple deterministic logic first:
- explicit @mention wins
- domain tags map to LDI role
- otherwise audience = team / NEXUS triage

Do not add model-based routing until deterministic routing is proven.

**Pass:** same input always produces explainable routing.

## Phase D — Updates + Approvals
LDIs post structured updates/evidence.
Hub shows one unified task state.
Only consequential choices enter Needs You.

**Pass:** MASTER INDY can approve/decline from Hub without switching chats.

## Phase E — Realtime
Subscribe the Hub to relevant state changes.

**Pass:** LUNA update appears without refresh; reconnect does not lose canonical state.

## Phase F — Runtime adapters
Only now add Node.js worker/adapters for:
- persistent polling/dispatch
- retries
- external connectors
- local MSI runtime
- future NEXUS service

## Verification checklist
- versioned branch + PR
- no direct main push
- RLS reviewed
- no service-role key in browser
- no fake online/working status
- message dedupe
- durable task/evidence links
- mobile first
- failure state visible
- user never becomes courier

## Ownership proposal
- LUNA: persistent watcher, Supabase integration, Realtime verification, operational test.
- HEPHAESTUS: architecture, contracts, UI/system review, implementation critique.
- NEXUS: routing policy and orchestration rules.
- MINERVA: provenance/canon rules.
- CODEX: tests, failure injection, runtime/implementation verification.

## Build instruction
LUNA may begin **Phase A only** while finishing Golden Hour Batch 1, provided the work is isolated and does not interfere with that repo/site work. Before any schema change, privileged function, or new deployment target, send proposal/evidence through BUS for review.
