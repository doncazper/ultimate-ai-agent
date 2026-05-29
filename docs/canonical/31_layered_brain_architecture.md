# 31 Layered Brain / Onion Architecture

Status: Canonical draft, v0.4.1

## Purpose

Build the Ultimate AI Agent like an onion or a brain: stable lower layers first, then higher-order intelligence on top.

## Core principle

Lower layers expose versioned contracts. Higher layers depend on those contracts, not on implementation internals.

## Layers

```text
Layer 0 — Kernel and Constitution
Layer 1 — Truth, Memory, Files, and Data Ownership
Layer 2 — Tools, Code, Web, and Execution Boundaries
Layer 3 — Orchestration and Spec-Driven Work
Layer 4 — Learning, Skills, and Intelligence Loops
Layer 5 — Relationship, Scanners, Proactivity, and Curation
Layer 6 — Ecosystem, Autopilot, and Agent Interoperability
```

## Foundation-first rule

> Do not build scanners, companion proactivity, skill factory, or self-improving code before the kernel, memory/file system, event ledger, permission model, tool broker, and contract tests work.

## Layer responsibilities

### Layer 0: Kernel and Constitution

Owns the agent constitution, execution contract, context pack contract, run state, event ledger, and core policy.

### Layer 1: Truth, Memory, Files, and Data Ownership

Owns canonical files, Memory Service, File Manager, user-owned data lifecycle, source-linked memories, and data deletion/export.

### Layer 2: Tools, Code, Web, and Execution Boundaries

Owns Tool Broker, code sandbox, governed web access, permission enforcement, rollback metadata, and connector boundaries.

### Layer 3: Orchestration and Spec-Driven Work

Owns Commander/Orchestrator, Spec SDLC Engine, Kanban state, QA/eval routing, and deliverable integration.

### Layer 4: Learning, Skills, and Intelligence Loops

Owns adaptive learning, playbook refinement, Skill Factory, self-improvement proposals, and eval-driven improvement.

### Layer 5: Relationship, Scanners, Proactivity, and Curation

Owns companion behavior, scanner modules, proactive notifications, news curation, attention budgets, and watchlists.

### Layer 6: Ecosystem, Autopilot, and Agent Interoperability

Owns long-running autopilot workflows, A2A interoperability, MCP ecosystem, marketplaces, and multi-agent collaboration.

## Dependency direction

Higher layers may depend on lower layers. Lower layers must not depend on higher layers.

Invalid examples:

```text
Memory Service depending on Reddit Scanner
Tool Broker depending on Companion Layer
Event Ledger depending on Skill Factory
Permission Ledger depending on Proactive Intelligence
```

Valid examples:

```text
Reddit Scanner depends on Tool Broker, Consent Ledger, Event Ledger, and Source Credibility Protocol
Skill Factory depends on Capability Registry, Tool Broker, Code Sandbox, and Event Ledger
Self-Improving Coding depends on Code Workspace, Contract Tests, Event Ledger, and Approval Gates
```
