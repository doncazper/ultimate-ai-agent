# UAA-P1-020 PolicyEngine Consolidation Map

Status: active gated foundation map
Baseline: v0.103.0 / 0.103.0
Scope: documentation and authority inventory only

This map identifies current policy and approval decision paths before any
UAA-P1-058 route-module extraction or broader product UI expansion proceeds.
It does not add backend routes, runtime authority, approval capture outside
existing contracts, connector writes, shell/subprocess execution, plugin runtime
import, memory writes, context injection, model/provider authority, public
distribution, or production authority.

Approval refs are identifiers only. A ref string is not authority unless the
owning LocalApprovalAuthority or scoped policy contract validates the exact
actor, action, resource, scope, status, expiry, revocation, replay,
idempotency, audit, and receipt posture required by that path.

## Required Boundary

| Boundary | Current owner | Current role |
|---|---|---|
| PolicyEngine / policy evaluators | `src/ultimate_ai_agent/core/approvals/v2/`, policy-specific core modules | Policy-only allow/deny/approval-required decisions. No execution authority by itself. |
| LocalApprovalAuthority | `src/ultimate_ai_agent/core/approvals/` | Exact-scope local approval request, grant, validation, expiry, revocation, and replay checks. |
| Route side-effect classification | `src/ultimate_ai_agent/api/manifest.py` | Authoritative side-effect class for `/api/manifest`, OpenAPI checks, route inventory, and Control Center route-status verification. |
| Foundation Gate | `src/ultimate_ai_agent/core/gate/`, `scripts/run_foundation_gate.py` | Release-blocking static and typed checks for unsafe authority expansion, route drift, redaction, OpenAPI, and evidence posture. |
| Control Center route-status manifest | `docs/control_center/route_status_manifest.json` | Visible-action metadata only. It does not replace `/api/manifest` and does not authorize work. |

## Decision Path Inventory

