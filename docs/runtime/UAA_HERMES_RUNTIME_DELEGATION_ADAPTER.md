# UAA Hermes Runtime Delegation Adapter

Status: implemented Phase 01 readiness contract, no live Hermes execution
Baseline: v0.104.0 / 0.104.0

This document records Hermes Runtime Adoption Phase 01. Hermes is an optional
delegated runtime target and read-only architectural reference. UAA remains the
authority owner: Python Agent Core, RuntimeGateway, PolicyEngine,
LocalApprovalAuthority, Evidence, Proof, receipts, redaction, and safe refs are
the product truth.

## Full-Strength Version

UAA should be able to supervise Hermes Agent, Codex, Claude, local agents, and
future runtimes while keeping UAA's own proof spine and operator-control model.
Full runtime delegation requires configured endpoint posture, approved network
or loopback transport, approval binding, redacted run receipts, event
redaction, stop support, CLI/API/Control Center parity, safe-disable posture,
and focused tests.

## Repo-Safe Current Version

Phase 01 implements a backend-owned readiness read model:

- Core contract: `src/ultimate_ai_agent/core/runtime_gateway/delegation.py`
- API read route: `GET /api/runtime/delegation-adapter`
- CLI inspection: `scripts/dev/uaa_runtime.py inspect-delegation-adapter`
- Control Center display: `/runtime`
- Verifier: `scripts/verify_hermes_runtime_adoption_phase_01.py`
- Focused tests: `tests/test_hermes_runtime_delegation_adapter.py`

The read model exposes runtime identity refs, endpoint posture, authority mode,
capability refs, health refs, proof refs, blocked reason refs, and next safe
action refs. It stores safe refs and bounded summaries only.

## Blocked / Needs Authority

The Phase 01 adapter does not grant:

- live run submission;
- runtime model calls;
- provider SDK calls;
- tool execution;
- shell or subprocess execution;
- browser automation;
- connector writes;
- background autonomy;
- production authority;
- raw prompt, response, provider payload, log, local path, credential material,
  or private-data persistence.

Control Center does not talk directly to Hermes and does not mint authority.

## Exact Promotion Path

Future promotion must be lane-specific and prove:

1. configured endpoint ref and credential ref without exposing material;
2. loopback or approved network policy;
3. exact approval envelope and idempotency;
4. run receipt refs and proof refs;
5. redacted event ingestion;
6. stop/cancel posture;
7. safe-disable and rollback or rollback-readiness posture;
8. CLI/API/Control Center parity;
9. focused tests and verifier coverage;
10. product-language truth that still names blocked broader authority.

Graduating Hermes readiness does not grant broad runtime authority for Hermes,
Codex, Claude, local agents, providers, tools, connectors, browser, shell,
remote execution, or production.
