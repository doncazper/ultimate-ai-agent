# Background Coworker Worker Contract

Status: contract-only foundation.

This document defines metadata-only contracts for representing future
background/coworker workers under durable runs. It does not add background
execution, schedulers, queue consumers, worker pools, autonomous model/provider
calls, provider SDK calls, tool execution, connector writes, live web,
browser or local-command execution, external process start, public beta,
public release, production authority, or raw payload persistence.

## Scope

The implementation adds Python Agent Core contracts for:

- worker identity refs
- coworker handoff envelopes
- lease and heartbeat metadata events
- cancel/resume request metadata
- parent/child run tree read models
- worker status read models
- repo-local CLI inspection through `inspect-coworker-workers`

These contracts use existing append-first durable run receipt storage. They do
not introduce a new event bus, scheduler, worker process, dispatch route, or
runtime adapter.

## Worker Identity

Worker identity contracts are safe-ref-only metadata. They include:

- worker ref
- worker kind
- capability scope refs
- allowed run type refs
- denied authority refs
- lease ref
- heartbeat ref
- parent run ref
- child run refs

Worker refs do not grant authority. Every worker identity keeps execution,
background execution, scheduler, provider SDK, model-call, tool execution,
connector write, live web, interactive surface, local command, queue consumer,
external process, public beta, public release, and production authority
disabled.

## Handoff Envelope

Coworker handoff envelopes are also safe-ref-only metadata. They include:

- parent run ref
- child run ref
- objective safe summary ref
- context pack ref
- approval scope ref
- evidence refs
- timeout ref
- expected output schema ref
- blocked authority refs

The context pack ref is an identifier only. It must not contain raw context,
raw prompts, raw responses, provider payloads, tool payloads, local paths,
environment dumps, credentials, usernames, hostnames, tokens, cookies, or
secret-like values. Handoff envelopes do not dispatch work and do not inject
context into a model/session.

## Lease And Heartbeat Metadata

The worker event contract recognizes these metadata-only event types:

- `lease_requested`
- `lease_granted_metadata_only`
- `heartbeat_recorded`
- `heartbeat_stale`
- `lease_expired`
- `worker_blocked`
- `handoff_recorded`
- `cancel_requested`
- `resume_requested`

Lease and heartbeat events are inspectable status records only. They do not
start a worker, extend a real lease, schedule a retry, consume a queue, call a
provider/model, execute a tool, write a connector, or control a process.

## Cancel And Resume Semantics

`cancel_requested` and `resume_requested` record operator or system intent as
durable metadata only. They do not cancel, resume, kill, start, or restart a
live worker. Future worker-control behavior requires a separate accepted
authority lane with exact approval scope, rollback/safe-disable posture,
audit/replay coverage, and tests.

## Read Model

The read model projects safe worker metadata from durable receipt summaries:

- worker status summaries
- parent/child run trees
- latest event type
- lease refs
- heartbeat refs
- stale-heartbeat visibility
- lease-expiry visibility
- blocked authority refs

All execution states are blocked or planned. The read model keeps authority
flags hard-false for background execution, scheduler behavior, autonomous
model calls, provider SDK calls, tool execution, connector writes, live web,
interactive surface runtime, local command runtime, external process start,
queue consumers, and production authority.

## Inspection

CLI inspection uses backend-owned durable state:

```bash
PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli inspect-coworker-workers
```

An optional run ref narrows inspection:

```bash
PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli inspect-coworker-workers task-decomposition-run:example
```

No API route or Control Center panel is added in this lane. Future API or UI
surfaces must remain read-only unless a later accepted lane adds exact mutation
contracts, route classification, OpenAPI coverage, CLI parity, and tests.

## Non-Goals

- No background execution.
- No scheduler.
- No queue consumer.
- No worker process, daemon, pool, or dispatch.
- No autonomous model/provider calls.
- No provider SDK calls.
- No tool execution expansion.
- No connector writes.
- No live web, browser, or local-command execution.
- No A2A or MCP runtime dispatch.
- No raw context or payload persistence.
- No public beta, public release, or production authority.

## Verification

Focused verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_background_coworker_worker_contract.py
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_product_truth.py
```