| Path | Owning module | Input contract | Policy/approval gate | Side-effect and risk behavior | Evidence/ref behavior | Tests | Status |
|---|---|---|---|---|---|---|---|
| Approval Authority v2 action policy | `ultimate_ai_agent.core.approvals.v2` | `ActionIntent`, `ApprovalGrant`, `ActionPolicy` | `evaluate_action_policy`, `evaluate_approval_grant`, evaluator-side revalidation | Policy-only decisions; execution remains false; high-risk or mismatched refs denied | Safe reason codes and approval/grant refs; approval ref alone denied | `tests/test_approval_authority_v2_contracts.py` | Allowed policy path |
| LocalApprovalAuthority grant validation | `ultimate_ai_agent.core.approvals` | `ApprovalRequest`, `ApprovalGrant`, `ApprovalValidationRequest` | `create_request`, `grant`, `validate_for_request`, `revoke` | Local/dev approval validation only; unknown, expired, revoked, replayed, mismatched, or arbitrary refs denied | Redacted approval receipt plans and matched grant refs only | `tests/test_approval_authority.py`, `tests/test_approval_expiration.py`, `tests/test_approval_scope.py`, `tests/test_approval_receipts.py`, `tests/test_approval_validation.py` | Allowed local approval path |
| Kernel local-dev task approval | `ultimate_ai_agent.core.kernel` | Kernel task request with tool/workspace approval refs | LocalApprovalAuthority request builders and exact validation | Local-dev workspace only; arbitrary approval refs return approval-required | Safe run refs and approval decision summaries | `tests/test_approval_integration_kernel.py`, `tests/test_kernel_request.py`, `tests/test_kernel_rollback.py` | Allowed only through LocalApprovalAuthority |
| Model router approval-sensitive routing | `ultimate_ai_agent.core.model_router` | `ModelRouteRequest`, model profiles, optional approval ref | LocalApprovalAuthority model-route request validation | Preview/route decision only; model/provider output is not authority | Route decision refs and approval-required status | `tests/test_approval_integration_model_router.py`, `tests/test_cost_governor.py` | Allowed policy path; provider calls blocked |
| Model runtime local loopback validation | `ultimate_ai_agent.core.model_runtime` | Runtime request/manifest/endpoint/smoke contracts | Typed validation and optional validated approval decision | Validation/fallback only; local loopback disabled by default and bearer-gated when enabled | Safe request/manifest/status refs; no provider payload passthrough | `tests/test_approval_integration_model_runtime.py`, `tests/test_m151_openwebui_local_gateway_api.py`, `tests/test_m167_live_model_hardening.py` | Partial; runtime authority remains blocked |
| ToolBroker authorization | `ultimate_ai_agent.core.tools` | `ToolManifest`, `ToolRequest`, `ConsentGrant`, firewall policy | ToolBroker risk policy, consent ledger, capability firewall, approval-required result | Dry-run/evaluate only; high-risk tool refs remain approval-required without exact authority | Tool decision refs, reason codes, safe summaries | `tests/test_tool_broker_authorization.py`, `tests/test_tool_broker_risk_policy.py`, `tests/test_stage_a_policy_hardening.py` | Allowed planning path |
| SecretBroker access evaluation | `ultimate_ai_agent.core.secrets` | `CredentialReference`, `SecretAccessRequest` | SecretBroker reference validation and access evaluation | Validation/evaluate only; raw secret values never returned | Credential refs and denial reason codes only | `tests/test_secret_credentials.py`, `tests/test_secret_broker_redaction.py` | Allowed reference-only path |
| Consent ledger evaluation | `ultimate_ai_agent.core.consent` | `ConsentGrant`, `ConsentQuery` | ConsentLedger query evaluation | Validation/evaluate only; consent ref alone is not action authority | Consent refs, subject/scope refs, reason codes | `tests/test_stage_a_policy_hardening.py`, `tests/test_tool_broker_authorization.py` | Allowed policy path |
| File review approval capture | `ultimate_ai_agent.core.file_review` | `FileReviewApprovalCaptureRequest` | Review-only capture contract, redaction validation | Local-dev workspace only; capture is review evidence, not file mutation | File review approval refs, audit refs, redacted summaries | `tests/test_file_review_authority_boundaries.py`, `tests/test_control_center_api_routes.py` | Allowed review-only path |
| File write proposal and atomic apply | `ultimate_ai_agent.core.files` | Safe file refs, patch proposal, approval request | LocalApprovalAuthority exact patch proposal approval; idempotency and rollback checks | Local-dev workspace only; proposal/apply/rollback are scoped, audited, rollback-aware | Safe file refs, pre/post image refs, mutation receipts, rollback receipts | `tests/test_file_write_proposals.py`, `tests/test_file_atomic_writes.py`, `tests/test_file_rollback.py`, `tests/test_file_secret_blocking.py` | Allowed only through exact scoped approval |
| Task-decomposition approvals | `ultimate_ai_agent.core.task_decomposition.runtime` | Approval request/grant/revoke payloads, task plan/run contracts | Service approval request, grant capture, revoke, capability approval binding | Local-dev workspace only; arbitrary approval refs do not unlock gated capabilities | Durable run refs, approval refs, audit refs, receipt refs, replay refs | `tests/test_task_decomposition_production_api.py`, `tests/test_operator_loop_p1_011.py` | Allowed local product-loop path |
| Founder Loop action inbox posture | `ultimate_ai_agent.core.storage.founder_loop` | Storage-backed action proposal records | No state-change gate in this slice; approval-envelope refs are dry-run identifiers | Local storage summaries only; action mutation, grant capture, and execution remain missing | Safe refs, dry-run envelope refs, receipt/audit/idempotency/rollback posture | `tests/test_founder_loop_storage.py`, `tests/test_control_center_founder_loop_api.py` | Partial; mutation path missing |
| macOS Setup Assistant approval envelopes | `ultimate_ai_agent.core.macos_setup_assistant` | Setup plan, setup step, approval-envelope metadata | Dry-run envelope validation only | Validation-only; installer, model download, LaunchAgent, service, credential, and rollback execution blocked | Dry-run approval refs, receipt-plan refs, rollback-plan refs, bounded preview refs | `tests/test_macos_setup_assistant.py`, `tests/test_control_center_api_routes.py` | Partial; setup mutation blocked |
| Mattermost role/tool action posture | `ultimate_ai_agent.api.mattermost`, Mattermost core modules | Status, role catalog, role bind/unbind, message event contracts | Disabled-by-default local bridge contracts; tool actions approval-required | Local-dev workspace only; unapproved connector writes blocked | Safe role refs, audit refs, receipt refs, reply-command proposals | `tests/test_mattermost_agent_rooms_api.py` | Partial; connector write authority blocked |
| Memory contracts | `ultimate_ai_agent.core.memory`, Founder Loop storage | Memory record/read/write-evaluate contracts and review records | Validation/evaluate only; Memory Review is inspection-only | Local-dev workspace only; automatic writes and context injection blocked | Memory refs, provenance/source/evidence refs, review posture | `tests/test_memory_api_routes.py`, `tests/test_founder_loop_storage.py` | Partial; write policy binding missing |
| Governed web evidence | `ultimate_ai_agent.api.web_evidence` | Governed evidence request/status contract | Allowlisted HTTPS GET envelope, bounded redacted preview, receipt refs | Governed network read-only; unrestricted browsing, redirects, downloads, and hidden access blocked | Receipt refs, bounded preview refs, disclosure refs | `tests/test_governed_web_evidence.py`, `tests/test_api_manifest.py` | Allowed scoped network-read path |
| Route side-effect classification | `ultimate_ai_agent.api.manifest` | FastAPI route path/method metadata | `route_side_effect_class` and API manifest generation | `none`, `validation_only`, `local_dev_workspace_only`, `governed_network_read_only`; no production runtime class | `/api/manifest`, OpenAPI, route inventory refs | `tests/test_api_manifest.py`, `tests/test_control_center_api_routes.py`, `tests/test_gate_evaluator_characterization.py` | Authoritative |
| Foundation Gate checks | `ultimate_ai_agent.core.gate` | Gate criteria and typed reports | Gate evaluator, docs/OpenAPI/static safety checks | Release-blocking; unsafe authority expansion fails before promotion | Foundation Gate report refs, lane refs, safe summaries | `tests/test_foundation_gate_criteria.py`, `tests/test_run_foundation_gate_script.py`, `tests/test_gate_evaluator_characterization.py` | Authoritative release gate |

