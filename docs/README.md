# Ultimate AI Agent Docs

Status: active
Current through: v0.102.3 plus accepted checkpoint-m168, completed
UAA-P1-065 Founder Command Center review cleanup, completed UAA-P1-067
Today-Spine Founder Command Center beta-readiness planning/currentness work,
completed UAA-P1-068 Today Product Spine Contract work, completed UAA-P1-069
Evidence History Grammar work, completed UAA-P1-070 Memory Source And
Provenance Model work, completed UAA-P1-071 Memory Review Decision Capture
work, completed UAA-P1-072 Business Memory And Memory Quality Controls work,
completed UAA-P1-073 Plans To Reviewable Action Envelopes work, completed
UAA-P1-074 Chat Local Operator Surface work, completed UAA-P1-075 Governed
Code Workbench V1 work, completed UAA-P1-076 Cross-Surface Memory Intake work,
completed UAA-P1-077 Memory-To-Loop Binding work, completed UAA-P1-078
Private Beta-Readiness Gate work, and completed UAA-P1-079 User Intent
Understanding V1 work, completed UAA-P1-080 API Route Classification And
Public/Protected Inventory work, completed UAA-P1-081 Centralized FastAPI
Security Headers work, and completed UAA-P1-082 Explicit Loopback CORS
Allowlist work. UAA-P1-083 through UAA-P1-086 remain planned/queued API
boundary hardening lanes, followed by the UAA-P1-087
Private Operator Trial And UI Functional Tuning sequence: UAA-P1-087.1 local
launcher dual-surface boot readiness, UAA-P1-087.2 in-person private UI
functional tuning, and UAA-P1-087.3 native SwiftUI boot cockpit
planning/source-only scaffold after the `.command` contract is proven. The
sequence is tracked in
`docs/macos/UAA_P1_087_PRIVATE_OPERATOR_BOOT_AND_UI_TRIAL_SEQUENCE.md`.

This is the human-facing entrypoint for active documentation. The full catalog
lives in `docs/DOCUMENTATION_INDEX.md`; historical releases, checkpoint imports,
and older roadmap snapshots stay under `docs/archive/` as audit artifacts, not
current implementation claims.

## Start Here

| Need | Start with |
|---|---|
| Current repository story | `README.md`, `VERSION.md`, `docs/release_notes/v0_102_3.md` |
| Active roadmap and board | `docs/canonical/09_roadmap.md`, `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`, `docs/kanban/current_board.md` |
| Founder Command Center planning | `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`, `docs/strategy/MACOS_OF_AGENTS_PRODUCT_PRINCIPLES.md`, `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`, `docs/kanban/founder_command_center_board.md` |
| Catch-up/surpass loop | `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`, `docs/backlog/codex_recommendation_log.md`, `docs/backlog/MORNING_RECONCILIATION_ARTIFACT.md` |
| Product claims and gaps | `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md` |
| Canonical navigation | `docs/DOCUMENTATION_INDEX.md`, `docs/canonical/CANONICAL_DOC_MAP.md` |
| API boundary | `docs/api/README.md`, `docs/api/openapi_contract.md`, `docs/api/route_inventory.md` |
| Security posture | `SECURITY.md`, `docs/security/SECURITY_TRIAGE_RUNBOOK.md` |
| Documentation policy | `docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md` |

## Current Baseline Packet

The product/package baseline is `v0.102.3` / `0.102.3`. The latest accepted
repository checkpoint tag is `checkpoint-m168`. The latest accepted local model
lane checkpoint tags remain `checkpoint-m166` and `checkpoint-m167`.

Current release and checkpoint refs:

```text
docs/archive/releases/v0_102_3/README_IMPORT.md
docs/archive/releases/v0_102_3/master_plan.md
docs/release_notes/v0_102_3.md
docs/implementation/foundation_gate_implementation_plan_v0_102_3.md
docs/release_notes/checkpoint_m168.md
docs/release_notes/checkpoint_m166.md
docs/release_notes/checkpoint_m167.md
```

