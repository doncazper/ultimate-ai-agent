# Governed Context Spine Plan

Status: planning artifact. This document does not implement backend routes,
frontend controls, storage changes, runtime context injection, model/provider
calls, connector behavior, graph infrastructure, event-store persistence, or
new authority.

The Governed Context Spine is the planned next layer for making the Founder
Command Center read as one coherent operating loop. The target is not classic
RAG. The target is governed, inspectable task context built from existing
safe refs, evidence, receipts, reviewed memory, approvals, durable runs, and
Founder Loop state.

Working rule:

```text
Events record. Graphs relate. Memory recalls. Evidence proves. Approvals
authorize. Context compiles.
```

## Summary

Build three additive, read-only slices before any future context-injection or
model-consumption work:

1. Product Event Timeline v1.
2. Founder Loop Graph v1.
3. CanonicalTaskContext v1 with a deterministic ContextCompiler.

All three slices must be safe-ref-only, redacted, inspectable through API and
CLI, reversible, and aligned with existing UAA authority boundaries. They must
derive from existing backend-owned state instead of creating a competing source
of truth.

## Non-Goals

This plan must not add:

- classic RAG ingestion
- embeddings, vector DB, semantic search, or background indexing
- hidden prompt stuffing or runtime context injection
- provider/model calls or provider SDK calls
- connector reads/writes, account sync, sends, or calendar writes
- browser automation, shell/subprocess authority, or remote execution
- memory-as-truth behavior
- a new product-wide event store in v1
- public beta, public release, production readiness, or production authority

## Product Event Timeline v1

Add a derived product-wide event timeline over existing Founder Loop state. This
is a read model only, not a new append-first product event ledger.

Planned inputs:

- Action Inbox envelope and decision receipts.
- Evidence Timeline events.
- Memory Review decisions and reviewed recall refs.
- Chat turn receipts and handoff refs.
- Plan and Today refs.
- Durable run lifecycle/read-model refs.
- Context-pack proposal and preview refs.

Planned API and CLI surfaces:

- `GET /control-center/product-events`
- `scripts/dev/uaa_founder_loop.py product-events`

Each event row should expose only bounded safe metadata:

- event ref and event kind
- source surface
- related Today, Action, Plan, Memory, Evidence, Chat, approval, and run refs
- receipt refs and evidence refs
- blocked authority refs
- stale, conflict, missing-source, or degraded posture refs
- why-visible refs

The timeline records what happened or what was proposed. It must not prove
truth by itself, authorize actions, persist raw content, or claim exactly-once
execution.

## Founder Loop Graph v1

Add a deterministic graph projection that relates existing Founder Loop refs.
This is not a graph database and must not infer magic relationships.

Planned API and CLI surfaces:

- `GET /control-center/founder-loop/graph`
- `scripts/dev/uaa_founder_loop.py founder-loop-graph`

Initial node kinds:

- Today item
- Plan
- Action envelope
- Approval envelope
- Durable run
- Evidence event
- Memory record or reviewed recall ref
- Decision
- Open question
- Blocker
- Receipt

Initial edge fields:

- relation kind
- source ref
- target ref
- evidence refs
- receipt refs
- why-related ref
- confidence or posture ref
- stale/conflict/blocked-state refs

The graph is a projection over existing safe refs. It relates state for
operator understanding, but it does not become truth authority, approval
authority, memory authority, execution authority, or context-injection
authority.

## CanonicalTaskContext v1 And ContextCompiler

Add a typed task context contract and a deterministic compiler that assembles
the context UAA can inspect before any model/runtime consumes it.

Planned API and CLI surfaces:

- `GET /control-center/context/task`
- `scripts/dev/uaa_founder_loop.py task-context`

Planned compiler inputs:

- Product Event Timeline v1.
- Founder Loop Graph v1.
- Existing Today and current task state.
- Action envelopes and approval posture.
- Evidence Timeline refs.
- Reviewed memory refs and memory context-pack proposals.
- Plan refs and open question refs.
- Durable run state, receipt refs, replay refs, rollback or safe-disable refs.

CanonicalTaskContext v1 should include:

