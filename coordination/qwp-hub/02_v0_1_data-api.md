# QPW HUB v0.1 — Data + API Contract

## Reuse existing tables first
Existing:
- `bus_messages`
- `coordination_tasks`
- `coordination_task_events`
- `bus_artifacts`

Avoid schema expansion until the first Hub loop works.

## Current schema caveat
`coordination_tasks.owner` / `updated_by` / `verified_by` are currently constrained to a small role set. Do not silently broaden them during initial UI work. Treat schema generalization as a reviewed migration after role semantics are agreed.

## Canonical command envelope
```json
{
  "kind": "command",
  "audience": "team",
  "summary": "...",
  "intent": "...",
  "priority": "normal",
  "requires_approval": false,
  "artifact_refs": []
}
```

## Internal response envelope
```json
{
  "kind": "update|decision|blocker|evidence|handoff",
  "task_id": "...",
  "summary": "...",
  "artifact_ref": "...",
  "requires_reply": false
}
```

## Minimal endpoints / operations
v0.1 only needs:
- `submitCommand(command)`
- `getNetworkSnapshot()`
- `ackMessage(messageId)`
- `submitUpdate(taskId, update)`
- `requestApproval(taskId, summary)`
- `resolveApproval(taskId, decision)`

Implementation may be Supabase client + one protected Edge Function rather than a permanent Node server.

## Artifact rule
Large payloads live in durable artifacts. BUS carries manifest/reference only.

GitHub is appropriate for public/non-sensitive code/spec artifacts.
Private/sensitive payloads must use an approved private store.
