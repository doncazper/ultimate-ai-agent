# Current Kanban Board - Operator Runtime Excellence Program

Status: Active operating board for closing the product/runtime gap while
preserving Ultimate AI Agent's stronger contract-first foundation.

Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`.
Founder Command Center product-loop planning board:
`docs/kanban/founder_command_center_board.md`.

This board does not grant production authority. Every item that adds runtime
authority, persistence, model calls, shell/subprocess behavior, browser actions,
network behavior, connector writes, plugin execution, mobile control, or release
distribution must pass the exact milestone gate and verifier updates described
in the source plan.

The Founder Command Center board is subordinate to this Operator Runtime
Excellence board. It translates the current product audit into future Codex
tasks for the single-user founder/operator loop and does not replace existing
Operator Runtime Excellence work. `UAA-P1-011` is the accepted readable-loop
baseline for the next Founder Command Center tasks; broader product surfaces
remain separately scoped.

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
UAA-P1-020 PolicyEngine consolidation map
Goal: map every policy/approval decision path before broadening product
authority.
Gate: every policy/approval decision path is identified; parallel authority
shortcuts are removed or explicitly blocked.
```

## Ready Next

```text
UAA-P1-021 FastAPI route grouping and side-effect classes
Gate: route owners, service modules, auth posture, side-effect classes, risk
classes, OpenAPI operation IDs, and release status remain consistent.

UAA-P1-052 API service-module extraction plan
Gate: module split plan covers health, manifest, local model gateway, task
decomposition, workspace files, approvals, evidence/receipts, observability,
extensions, and release verification without route-contract drift.
```

## Shaping

```text
UAA-P1-053 CI lane workflow expansion
Goal: expose named docs, OpenAPI, Foundation Gate, API safety, frontend,
security/redaction, local model, durability, performance, and packaging lanes in
CI with safe output.

UAA-P1-054 Control Center differentiator screens
Goal: product-grade screens for route authority, approval state, evidence
receipts, safe workspace previews, local model status, and M167 observability
timeline.

UAA-P1-055 Security automation and artifact redaction lane
Goal: add automated security scanning and release artifact redaction checks
without external-audit, public-distribution, or signed-release claims.

UAA-P1-057 Product truth regression checks
Goal: prevent blocked, skipped, pending, mock-only, planned, or not-scoped work
from being described as complete, production-ready, or publicly released.
```

## Spec Draft

