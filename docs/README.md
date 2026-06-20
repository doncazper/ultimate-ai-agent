# Ultimate AI Agent Docs

Status: active
Current through: v0.102.1 plus accepted checkpoint-m168 and active Operator
Runtime Excellence P2 ecosystem inspection work through UAA-P2-051

This is the human-facing entrypoint for active documentation. The full catalog
lives in `docs/DOCUMENTATION_INDEX.md`; historical releases, checkpoint imports,
and older roadmap snapshots stay under `docs/archive/` as audit artifacts, not
current implementation claims.

## Start Here

| Need | Start with |
|---|---|
| Current repository story | `README.md`, `VERSION.md`, `docs/release_notes/v0_102_1.md` |
| Active roadmap and board | `docs/canonical/09_roadmap.md`, `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`, `docs/kanban/current_board.md` |
| Catch-up/surpass loop | `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`, `docs/backlog/codex_recommendation_log.md` |
| Product claims and gaps | `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md` |
| Canonical navigation | `docs/DOCUMENTATION_INDEX.md`, `docs/canonical/CANONICAL_DOC_MAP.md` |
| API boundary | `docs/api/README.md`, `docs/api/openapi_contract.md`, `docs/api/route_inventory.md` |
| Security posture | `SECURITY.md`, `docs/security/SECURITY_TRIAGE_RUNBOOK.md` |
| Documentation policy | `docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md` |

## Current Baseline Packet

The product/package baseline is `v0.102.1` / `0.102.1`. The latest accepted
repository checkpoint tag is `checkpoint-m168`. The latest accepted local model
lane checkpoint tags remain `checkpoint-m166` and `checkpoint-m167`.

Current release and checkpoint refs:

```text
docs/archive/releases/v0_102_1/README_IMPORT.md
docs/archive/releases/v0_102_1/master_plan.md
docs/release_notes/v0_102_1.md
docs/implementation/foundation_gate_implementation_plan_v0_102_1.md
docs/release_notes/checkpoint_m168.md
docs/release_notes/checkpoint_m166.md
docs/release_notes/checkpoint_m167.md
```

The active Operator Runtime Excellence P2 ecosystem inspection lane is
docs/verifier/security/evidence/performance/operator-shell scaffolding. It adds
no production authority, public distribution, broad autonomy, shell/subprocess
authority, unrestricted network/browser automation, connector writes, plugin
runtime import, mobile control, model/provider authority, raw prompt export,
raw response export, raw provider payload export, or no-secret-output
regression.

## Active Program Areas

| Area | Current docs |
|---|---|
| Operator Runtime Excellence | `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` |
| Catch-up/surpass loop | `docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md`, `docs/backlog/codex_recommendation_log.md` |
| Product truth packet | `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md` |
| Control Center readiness | `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`, `docs/control_center/PRODUCT_LANGUAGE_RULES.md` |
| Local model production-readiness lane | `docs/production/M166_PRODUCTION_AUTHORITY_GATE.md`, `docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md`, `docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md`, `docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`, `docs/production/M167_OPENWEBUI_LOCAL_INSTALLER.md`, `docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md` |
| Local model operations | `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`, `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md` |
| Release verification and evidence | `docs/production/RELEASE_VERIFICATION_LANES.md`, `docs/production/RELEASE_EVIDENCE_PACKET.md`, `docs/production/BACKUP_RESTORE_VERIFICATION.md`, `docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md`, `docs/production/LOCAL_RUNTIME_PACKAGING.md`, `docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md` |
| Performance and API cache | `docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md`, `docs/api/SAFE_STATIC_MANIFEST_CACHING.md` |
| Redacted observability | `docs/observability/SESSION_LOGGING_M167.md` |
| Plugin/skill ecosystem boundary | `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md`, `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`, `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`, `docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md`, `docs/schemas/plugin_skill_trust_manifest.schema.json`, `docs/schemas/inspectable_extension_catalog.schema.json`, `docs/schemas/extension_activation_grant.schema.json` |

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
