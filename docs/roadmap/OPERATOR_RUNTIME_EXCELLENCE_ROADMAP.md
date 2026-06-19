# Operator Runtime Excellence Roadmap

Status: Active product/runtime excellence plan.

This plan is a repo-owned execution artifact for bringing Ultimate AI Agent to
credible parity with mature local operator-console systems, then moving beyond
them through a stronger foundation, cleaner structure, lower latency, tighter
security, and more durable local operation.

This plan does not grant production authority. It does not add runtime model
calls, shell/subprocess execution, unrestricted network access, browser
automation, plugin execution, mobile sensor access, connector writes, public
distribution, or broad autonomy by itself. Any item that needs those powers must
use a scoped milestone with authority boundary, risk ceiling, approval model,
persistence model, test plan, verifier updates, and rollback plan.

## Strategic Position

Mature peer operator consoles are ahead as shipped products: broader UI,
gateway runtime, durable workflows, code workbenches, integrations, release
evidence, packaging, and public security posture.

Ultimate AI Agent is ahead as a governed Python core: stricter contracts,
safe-ref discipline, exact approval boundaries, milestone gates, OpenAPI
discipline, and a sharper M160-M167 local model production-readiness lane.

The goal is not to clone a peer console. The goal is to build the better
architecture:

- Python Agent Core remains the brain.
- Control Center and OpenWebUI are shells, not authority.
- PolicyEngine and LocalApprovalAuthority remain hard boundaries.
- Runtime authority is opt-in, exact-scope, redacted, replay-safe, revocable,
  and test-bound.
- Product surfaces expose operational truth instead of hiding state.
- Performance and durability are first-class release gates, not cleanup tasks.

## Excellence Targets

| Pillar | Peer Strength | UAA Excellence Target |
|---|---|---|
| Product shell | Full Mission Control surface | Leaner operator shell with fewer but deeper truth surfaces |
| Runtime gateway | Broad Fastify gateway | Typed FastAPI gateway with stable OpenAPI, side-effect classes, and hard policy gates |
| Local models | Provider/local runtime support | Exact-approved GGUF acquisition, llama.cpp lifecycle, OpenWebUI E2E, tuning, and M166/M167 evidence gates |
| Durable work | Durable runs and replay proof | Simpler append-first local run spine with idempotency, restart recovery, receipt hashes, and rollback |
| Code/workspace | Governed Code Mode | Safer local workspace workbench before shell, with atomic patching and rollback by default |
| Memory | Operator-visible lifecycle | Source-prioritized recall, no hidden prompt injection, explicit write policy, and decay/dedupe evidence |
| Security | Public policy and many tests | More formal authority map, redaction invariants, route side-effect classes, and security-lane gates |
| Performance | Product verification lanes | p50/p95 budget gates for API, planning, file preview, local model, and UI smoke paths |
| Packaging | Docker and Windows installers | Reproducible loopback-first local stack, signed-release path later, no trust claims without proof |
| Ecosystem | MCP, skills, extensions | Manifest-first skill/plugin ecosystem with no runtime import until explicitly approved |

## Non-Negotiable Invariants

- No raw prompt, raw response, raw provider payload, raw path, raw log, username,
  hostname, serial, environment dump, or credential material in durable evidence.
- No OpenWebUI authority over UAA. OpenWebUI remains a shell.
- No model/provider output as production authority by itself.
- No tool, shell, network, browser, plugin, connector, mobile, or remote action
  without reviewed capability scope and exact approval where required.
- No bypass around PolicyEngine, LocalApprovalAuthority, route side-effect
  classification, OpenAPI checks, or Foundation Gate checks.
- Every mutating path must have idempotency, audit, rollback, and test evidence.
- Every product claim must be backed by source, tests, docs, or release evidence.

## Program Milestones

### M168 - Currentness and Product Truth

Goal: make the repo tell one current story.

Tasks:

