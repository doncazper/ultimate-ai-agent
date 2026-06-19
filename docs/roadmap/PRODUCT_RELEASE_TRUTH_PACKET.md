# Product Release-Truth Packet

Status: active Operator Runtime Excellence product-truth packet
Task: UAA-P0-002
Baseline: v2.0.0 / 2.0.0
Accepted repository checkpoint: checkpoint-m168
Accepted local model lane checkpoints: checkpoint-m166, checkpoint-m167
Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`

This packet is the repo-owned product truth and gap matrix for the Operator
Runtime Excellence Program. It is a release-claim discipline artifact, not a
runtime implementation plan by itself.

External benchmark and peer-console context is product-shaping evidence only.
It is not an implementation dependency, product dependency, authority source,
or template for bypassing UAA governance.

## Release Truth

Allowed current claims:

| Claim | Evidence source |
|---|---|
| The active product/package baseline is v2.0.0 / 2.0.0. | `VERSION.md`, `README.md`, `docs/release_notes/v2_0_0.md` |
| The latest accepted repository checkpoint tag is checkpoint-m168; checkpoint-m166 and checkpoint-m167 remain the latest accepted local model lane checkpoint tags. | `README.md`, `VERSION.md`, `docs/release_notes/checkpoint_m168.md`, `docs/release_notes/checkpoint_m166.md`, `docs/release_notes/checkpoint_m167.md` |
| The current API boundary is a FastAPI route contract with 94 OpenAPI paths. | `README.md`, `docs/api/openapi_contract.md`, `docs/api/route_inventory.md`, `tests/test_api_manifest.py` |
| OpenWebUI is a shell; Python Agent Core remains authority. | `docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL.md`, `docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md` |
| The local model lane is scoped to M160-M167 and requires safe-ref, redacted, reviewed evidence. | `docs/model_management/M160_M165_LIVE_LANE_BOUNDARY.md`, `docs/production/LOCAL_MODEL_PRODUCTION_READINESS_GATE.md`, `docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md` |
| Local `llama-server` packaging/provenance review is documented as a checklist only; unverified binaries remain blocked or not production-ready. | `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`, `docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_RUNBOOK.md` |
| Local tuning advice is hardened for lag, out-of-memory, crash loop, reload loop, slow token rate, and one-change rollback cases without granting runtime authority. | `src/ultimate_ai_agent/core/local_model_management/tuning.py`, `tests/test_m167_live_model_hardening.py` |
| Local model operational recovery guidance is documented for safe, degraded, blocked, and unsupported states without public production support claims. | `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`, `docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_RUNBOOK.md` |
| Product gaps remain for reviewed live evidence attachment and completed Control Center product surfaces. | `docs/kanban/current_board.md`, `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`, `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`, `docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md`, `docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`, `docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md` |

Do not claim production readiness, public release, public beta distribution,
broad autonomy, unrestricted runtime authority, or peer-product parity until the
blocking gates below have evidence and the required verifiers pass.

## Product Excellence Matrix

Status values:

- Shipped: evidence-backed current repository capability only, not a production
  readiness or public release claim.
- Planned: named by the Operator Runtime Excellence roadmap but not shipped as
  product behavior.
- Blocked: cannot be claimed until the named gate is met.
- Future-scoped: requires a later accepted milestone before implementation or
  user-facing claims.

| Capability | Current UAA state | Target production-ready state | Priority | Status | Evidence source or missing evidence | Blocking gate |
|---|---|---|---|---|---|---|
| Product shell | CCC Web is a preview/read-only local shell, and OpenWebUI has a local test-shell role only; UAA-P0-007 maps Chat, Plans, Models, Approvals, Files, Runtime, Evidence, and Settings to current routes, missing routes, side-effect classes, authority boundaries, approval needs, evidence, blockers, and language rules. | A focused operator shell exposes Chat, Plans, Models, Approvals, Files, Runtime, Evidence, and Settings without hiding authority state. | P0 | Shipped for the operator-shell gap map; blocked for product-readiness claims. | Evidence: `README.md` capability map, `docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md`, `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`, `docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL.md`. Missing: route status manifest and completed product surfaces. | UAA-P1-030 and M172 route/surface gates. |
| API and route truth | `/api/manifest` and OpenAPI expose the current 93-path boundary with side-effect metadata. | Every visible surface maps to owner, auth posture, side-effect class, risk class, OpenAPI operation id, and release status. | P0/P1 | Shipped for the 93-path API boundary; planned for full surface mapping. | Evidence: `docs/api/openapi_contract.md`, `docs/api/route_inventory.md`, `tests/test_api_manifest.py`. Missing: Control Center route status manifest. | UAA-P1-021 and UAA-P1-030. |
| Performance baseline | UAA-P0-006 measures p50/p95 for Foundation Gate plus release-critical local paths and writes redacted reports under `reports/performance`; Control Center render timing is safely skipped until a scoped frontend timing runner exists. | Required local paths have release-blocking p95 budgets, historical comparisons, and frontend render timing once scoped. | P0/P1 | Shipped for backend/local baseline harness; planned for frontend render timing and historical regression trends. | Evidence: `docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md`, `scripts/benchmark_foundation_gate.py`, `scripts/check_foundation_gate_latency.py`, `reports/performance/latest_release_latency_baseline.json`. Missing: scoped frontend render timing runner and historical trend storage. | UAA-P0-006 met for required backend/local paths; UAA-P1-041/UAA-P1-043 remain planned. |
| Local model product loop | M151-M167 define a scoped local OpenWebUI, GGUF, llama.cpp, local `/v1`, tuning, and production-readiness evidence lane; the UAA-P0-004 matrix scaffold records required hardware rows with safe refs only, UAA-P0-005 adds a local/dev E2E smoke harness, UAA-P0-006 measures local `/v1` list/chat latency, UAA-P0-015 documents `llama-server` packaging/provenance review, UAA-P0-016 hardens tuning advice for lag, out-of-memory, crash loop, reload loop, slow token rate, and one-change rollback cases, and UAA-P0-017 documents local operational recovery. | A reviewer can run local model E2E smoke, inspect safe evidence, and confirm no tools/functions or streaming authority. | P0 | Shipped for local/dev smoke, latency scaffolding, packaging checklist, tuning-advisor hardening tests, and operational runbook; blocked for production-readiness claims. | Evidence: `docs/model_management/M153_M165_LOCAL_MODEL_MANAGEMENT_PROGRESSION.md`, `docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md`, `docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md`, `docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`, `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`, `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`, `docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md`, `src/ultimate_ai_agent/core/local_model_management/tuning.py`, `tests/test_m151_openwebui_local_gateway_api.py`, `tests/test_m167_live_model_hardening.py`. Missing: reviewed live evidence attachment across the required M167 hardware rows. | Reviewed M167 evidence refs. |
| Public trust and security posture | Root `SECURITY.md` and maintainer triage runbook explain reporting, supported lines, severity, response targets, redaction, and no-secret-output invariants. | Security posture remains public, repeatable, verifier-backed, and free of external audit, signed-release, or public distribution claims. | P0 | Shipped for UAA-P0-003 security docs; future-scoped for rate-limit posture. | Evidence: `SECURITY.md`, `docs/security/SECURITY_TRIAGE_RUNBOOK.md`, `docs/public_readiness/PUBLIC_GITHUB_READINESS.md`, `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`. Missing: later UAA-P0-014 rate-limit posture. | UAA-P0-003 met; UAA-P0-014 remains future. |
| Durable work spine | Execution, approval, and event-ledger contracts exist, but the active durable run spine is not the current product loop. | Append-first local run records support idempotency, restart recovery, receipt hashes, rollback, pause/resume/cancel, and offline restore. | P1 | Planned; blocked for durable-run claims. | Evidence: `docs/execution/EXECUTION_STATE_MACHINE.md`, `docs/approvals/APPROVAL_AUTHORITY_V2.md`, `docs/canonical/22_observability_and_event_ledger.md`. Missing: M171 durable local storage evidence. | UAA-P1-010 and M171. |
| Workspace workbench | Safe local filesystem metadata, bounded redacted preview, safe file tree refs, review approval contracts, approval-bound patch proposals, atomic patch apply receipts, rollback receipts, secret-like diff blocking, and approval-only workspace mutation enforcement exist; shell execution remains denied. | File tree refs, bounded previews, patch proposals, atomic apply, rollback receipts, and secret-like diff blocking exist before any shell lane. | P1 | Shipped for local safe-preview and approval-bound patch receipt contracts; blocked for broader mutating-workbench product claims. | Evidence: `docs/tools/FILESYSTEM_METADATA_TOOL.md`, `docs/tools/REDACTED_FILE_PREVIEW_TOOL.md`, `docs/files/FILE_REVIEW_APPROVAL_CAPTURE.md`, `tests/test_file_tree_preview.py`, `tests/test_file_write_proposals.py`, `tests/test_file_atomic_writes.py`, `tests/test_file_rollback.py`, `tests/test_file_secret_blocking.py`. Missing: M173 product-surface proof. | M173 product-surface proof and any later scoped mutation UI gate. |
| Redacted observability | Redacted observability export and evidence contracts exist, but runtime observability is not the active product lane. | Latency, cost, model, approval, tool, and error events are structured and redacted, with no raw prompt, response, path, log, environment, or credential material. | P1 | Planned; future-scoped for runtime observability claims. | Evidence: `docs/observability/REDACTED_OBSERVABILITY_EXPORT.md`, `docs/truth/CLAIM_EVIDENCE_CHAIN.md`. Missing: active runtime observability implementation and verifier lane. | UAA-P1-023 and release verification lanes. |
| Packaging and local runtime operations | Developer launcher and local docs exist; UAA-P0-015 documents local `llama-server` discovery, allowed locations, provenance, checksum/signature review, offline operation, rollback, cache cleanup, and blocked/unknown provenance handling; UAA-P0-017 documents cache cleanup, corrupted GGUF, stuck download, port conflict, credential rotation, rollback, offline mode, safe evidence collection, blocked/unknown model state, and safe-disable recovery. Public distribution and production packaging are not claimed. | A reproducible loopback-first local stack has generated secrets, rollback instructions, local model runtime checks, and no broad distribution claim. | P1 | Shipped for the local `llama-server` checklist and operational runbook; blocked for packaging and distribution claims. | Evidence: `docs/developer/LOCAL_LAUNCHER.md`, `scripts/dev/README.md`, `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`, `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`, `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`. Missing: M170/M171/M172 operational proof and UAA-P1-014 packaging proof. | UAA-P1-014 plus M170 local model gates. |
| Plugin and skill ecosystem | Manifest and install-review governance exists; plugin runtime import remains disabled by default. | A manifest-first ecosystem has static review, explicit activation grants, rollback proof, and no arbitrary runtime import. | P1/P2 | Future-scoped; blocked for activation/runtime-import claims. | Evidence: `docs/tooling/PLUGIN_MANIFEST_SECURITY_MODEL.md`, `docs/tooling/PLUGIN_INSTALL_REVIEW.md`, `docs/tooling/PLUGIN_EXECUTION_SANDBOX.md`. Missing: UAA-P1-024 boundary map and later scoped activation proof. | UAA-P1-024 and later scoped milestone approval. |
| Policy and approval consolidation | PolicyEngine, LocalApprovalAuthority, route side-effect classification, OpenAPI checks, and Foundation Gate checks remain required boundaries. | Every authority path is consolidated through the reviewed policy and approval layers with no parallel shortcut. | P1 | Planned; blocked for consolidated-authority claims. | Evidence: `docs/approvals/ACTION_POLICY.md`, `docs/approvals/APPROVAL_AUTHORITY_V2.md`, `docs/api/route_inventory.md`, `docs/implementation/foundation_gate_implementation_plan_v2_0_0.md`. Missing: consolidation map over all decision paths. | UAA-P1-020. |

## Non-Goals

This packet does not add:

- production authority
- public distribution, public release, or public beta
- broad autonomy or autonomous background sessions by default
- unapproved runtime authority
- shell execution, command execution, subprocess execution, or process spawn
- unrestricted network access or unrestricted browser automation
- connector writes
- plugin runtime import or arbitrary plugin execution
- mobile control or mobile sensor runtime
- model/provider output as production authority
- raw prompt, raw response, raw provider payload, raw path, raw log, username,
  hostname, serial, environment dump, or credential material in evidence

Any future claim that one of these non-goals has become available must point to
an accepted scoped milestone, authority boundary, approval model, test evidence,
verifier update, and rollback plan.