## Duplicate, Parallel, Missing, And Future-Scoped Paths

| Classification | Path | Current disposition |
|---|---|---|
| Blocked | Caller-supplied approval ref as authority | Denied. Approval refs alone are identifiers only. |
| Blocked | `approval_test_` refs as runtime authority | Denied outside explicit local test fixtures. |
| Blocked | Model/provider output as authority | Denied. Model routes and OpenWebUI shell output are not authority. |
| Blocked | Memory refs or context-pack refs as authority | Denied. Memory is recall, not truth or authority; context injection remains scoped separately. |
| Blocked | Tool-intent refs as authority | Denied. ToolBroker must evaluate manifest, request, consent, firewall, and approval posture. |
| Blocked | Control Center React state as product authority | Denied. UI state is presentation only unless backed by Python core/API contracts. |
| Blocked | OpenWebUI bridge, Mattermost bridge, connector writes, plugin import, browser automation, shell/subprocess, mobile control | Not scoped for current authority. |
| Duplicate/parallel risk | File review local UI approve/deny state | Treated as review-only local UI state; not product approval evidence. |
| Duplicate/parallel risk | Founder Loop action approval-envelope refs | Dry-run posture only until state-change and grant-capture contracts exist. |
| Missing | Single cross-module PolicyEngine facade for all product workflows | Future consolidation work. Current map freezes owners and blocks shortcut claims. |
| Missing | CLI inspection path for new Founder Loop action and memory review decisions | Future scoped work before product-readiness claims. |
| Future-scoped | UAA-P1-058 route extraction | Blocked until this map, route grouping map, service-module plan, Foundation Gate, OpenAPI, and `/api/manifest` are green. |

## Acceptance Notes

- No current decision path may bypass PolicyEngine-like evaluation,
  LocalApprovalAuthority, route side-effect classification, OpenAPI checks, or
  Foundation Gate checks for convenience.
- Any later mutating path must be exact-scoped, approval-bound, idempotent,
  auditable, rollback-aware, redacted, receipt-backed, and tested.
- This document accepts UAA-P1-020 as a foundation map only. It does not
  implement consolidation code, service extraction, new routes, or UI controls.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_approval_authority.py tests/test_approval_authority_v2_contracts.py tests/test_approval_integration_kernel.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```