- `UAA-P0-001` Repair README/version/current-baseline truth across M150-M167.
- `UAA-P0-002` Add repo-owned product gap and excellence matrix in
  `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`.
- `UAA-P0-008` Update docs index/canonical map for M160-M167 and this roadmap.
- `UAA-P0-009` Make OpenAPI path count and API manifest current.
- `UAA-P0-010` Add verifier rule for stale active-board labels.

Acceptance:

- Current baseline, latest checkpoint tags, README status, roadmap status, and
  OpenAPI route count do not contradict each other.
- External benchmark and peer-console context is recorded as product-shaping
  evidence only, not as a product dependency, implementation dependency,
  authority source, or implementation template.
- Documentation integrity and OpenAPI checks pass.

Verification:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
```

### M169 - Public Trust and Security Package

Goal: match and improve on the public trust posture expected from mature local
operator products.

Tasks:

- `UAA-P0-003` Add `SECURITY.md` with supported lines, private reporting path,
  severity definitions, response targets, and invariants.
- `UAA-P0-011` Add security triage runbook for secret scanning, dependency
  alerts, unsafe logging, route auth, and redaction regressions.
- `UAA-P0-012` Add static checks for raw prompt/provider payload/path/log
  language in release-facing docs.
- `UAA-P0-013` Add API safe-error and no-secret-output regression tests to the
  required verification lane.
- `UAA-P0-014` Add rate-limit posture to mutating local-dev routes.

Acceptance:

- External reporters can understand how to report vulnerabilities.
- Maintainers have a repeatable triage process.
- Safe exception messages, redaction, and no-raw evidence checks are tested.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_safe_exception_messages.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_secret_broker_redaction.py
.venv/bin/python scripts/verify_all.py --skip-ruff --skip-pytest
```

### M170 - Local Model Product Loop

Goal: convert the M160-M167 local model lane into the first visible product loop
where UAA is strongest on local model safety and operational clarity.

Tasks:

- `UAA-P0-004` Build the M167 live evidence matrix with safe refs, reviewer refs,
  hardware profiles, blockers, and status in
  `docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md`.
- `UAA-P0-005` Add local model E2E smoke harness over approved GGUF, llama.cpp,
  local `/v1/models`, local `/v1/chat/completions`, and OpenWebUI shell in
  `docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`.
- `UAA-P0-015` Add installer/runtime packaging checklist for llama-server
  discovery, provenance, checksum/signature review, rollback, and offline mode
  in `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`.
- `UAA-P0-016` Add tuning advisor hardening cases for lag, OOM, crash loop,
  reload loop, slow tokens per second, and one-change rollback.
- `UAA-P0-017` Add local model operator runbook for cache cleanup, corrupted
  GGUF, stuck download, port conflict, credential rotation, rollback, offline
  mode, safe evidence collection, blocked/unknown model state, and safe-disable
  in `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`.

Acceptance:

- OpenWebUI can be tested as a shell against UAA's local `/v1` gateway.
- Tools/functions and streaming remain denied unless separately scoped later.
- All evidence is redacted summary only and safe-ref only.
- M166 authority remains exact-bound to local llama.cpp/OpenWebUI shell scope.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_m166_production_release_gate.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_m167_live_model_hardening.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_m151_openwebui_local_gateway_api.py
```

### M171 - Durable Local Runtime Spine

Goal: add the minimal durable state model needed for reliable operator work
without creating a sprawling runtime.

Tasks:

- `UAA-P1-010` Done: define durable run records, run states, transitions,
  idempotency keys, audit refs, receipt refs, replay refs, rollback refs,
  restart recovery, checksum snapshot validation, and safety tests.
- `UAA-P1-025` Done: implement append-first local storage for runs and receipt
  summaries with atomic writes and corruption detection.
- `UAA-P1-026` Done: add pause, resume, cancel, retry, dead-letter, and
  restart recovery contracts.
- `UAA-P1-027` Done: bind task decomposition runs to durable run records,
  approval refs, receipt refs, replay validation, restart visibility, and
  explicit idempotency replay denial.
- `UAA-P1-028` Done: define backup minimum set, verification checks, rollback,
  and offline/operator-run restore plan.
- `UAA-P1-029` Done: add replay-safe receipt hashing for mutating local paths.

Acceptance:

- A local task run can survive process restart without losing run truth.
- Duplicate mutation attempts are blocked by idempotency keys.
- Receipt hashes support replay validation without exposing private runtime
  content.
- Restore is offline/operator-run until a later scoped milestone proves live
  restore safety.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_execution_state_machine_safety.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_event_ledger_append_only.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_file_atomic_writes.py
```

