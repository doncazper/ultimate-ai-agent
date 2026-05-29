# 05 Development Workflow v0.5.2

Status: Canonical foundation workflow with scalable stack strategy incorporated.

## Purpose

Define how the Ultimate AI Agent project is planned, gated, executed, reviewed, and protected from scope explosion.

## Operating model

Use **Spec-Kanban Development**:

```text
North Star
  -> Roadmap Themes
  -> Milestones
  -> Feature Specs
  -> Kanban Execution
  -> Tests / Evals
  -> Release
  -> Retro / Memory + Canonical Updates
```

## Stack baseline

```text
Python Agent Core for foundation runtime.
TypeScript Control Center for user-facing control surfaces later.
OpenWebUI as optional early chat shell, not the brain.
Stable API Boundary between all clients and Agent Core.
Postgres for durable state.
Docker Compose for local development.
```

## Foundation-first rule

The project must be built like an onion or a brain. Lower layers must work before higher-order capabilities are implemented.

**Mandatory rule:**

> Do not build scanners, companion proactivity, Skill Factory, self-improving code, or autopilot workflows before the kernel, memory/file system, event ledger, permission model, tool broker, model router, cost governor, API boundary, rollback primitives, and contract tests work.

Advanced modules may be researched, shaped, specced, and parked, but they cannot move into `Ready for Build` until the Foundation Gate passes.

## Kanban columns

```text
Inbox
Shaping
Spec Draft
Spec Review
Ready for Build
Building
Code Review
QA / Evals
Release Candidate
Done
Parking Lot
Blocked
```

## WIP limits

```text
Active product goal: 1
Active milestone: 1
Spec Draft: 2
Ready for Build: 5
Building: 2
QA / Evals: 3
Release Candidate: 2
```

## Foundation Gate

The Foundation Gate passes only when these are working and tested:

```text
Execution Contract schema/model
Context Pack schema/model
Run/Event Ledger schema/model
Model Router V1 policy stub
Cost Governor minimal integration
Consent Ledger V1
Tool Broker V1
Memory Service V1
File Manager V1
Agent API Boundary
OpenWebUI cannot bypass Agent Core policy
Capability Registry and Dependency Graph
Rollback primitives
Contract test suite
Shadow replay harness
Basic QA/eval baseline
```

## Advanced modules blocked until Foundation Gate passes

```text
Scanner Modules
Companion Proactivity
Skill Factory / Skill Acquisition Service
Self-Improving Coding Framework
Autopilot Workflows
High-autonomy External Execution
```

## Focus rules

1. One active product goal at a time.
2. No major feature without a spec.
3. No spec without acceptance criteria.
4. No implementation without Definition of Ready.
5. No release without evals.
6. No architecture change without an ADR.
7. No persistent decision without canonical file update.
8. No more than two active build items.
9. New ideas go to Parking Lot unless urgent or blocking.
10. If memory and canonical files disagree, canonical files win.
11. No external scanner runs without explicit connector permission.
12. No self-improvement merge without tests, evals, review, and approval gates appropriate to risk.
13. No external skill install without trust evaluation and quarantine.
14. No advanced module can bypass the Foundation Gate.
15. No UI surface can bypass the Agent API Boundary, Consent Ledger, Tool Broker, or Event Ledger.

## Definition references

- `docs/definitions/definition_of_ready.md`
- `docs/definitions/definition_of_done.md`
- `docs/operating/foundation_first_build_policy.md`
- `docs/kanban/current_board.md`
- `docs/canonical/38_scalable_stack_and_ui_strategy.md`
## v0.5.3 Minimum Lovable Kernel update

The first implementation proof is no longer a text-only spec-generation slice. The project must first prove the Minimum Lovable Kernel defined in `docs/canonical/43_minimum_lovable_kernel.md`: a real, safe, reversible file mutation through Execution Contract, Context Pack, Consent Ledger, Tool Broker, File Manager, Event Ledger, Memory Service, rollback, and Verification Contract.

