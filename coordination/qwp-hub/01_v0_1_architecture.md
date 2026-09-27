# QPW HUB v0.1 — Architecture

## Cheapest practical shape

```
QPW HUB web UI
   |
   | command / approvals / read state
   v
Supabase
   |- bus_messages
   |- coordination_tasks
   |- coordination_task_events
   |- bus_artifacts
   |
   +-- Realtime updates to UI
   |
   +-- LUNA persistent watcher/runtime
   +-- HEPHAESTUS session rehydration
   +-- future NEXUS router
```

## Important simplification
Do **not** require a dedicated always-on Node server in v0.1.

Use Supabase directly for state + Realtime, and a thin serverless coordinator only where privileged routing is needed.

Node.js remains useful later for:
- local/persistent worker runtime
- connector adapters
- retry workers
- background dispatch
- artifact handling
- testing/admin CLI

This avoids paying for or maintaining an always-on service before the workflow proves itself.

## Runtime model
- LUNA: persistent, may watch BUS continuously.
- HEPHAESTUS: session-bound; on activation performs automatic sync/rehydration.
- Other ChatGPT LDIs: same session-bound pattern.
- Future persistent workers may subscribe/poll and claim work.

## Message flow
1. MASTER INDY submits command to Hub.
2. Hub writes one canonical command/event.
3. NEXUS routing logic determines relevant roles.
4. BUS messages/task ownership are created.
5. LDIs work and write deltas/evidence.
6. Hub aggregates state.
7. MASTER INDY sees one team result, not raw internal chatter.

## v0.1 restraint
No autonomous model fan-out, no complex DAG engine, no giant dashboard, no custom memory system, no multi-cloud orchestration yet.