### M172 - Control Center Operator Shell v1

Goal: build a focused set of surfaces and make each one operationally truthful,
fast, and inspectable.

Required surfaces:

- Chat Shell: local OpenWebUI/Control Center entry point with model/status truth.
- Plans: task decomposition, approval needs, DAG status, and safe execution.
- Models: GGUF search, acquisition status, llama.cpp status, tuning, and rollback.
- Approvals: exact-scope pending approvals, grant capture, revoke, and audit.
- Files: safe refs, bounded preview, diff proposal, atomic apply, rollback.
- Runtime: health, latency, queue, local model status, storage status.
- Evidence: receipts, audit summaries, verifier reports, and release proof.
- Settings: loopback/auth tokens, feature flags, safe defaults, kill switches.

Tasks:

- `UAA-P0-007` Map each surface to current routes and missing routes in
  `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`.
- `UAA-P1-030` Done: add route status manifest for visible surface readiness in
  `docs/control_center/ROUTE_STATUS_MANIFEST.md`.
- `UAA-P1-031` Done: add enforceable product language rules in
  `docs/control_center/PRODUCT_LANGUAGE_RULES.md` for no hidden authority, no
  fake completion, no raw JSON as the primary UI for operator-critical flows,
  no unsupported production/public distribution claims, no model/provider output
  as authority, and no completed-state language for blocked/skipped/pending work.
- `UAA-P1-032` Done: add browser smoke readiness for the first product loop in
  `docs/control_center/LOCAL_BROWSER_SMOKE.md`,
  `docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md`, and
  `apps/control-center/src/App.test.tsx` with real/mocked/skipped/blocked
  states and explicit blockers for missing prerequisites.
- `UAA-P1-033` Done: add accessible loading/error/empty/blocked/denied
  operator states for Chat Shell, Plans, Models, Approvals, Files, Runtime,
  Evidence, and Settings in `apps/control-center/src/components/OperatorSurfaceStates.tsx`,
  `apps/control-center/src/routes.tsx`, `apps/control-center/src/App.test.tsx`,
  and `scripts/verify_control_center_frontend.py`.

Acceptance:

- A user can complete the first product loop without reading raw API payloads:
  select local model, run local shell smoke, create plan, approve safe handler,
  inspect receipt, and rollback a local file proposal.
- Every visible action maps to route authority and side-effect class.
- Product language rules are documented and statically checked for
  Control Center and release-facing copy where practical.
- Browser smoke coverage opens the shell, verifies safe readable UI states for
  the first product loop, and reports blocked prerequisites without hidden
  authority or raw JSON primary UI.
- Loading, error, empty, blocked, and denied states are accessible,
  operator-actionable, and distinct from product readiness or authority claims.

Verification:

```bash
make frontend-check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
```

### M173 - Safer Workspace Workbench

Goal: sequence safety before shell execution and make local workspace mutation
reversible by default.

Tasks:

- `UAA-P1-012` Build file tree safe refs and bounded previews.
- `UAA-P1-034` Add patch proposal contracts with exact file/path binding.
- `UAA-P1-035` Add atomic apply and rollback receipts.
- `UAA-P1-036` Add secret-like diff blocking and redacted preview.
- `UAA-P1-037` Add approval-bound mutation only; no shell execution.
- `UAA-P2-038` Shape future shell/subprocess lane separately after M171-M173 are
  green.

Acceptance:

- UAA can safely review and apply local patches with rollback evidence before
  any shell/code-execution authority exists.
- All file writes are exact-approved, idempotent, audit-bound, and reversible.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_file_write_proposals.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_file_rollback.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_file_secret_blocking.py
```

### M174 - Performance and Latency Gate

Goal: make speed a release blocker.

Tasks:

- `UAA-P0-006` Done: add p50/p95 timing harness with budget definitions and
  latest safe reports under `reports/performance`; canonical doc is
  `docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md`.
- `UAA-P1-039` Refine budgets from repeated local evidence for API manifest,
  model route preview, task decomposition, file preview, local model list,
  local chat, and dashboard.
- `UAA-P1-040` Add historical regression trend output under `reports/performance`.
- `UAA-P1-041` Add hot-path profiling for task decomposition and OpenAPI build.
- `UAA-P1-042` Cache safe static manifest data without caching authority
  decisions.
- `UAA-P1-043` Add latency gate to Foundation Gate report.

Initial budgets:

| Path | Local target |
|---|---:|
| `/health` | p95 under 50 ms |
| `/api/manifest` | p95 under 150 ms |
| `/models/route/preview` | p95 under 150 ms |
| `/task-decomposition/classify` | p95 under 100 ms |
| `/task-decomposition/decompose` | p95 under 250 ms |
| `/files/read/preview` bounded text | p95 under 150 ms |
| `/v1/models` local gateway | p95 under 100 ms |
| `/v1/chat/completions` local path | p95 under 250 ms |
| Control Center first useful local render | p95 under 1500 ms |

Acceptance:

- Every release candidate reports latency budgets.
- Authority decisions are never skipped for speed.
- Cache invalidation is explicit and tested.

Verification:

```bash
.venv/bin/python scripts/benchmark_foundation_gate.py
.venv/bin/python scripts/check_foundation_gate_latency.py
```

### M175 - Release, Packaging, and Recovery Proof

Goal: match mature release discipline without overclaiming distribution.

Tasks:

- `UAA-P1-013` Add named verification lanes for docs, OpenAPI, API safety,
  security/redaction, local model E2E, durability, frontend, and performance.
- `UAA-P1-014` Add Docker/local runtime packaging with loopback-only defaults.
- `UAA-P1-044` Add release evidence packet format with commit, checks, reports,
  accepted failures, and artifact hashes.
- `UAA-P1-045` Add backup/restore verification for local state.
- `UAA-P1-046` Add rollback runbook for local model cache, settings, registry,
  approvals, and audit state.
- `UAA-P2-047` Shape signed installer and public distribution lane only after
  local loop, security, and durability gates are green.

Acceptance:

- A local release candidate can be verified, backed up, restored offline, and
  rolled back with redacted evidence.
- Public distribution remains unclaimed until signed artifact proof exists.

Verification:

```bash
.venv/bin/python scripts/verify_all.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

### M176 - Ecosystem and Extension Boundary

Goal: make extension trust visible and non-magical before broad plugin runtime
authority exists.

Tasks:

- `UAA-P1-024` Define plugin/skill manifest trust schema.
- `UAA-P2-048` Add static package review with provenance and per-file hashes.
- `UAA-P2-049` Add inspectable catalog separate from callable catalog.
- `UAA-P2-050` Add activation grants with exact capabilities and revocation.
- `UAA-P2-051` Add MCP/A2A compatibility watchlist without runtime authority.

Acceptance:

- Users can inspect extension capabilities before activation.
- Runtime import remains disabled by default.
- Activation is exact-scope, revocable, and audit-bound.

## ASAP Task List

### First 48 Hours

