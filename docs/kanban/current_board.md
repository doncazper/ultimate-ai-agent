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
No active P0 item in this patch. Pull UAA-P1-010 next.
```

## Ready Next

```text
UAA-P1-010 Durable run spine v1
Gate: durable local run records cover idempotency keys, replay-safe receipts,
pause/resume/cancel states, restart recovery, and rollback refs.
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
Command: PYTHONPATH=src .venv/bin/python -m pytest tests/test_m166_production_release_gate.py
Command: PYTHONPATH=src .venv/bin/python -m pytest tests/test_m167_live_model_hardening.py
Command: PYTHONPATH=src .venv/bin/python -m pytest tests/test_m151_openwebui_local_gateway_api.py
Command: PYTHONPATH=src .venv/bin/python -m pytest tests/test_m167_gate_integration.py
Command: PYTHONPATH=src .venv/bin/python -m pytest tests/test_task_decomposition_production_api.py
Command: PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_safe_exception_messages.py
Command: PYTHONPATH=src .venv/bin/python -m pytest tests/test_secret_broker_redaction.py

UAA-QA-004 Foundation Gate report
Command: .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only

UAA-QA-005 Performance baseline
Command: .venv/bin/python scripts/benchmark_foundation_gate.py
Command: .venv/bin/python scripts/check_foundation_gate_latency.py
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

UAA-P0-002 Product release-truth packet
Gate met: product excellence matrix is repo-owned, linked, evidence-backed, and
verifier-safe.

UAA-P0-003 Public security posture
Gate met: SECURITY.md, triage runbook, report intake, severity targets,
secret/redaction invariants, static release-doc checks, and focused tests exist.

UAA-P0-004 M167 live model evidence matrix
Gate met: Apple Silicon, CPU-only, low RAM, discrete GPU, and limited disk rows
exist with safe-ref-only evidence placeholders, reviewer refs, blocker refs,
verification refs, rollback refs, and production-readiness status.

UAA-P0-005 Local model E2E smoke harness
Gate met: llama.cpp supervisor, local /v1 gateway, OpenWebUI shell, auth failure,
safe failure, rollback, tools/functions/streaming denial, and pass/fail/blocked/
skipped states are covered by redacted safe-ref harness evidence.

UAA-P0-006 Performance baseline harness
Gate met: p50/p95 budgets for health, manifest, model route preview, task
decomposition, bounded file preview, local /v1 model list, and local /v1 chat
path are measured; reports are written under reports/performance with safe
skipped status for Control Center render timing.

UAA-P0-007 Control Center operator-shell gap map
Gate met: Chat, Plans, Models, Approvals, Files, Runtime, Evidence, and
Settings are mapped to current frontend surfaces, current backend routes,
missing routes, authority boundaries, side-effect classes, approval
requirements, evidence/audit outputs, readiness status, product language rules,
and production-readiness blockers in
`docs/control_center/OPERATOR_SHELL_GAP_MAP.md`.

UAA-P0-015 llama-server packaging/provenance checklist
Gate met: local llama-server discovery, allowed locations, provenance review,
checksum/signature verification, offline operation, rollback, cache cleanup,
and blocked/unknown provenance handling are documented in
`docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md` without broad
authority, public distribution, signed installer, or unreviewed binary-trust
claims.

UAA-P0-016 tuning advisor hardening cases
Gate met: lag, out-of-memory, crash loop, reload loop, slow tokens per second,
and one-change rollback are covered in `tests/test_m167_live_model_hardening.py`;
recommendations remain safe, bounded, redacted, operator-confirmable,
rollback-aware, and unable to apply settings without exact approval.

UAA-P0-017 local model operational runbook
Gate met: cache cleanup, corrupted GGUF, stuck download, port conflict,
credential rotation, rollback, offline mode, safe evidence collection,
blocked/unknown model state, and safe-disable recovery are documented in
`docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md` with safe, degraded,
blocked, and unsupported state semantics.
```

## ASAP Sequence

```text
1. Build only the mapped operator surfaces with tests after route/status gaps are scoped.
2. Land UAA-P1-010 to shape the durable run spine.
3. Land UAA-P1-011 to connect task decomposition to the operator loop.
```
