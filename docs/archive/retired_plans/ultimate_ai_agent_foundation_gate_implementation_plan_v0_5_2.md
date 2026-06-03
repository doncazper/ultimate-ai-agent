Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Foundation Gate Implementation Plan v0.5.2

Status: Active implementation plan.

## Purpose

Define the coding sequence for the foundation now that the scalable stack decision is accepted.

## Active stack

```text
Python Agent Core: foundation runtime
FastAPI: API boundary
Pydantic: runtime models and validators
Postgres: durable database
Alembic: migrations
pytest: tests
Docker Compose: local services
OpenWebUI: optional chat shell only
TypeScript/Next.js: Control Center later
```

## M0 — Repository, Canonical Foundation, and Stack Skeleton

### Goal

Create a repo that can validate project artifacts and begin Agent Core implementation without starting advanced modules.

### Deliverables

```text
Repo layout
Python package skeleton under /services/agent-core
/tests structure
/scripts validation tools
/schema validation command
/prompt registry validation command
basic FastAPI app or placeholder
Docker Compose structure
.env.example
OpenWebUI config folder, optional and policy-bounded
TypeScript Control Center placeholder optional
CI skeleton
```

### Acceptance

```text
All JSON schemas parse.
Prompt registry paths validate.
Docs import cleanly.
Foundation-first rule is visible in README.
FastAPI health endpoint returns OK if implemented.
OpenWebUI has no direct access to memory/tools/files.
CI can run validation scripts.
```

## M1 — Execution Contract + Context Pack

Build runtime models and validators for the brainstem.

Acceptance:

```text
Execution Contract validates goal, mode, risk, autonomy, tools, models, consent, cost, rollback, and acceptance criteria.
Context Pack validates allowed context sources and redactions.
Advanced module contracts are rejected until Foundation Gate passes.
```

## M2 — Event Ledger / Observability

Build append-only event logging and receipt generation.

Acceptance:

```text
Agent runs can be reconstructed from event records.
Mutating actions require Event Ledger records.
Receipts omit secrets.
OpenWebUI/API-triggered runs produce receipts.
```

## M3 — Consent Ledger + Tool Broker

Build permission checks and controlled tool execution.

Acceptance:

```text
Disallowed actions are blocked.
Allowed tool calls are schema-validated and logged.
Tool Broker creates rollback metadata when relevant.
Consent grants can expire, be revoked, and be audited.
```

## M4 — Memory Service + File Manager

Build durable context and canonical file operations.

Acceptance:

```text
Memory writes are source-linked and scoped.
File writes use diffs/atomic operations.
Canonical files outrank memory.
File and memory writes generate event records and rollback metadata.
```

## M5 — Orchestrator Minimal Vertical Slice

Build first end-to-end workflow.

Target demo:

```text
User asks: Create the Memory V1 feature spec.
Orchestrator creates Execution Contract.
Context Pack loads project truth.
Model Router chooses model class.
Spec Generator produces spec files.
File Manager saves them.
Memory Curator records source-linked memory.
Event Ledger records all steps.
Receipt is generated.
```

## M6 — Contract Tests, Shadow Replay, Foundation Gate Decision

Run all foundation tests and decide if controlled expansion may begin.

Required tests:

```text
execution_contract_eval
context_pack_eval
event_ledger_eval
consent_permission_eval
tool_broker_eval
memory_service_eval
file_manager_eval
model_routing_eval
api_boundary_eval
openwebui_bypass_eval
foundation_gate_eval
```

## Gate rule

No scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, or high-autonomy external execution until M6 passes.
