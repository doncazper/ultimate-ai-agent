# Milestone Charters

Status: Active roadmap governance template for v0.18.4.

This document defines the required charter shape for every future milestone prompt. A milestone charter is planning authority only. It does not implement runtime behavior, frontend behavior, backend API routes, provider calls, network calls, remote execution, mobile sensor access, plugin enablement, native build workflows, production persistence, or external actions.

## Required Charter Fields

Every future milestone must state:

- version.
- milestone code.
- title.
- status.
- purpose.
- allowed scope.
- must not add.
- dependencies.
- acceptance criteria.
- review prompt required.
- hardening patch expectation.
- source-of-truth docs.
- notes.

## Standard Template

```text
Version:
Milestone code:
Title:
Status:

Purpose:

Allowed scope:

Must not add:

Dependencies:

Acceptance criteria:

Review prompt required:

Hardening patch expectation:

Source-of-truth docs:

Notes:
```

## Governance Rules

- Python Agent Core remains the brain.
- OpenWebUI is the preferred conversational web shell, not the agent brain.
- CCC means Control Center Clients: CCC Web, CCC iOS, CCC Android, and CCC macOS.
- CCC is the governance/control client family and cannot bypass Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Foundation Gate, or governed source systems.
- TypeScript Control Center is CCC Web.
- Mobile Companion is a future control, approval, capture, receipt, and status surface, not the agent brain.
- Open Design governs custom CCC surfaces and does not replace OpenWebUI.
- The model is never the source of truth, and model output is not authoritative evidence.
- Consent and credentials are separate.
- Arbitrary string refs are not authority.
- External tools and plugins are not authority.
- Remote worker output is never trusted control input.
- Mobile sensor output is not trusted control input by default.
- Parked work must not become active without an explicit reintroduction prompt.
- No milestone may skip review gates.
- M14-M20 remain frozen and unchanged unless a reviewed roadmap patch supersedes them.
- M21-M40 are planned/provisional in `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`.
- Future prompts after M20 must read `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`, and `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`.

## Review And Hardening Rule

Every new user-facing, API, runtime, mobile, remote, plugin, or design-governance surface should be followed by a focused review or hardening patch before the next major milestone expands scope. Hardening patches must preserve the previous milestone boundary unless a new reviewed milestone explicitly changes it.
