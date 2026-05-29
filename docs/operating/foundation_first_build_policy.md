# Foundation-First Build Policy

Status: Accepted operational policy, v0.4.5

## Policy statement

The Ultimate AI Agent must be built in layers. Foundational capabilities must work before higher-order capabilities are implemented.

Mandatory rule:

> Do not build scanners, companion proactivity, skill factory, or self-improving code before the kernel, memory/file system, event ledger, permission model, model router, tool broker, cost controls, and contract tests work.

## Why

The project is intentionally ambitious. Without a stable foundation, advanced modules will create brittle coupling, hidden state, unsafe autonomy, memory drift, and hard-to-debug behavior.

## Foundation modules

```text
Kernel contracts
Run/Event Ledger
Memory Service
File Manager
Consent and Permissions Ledger
Tool Broker
Model Router
Cost Governor
Capability Registry and Dependency Graph
Rollback primitives
Contract tests
Shadow replay harness
QA/eval baseline
```

## Higher-order modules

```text
Scanners
Proactive intelligence
Companion behavior
Skill Factory
Self-improving code
Autopilot workflows
High-autonomy external execution
```

## Allowed before Foundation Gate

The team may do the following for higher-order modules before the Foundation Gate passes:

```text
Research
Competitive analysis
Feature parity mapping
Requirement drafting
Architecture sketches
Threat modeling
Backlog entry creation
Parking Lot organization
```

## Not allowed before Foundation Gate

The team may not do the following before the Foundation Gate passes:

```text
Production scanner implementation
Autonomous proactive notifications
External skill installation
Self-modifying code merge loops
Autopilot execution
High-autonomy external actions
Connector-based email/message scanning
```

## Foundation Gate checklist

- [ ] Execution Contract schema exists and has contract tests.
- [ ] Context Pack schema exists and has contract tests.
- [ ] Run/Event Ledger exists and records complete traces.
- [ ] Memory Service V1 can write, recall, supersede, and cite memories.
- [ ] File Manager V1 can create, diff, patch, and version project files.
- [ ] Consent/Permission Ledger V1 exists and is deny-by-default.
- [ ] Tool Broker V1 routes all tool use and logs risk/approval state.
- [ ] Model Router V1 routes tasks by model class with cost/privacy policy.
- [ ] Model capability registry exists and is represented in the Capability Registry.
- [ ] Routing decisions are logged in the Event Ledger.
- [ ] Model routing evals pass for cost, privacy, and critical verification.
- [ ] Capability Registry maps dependencies and blocked modules.
- [ ] Rollback metadata exists for mutating operations.
- [ ] Contract test suite passes.
- [ ] Shadow replay harness can replay at least three golden traces.
- [ ] Basic QA/eval baseline passes.

## Enforcement in Kanban

Advanced module cards must stay in `Parking Lot` or `Blocked` until the Foundation Gate passes. They cannot move to `Ready for Build`.

## Enforcement in specs

Every feature spec must include:

```text
Foundation Gate dependency: required | not required
Upstream capabilities
Permission impact
Memory impact
File impact
Rollback plan
Contract tests
Evals
```

## Enforcement in code

Foundation interfaces must be versioned. Higher layers call public service contracts only, not implementation internals.

## Change control

Any change to foundation contracts requires:

```text
Change proposal
Dependency graph impact analysis
Contract tests
Shadow replay
Feature flag or migration plan
Rollback plan
Release notes
```

## v0.5.2 Stack Enforcement Addendum

The scalable stack is part of the foundation gate.

Rules:

```text
Python Agent Core owns durable policy and execution.
OpenWebUI is an optional chat shell only.
TypeScript Control Center is a UI/control surface only.
All clients enter through Agent API Boundary.
No client bypasses Consent Ledger, Tool Broker, Event Ledger, or Memory/File policy.
```

Advanced modules remain blocked until API boundary and OpenWebUI bypass evals pass.