The active Operator Runtime Excellence sequence now points from completed
UAA-P1-065 Founder Command Center review cleanup, completed UAA-P1-067
Today-spine beta-readiness planning/currentness, completed UAA-P1-068 Today
Product Spine Contract, completed UAA-P1-069 Evidence History Grammar,
completed UAA-P1-070 Memory Source And Provenance Model, completed
UAA-P1-071 Memory Review Decision Capture, completed UAA-P1-072 Business
Memory And Memory Quality Controls, and completed UAA-P1-073 Plans To
Reviewable Action Envelopes, and completed UAA-P1-074 Chat Local Operator
Surface, completed UAA-P1-075 Governed Code Workbench V1, and completed
UAA-P1-076 Cross-Surface Memory Intake, and completed UAA-P1-077
Memory-To-Loop Binding, and completed UAA-P1-078 Private Beta-Readiness Gate
to completed UAA-P1-079 User Intent Understanding V1, and completed UAA-P1-080
API Route Classification And Public/Protected Inventory, and completed
UAA-P1-081 Centralized FastAPI Security Headers, and completed UAA-P1-082
Explicit Loopback CORS Allowlist. UAA-P1-083 through UAA-P1-086 remain
planned/queued API boundary hardening lanes, followed by
the ordered UAA-P1-087.1, UAA-P1-087.2, and UAA-P1-087.3 private boot/UI
trial sequence. UAA-P1-066
remains queued as a strictly read-only Local Model
Control Center inventory/status support lane.
This sequence makes Today the product spine and keeps memory,
Evidence, Plans, Chat, Code, and Actions bound to safe refs, review decisions,
receipts, and rollback posture. It adds no production authority, public beta,
public distribution, broad autonomy, shell/subprocess authority, unrestricted
network/browser automation, connector writes, plugin runtime import, mobile
control, model/provider authority, raw prompt export, raw response export, raw
provider payload export, or no-secret-output regression.

## Active Program Areas

| Area | Current docs |
|---|---|
| Operator Runtime Excellence | `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` |
| Founder Command Center product-loop planning | `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`, `docs/strategy/MACOS_OF_AGENTS_PRODUCT_PRINCIPLES.md`, `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`, `docs/kanban/founder_command_center_board.md`, `docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md`, `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`, `docs/metrics/NORTH_STAR_METRICS.md`, `docs/codex/CODEX_EXECUTION_PROMPTS.md` |
| Catch-up/surpass loop | `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`, `docs/backlog/codex_recommendation_log.md`, `docs/backlog/MORNING_RECONCILIATION_ARTIFACT.md` |
| Product truth packet | `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`, `docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md` |
| Control Center readiness | `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`, `docs/control_center/ROUTE_STATUS_MANIFEST.md`, `docs/control_center/route_status_manifest.json`, `docs/control_center/PRODUCT_LANGUAGE_RULES.md`, `docs/control_center/UAA_P1_065_FOUNDER_COMMAND_CENTER_REVIEW_CLEANUP.md`, `docs/control_center/UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md`, `docs/control_center/UAA_P1_069_EVIDENCE_HISTORY_GRAMMAR.md`, `docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md`, `docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md`, `docs/control_center/UAA_P1_072_BUSINESS_MEMORY_QUALITY_CONTROLS.md`, `docs/control_center/UAA_P1_073_PLANS_ACTION_ENVELOPES.md`, `docs/control_center/UAA_P1_074_CHAT_LOCAL_OPERATOR_SURFACE.md`, `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`, `docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md`, `docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md`, `docs/control_center/UAA_P1_078_PRIVATE_BETA_READINESS_GATE.md`, `docs/control_center/UAA_P1_079_USER_INTENT_UNDERSTANDING.md` |
| Local model production-readiness lane | `docs/production/M166_PRODUCTION_AUTHORITY_GATE.md`, `docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md`, `docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md`, `docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`, `docs/production/M167_OPENWEBUI_LOCAL_INSTALLER.md`, `docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md` |
| Local model operations | `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`, `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`, `docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md`, `docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md`, `docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md` |
| Release verification and evidence | `docs/production/RELEASE_VERIFICATION_LANES.md`, `docs/production/RELEASE_EVIDENCE_PACKET.md`, `docs/production/BACKUP_RESTORE_VERIFICATION.md`, `docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md`, `docs/production/LOCAL_RUNTIME_PACKAGING.md`, `docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md` |
| Performance and API cache | `docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md`, `docs/api/SAFE_STATIC_MANIFEST_CACHING.md` |
| Redacted observability | `docs/observability/SESSION_LOGGING_M167.md` |
| Plugin/skill ecosystem boundary | `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md`, `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`, `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`, `docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md`, `docs/schemas/plugin_skill_trust_manifest.schema.json`, `docs/schemas/inspectable_extension_catalog.schema.json`, `docs/schemas/extension_activation_grant.schema.json` |

The Founder Command Center docs are planning and execution artifacts for the
next product loop. They do not grant production authority, public distribution,
broad autonomy, runtime connector writes, unrestricted shell/browser/network
authority, plugin runtime import, provider/model authority, mobile runtime, or
new backend/Control Center behavior by themselves.

## Verification Commands

Use these before release-facing claims or milestone status changes:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

The named release lanes are described in
`docs/production/RELEASE_VERIFICATION_LANES.md`. Release evidence packets are
defined in `docs/production/RELEASE_EVIDENCE_PACKET.md`.

## Historical Docs

Use active canonical docs and active roadmap docs for current work. Use archive
docs only for historical review. Git tags and release history preserve exact
historical snapshots.

Historical notes such as v0.29.5 documentation policy polish, v0.38.0 M34
file capability review, v0.41.0 M37 review approval capture, and M57-M60
planning remain available under `docs/archive/` and the full documentation
index. They are not current release or production-readiness claims.
