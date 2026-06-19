# Current Kanban Board - Operator Runtime Excellence Program

Status: Active operating board for closing the product/runtime gap while
preserving Ultimate AI Agent's stronger contract-first foundation.

Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`.

This board does not grant production authority. Every item that adds runtime
authority, persistence, model calls, shell/subprocess behavior, browser actions,
network behavior, connector writes, plugin execution, mobile control, or release
distribution must pass the exact milestone gate and verifier updates described
in the source plan.

## WIP Limits

```text
P0 building items: max 2
Runtime authority changes: max 1 scoped milestone at a time
Control Center product-surface changes: max 2 visible surfaces at a time
Verification/release lane changes: max 2 at a time
Unscoped production authority: 0
```

## Legend

```text
P0 = blocks credible parity or local product loop
P1 = needed after P0 spine exists
P2 = expansion or polish after core proof
Gate = required acceptance evidence before Done
```

## Now / Building

```text
UAA-P0-002 Product release-truth packet
Gate: product excellence matrix is repo-owned, linked, and verifier-safe.
```

## Ready Next

```text
UAA-P0-003 Public security posture
Gate: SECURITY.md, triage policy, secret/redaction invariants, and report intake docs.

UAA-P0-004 M167 live model evidence matrix
Gate: Apple Silicon, CPU-only, low RAM, discrete GPU, and limited disk rows exist
with safe-ref-only evidence placeholders and reviewer bindings.

UAA-P0-005 Local model E2E smoke harness
Gate: llama.cpp supervisor, local /v1 gateway, OpenWebUI shell, auth failure,
safe failure, rollback, and no-tools/no-functions assertions are covered.

UAA-P0-006 Performance baseline harness
Gate: p50/p95 budgets for manifest, model route preview, task decomposition,
file preview, local /v1 model list, and local /v1 chat path are measured.

UAA-P0-007 Control Center operator-shell gap map
Gate: visible Chat, Plan, Models, Approvals, Files, Runtime, Evidence, and
Settings surfaces are mapped to current API routes and missing endpoints.
```

## Shaping

```text
UAA-P1-010 Durable run spine v1
Goal: durable local run records, idempotency keys, replay-safe receipts,
pause/resume/cancel states, and restart recovery over local storage.

UAA-P1-011 Task decomposition operator loop
Goal: plan, approve, execute safe registered handlers, inspect audit summaries,
and replay validation from Control Center.

UAA-P1-012 Local workspace workbench v1
Goal: file tree refs, bounded previews, patch proposals, atomic apply,
rollback, and approval-bound mutation without shell execution.

UAA-P1-013 Release verification lanes
Goal: named lanes for security, docs, API compatibility, durability, local
model E2E, performance, redaction, and product-surface smoke.

UAA-P1-014 Docker/local runtime packaging
Goal: reproducible local dev stack, loopback-only defaults, generated secrets,
and rollback instructions without broad production distribution claims.
```

## Spec Draft

```text
UAA-P1-020 PolicyEngine consolidation map
Goal: identify every policy/approval decision path and remove parallel
authority shortcuts.

UAA-P1-021 FastAPI route grouping and side-effect classes
Goal: every API path has owner, auth posture, side-effect class, risk class,
OpenAPI operation id, and release status.

UAA-P1-022 Storage migration contract
Goal: SQLite first, optional Postgres later, forward migrations, backup
minimum set, verify, and offline restore.

UAA-P1-023 Redacted observability runtime
Goal: structured latency, cost, model, approval, tool, and error events with
no raw prompts, raw responses, raw paths, secrets, or env dumps.

UAA-P1-024 Plugin/skill ecosystem boundary
Goal: inspectable packages, static manifest review, no runtime import by
default, explicit activation grants, and rollback proof.
```

## QA / Verification

```text
UAA-QA-001 Documentation integrity check
Command: .venv/bin/python scripts/verify_documentation_integrity.py

UAA-QA-002 OpenAPI contract check
Command: PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py

UAA-QA-003 Focused pytest lanes
Command: PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
Command: PYTHONPATH=src .venv/bin/python -m pytest tests/test_m167_gate_integration.py
Command: PYTHONPATH=src .venv/bin/python -m pytest tests/test_task_decomposition_production_api.py

UAA-QA-004 Foundation Gate report
Command: .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

## Blocked Until Scoped Milestone Approval

```text
Unrestricted shell/subprocess execution
Unrestricted network or browser automation
Provider/model output as production authority
Raw prompt or raw provider payload logging
External connector mutations beyond exact-approved low-risk scopes
Plugin runtime import or arbitrary plugin execution
Mobile sensor runtime
Public beta/release distribution
Autonomous background sessions by default
```

## Done

```text
UAA-P0-001 Baseline currentness repair
Gate met: README, roadmap, tags, API path count, and M160-M167 state tell one story.
```

## ASAP Sequence

```text
1. Finish UAA-P0-002 so the repo has a release-truth packet after UAA-P0-001.
2. Land UAA-P0-003 so outside users have a security/reporting contract.
3. Land UAA-P0-004 and UAA-P0-005 to turn the M160-M167 local model lane into
   a visible product proof loop.
4. Land UAA-P0-006 before broad product work so latency regressions are caught.
5. Land UAA-P0-007, then build only the mapped operator surfaces with tests.
```
