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
No active P1 item in this patch. Pull UAA-P1-011 next.
```

## Ready Next

```text
UAA-P1-011 Task decomposition operator loop
Gate: Control Center operator loop uses the existing task decomposition durable
binding, exact approvals, safe registered handlers, redacted audit summaries,
and replay validation without hidden authority.
```

## Shaping

```text
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

UAA-P1-010 Durable run spine v1
Gate met: durable run records cover explicit states, transition rules,
idempotency keys, audit refs, receipt refs, replay refs, rollback refs, failure
refs, restart recovery refs, checksum snapshot validation, invalid-transition
denials, duplicate mutation denials, replay-ref denial, and restart visibility
in `docs/execution/DURABLE_RUN_SPINE.md`,
`src/ultimate_ai_agent/core/execution/durable_runs.py`,
`tests/test_execution_state_machine_safety.py`, and
`tests/test_event_ledger_append_only.py`.

UAA-P1-025 Append-first local run storage
Gate met: durable run records and receipt summaries append as hash-chained JSONL
entries with idempotency keys, audit refs, receipt refs, rollback refs, atomic
replacement, safe failure cleanup, corruption detection, duplicate-write denial,
restart recovery visibility, and redacted summary-only receipt storage in
`docs/execution/APPEND_FIRST_RUN_STORAGE.md`,
`src/ultimate_ai_agent/core/execution/run_storage.py`, and
`tests/test_file_atomic_writes.py`.

UAA-P1-026 Durable run lifecycle contracts
Gate met: pause, resume, cancel, retry, dead-letter, and restart recovery are
state-only durable run lifecycle transitions with expected-state checks,
authority-boundary refs, exact lifecycle idempotent replay, conflicting
idempotency denial, dead-letter failure refs, restart refs, terminal-state
truth, and tests for allowed, denied, repeated, stale, and restart cases in
`docs/execution/DURABLE_RUN_SPINE.md`,
`src/ultimate_ai_agent/core/execution/durable_runs.py`, and
`tests/test_execution_state_machine_safety.py`.

UAA-P1-027 Task decomposition durable-run binding
Gate met: task decomposition decompose, run, and plan execution paths attach
durable run records with safe approval refs, handler refs, audit refs, receipt
refs, replay refs, rollback refs, restart visibility, explicit idempotency
replay denial, and redacted safe binding responses in
`docs/execution/DURABLE_RUN_SPINE.md`,
`src/ultimate_ai_agent/core/task_decomposition/runtime.py`,
`src/ultimate_ai_agent/core/task_decomposition/contracts.py`, and
`tests/test_task_decomposition_production_api.py`.

UAA-P1-028 Backup/verify/offline restore plan
Gate met: backup minimum set covers runs, receipts, approvals, settings,
registry, audit summaries, and local model cache references; verification,
rollback, and offline/operator-run restore are documented without live restore
claims in `docs/execution/DURABLE_RUN_BACKUP_RESTORE.md`.

UAA-P1-029 Replay-safe receipt hashing
Gate met: durable receipt summaries carry stable receipt hash refs and replay
validation refs over redacted summary data only; private-data-shaped receipt
keys are denied, duplicate mutations remain idempotency-blocked, and replay
validation is covered in `src/ultimate_ai_agent/core/execution/run_storage.py`
and `tests/test_file_atomic_writes.py`.

UAA-P1-030 Route status manifest
Gate met: visible Control Center routes and actions are mapped to owners, auth
posture, side-effect classes, risk classes, OpenAPI operation ids, release
status, UI surfaces, approval requirements, evidence/audit outputs, and
unready blockers in `docs/control_center/ROUTE_STATUS_MANIFEST.md` and
`docs/control_center/route_status_manifest.json`; tests and frontend verifier
coverage keep unimplemented or unsafe actions out of ready status.

UAA-P1-031 Product language rules
Gate met: Control Center and release-facing product language rules are
documented in `docs/control_center/PRODUCT_LANGUAGE_RULES.md`; verifier
coverage rejects hidden-authority, fake-completion, unsupported readiness,
unsupported public-distribution, output-as-authority, primary raw-JSON UI, and
completed-state wording for blocked/skipped/pending work where practical.

UAA-P1-032 Browser smoke readiness
Gate met: first product loop browser smoke readiness is documented in
`docs/control_center/LOCAL_BROWSER_SMOKE.md` and
`docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md`, with Vitest coverage in
`apps/control-center/src/App.test.tsx` and verifier coverage in
`scripts/verify_control_center_frontend.py` plus
`scripts/verify_control_center_browser_smoke_readiness.py`. The lane marks
available UI states as mocked/local-only and missing GGUF, chat shell, Plans,
approval-binding, latency, and rollback prerequisites as blocked rather than
complete.

UAA-P1-033 Accessible loading/error/empty states
Gate met: Chat Shell, Plans, Models, Approvals, Files, Runtime, Evidence, and
Settings expose accessible loading, error, empty, blocked, and denied states in
`apps/control-center/src/components/OperatorSurfaceStates.tsx`, with route
coverage in `apps/control-center/src/routes.tsx`, Vitest coverage in
`apps/control-center/src/App.test.tsx`, and static verifier coverage in
`scripts/verify_control_center_frontend.py`. The states remain local UI/status
only and do not add runtime, model, approval, file mutation, settings, or
completion authority.
```

## ASAP Sequence

```text
1. Build only the mapped operator surfaces with tests after route/status gaps are scoped.
2. Land UAA-P1-011 to connect task decomposition to the operator loop.
3. Scope UAA-P1-012 local workspace workbench only after P1-011 is green.
```
