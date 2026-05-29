# 09 Roadmap

Status: Canonical draft, v0.4.1

## Roadmap principle

The roadmap is layered. Lower layers expose stable versioned contracts. Higher layers depend on those contracts and must not depend on internal implementation details.

## Foundation-first rule

> Do not build scanners, companion proactivity, skill factory, or self-improving code before the kernel, memory/file system, event ledger, permission model, tool broker, and contract tests work.

## Phase A: Foundation / Kernel

### M0 — Project Foundation

Deliver:

```text
Canonical file tree
Core ADRs
Agent constitution
Spec SDLC policy
Kanban board
Definition of Ready
Definition of Done
Foundation-first build policy
```

Exit gate:

```text
Docs exist and are accepted as working baseline.
```

### M1 — Kernel Contracts and Event Ledger V1

Deliver:

```text
Execution Contract schema
Context Pack schema
Run/Event Ledger schema
Tool Call schema
Approval Request schema
Trace completeness rules
```

Exit gate:

```text
A run can be represented, traced, replayed, and audited.
```

### M2 — Consent, Permissions, and User Control Shell V1

Deliver:

```text
Consent Ledger schema
Permission categories
Approval queue model
User Control Center shell
Pause learning / pause scanners control model
Permission revoke flow
```

Exit gate:

```text
Every tool/action category has explicit permission and approval behavior.
```

### M3 — Memory and File Foundation V1

Deliver:

```text
Memory Service V1
Project memory
User preference memory
Memory source references
File Manager V1
Canonical file manager
Diff/patch workflow
Artifact registry
```

Exit gate:

```text
The agent can load context, save project truth, update files safely, and cite memory/file sources.
```

### M4 — Tool Broker and Capability Registry V1

Deliver:

```text
Tool Broker V1
Tool risk categories
Capability manifests
Capability dependency graph
Denied-by-default execution policy
Rollback metadata fields
```

Exit gate:

```text
Tools can be registered, permissioned, audited, and dependency-mapped.
```

### M5 — Orchestrator and Spec SDLC Engine V1

Deliver:

```text
Commander/Orchestrator MVP
Intent classification
Execution contract creation
Context pack loading
Spec generator
ADR generator
Task generator
Spec compliance checklist
```

Exit gate:

```text
The agent can turn a project request into a spec-backed deliverable with traceable state.
```

### M6 — Contract Tests, Shadow Mode, and Eval Baseline V1

Deliver:

```text
Contract test suite
Foundation Gate test suite
Shadow replay harness
Golden traces
Basic regression evals
Rollback drill
```

Exit gate:

```text
Foundation Gate passes. Advanced modules may now move from Parking Lot into Spec Draft or Ready for Build if individually ready.
```

## Phase B: Controlled Capabilities

### M7 — Governed Web Research V1

Deliver:

```text
Web search/read/cite
Source credibility scoring
Rumor protocol integration
Research artifact generation
Prompt-injection defenses for web content
```

### M8 — Code Workspace V1

Deliver:

```text
Code generation
Patch generation
Sandboxed execution
Test runner
Lint/type validation
Build logs
```

Note: this is not the self-improving coding framework. Self-improvement remains blocked until the foundation and code workspace prove reliable.

### M9 — Verification / Evals V1

Deliver:

```text
Memory recall evals
Spec compliance evals
Tool approval evals
Canonical precedence evals
Trace completeness evals
Security red-team evals
```

## Phase C: Higher Intelligence

### M10 — External Execution with Approvals V1

Email, calendar, GitHub, CRM, and message-draft workflows through approval gates.

### M11 — Adaptive Learning V1

Feedback capture, preference updates, playbook refinement, and user-controlled learning review.

### M12 — Proactive Intelligence V1

Watchlists, event monitors, breaking-news verification, relevance scoring, notification policies, digests, interrupt rules, and feedback learning.

### M13 — Scanner Modules V1

Reddit, news, weather, email, message, calendar, GitHub, dependency, academic, and market scanners.

Blocked until: Foundation Gate passed, Consent Ledger active, Source Credibility/Rumor Protocol active, Notification Policy active.

### M14 — Skill Factory V1

Skill manifests, skill specs, sandbox tests, quarantine, approval workflow, skill registry, usage metrics.

Blocked until: Foundation Gate passed, Capability Registry active, Tool Broker active, Skill trust policy active.

### M15 — Self-Improving Coding Framework V1

Issue creation, branch creation, patch generation, test/eval/lint/security checks, review gates, feature flags, canaries, rollback.

Blocked until: Foundation Gate passed, Code Workspace V1 stable, Contract tests stable, Event Ledger active, Approval policy active.

### M16 — Companion Layer V1

Relationship-aware assistant behavior, communication style learning, trust boundaries, companion safety evals.

Blocked until: Foundation Gate passed, Data Lifecycle controls active, Memory review active, Notification policy active.

### M17 — Autopilot Workflows V1

Scheduled, recurring, trusted workflows with pause, audit, alert, and rollback controls.

Blocked until: all relevant permissions, observability, rollback, and evals are active.

## Current active goal

Build M0 through M6. Do not implement higher-order modules until the Foundation Gate passes.