```text
UAA-P1-022 Storage migration contract
Goal: SQLite first, optional Postgres later, forward migrations, backup
minimum set, verify, and offline restore.

UAA-P1-058 First low-risk API route-module extraction
Goal: extract one read-only route group without changing path behavior, auth
posture, side-effect classification, API manifest, or operation IDs.

UAA-P1-059 Route-module ownership tests
Goal: future routes must declare owner, service module, side-effect class, risk,
auth posture, evidence behavior, and release status.

UAA-P1-060 Operator-readiness status taxonomy
Goal: share shipped/planned/blocked/skipped/mock/not-scoped status semantics
across docs, route manifests, Control Center states, release evidence, and
Foundation Gate reports.

UAA-P1-061 Morning reconciliation artifact check
Goal: looped ChatGPT/Codex work sessions produce safe reconciliation summaries
with completed, deferred, rejected, and blocked recommendation refs.

UAA-P2-047 Signed installer and public distribution lane shaping
Goal: shape installer/release workflow proof only after the local operator loop,
security, durability, and artifact evidence gates are green.

UAA-P2-056 Extension trust product surface
Goal: surface static package review, provenance, hash refs, declared
capabilities, requested grants, activation/revocation state, and risk flags
without runtime import or execution.
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

UAA-P1-012 Local workspace workbench v1
Gate met: `/files/tree/preview` exposes bounded safe tree refs with raw paths
omitted, file previews remain bounded and redacted, unsafe access fails safely,
write proposal/diff paths stay approval-bound and idempotency-aware, and no
shell/subprocess authority is introduced.

UAA-P1-034 Patch proposal contracts
Gate met: typed patch proposals bind exact safe file refs, safe path refs,
expected content hashes, approval scope refs, audit refs, idempotency keys,
expiration checks, redacted previews, and rollback capture; apply is denied
without exact LocalApprovalAuthority validation, stale proposals and duplicate
applies fail safely, and unsafe diff content is blocked.

UAA-P1-035 Atomic apply and rollback receipts
Gate met: approval-bound patch apply uses atomic replacement with preimage and
postimage safe refs, emits redacted mutation receipts, records redacted rollback
receipts, blocks duplicate apply and rollback attempts by idempotency, and leaves
failed apply/rollback attempts inspectable without storing raw content or raw
paths.

UAA-P1-036 Secret-like diff blocking and redacted preview
Gate met: workspace write and patch proposal paths block high-confidence
secret-like diff content before approval or apply, read previews redact
secret-like values, safe placeholders and planning text remain allowed, and
decision/result evidence uses safe refs and redacted summaries without raw
secret-like values.

UAA-P1-037 Approval-bound workspace mutation only
Gate met: direct workspace write and rollback helpers deny mutation, patch
apply passes the workspace mutation PolicyEngine gate before requiring exact
LocalApprovalAuthority validation, rollback requires exact approval-bound
receipt flow, approval bypass attempts are tested, and shell/subprocess
mutation paths remain unavailable.

UAA-P1-039 Latency budget gate
Gate met: required local release paths have explicit p95 budgets, missing
required measurements fail the gate, required budget regressions fail the gate,
optional dashboard render timing remains visible as skipped with a reason code,
and authority checks are not cached, skipped, or bypassed for speed.

UAA-P1-040 Performance regression reports
Gate met: benchmark output writes JSON and Markdown regression reports with p50,
p95, sample count, safe environment summary, pass/fail/skipped status, budget
comparison, operator action labels, and retention guidance without raw local
paths, hostnames, usernames, environment dumps, logs, prompts, responses,
provider payloads, or credential material.

UAA-P1-041 Hot-path profiling
Gate met: task decomposition classify/decompose route handlers and OpenAPI
schema build have safe timing-summary-only JSON and Markdown profile reports;
profiling preserves bearer-gated route behavior, restores OpenAPI schema cache,
records p50, p95, mean, samples, warmups, and reason codes, and excludes raw
requests, responses, schema bodies, local paths, logs, machine identity,
environment dumps, prompts, provider payloads, and credential material.

UAA-P1-042 Safe static manifest caching
Gate met: `/api/manifest` caches only process-local static route metadata,
versions, baseline labels, route groups, route inventory, and static
declared/blocked capability lists; foundation gate status, policy decisions,
approvals, runtime authority, user data, mutable state, and secrets are
excluded, cache invalidates on route/version/capability fingerprint changes,
and tests prove dynamic status remains live.

UAA-P1-043 Foundation Gate latency integration
Gate met: Foundation Gate JSON and Markdown reports include a typed
`latency_gate` summary with p50/p95 status, pass/fail/skipped path state,
accepted failures, performance report refs, optional prerequisite visibility,
environment-safe summary, authority invariants, and report-safety flags.

UAA-P1-013 Release verification lanes
Gate met: docs, OpenAPI, API safety, security/redaction, local model E2E,
durability, frontend, and performance lanes are named in
`docs/production/RELEASE_VERIFICATION_LANES.md`; `scripts/verify_release_lanes.py`
validates lane definitions without executing commands, `scripts/verify_all.py`
guards the manifest, and Foundation Gate report-only output includes a compact
`release_verification_lanes` summary.

UAA-P1-014 Docker/local runtime packaging
Gate met: `docs/production/LOCAL_RUNTIME_PACKAGING.md` and
`packaging/local-runtime/` define a loopback-first local UAA API and Control
Center Docker stack with host-only `127.0.0.1` published ports, generated
local secret refs under ignored `.uaa/` state, rollback instructions,
`.dockerignore` context exclusions, and no public distribution, hosted
production support, signed installer, OpenWebUI, `llama-server`, connector
write, plugin import, browser automation, mobile control, or autonomous
background execution claim.

UAA-P1-023 Redacted observability runtime
Gate met: M167 adds passive local session/run logging for UAA-managed launcher,
API, task decomposition, capability lifecycle, receipt/evidence refs,
duration status, and Control Center client-error summaries under `.uaa/` with
bounded safe-summary API access, unsafe metadata rejection, secret-like value
blocking, and focused regression tests.

UAA-P1-044 Release evidence packet
Gate met: release evidence packet format, schema, template, verifier, tests,
and docs (`docs/production/RELEASE_EVIDENCE_PACKET.md`) define commit refs,
verification lanes, report refs, accepted
failures, artifact hashes, rollback notes, non-goals, release blockers, not
scoped capabilities, and safety flags with safe refs and redacted summaries
only. The packet verifier is inspection-only and does not create artifacts,
execute release lane commands, accept failures by itself, claim public
distribution, claim signed installer readiness, or grant production authority.

UAA-P1-045 Backup/restore verification
Gate met: `docs/production/BACKUP_RESTORE_VERIFICATION.md`,
`scripts/verify_backup_restore.py`, and
`tests/test_backup_restore_verification.py` verify the UAA-P1-028 minimum set
for runs, receipts, approvals, settings, registry, audit summaries, and local
model cache refs with synthetic safe refs, SHA-256 integrity checks, offline
restore validation, corruption detection, safe report flags, and no raw paths,
raw logs, prompts, responses, provider payloads, usernames, hostnames,
environment dumps, credential material, live restore claim, public
distribution claim, or production authority.

UAA-P1-046 Rollback runbook
Gate met: `docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md` documents
backup-before-rollback, rollback, safe-disable, backup restore, unsupported
recovery, safety checks, redacted examples, and release evidence bindings for
local model cache, settings, registry, approvals, audit state, and run/receipt
state without live restore, broad mutation, shell/subprocess, connector write,
plugin runtime import, mobile control, public distribution, or production
authority claims.

UAA-P1-010 Durable run spine v1
Gate met: `docs/execution/DURABLE_RUN_SPINE.md`,
`src/ultimate_ai_agent/core/execution/durable_runs.py`, and
`tests/test_execution_state_machine_safety.py` define durable run records,
states, transitions, idempotency keys, audit refs, receipt refs, replay refs,
failure states, pause/resume/cancel/retry/dead-letter/restart recovery
contracts, invalid-transition denial, replay safety, restart visibility, and
safe-ref/redacted evidence without broad autonomy or unscoped execution.

UAA-P1-011 Task decomposition operator loop
Gate met: the Control Center Operator Loop presents the first readable loop
proof chain for runtime health, local model readiness, UAA `/v1` chat
readiness, task plan creation, one safe capability approval path, and
receipt/audit/latency/rollback inspection. The API path is covered by
`tests/test_operator_loop_p1_011.py`; the UI path is covered by
`apps/control-center/src/App.test.tsx`; no broad authority, connector writes,
shell/browser/plugin runtime, provider/model authority, raw evidence, or
production/public claim is added.

UAA-P1-025 Append-first local run storage
Gate met: `docs/execution/APPEND_FIRST_RUN_STORAGE.md`,
`src/ultimate_ai_agent/core/execution/run_storage.py`, and storage/ledger tests
define append-first atomic run and receipt persistence with idempotency-bound
writes, audit links, corruption detection, safe recovery behavior, and redacted
evidence only.

UAA-P1-026 Durable run lifecycle contracts
Gate met: durable run lifecycle tests cover allowed, denied, repeated, stale,
cancel, retry, dead-letter, and restart cases; repeated lifecycle requests are
idempotent, failure states stay inspectable, and no lifecycle action grants
unscoped runtime authority.

UAA-P1-027 Task decomposition durable-run binding
Gate met: task decomposition run APIs bind planning, approvals, registered
handlers, receipts, audit summaries, replay refs, and duplicate-mutation
denial to durable run truth while preserving redacted safe-ref evidence.

UAA-P1-030 Route status manifest
Gate met: `docs/control_center/ROUTE_STATUS_MANIFEST.md`,
`docs/control_center/route_status_manifest.json`, and Control Center route
tests map visible actions to owner, auth posture, side-effect class, risk
class, OpenAPI operation id, UI surface, approval requirement, release status,
and evidence/audit output without marking unimplemented or unsafe actions
ready.

UAA-P1-031 Product language rules
Gate met: `docs/control_center/PRODUCT_LANGUAGE_RULES.md`,
`tests/test_control_center_api_routes.py`, and
`scripts/verify_control_center_frontend.py` enforce no hidden authority, no
fake completion, no raw JSON as the primary UI for operator-critical flows, no
unsupported production/public distribution claims, no model/provider output as
authority, and no completed-state language for blocked, skipped, pending, or
mock-only work.

UAA-P1-032 Browser smoke readiness
Gate met: `docs/control_center/LOCAL_BROWSER_SMOKE.md`,
`docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md`,
`scripts/verify_control_center_browser_smoke_readiness.py`, and frontend checks
define local-only browser smoke readiness with real, mocked, skipped, and
blocked state semantics; no browser authority, external site access,
authenticated profile use, public distribution, or production readiness is
claimed.

UAA-P1-033 Accessible loading/error/empty states
Gate met: Control Center Chat Shell, Plans, Models, Approvals, Files, Runtime,
Evidence, and Settings surfaces expose accessible loading, error, empty,
blocked, and denied states with safe operator-actionable language and no raw
private data in error messages.

UAA-P1-024 Plugin/skill ecosystem boundary
Gate met: `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md` and
`docs/schemas/plugin_skill_trust_manifest.schema.json` define package identity,
provenance, per-file hashes, declared capabilities, risk class, requested
grants, exact-scope activation records, revocation behavior, audit refs,
inspectable catalog binding, callable catalog separation, and disabled runtime
import/execution defaults without plugin install, plugin execution, connector
writes, shell/subprocess, network/browser, mobile control, autonomous
background execution, public distribution, or production authority claims.

UAA-P2-049 Inspectable catalog
Gate met: `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`,
`docs/schemas/inspectable_extension_catalog.schema.json`, and
`GET /extensions/catalog` define read-only extension catalog inspection for
declared capabilities, provenance, hashes, risk, activation status, and
blocked/unknown state while keeping callable catalog, runtime import, plugin
execution, connector writes, shell/subprocess, network/browser automation,
mobile control, autonomous background execution, public distribution, and
production authority unavailable.

UAA-P2-050 Extension activation grants
Gate met: `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`,
`docs/schemas/extension_activation_grant.schema.json`, and
`tests/test_extension_activation_grants.py` define exact-scope activation and
revocation records with approval refs, scope refs, capability refs, audit refs,
replay refs, duplicate denial, stale-grant denial, and revoked-grant denial
while keeping runtime import, callable catalog, plugin execution, connector
writes, shell/subprocess, network/browser automation, mobile control,
autonomous background execution, public distribution, and production authority
unavailable.

UAA-P2-051 MCP/A2A compatibility watchlist
Gate met: `docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md` records MCP/A2A
concepts, risks, required future gates, compatibility questions, and
manifest/capability implications as strategy/watchlist only while keeping
runtime authority, connector writes, plugin execution, broad tool invocation,
network authority, backend routes, OpenAPI paths, public distribution, and
production authority unavailable.
```

## ASAP Sequence

```text
1. Build only the mapped operator surfaces with tests after route/status gaps are scoped.
2. Use UAA-P1-011 as the readable operator-loop baseline for the next Founder
   Command Center slice: FCC-MAC-001, FCC-P0-002, Action Inbox, Morning
   Briefing, then read-only email/calendar contracts later.
3. Scope the next storage migration or operator-surface milestone only after
   route authority, evidence, and rollback gates are explicit.
```