- active goal
- current task
- constraints
- decisions
- evidence refs
- reviewed memory refs
- approval posture
- open questions
- assumptions
- blockers
- conflicts and stale state
- included refs and excluded refs with reasons
- token or context-budget posture
- blocked authority refs
- redaction posture
- source precedence posture

The compiler must separate facts, evidence, memory recall, assumptions,
decisions, and open questions. Memory may inform reasoning, but memory must not
be treated as truth or authority.

The v1 output is inspectable context only. It must not write prompt context,
call a provider/model, inject context into a runtime, create an action, approve
work, or mutate memory.

## Control Center Inspection

If UI is added in a later implementation slice, keep it read-only and
backend-owned:

- Evidence or Proof can show Product Event Timeline rows.
- Today, Memory, or Evidence can show the Founder Loop Graph projection.
- Today, Plans, or Actions can show a Task Context preview.

UI labels must make the posture clear:

- events are records
- graphs are projections
- memory is recall
- evidence and receipts are proof surfaces
- approvals authorize exact lanes only
- context is proposed or inspectable until a later scoped milestone grants
  context materialization or injection

Mock or degraded frontend fallback data must remain visibly non-authoritative.
No raw JSON should be the primary operator view for critical flows.

## Docs And Manifest Updates

When implemented, update the smallest relevant truth surfaces:

- `docs/DOCUMENTATION_INDEX.md`
- `docs/api/openapi_contract.md`
- `docs/api/route_inventory.md`
- `/api/manifest` route metadata and side-effect classification
- `docs/control_center/release_surface_manifest.json`
- `docs/control_center/route_status_manifest.json`
- operational maturity metadata if any route claims more than planning or
  read-model posture

Do not create a competing roadmap. Cross-link this plan from existing Founder
Command Center and Control Center planning surfaces when needed.

## Tests And Verification

Focused tests should prove:

- deterministic ordering for product events
- stable graph nodes and edges across repeated runs
- no raw prompt, response, provider payload, local path, raw log, environment,
  credential, username, hostname, secret-like value, or raw private content
- no authority inference from memory refs, graph refs, approval refs, context
  refs, model output, or runtime output
- `context_injection_performed=false`
- provider/model calls, connector writes, action execution, memory writes,
  semantic search, embeddings, vector DB, and background indexing remain false
- included and excluded refs carry reason refs
- stale, conflict, missing-source, and blocked states remain visible
- OpenAPI, `/api/manifest`, route inventory, and release-surface metadata stay
  aligned
- frontend fallback data is visibly non-authoritative if UI is touched

Recommended focused checks for an implementation PR:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
```

Add new focused tests and verifiers for the Product Event Timeline, Founder
Loop Graph, and CanonicalTaskContext contracts when those slices are
implemented.

## Reversibility

The v1 implementation should be easy to undo:

- no migration
- no new durable product event store
- no graph database
- no new dependency
- no hidden prompt/context consumer
- no writes to existing Memory, Evidence, Actions, approvals, durable runs, or
  route authority

Rollback should be removal of the new contracts, builders, routes, CLI
subcommands, UI panels, docs, and tests. Existing Founder Loop state should
remain untouched.

## Future Milestones

Only after the read-only spine is useful and verified should UAA consider:

- a real append-first product event ledger
- reviewed context materialization artifacts
- exact approved context injection
- semantic/vector search
- graph persistence or query acceleration

Each future milestone must be separately scoped with authority boundaries,
redaction, idempotency, receipts, rollback or safe-disable posture, CLI/API/UI
parity, route classification, focused tests, and verifier coverage.

## Queue Prompt

Use this prompt to queue implementation in a separate thread:

```text
Implement the plan in docs/control_center/GOVERNED_CONTEXT_SPINE_PLAN.md.

Treat that file as the canonical task brief. Do not rely on conversation
memory.

Implement only the read-only Governed Context Spine slices described there:
Product Event Timeline v1, Founder Loop Graph v1, and CanonicalTaskContext v1
with a deterministic ContextCompiler.

Preserve all constraints in the plan: no classic RAG, no embeddings/vector DB,
no semantic search, no provider/model calls, no connector writes, no hidden
context injection, no new product-wide event store, no authority expansion, and
no production/public-beta claims.

Update API/CLI/UI/docs/manifests/tests only as required by that plan. Final
response must list files changed, tests run, skipped checks, and remaining
blocked items.
```