- `UAA-P0-001` Done: repair baseline/currentness.
- `UAA-P0-002` Done: land product release-truth packet.
- `UAA-P0-003` Done: add public security posture.
- `UAA-P0-004` Done: create M167 evidence matrix skeleton.
- `UAA-P0-005` Done: add local model E2E smoke harness.
- `UAA-P0-006` Done: add first performance budget harness.

### First Week

- `UAA-P0-007` Done: Control Center operator-shell gap map.
- `UAA-P0-015` Done: llama-server packaging/provenance checklist.
- `UAA-P0-016` Done: tuning advisor hardening cases.
- `UAA-P0-017` Done: Local model operational runbook.

### Weeks 2-3

- `UAA-P1-010` Done: durable run spine spec and tests.
- `UAA-P1-025` Done: append-first local run storage.
- `UAA-P1-026` Done: durable run lifecycle contracts.
- `UAA-P1-027` Done: task decomposition to durable run binding.
- `UAA-P1-028` Done: backup/verify/offline restore plan.
- `UAA-P1-029` Done: replay-safe receipt hashing for mutating local paths.
- `UAA-P1-030` Done: visible route status manifest.
- `UAA-P1-031` Done: product language rules.
- `UAA-P1-032` Done: browser smoke readiness for first product loop.
- `UAA-P1-033` Done: accessible loading/error/empty/blocked/denied states for
  eight Control Center operator surfaces.

### Weeks 4-6

- `UAA-P1-012` Workspace workbench safe refs and previews.
- `UAA-P1-034` Patch proposal contracts.
- `UAA-P1-035` Atomic apply and rollback receipts.
- `UAA-P1-039` Latency budget gate.
- `UAA-P1-044` Release evidence packet.

## Definition of Ready

An item may enter Ready only when it has:

- exact capability/surface name
- authority boundary
- risk ceiling
- approval model
- persistence model
- redaction and audit requirements
- test plan
- verifier updates
- rollback plan
- docs impact

## Definition of Done

An item is Done only when:

- implementation or docs match the scoped milestone
- tests pass for the changed surface
- OpenAPI/Foundation Gate impact is updated when applicable
- no raw private data or secret-like evidence is introduced
- user-facing claims match implementation
- rollback or non-goal language is explicit
- the Kanban board is updated

## Excellence Scorecard

| Capability | Current UAA | Target State | Priority |
|---|---|---|---|
| Current release truth | mixed M150-M167 story | single currentness packet | P0 |
| Public security posture | missing tracked `SECURITY.md` | public reporting and triage | P0 |
| Local model product loop | strong contracts, partial live lane | real redacted E2E proof | P0 |
| Operator UI | small Control Center | focused product shell | P0 |
| Durable runtime | contracts and local pieces | restart-safe run spine | P1 |
| Workspace workbench | file contracts and previews | safe patch/apply/rollback | P1 |
| Performance gate | foundation latency scripts | release-blocking p95 budgets | P1 |
| Packaging/release | local dev and CI | reproducible local stack and evidence packet | P1 |
| Extension ecosystem | capability/plugin contracts | inspectable, activatable, revocable catalog | P2 |
| Mobile companion | iOS skeleton/read-only contracts | companion after core loop is stable | P2 |

## First Product Loop

The first loop that proves UAA is becoming a product:

1. Start local FastAPI app.
2. Open Control Center.
3. Inspect runtime health and local model readiness.
4. Select or approve a local GGUF model.
5. Launch loopback llama.cpp through reviewed settings.
6. Use OpenWebUI or Control Center chat shell through UAA `/v1`.
7. Create a task decomposition plan.
8. Capture exact approval for one safe registered capability.
9. Execute the plan through durable local run state.
10. Inspect redacted receipt, audit summary, latency report, and rollback status.

This is stronger than a broad console claim because it proves authority, state,
evidence, and speed in one narrow but real operator loop.
