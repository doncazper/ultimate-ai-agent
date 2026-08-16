#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.authority import (  # noqa: E402
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.control_center.action_decisions import (  # noqa: E402
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.local_tasks import (  # noqa: E402
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF,
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.control_center.operational_status import (  # noqa: E402
    build_control_center_local_models_status,
)
from ultimate_ai_agent.core.storage import (  # noqa: E402
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)


SUCCESS_MESSAGE = "Operational maturity manifest verification passed."
MANIFEST_PATH = ROOT / "docs/control_center/operational_maturity_manifest.json"
SCHEMA_PATH = ROOT / "docs/schemas/operational_maturity_manifest.schema.json"
AUTHORITY_SCORECARD_PATH = (
    ROOT / "docs/control_center/authority_candidate_scorecard.json"
)
AUTHORITY_SCORECARD_SCHEMA_PATH = (
    ROOT / "docs/schemas/authority_candidate_scorecard.schema.json"
)
AUTHORITY_CONVEYOR_DOC_PATH = ROOT / "docs/control_center/AUTHORITY_RAMP_CONVEYOR.md"
LADDER_DOC_PATH = ROOT / "docs/control_center/OPERATIONALIZATION_LADDER.md"
GAP_MAP_PATH = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
PRODUCT_LANGUAGE_RULES_PATH = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
FOUNDER_BOARD_PATH = ROOT / "docs/kanban/founder_command_center_board.md"
CONTROL_CENTER_MOCK_DATA_PATH = (
    ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
)

EXPECTED_MODULES = {
    "action_inbox",
    "files_patch_workbench",
    "memory",
    "chat_plans",
    "evidence",
    "local_models",
    "inbox_sources_connectors",
    "settings",
}
LADDER_LABELS = {
    0: "docs_only",
    1: "read_only_status",
    2: "proposal_review",
    3: "decision_receipts",
    4: "execution_ready_contract",
    5: "local_execution_receipt_evidence",
    6: "rollback_safe_disable_verified",
    7: "routine_operational_loop",
}
AUTHORITY_TIER_DOC_REF = "docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md"
AUTHORITY_TIER_DOCTRINE = "Earned authority, low friction by default, strict only where consequences justify it."
EXPECTED_USABLE_AUTHORITY_TIERS = {
    0: "tier_0_ui_ephemeral_state",
    1: "tier_1_local_read_preview",
    2: "tier_2_local_draft_proposal",
    3: "tier_3_reversible_local_mutation",
    4: "tier_4_external_mutation",
    5: "tier_5_background_standing_authority",
}
LOW_FRICTION_TIER_IDS = {
    "tier_1_local_read_preview",
    "tier_2_local_draft_proposal",
}
TIER_LOW_FRICTION_FORBIDDEN_CLAIMS = {
    "provider_model_call",
    "connector_write",
    "browser_automation",
    "shell_subprocess_execution",
    "external_mutation",
    "background_standing_authority",
    "runtime_context_injection",
    "broad_autonomy",
    "production_authority",
}
TIER_MODEL_REQUIRED_GUARDRAILS = {
    "tier_0_may_remain_ui_owned_for_presentation_only",
    "tier_1_local_read_preview_no_approval_required",
    "tier_2_local_draft_no_approval_required_to_create",
    "tier_2_commit_send_apply_requires_later_authority",
    "tier_3_reversible_local_mutation_must_show_undo_or_safe_disable",
    "tier_4_external_mutation_requires_exact_approval_receipt_idempotency",
    "tier_5_background_standing_authority_requires_mode_domain_lease",
    "control_center_no_durable_truth",
    "draft_available_does_not_mean_send_available",
    "preview_available_does_not_mean_runtime_execution",
}
EXPECTED_POLICY_DECISIONS = {"allow", "ask", "deny", "degrade_to_draft"}
LEGACY_LANE_STATUS = "compatibility_audit_only"
CANONICAL_AUTHORITY_SOURCE = "authority_capabilities"
AUTHORITY_MODE_CANON_SNIPPETS = {
    "active authority foundation canon for authoritylease v1",
    "mode/domain/lease authority",
    "operator-selected session leases",
    "mission-scoped leases",
    "unsupported browser/app/payment/calendar/messages/home assistant adapters "
    "remain denied or draft-degraded",
    "read-only",
    "ask before changes",
    "approved safe local work",
}
PRODUCT_LANGUAGE_TIER_SNIPPETS = {
    "authority modes and usable tiers",
    "authoritylease",
    "tier 1 local read/preview",
    "tier 2 local draft/proposal",
    "draft available is not send available",
    "preview available is not runtime execution",
}
LOCAL_TASK_ROUTE = "POST /control-center/actions/{action_id}/local-task/commit"
LOCAL_TASK_PATH = "/control-center/actions/{action_id}/local-task/commit"
LOCAL_TASK_LANE_ID = "local_task_create"
LOCAL_TASK_RECEIPT_REF = "receipt:founder-loop-local-task:*"
LOCAL_TASK_EVENT_REF = "evidence-event-type:local_task_created"
LOCAL_TASK_ROLLBACK_REF = FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF
LOCAL_TASK_SAFE_DISABLE_REF = FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF
LOCAL_TASK_REPEATABILITY_GATE_REF = "FCC-ACTION-002"
LOCAL_TASK_REPEATABILITY_REQUIRED_FOCUSED_TEST_REFS = {
    "tests/test_founder_loop_storage_actions.py::test_action_inbox_local_task_commit_requires_exact_approval_and_records_evidence",
    "tests/test_founder_loop_storage_actions.py::test_action_inbox_local_task_commit_denies_when_safe_disabled",
    "tests/test_founder_loop_storage_actions.py::test_action_inbox_local_task_commit_rejects_unsupported_action_kind",
    "tests/test_founder_loop_storage_actions.py::test_action_inbox_local_task_commit_rejects_expired_backend_approval",
    "tests/test_control_center_api_routes.py::test_control_center_action_local_task_commit_requires_exact_approval_and_receipts",
    "tests/test_control_center_api_routes.py::test_control_center_action_local_task_commit_denies_safe_disabled_lane",
    "tests/test_fcc_v1_003_founder_loop_vertical_slice.py::test_founder_loop_cli_commits_local_task_with_safe_refs",
}
LOCAL_TASK_REPEATABILITY_REQUIRED_FRONTEND_TEST_REFS = {
    "apps/control-center/src/App.test.tsx::commits only the eligible Action Inbox local-task create lane through the typed route",
    "apps/control-center/src/App.test.tsx::keeps local task commit receipt local and explicit when backend read-model refresh fails",
    "apps/control-center/src/App.test.tsx::shows replay posture from the refreshed Action Inbox read model",
    "apps/control-center/src/App.test.tsx::keeps conflicting local task commits out of committed UI state",
}
LOCAL_TASK_REPEATABILITY_REQUIRED_VERIFIER_REFS = {
    "scripts/verify_operational_maturity.py::_append_mock_fallback_fixture_failures",
    "scripts/verify_operational_maturity.py::_append_behavior_probe_failures",
    "scripts/verify_operational_maturity.py::_append_cli_probe_failures",
    "scripts/verify_operational_maturity.py::_append_local_task_repeatability_gate_failures",
}
LOCAL_TASK_AUTHORITY_CAPABILITY_ID = (
    "authority-capability:action-inbox:local-task-create"
)
LOCAL_TASK_AUTHORITY_DOMAIN_REF = "authority-domain-ref:workspace"
LOCAL_TASK_AUTHORITY_CAPABILITY_REF = "authority-capability-ref:write"
LOCAL_TASK_AUTHORITY_MODE_REF = "authority-mode-ref:ask-before-changes"
LOCAL_TASK_AUTHORITY_LEASE_REQUIREMENT_REF = (
    "authority-lease-requirement-ref:local-task-commit:workspace:write"
)
MEMORY_REVIEWED_RECALL_WRITE_LANE_ID = "reviewed_memory_recall_write"
MEMORY_REVIEWED_RECALL_WRITE_ROUTES = {
    "POST /control-center/memory/review/{candidate_ref}/accept",
    "POST /control-center/memory/review/{candidate_ref}/correct",
}
MEMORY_REVIEWED_RECALL_WRITE_POSTURE_REFS = {
    "rollback-ref:memory-review:suppress-reviewed-recall-record",
    "safe-disable-ref:memory-review:accept-correct-reviewed-recall-write",
}
MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_CAPABILITY_ID = (
    "authority-capability:memory:reviewed-recall-write"
)
MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_DOMAIN_REF = "authority-domain-ref:memory"
MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_CAPABILITY_REF = "authority-capability-ref:write"
MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_MODE_REF = (
    "authority-mode-ref:ask-before-changes"
)
MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_LEASE_REQUIREMENT_REF = (
    "authority-lease-requirement-ref:memory-review:memory:write"
)
MEMORY_REVIEWED_RECALL_WRITE_CLI_REF = (
    "scripts/dev/uaa_founder_loop.py record-memory-decision"
)
MEMORY_REVIEWED_RECALL_WRITE_TEST_REFS = {
    "tests/test_fcc_v1_005_memory_review_decisions.py::test_memory_review_decisions_persist_append_first_replay_and_conflict",
    "tests/test_fcc_v1_005_memory_review_decisions.py::test_memory_review_accept_correct_denied_when_write_lane_safe_disabled",
    "tests/test_fcc_v1_005_memory_review_decisions.py::test_memory_review_cli_records_and_inspects_reviewed_recall_write",
}
MEMORY_CONTEXT_PACK_ROUTE = "GET /control-center/memory/context-packs"
MEMORY_CONTEXT_PACK_PREVIEW_ROUTE = (
    "GET /control-center/memory/context-packs/{context_pack_ref}/preview"
)
MEMORY_CONTEXT_MANIFEST_ROUTE = "GET /control-center/memory/context-manifest"
MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_ROUTE = (
    "POST /control-center/memory/context-packs/{context_pack_ref}/action-proposal"
)
MEMORY_CONTEXT_PACK_TEST_REFS = {
    "tests/test_governed_memory_context_pack_proposals.py",
    "tests/test_governed_memory_phase6_execution_hooks.py",
    "tests/test_founder_loop_storage_actions.py::test_memory_context_packs_derive_from_reviewed_l3_refs_only",
}
MEMORY_CONTEXT_PACK_VERIFIER_REFS = {
    "scripts/verify_governed_cognitive_memory_spine_v1.py",
    "scripts/verify_operational_maturity.py",
}
CONTEXT_INJECTION_CANDIDATE_ID = "context_injection"
CONTEXT_INJECTION_CONTRACT_DOC_REF = (
    "docs/context/CONTEXT_INJECTION_PREREQUISITE_CONTRACT.md"
)
CONTEXT_INJECTION_CLI_REF = "scripts/dev/uaa_founder_loop.py memory-context-manifest"
CONTEXT_PACK_PREVIEW_CLI_REF = (
    "scripts/dev/uaa_founder_loop.py memory-context-pack-preview"
)
CONTEXT_INJECTION_REQUIRED_TEST_REFS = {
    "tests/test_fcc_mem_016_020_memory_diagnostics.py::test_founder_loop_cli_memory_context_manifest_omits_raw_paths",
    "tests/test_fcc_mem_016_020_memory_diagnostics.py::test_founder_loop_cli_memory_context_pack_preview_omits_raw_paths",
    "tests/test_governed_memory_context_pack_proposals.py::test_context_pack_api_route_is_backend_backed_and_read_only",
    "tests/test_governed_memory_context_pack_proposals.py::test_context_pack_preview_api_route_is_backend_backed_and_read_only",
}
CONTEXT_INJECTION_REQUIRED_VERIFIER_REFS = {
    "scripts/verify_fcc_mem_016_020_memory_diagnostics.py",
    "scripts/verify_operational_maturity.py",
}
CONTEXT_INJECTION_REQUIRED_BLOCKED_AUTHORITIES = {
    "runtime_prompt_context_injection",
    "live_model_context_injection",
    "automatic_memory_inclusion",
    "provider_model_call",
    "provider_prompt_context_injection",
    "connector_derived_context_injection",
    "browser_web_derived_context_injection",
    "shell_file_derived_context_injection",
    "raw_payload_persistence",
    "broad_autonomy",
    "public_beta_claim",
    "public_distribution_claim",
    "production_readiness_claim",
    "production_authority",
}
CONTEXT_INJECTION_CONTRACT_DOC_SNIPPETS = {
    "planned-only prerequisite contract",
    "runtime injection blocked",
    "exact-scope-ref:context-injection:context-pack-preview-materialization",
    "LocalApprovalAuthority",
    "scripts/dev/uaa_founder_loop.py memory-context-manifest",
    "runtime prompt/context injection",
    "raw payload persistence",
}
PATCH_WORKBENCH_MODULE_ID = "files_patch_workbench"
PATCH_WORKBENCH_APPLY_ROUTE = "POST /files/patch/apply"
PATCH_WORKBENCH_REQUIRED_MISSING_CONTRACTS = {
    "atomic_apply",
    "rollback_receipt",
    "secret_like_diff_blocking",
}
PATCH_WORKBENCH_REQUIRED_BLOCKED_AUTHORITIES = {
    "code_apply_execution",
    "unrestricted_shell",
    "production_authority",
}
PATCH_WORKBENCH_MUTATION_READY_REQUIREMENTS = {
    "exact approval",
    "idempotency",
    "durable receipt",
    "evidence timeline event",
    "rollback or safe-disable",
    "CLI parity",
    "focused tests",
    "verifier refs",
}
LOCAL_MODEL_CLI_REF = "scripts/dev/uaa_local_model.py status"
STALE_UI_STATUS_PHRASES = [
    "routes not implemented",
    "no dedicated manifest",
    "blocked: settings routes not implemented",
    "mock-only",
    "proposal only",
    "proposal-only",
    "ui-only",
    "not wired",
    "placeholder",
]
EXPECTED_AUTHORITY_FOUNDATIONS = {
    "read_only_real_world_web_fetch",
    "read_only_connector_metadata",
    "memory_to_loop_proposal_ux",
    "context_pack_proposal_display",
}
EXPECTED_AUTHORITY_CANDIDATES = {
    "connector_write",
    "memory_write",
    "shell_subprocess_local_maintenance",
    "browser_automation",
    "provider_model_authority",
    "context_injection",
}
EXPECTED_FOLLOW_ON_CANDIDATE_RANKING = (
    "memory_write",
    "context_injection",
    "shell_subprocess_local_maintenance",
    "connector_write",
    "browser_automation",
    "provider_model_authority",
)
AUTHORITY_CANDIDATE_STATUSES = {
    "not_ready",
    "proposal_only_ready",
    "contract_ready",
    "authority_capability_candidate",
    "implemented",
    "blocked_by_policy",
}
AUTHORITY_CAPABILITY_REQUIRED_PREREQUISITE_FIELDS = [
    "backend_core_owner_ref",
    "route_side_effect_ref",
    "exact_scope_ref",
    "approval_plan_ref",
    "idempotency_plan_ref",
    "receipt_evidence_plan_ref",
    "rollback_safe_disable_plan_ref",
    "redaction_plan_ref",
]
AUTHORITY_CAPABILITY_REQUIRED_PREREQUISITE_LIST_FIELDS = [
    "cli_api_core_parity_refs",
    "focused_test_refs",
    "verifier_refs",
]
FIRST_IMPLEMENTATION_LANE_ID = "read_only_real_world_web_fetch"
FIRST_IMPLEMENTATION_PROMPT_REF = (
    "docs/prompts/fcc_authority_ramp/02_read_only_proposal_foundation.prompt.md"
)
FIRST_IMPLEMENTATION_REQUIRED_ALLOWED_SCOPE = {
    "https_get_only",
    "explicit_public_allowlist",
    "bounded_redacted_preview",
    "safe_refs_only",
    "gateway_audit_request_ref_posture",
}
FIRST_IMPLEMENTATION_REQUIRED_BLOCKED_AUTHORITIES = {
    "browser_observe",
    "browser_action_dry_run",
    "browser_automation",
    "provider_sdk_call",
    "connector_read",
    "connector_write",
    "authenticated_session",
    "credential_or_cookie_use",
    "download_upload",
    "non_get_method",
    "memory_write",
    "context_injection",
    "action_execution",
    "generic_browsing",
    "production_authority",
}
FIRST_IMPLEMENTATION_REQUIRED_VERIFICATION_REFS = {
    "scripts/inspect_read_only_web_fetch.py",
    "tests/test_inspect_read_only_web_fetch.py",
    "tests/test_m72_gate_integration.py",
    "tests/test_m72_read_only_http_fetch_tool.py",
    "tests/test_web_access_gateway.py",
    "tests/test_web_access_static_guards.py",
    "scripts/verify_web_runtime_authority.py",
    "scripts/verify_operational_maturity.py",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _compact_text(path: Path) -> str:
    return _compact_string(path.read_text(encoding="utf-8"))


def _compact_string(text: str) -> str:
    return " ".join(text.lower().split())


def verify(
    root: Path = ROOT,
    manifest_override: dict[str, Any] | None = None,
    scorecard_override: dict[str, Any] | None = None,
) -> list[str]:
    failures = verify_contracts(
        root=root,
        manifest_override=manifest_override,
        scorecard_override=scorecard_override,
    )
    _append_public_request_schema_failures(failures)
    _append_mock_fallback_fixture_failures(failures, root)
    _append_behavior_probe_failures(failures, root)
    _append_read_only_status_probe_failures(failures)
    return failures


def verify_contracts(
    root: Path = ROOT,
    manifest_override: dict[str, Any] | None = None,
    scorecard_override: dict[str, Any] | None = None,
) -> list[str]:
    """Validate static operational-maturity contracts without runtime probes."""
    failures: list[str] = []
    manifest = (
        manifest_override
        if manifest_override is not None
        else _load_json(root / MANIFEST_PATH.relative_to(ROOT))
    )
    scorecard = (
        scorecard_override
        if scorecard_override is not None
        else _load_json(root / AUTHORITY_SCORECARD_PATH.relative_to(ROOT))
    )
    schema = _load_json(root / SCHEMA_PATH.relative_to(ROOT))
    scorecard_schema = _load_json(
        root / AUTHORITY_SCORECARD_SCHEMA_PATH.relative_to(ROOT)
    )
    ladder_text = _compact_text(root / LADDER_DOC_PATH.relative_to(ROOT))
    conveyor_text = _compact_text(root / AUTHORITY_CONVEYOR_DOC_PATH.relative_to(ROOT))
    gap_map_text = _compact_text(root / GAP_MAP_PATH.relative_to(ROOT))
    board_text = _compact_text(root / FOUNDER_BOARD_PATH.relative_to(ROOT))
    api_manifest = build_api_manifest(app).model_dump(mode="json")
    routes_by_ref = {
        f"{route['method']} {route['path']}": route for route in api_manifest["routes"]
    }

    _append_schema_shape_failures(failures, schema)
    _append_authority_scorecard_schema_failures(failures, scorecard_schema)
    _append_manifest_shape_failures(failures, manifest)
    _append_authority_tier_model_failures(failures, manifest, root)
    _append_authority_scorecard_failures(
        failures,
        scorecard,
        routes_by_ref,
        root,
        conveyor_text,
    )
    _append_ladder_doc_failures(failures, ladder_text)
    _append_module_failures(failures, manifest, routes_by_ref, root)
    _append_first_lane_failures(failures, manifest, routes_by_ref, root)
    _append_ref_resolution_failures(failures, manifest, root)
    _append_status_doc_failures(failures, gap_map_text, board_text)
    return failures


def _append_schema_shape_failures(
    failures: list[str],
    schema: dict[str, Any],
) -> None:
    if schema.get("title") != "Control Center Operational Maturity Manifest":
        failures.append("operational maturity schema title drifted")
    top_level_required = set(schema.get("required", []))
    for field in [
        "authority_tier_doc_ref",
        "authority_tier_model",
        "authority_capability_contract",
    ]:
        if field not in top_level_required:
            failures.append(f"operational maturity schema missing field {field}")
    defs = schema.get("$defs", {})
    for def_name in [
        "usable_authority_tier",
        "authority_tier_guardrails",
        "authority_tier_model",
        "authority_capability_contract",
    ]:
        if def_name not in defs:
            failures.append(f"operational maturity schema missing def {def_name}")
    module_required = set(schema.get("$defs", {}).get("module", {}).get("required", []))
    for field in [
        "module_id",
        "role",
        "primary_surface",
        "current_rank",
        "honest_status",
        "next_target_rank",
        "backend_routes",
        "cli_or_script_refs",
        "evidence_refs",
        "test_refs",
        "blocked_authorities",
        "missing_contracts",
        "smallest_next_operational_action",
        "authority_capabilities",
    ]:
        if field not in module_required:
            failures.append(f"operational maturity schema missing module field {field}")
    if "lane" in schema.get("$defs", {}):
        failures.append("operational maturity schema must not define legacy lane")
    module_properties = set(
        schema.get("$defs", {}).get("module", {}).get("properties", {})
    )
    if "graduated_lanes" in module_properties:
        failures.append("operational maturity schema must reject graduated_lanes")
    capability_required = set(
        schema.get("$defs", {}).get("authority_capability", {}).get("required", [])
    )
    if "policy_decisions" not in capability_required:
        failures.append(
            "operational maturity schema missing authority capability field policy_decisions"
        )
    if "blocked_authorities" not in capability_required:
        failures.append(
            "operational maturity schema missing authority capability field blocked_authorities"
        )
    binding_required = set(
        schema.get("$defs", {}).get("ui_status_binding", {}).get("required", [])
    )
    for field in [
        "surface",
        "status_route_ref",
        "frontend_endpoint_ref",
        "frontend_client_ref",
        "frontend_type_ref",
        "frontend_component_refs",
        "frontend_test_refs",
        "backend_only_status",
        "backend_only_reason",
        "backend_only_doc_ref",
        "backend_only_blocker_ref",
        "stale_language_scan_refs",
    ]:
        if field not in binding_required:
            failures.append(
                f"operational maturity schema missing ui_status_binding field {field}"
            )


def _append_authority_scorecard_schema_failures(
    failures: list[str],
    schema: dict[str, Any],
) -> None:
    if schema.get("title") != "Founder Command Center Authority Candidate Scorecard":
        failures.append("authority scorecard schema title drifted")
    required = set(schema.get("required", []))
    for field in [
        "schema_version",
        "status",
        "baseline",
        "authority_model",
        "conveyor_doc_ref",
        "verifier_ref",
        "operational_maturity_manifest_ref",
        "first_implementation_lane",
        "proposal_foundation",
        "authority_candidates",
        "follow_on_candidate_ranking",
        "first_authority_capability_decision",
    ]:
        if field not in required:
            failures.append(f"authority scorecard schema missing field {field}")
    candidate_statuses = set(
        schema.get("$defs", {})
        .get("authority_candidate", {})
        .get("properties", {})
        .get("status", {})
        .get("enum", [])
    )
    if candidate_statuses != AUTHORITY_CANDIDATE_STATUSES:
        failures.append("authority scorecard schema candidate statuses drifted")
    first_lane_required = set(
        schema.get("$defs", {}).get("first_implementation_lane", {}).get("required", [])
    )
    for field in [
        "lane_id",
        "prompt_ref",
        "foundation_ref",
        "status",
        "safe_summary",
        "allowed_scope",
        "blocked_authorities",
        "verification_refs",
        "next_safe_action",
    ]:
        if field not in first_lane_required:
            failures.append(
                f"authority scorecard schema missing first implementation lane field {field}"
            )
    prerequisite_required = set(
        schema.get("$defs", {})
        .get("authority_candidate", {})
        .get("properties", {})
        .get("prerequisite_refs", {})
        .get("required", [])
    )
    for field in (
        AUTHORITY_CAPABILITY_REQUIRED_PREREQUISITE_FIELDS
        + AUTHORITY_CAPABILITY_REQUIRED_PREREQUISITE_LIST_FIELDS
    ):
        if field not in prerequisite_required:
            failures.append(
                f"authority scorecard schema missing prerequisite field {field}"
            )


def _append_manifest_shape_failures(
    failures: list[str],
    manifest: dict[str, Any],
) -> None:
    if manifest.get("schema_version") != "uaa-control-center-operational-maturity.v1":
        failures.append("operational maturity manifest schema_version drifted")
    if manifest.get("status") != "active operational maturity manifest":
        failures.append("operational maturity manifest status drifted")
    if (
        manifest.get("ladder_doc_ref")
        != "docs/control_center/OPERATIONALIZATION_LADDER.md"
    ):
        failures.append("operational maturity manifest ladder_doc_ref drifted")
    if manifest.get("verifier_ref") != "scripts/verify_operational_maturity.py":
        failures.append("operational maturity manifest verifier_ref drifted")
    if manifest.get("authority_tier_doc_ref") != AUTHORITY_TIER_DOC_REF:
        failures.append("operational maturity manifest authority_tier_doc_ref drifted")
    _append_authority_capability_contract_failures(failures, manifest)
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        failures.append("operational maturity manifest modules must be a list")
        return
    module_ids = [str(module.get("module_id")) for module in modules]
    if set(module_ids) != EXPECTED_MODULES:
        failures.append(
            f"operational maturity manifest module set drifted: {sorted(module_ids)}"
        )
    if len(module_ids) != len(set(module_ids)):
        failures.append("operational maturity manifest contains duplicate modules")


def _append_authority_capability_contract_failures(
    failures: list[str],
    manifest: dict[str, Any],
) -> None:
    contract = manifest.get("authority_capability_contract")
    if not isinstance(contract, dict):
        failures.append(
            "operational maturity manifest requires authority_capability_contract"
        )
        return
    if contract.get("canonical_authority_source") != CANONICAL_AUTHORITY_SOURCE:
        failures.append(
            "authority capability contract canonical_authority_source drifted"
        )
    if contract.get("legacy_lane_posture") != LEGACY_LANE_STATUS:
        failures.append("authority capability contract legacy_lane_posture drifted")
    if contract.get("default_unknown_authority_decision") != "deny":
        failures.append(
            "authority capability contract must deny unknown authority by default"
        )
    if set(contract.get("policy_decisions", [])) != EXPECTED_POLICY_DECISIONS:
        failures.append("authority capability contract policy decisions drifted")
    if contract.get("lease_evaluation_required") is not True:
        failures.append("authority capability contract must require lease evaluation")
    operator_copy_rule = str(contract.get("operator_copy_rule", ""))
    for fragment in ["trust mode", "domain", "capability", "AuthorityLease", "receipt"]:
        if fragment not in operator_copy_rule:
            failures.append(
                "authority capability contract operator_copy_rule missing "
                f"{fragment}"
            )


def _append_authority_tier_model_failures(
    failures: list[str],
    manifest: dict[str, Any],
    root: Path,
) -> None:
    model = manifest.get("authority_tier_model")
    if not isinstance(model, dict):
        failures.append("operational maturity manifest requires authority_tier_model")
        return
    if model.get("doctrine") != AUTHORITY_TIER_DOCTRINE:
        failures.append("authority tier model doctrine drifted")

    tiers = model.get("tiers")
    if not isinstance(tiers, list):
        failures.append("authority tier model tiers must be a list")
        tiers = []
    tiers_by_number: dict[int, dict[str, Any]] = {}
    for tier in tiers:
        if not isinstance(tier, dict):
            failures.append("authority tier model contains non-object tier")
            continue
        tier_number = tier.get("tier")
        if not isinstance(tier_number, int):
            failures.append("authority tier model tier number must be int")
            continue
        if tier_number in tiers_by_number:
            failures.append(f"authority tier model duplicate tier {tier_number}")
        tiers_by_number[tier_number] = tier

    if set(tiers_by_number) != set(EXPECTED_USABLE_AUTHORITY_TIERS):
        failures.append(
            f"authority tier model tier set drifted: {sorted(tiers_by_number)}"
        )
    for tier_number, expected_tier_id in EXPECTED_USABLE_AUTHORITY_TIERS.items():
        tier = tiers_by_number.get(tier_number)
        if not tier:
            failures.append(f"authority tier model missing tier {tier_number}")
            continue
        if tier.get("tier_id") != expected_tier_id:
            failures.append(f"authority tier {tier_number} expected {expected_tier_id}")
        for field in [
            "label",
            "durable_truth_owner",
            "approval_posture",
            "examples",
            "blocked_claims",
        ]:
            if field not in tier:
                failures.append(
                    f"authority tier {expected_tier_id} missing field {field}"
                )
        if tier.get("tier_id") in LOW_FRICTION_TIER_IDS:
            if "no approval" not in _compact_string(
                str(tier.get("approval_posture", ""))
            ):
                failures.append(
                    f"authority tier {expected_tier_id} must stay low-friction/no-approval for initiation"
                )
            blocked_claims = set(tier.get("blocked_claims", []))
            missing = TIER_LOW_FRICTION_FORBIDDEN_CLAIMS - blocked_claims
            for claim in sorted(missing):
                failures.append(f"authority tier {expected_tier_id} must block {claim}")

    guardrails = model.get("guardrails")
    if not isinstance(guardrails, dict):
        failures.append("authority tier model guardrails must be an object")
        guardrails = {}
    for guardrail in sorted(TIER_MODEL_REQUIRED_GUARDRAILS):
        if guardrails.get(guardrail) is not True:
            failures.append(f"authority tier model guardrail missing {guardrail}")

    plan_path = root / AUTHORITY_TIER_DOC_REF
    if not plan_path.exists():
        failures.append(f"authority tier plan missing {AUTHORITY_TIER_DOC_REF}")
    else:
        plan_text = _compact_text(plan_path)
        for snippet in sorted(AUTHORITY_MODE_CANON_SNIPPETS):
            if snippet not in plan_text:
                failures.append(f"authority mode canon missing '{snippet}'")

    product_language_text = _compact_text(
        root / PRODUCT_LANGUAGE_RULES_PATH.relative_to(ROOT)
    )
    for snippet in sorted(PRODUCT_LANGUAGE_TIER_SNIPPETS):
        if snippet not in product_language_text:
            failures.append(f"product language missing authority tier rule '{snippet}'")


def _append_authority_scorecard_failures(
    failures: list[str],
    scorecard: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
    root: Path,
    conveyor_text: str,
) -> None:
    if (
        scorecard.get("schema_version")
        != "uaa-control-center-authority-candidate-scorecard.v2"
    ):
        failures.append("authority scorecard schema_version drifted")
    if scorecard.get("status") != "active authority candidate scorecard":
        failures.append("authority scorecard status drifted")
    if (
        scorecard.get("conveyor_doc_ref")
        != "docs/control_center/AUTHORITY_RAMP_CONVEYOR.md"
    ):
        failures.append("authority scorecard conveyor_doc_ref drifted")
    if scorecard.get("verifier_ref") != "scripts/verify_operational_maturity.py":
        failures.append("authority scorecard verifier_ref drifted")
    if (
        scorecard.get("operational_maturity_manifest_ref")
        != "docs/control_center/operational_maturity_manifest.json"
    ):
        failures.append("authority scorecard manifest ref drifted")

    for snippet in [
        "does not grant authority by itself",
        "authority capability conveyor",
        "fixed first implementation capability",
        "read_only_real_world_web_fetch through webaccessgateway",
        "not a follow-on authority candidate",
        "at most one candidate may be selected",
        "first follow-on authority capability is selected",
        "reviewed_memory_recall_write",
        "local_task_create",
    ]:
        if snippet not in conveyor_text:
            failures.append(f"authority capability conveyor doc missing '{snippet}'")

    _append_first_implementation_lane_failures(
        failures,
        scorecard.get("first_implementation_lane"),
        root,
    )

    foundations = scorecard.get("proposal_foundation")
    if not isinstance(foundations, list):
        failures.append("authority scorecard proposal_foundation must be a list")
        foundations = []
    foundation_ids = [str(item.get("foundation_id")) for item in foundations]
    if set(foundation_ids) != EXPECTED_AUTHORITY_FOUNDATIONS:
        failures.append(
            f"authority scorecard foundation set drifted: {sorted(foundation_ids)}"
        )
    if len(foundation_ids) != len(set(foundation_ids)):
        failures.append("authority scorecard contains duplicate foundation lanes")
    for foundation in foundations:
        _append_authority_foundation_failures(
            failures,
            foundation,
            routes_by_ref,
            root,
        )

    candidates = scorecard.get("authority_candidates")
    if not isinstance(candidates, list):
        failures.append("authority scorecard authority_candidates must be a list")
        candidates = []
    candidate_ids = [str(item.get("candidate_id")) for item in candidates]
    if set(candidate_ids) != EXPECTED_AUTHORITY_CANDIDATES:
        failures.append(
            f"authority scorecard candidate set drifted: {sorted(candidate_ids)}"
        )
    if len(candidate_ids) != len(set(candidate_ids)):
        failures.append("authority scorecard contains duplicate authority candidates")
    if FIRST_IMPLEMENTATION_LANE_ID in set(candidate_ids):
        failures.append(
            "fixed first implementation lane must not be a follow-on authority candidate"
        )
    selected = [
        candidate
        for candidate in candidates
        if candidate.get("selected_for_authority_capability") is True
    ]
    if len(selected) > 1:
        failures.append(
            "authority scorecard must select at most one authority capability candidate"
        )
    for candidate in candidates:
        _append_authority_candidate_failures(
            failures,
            candidate,
            routes_by_ref,
            root,
        )
        if str(candidate.get("candidate_id")) == CONTEXT_INJECTION_CANDIDATE_ID:
            _append_context_injection_contract_ready_failures(
                failures,
                candidate,
                routes_by_ref,
                root,
            )
    _append_follow_on_candidate_ranking_failures(
        failures,
        scorecard.get("follow_on_candidate_ranking"),
        candidates,
    )
    _append_first_authority_capability_decision_failures(
        failures,
        scorecard.get("first_authority_capability_decision"),
        selected,
        scorecard.get("follow_on_candidate_ranking"),
    )


def _append_first_implementation_lane_failures(
    failures: list[str],
    lane: Any,
    root: Path,
) -> None:
    if not isinstance(lane, dict):
        failures.append("authority scorecard requires first_implementation_lane")
        return
    if lane.get("lane_id") != FIRST_IMPLEMENTATION_LANE_ID:
        failures.append(
            "first implementation lane id must be read_only_real_world_web_fetch"
        )
    if lane.get("prompt_ref") != FIRST_IMPLEMENTATION_PROMPT_REF:
        failures.append(
            f"first implementation lane prompt_ref must be {FIRST_IMPLEMENTATION_PROMPT_REF}"
        )
    if lane.get("foundation_ref") != FIRST_IMPLEMENTATION_LANE_ID:
        failures.append(
            "first implementation lane foundation_ref must match read_only_real_world_web_fetch"
        )
    if lane.get("status") not in {"partial", "blocked", "implemented"}:
        failures.append("first implementation lane status is invalid")
    if not lane.get("safe_summary"):
        failures.append("first implementation lane requires safe_summary")
    if not lane.get("next_safe_action"):
        failures.append("first implementation lane requires next_safe_action")
    status = lane.get("status")
    next_safe_action = str(lane.get("next_safe_action", ""))
    if status != "implemented" and "Prompt 02" not in next_safe_action:
        failures.append(
            "first implementation lane next_safe_action must point to Prompt 02"
        )
    if status == "implemented" and "follow-on" not in next_safe_action:
        failures.append(
            "implemented first lane next_safe_action must point follow-on authority to the scorecard"
        )
    allowed_scope = set(lane.get("allowed_scope", []))
    for scope in sorted(FIRST_IMPLEMENTATION_REQUIRED_ALLOWED_SCOPE):
        if scope not in allowed_scope:
            failures.append(f"first implementation lane missing allowed scope {scope}")
    blocked_authorities = set(lane.get("blocked_authorities", []))
    for authority in sorted(FIRST_IMPLEMENTATION_REQUIRED_BLOCKED_AUTHORITIES):
        if authority not in blocked_authorities:
            failures.append(f"first implementation lane must block {authority}")
    verification_refs = set(lane.get("verification_refs", []))
    for ref in sorted(FIRST_IMPLEMENTATION_REQUIRED_VERIFICATION_REFS):
        if ref not in verification_refs:
            failures.append(f"first implementation lane missing verification ref {ref}")
    _append_source_ref_failure(
        failures,
        root,
        FIRST_IMPLEMENTATION_PROMPT_REF,
        "first_implementation_lane.prompt_ref",
    )
    for ref in verification_refs:
        _append_authority_ref_failure(
            failures,
            root,
            {},
            str(ref),
            "first_implementation_lane.verification_refs",
        )


def _append_authority_foundation_failures(
    failures: list[str],
    foundation: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
    root: Path,
) -> None:
    foundation_id = str(foundation.get("foundation_id"))
    if foundation.get("status") not in {
        "partial",
        "proposal_only_ready",
        "implemented",
    }:
        failures.append(f"{foundation_id} has invalid foundation status")
    for field in [
        "safe_summary",
        "surface_refs",
        "test_refs",
        "blocked_authorities",
        "next_safe_action",
    ]:
        if not foundation.get(field):
            failures.append(f"{foundation_id} authority foundation requires {field}")
    if foundation_id != FIRST_IMPLEMENTATION_LANE_ID and not foundation.get(
        "route_refs"
    ):
        failures.append(f"{foundation_id} authority foundation requires route_refs")
    if foundation.get("status") == "partial" and not foundation.get(
        "missing_contracts"
    ):
        failures.append(
            f"{foundation_id} partial authority foundation requires missing_contracts"
        )
    for route_ref in foundation.get("route_refs", []):
        if route_ref not in routes_by_ref:
            failures.append(f"{foundation_id} references missing route {route_ref}")
    for ref in foundation.get("surface_refs", []):
        _append_source_ref_failure(
            failures,
            root,
            str(ref),
            f"{foundation_id}.surface_refs",
        )
    for ref in foundation.get("test_refs", []):
        _append_authority_ref_failure(
            failures,
            root,
            routes_by_ref,
            str(ref),
            f"{foundation_id}.test_refs",
        )


def _append_authority_candidate_failures(
    failures: list[str],
    candidate: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
    root: Path,
) -> None:
    candidate_id = str(candidate.get("candidate_id"))
    status = candidate.get("status")
    if status not in AUTHORITY_CANDIDATE_STATUSES:
        failures.append(
            f"{candidate_id} has invalid authority candidate status {status}"
        )
    if candidate.get("selected_for_authority_capability") is True and status not in {
        "authority_capability_candidate",
        "implemented",
    }:
        failures.append(
            f"{candidate_id} selected authority capability must be authority_capability_candidate or implemented"
        )
    if not candidate.get("safe_summary"):
        failures.append(f"{candidate_id} authority candidate requires safe_summary")
    if not candidate.get("smallest_next_safe_action"):
        failures.append(
            f"{candidate_id} authority candidate requires smallest_next_safe_action"
        )
    score = candidate.get("score")
    if not isinstance(score, dict):
        failures.append(f"{candidate_id} authority candidate requires score")
    else:
        for field, value in score.items():
            if not isinstance(value, int) or value < 0 or value > 5:
                failures.append(f"{candidate_id} score {field} must be 0-5")
    prerequisite_refs = candidate.get("prerequisite_refs")
    if not isinstance(prerequisite_refs, dict):
        failures.append(
            f"{candidate_id} authority candidate requires prerequisite_refs"
        )
        return
    for field in [
        "backend_core_owner_ref",
        "route_side_effect_ref",
        "redaction_plan_ref",
    ]:
        ref = prerequisite_refs.get(field)
        if ref:
            _append_authority_ref_failure(
                failures,
                root,
                routes_by_ref,
                str(ref),
                f"{candidate_id}.prerequisite_refs.{field}",
            )
    for ref in prerequisite_refs.get("focused_test_refs", []):
        _append_authority_ref_failure(
            failures,
            root,
            routes_by_ref,
            str(ref),
            f"{candidate_id}.focused_test_refs",
        )
    for ref in prerequisite_refs.get("verifier_refs", []):
        _append_authority_ref_failure(
            failures,
            root,
            routes_by_ref,
            str(ref),
            f"{candidate_id}.verifier_refs",
        )
    if status == "blocked_by_policy":
        if not candidate.get("blocked_authorities"):
            failures.append(
                f"{candidate_id} blocked_by_policy requires blocked_authorities"
            )
        if not candidate.get("missing_prerequisites"):
            failures.append(
                f"{candidate_id} blocked_by_policy requires missing_prerequisites"
            )
    if status not in {"authority_capability_candidate", "implemented"}:
        return
    for field in AUTHORITY_CAPABILITY_REQUIRED_PREREQUISITE_FIELDS:
        ref = prerequisite_refs.get(field)
        if not ref:
            failures.append(
                f"{candidate_id} authority capability candidate requires {field}"
            )
            continue
        _append_authority_ref_failure(
            failures,
            root,
            routes_by_ref,
            str(ref),
            f"{candidate_id}.prerequisite_refs.{field}",
        )
    for field in AUTHORITY_CAPABILITY_REQUIRED_PREREQUISITE_LIST_FIELDS:
        refs = prerequisite_refs.get(field)
        if not refs:
            failures.append(
                f"{candidate_id} authority capability candidate requires {field}"
            )
            continue
        for ref in refs:
            _append_authority_ref_failure(
                failures,
                root,
                routes_by_ref,
                str(ref),
                f"{candidate_id}.prerequisite_refs.{field}",
            )


def _append_context_injection_contract_ready_failures(
    failures: list[str],
    candidate: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
    root: Path,
) -> None:
    if candidate.get("status") != "contract_ready":
        failures.append("context_injection must stay contract_ready")
    if candidate.get("selected_for_authority_capability") is not False:
        failures.append("context_injection must remain unselected")
    prerequisite_refs = candidate.get("prerequisite_refs")
    if not isinstance(prerequisite_refs, dict):
        failures.append("context_injection requires prerequisite refs")
        return
    if prerequisite_refs.get("route_side_effect_ref") != MEMORY_CONTEXT_MANIFEST_ROUTE:
        failures.append(
            "context_injection route_side_effect_ref must be memory context-manifest"
        )
    route = routes_by_ref.get(MEMORY_CONTEXT_MANIFEST_ROUTE)
    if route is None:
        failures.append("context_injection references missing context-manifest route")
    else:
        if route.get("method") != "GET":
            failures.append("context_injection prerequisite route must stay GET")
        if route.get("side_effect_class") not in {
            "validation_only",
            "local_dev_workspace_only",
        }:
            failures.append(
                "context_injection prerequisite route must stay read-only local posture"
            )
        if route.get("idempotency_required") is not False:
            failures.append(
                "context_injection prerequisite route must not require idempotency"
            )
    for route_ref in routes_by_ref:
        lowered = route_ref.lower()
        if "context-injection" in lowered or "context_injection" in lowered:
            failures.append(
                f"context_injection runtime route must not exist: {route_ref}"
            )
    for field in AUTHORITY_CAPABILITY_REQUIRED_PREREQUISITE_FIELDS:
        ref = prerequisite_refs.get(field)
        if not ref:
            failures.append(f"context_injection contract_ready requires {field}")
            continue
        _append_authority_ref_failure(
            failures,
            root,
            routes_by_ref,
            str(ref),
            f"context_injection.prerequisite_refs.{field}",
        )
    cli_refs = set(prerequisite_refs.get("cli_api_core_parity_refs") or [])
    if CONTEXT_INJECTION_CLI_REF not in cli_refs:
        failures.append("context_injection missing memory-context-manifest CLI ref")
    for ref in cli_refs:
        _append_cli_or_script_ref_failure(
            failures,
            root,
            str(ref),
            "context_injection.prerequisite_refs.cli_api_core_parity_refs",
        )
    test_refs = set(prerequisite_refs.get("focused_test_refs") or [])
    for ref in CONTEXT_INJECTION_REQUIRED_TEST_REFS:
        if ref not in test_refs:
            failures.append(f"context_injection missing focused test {ref}")
    verifier_refs = set(prerequisite_refs.get("verifier_refs") or [])
    for ref in CONTEXT_INJECTION_REQUIRED_VERIFIER_REFS:
        if ref not in verifier_refs:
            failures.append(f"context_injection missing verifier {ref}")
    blocked_authorities = set(candidate.get("blocked_authorities") or [])
    for blocked in CONTEXT_INJECTION_REQUIRED_BLOCKED_AUTHORITIES:
        if blocked not in blocked_authorities:
            failures.append(f"context_injection must block {blocked}")
    doc_path = root / CONTEXT_INJECTION_CONTRACT_DOC_REF
    if not doc_path.exists():
        failures.append("context_injection prerequisite contract doc missing")
        return
    doc_text = _compact_string(doc_path.read_text(encoding="utf-8"))
    for snippet in CONTEXT_INJECTION_CONTRACT_DOC_SNIPPETS:
        if _compact_string(snippet) not in doc_text:
            failures.append(
                f"context_injection prerequisite contract doc missing '{snippet}'"
            )


def _append_follow_on_candidate_ranking_failures(
    failures: list[str],
    ranking: Any,
    candidates: list[dict[str, Any]],
) -> None:
    if not isinstance(ranking, dict):
        failures.append("authority scorecard requires follow_on_candidate_ranking")
        return
    if ranking.get("status") not in {
        "ranked_no_authority_granted",
        "ranked_with_selected_authority_capability",
    }:
        failures.append(
            "follow-on candidate ranking must be ranked_no_authority_granted or ranked_with_selected_authority_capability"
        )
    if ranking.get("fixed_first_lane_ref") != FIRST_IMPLEMENTATION_LANE_ID:
        failures.append("follow-on ranking must reference the fixed first lane")
    ranked_ids = tuple(
        str(candidate_id) for candidate_id in ranking.get("ranked_candidate_ids", [])
    )
    if ranked_ids != EXPECTED_FOLLOW_ON_CANDIDATE_RANKING:
        failures.append(
            f"follow-on candidate ranking order drifted: {list(ranked_ids)}"
        )
    if FIRST_IMPLEMENTATION_LANE_ID in ranked_ids:
        failures.append("follow-on ranking must not include the fixed first lane")
    if len(ranked_ids) != len(set(ranked_ids)):
        failures.append("follow-on ranking contains duplicate candidates")
    implemented_selected = any(
        candidate.get("selected_for_authority_capability") is True
        and candidate.get("status") == "implemented"
        for candidate in candidates
    )
    if implemented_selected:
        if ranking.get("no_authority_granted") is not False:
            failures.append(
                "follow-on ranking with implemented selected authority capability must set no_authority_granted false"
            )
    elif ranking.get("no_authority_granted") is not True:
        failures.append("follow-on ranking must not grant authority")
    if ranking.get("safest_candidate_id") != EXPECTED_FOLLOW_ON_CANDIDATE_RANKING[0]:
        failures.append("follow-on ranking safest candidate must match rank 1")

    candidate_by_id = {
        str(candidate.get("candidate_id")): candidate for candidate in candidates
    }
    safest_candidate = candidate_by_id.get(str(ranking.get("safest_candidate_id")))
    if safest_candidate is None:
        failures.append("follow-on ranking safest candidate is not in candidates")
    elif ranking.get("safest_candidate_status") != safest_candidate.get("status"):
        failures.append("follow-on ranking safest candidate status drifted")
    for field in [
        "ranking_method",
        "safe_summary",
        "selection_blocked_reason",
        "next_safe_action",
    ]:
        if not ranking.get(field):
            failures.append(f"follow-on ranking requires {field}")


def _append_first_authority_capability_decision_failures(
    failures: list[str],
    decision: Any,
    selected: list[dict[str, Any]],
    ranking: Any,
) -> None:
    if not isinstance(decision, dict):
        failures.append(
            "authority scorecard requires first_authority_capability_decision"
        )
        return
    if not selected:
        if decision.get("status") != "no_go":
            failures.append(
                "authority scorecard with no selected candidate requires no_go decision"
            )
        if decision.get("selected_candidate_id") is not None:
            failures.append(
                "no_go authority decision must not name selected_candidate_id"
            )
        if not decision.get("no_go_reason"):
            failures.append("no_go authority decision requires no_go_reason")
        if not decision.get("smallest_next_safe_action"):
            failures.append(
                "no_go authority decision requires smallest_next_safe_action"
            )
        if isinstance(ranking, dict):
            safest_candidate_id = str(ranking.get("safest_candidate_id", ""))
            safest_candidate_status = str(ranking.get("safest_candidate_status", ""))
            no_go_reason = str(decision.get("no_go_reason", ""))
            next_safe_action = str(decision.get("smallest_next_safe_action", ""))
            if safest_candidate_id and safest_candidate_id not in no_go_reason:
                failures.append(
                    "no_go authority decision must explain the top-ranked candidate blocker"
                )
            if safest_candidate_status and safest_candidate_status not in no_go_reason:
                failures.append(
                    "no_go authority decision must include the top-ranked candidate status"
                )
            for fragment in [
                "exact scope",
                "LocalApprovalAuthority",
                "rollback/safe-disable",
                "CLI parity",
                "tests",
            ]:
                if fragment not in f"{no_go_reason} {next_safe_action}":
                    failures.append(
                        f"no_go authority decision missing blocker fragment {fragment}"
                    )
        return
    selected_id = str(selected[0].get("candidate_id"))
    if decision.get("status") != "selected":
        failures.append("selected authority candidate requires selected decision")
    if decision.get("selected_candidate_id") != selected_id:
        failures.append("selected authority decision must match selected candidate")
    if not decision.get("decision_ref"):
        failures.append("selected authority decision requires decision_ref")


def _append_ladder_doc_failures(failures: list[str], ladder_text: str) -> None:
    for rank, label in LADDER_LABELS.items():
        if f"| {rank} | `{label}` |" not in ladder_text:
            failures.append(f"ladder doc missing rank {rank} {label}")
    for snippet in [
        "rank 3 or higher requires backend-owned receipt state",
        "rank 4 or higher requires exact scope",
        "rank 5 or higher requires a real allowlisted local state change",
        "authoritylease capability conveyor",
        "docs/strategy/uaa_authority_modes_and_mission_leases.md",
        "unknown authority remains denied",
        "first implemented authority capability",
        "authority-capability:action-inbox:local-task-create",
        "active workspace/write lease",
        "post /control-center/actions/{action_id}/local-task/commit",
        "local_task_create",
    ]:
        if snippet not in ladder_text:
            failures.append(f"ladder doc missing '{snippet}'")


def _append_module_failures(
    failures: list[str],
    manifest: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
    root: Path,
) -> None:
    for module in manifest.get("modules", []):
        module_id = str(module.get("module_id"))
        rank = module.get("current_rank")
        label = module.get("current_rank_label")
        role = str(module.get("role"))
        if rank not in LADDER_LABELS:
            failures.append(f"{module_id} has invalid current_rank {rank}")
            continue
        if label != LADDER_LABELS[rank]:
            failures.append(
                f"{module_id} current_rank_label does not match rank {rank}"
            )
        if int(module.get("next_target_rank", -1)) < int(rank):
            failures.append(f"{module_id} next_target_rank is behind current_rank")
        if not module.get("honest_status"):
            failures.append(f"{module_id} missing honest_status")
        if not module.get("smallest_next_operational_action"):
            failures.append(f"{module_id} missing smallest_next_operational_action")
        for route_ref in module.get("backend_routes", []):
            if route_ref not in routes_by_ref:
                failures.append(
                    f"{module_id} references missing backend route {route_ref}"
                )
        _append_ui_status_binding_failures(
            failures,
            module,
            routes_by_ref,
            root,
        )
        if rank >= 3:
            if module.get("backend_owned_receipts") is not True:
                failures.append(f"{module_id} rank 3+ requires backend_owned_receipts")
            if not module.get("receipt_refs"):
                failures.append(f"{module_id} rank 3+ requires receipt_refs")
        if rank >= 4:
            for field in [
                "exact_scope_required",
                "idempotency_required",
                "rollback_or_safe_disable_required",
            ]:
                if module.get(field) is not True:
                    failures.append(f"{module_id} rank 4+ requires {field}")
            if not module.get("route_metadata_refs"):
                failures.append(f"{module_id} rank 4+ requires route_metadata_refs")
        if rank >= 5:
            if module.get("durable_receipt") is not True:
                failures.append(f"{module_id} rank 5+ requires durable_receipt")
            if module.get("evidence_timeline_event") is not True:
                failures.append(f"{module_id} rank 5+ requires evidence_timeline_event")
            if not module.get("test_refs"):
                failures.append(f"{module_id} rank 5+ requires test_refs")
            if role != "support":
                if module.get("real_local_mutation") is not True:
                    failures.append(f"{module_id} rank 5+ requires real_local_mutation")
                if not module.get("cli_or_script_refs"):
                    failures.append(f"{module_id} rank 5+ requires cli_or_script_refs")
        _append_authority_capability_failures(
            failures,
            module_id,
            module,
            routes_by_ref,
        )
        if module_id == "memory":
            _append_memory_context_pack_manifest_failures(failures, module)
        if module_id == PATCH_WORKBENCH_MODULE_ID:
            _append_patch_workbench_manifest_failures(failures, module)
        if module_id == "local_models":
            _append_local_model_manifest_failures(failures, module)


def _append_memory_context_pack_manifest_failures(
    failures: list[str],
    module: dict[str, Any],
) -> None:
    route_refs = set(module.get("backend_routes", []))
    test_refs = set(module.get("test_refs", []))
    verifier_refs = set(module.get("verifier_refs", []))
    for route_ref in [
        MEMORY_CONTEXT_PACK_ROUTE,
        MEMORY_CONTEXT_PACK_PREVIEW_ROUTE,
        MEMORY_CONTEXT_MANIFEST_ROUTE,
        MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_ROUTE,
    ]:
        if route_ref not in route_refs:
            failures.append(f"memory context-pack readiness missing route {route_ref}")
    for test_ref in MEMORY_CONTEXT_PACK_TEST_REFS:
        if test_ref not in test_refs:
            failures.append(f"memory context-pack readiness missing test {test_ref}")
    for verifier_ref in MEMORY_CONTEXT_PACK_VERIFIER_REFS:
        if verifier_ref not in verifier_refs:
            failures.append(
                f"memory context-pack readiness missing verifier {verifier_ref}"
            )
    if MEMORY_REVIEWED_RECALL_WRITE_CLI_REF not in set(
        module.get("cli_or_script_refs", [])
    ):
        failures.append(
            "memory reviewed recall-write authority capability missing CLI parity ref"
        )
    if CONTEXT_INJECTION_CLI_REF not in set(module.get("cli_or_script_refs", [])):
        failures.append("memory context-injection contract missing CLI parity ref")
    if CONTEXT_PACK_PREVIEW_CLI_REF not in set(module.get("cli_or_script_refs", [])):
        failures.append("memory context-pack preview missing CLI parity ref")
    blocked_authorities = set(module.get("blocked_authorities", []))
    for blocked in CONTEXT_INJECTION_REQUIRED_BLOCKED_AUTHORITIES:
        if blocked not in blocked_authorities:
            failures.append(f"memory context-injection contract must block {blocked}")
    capabilities_by_id = {
        str(capability.get("capability_id")): capability
        for capability in module.get("authority_capabilities", [])
    }
    capabilities_by_legacy_lane = {
        str(capability.get("legacy_lane_id")): capability
        for capability in module.get("authority_capabilities", [])
        if capability.get("legacy_lane_id")
    }
    for capability in module.get("authority_capabilities", []):
        legacy_lane_id = str(capability.get("legacy_lane_id", ""))
        if legacy_lane_id in {
            "context_injection",
            "context_pack_preview_materialization",
        }:
            failures.append(
                "memory must not mark context_injection as implemented authority capability"
            )
            break
    capability = capabilities_by_id.get(
        MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_CAPABILITY_ID
    ) or capabilities_by_legacy_lane.get(MEMORY_REVIEWED_RECALL_WRITE_LANE_ID)
    if capability is None:
        failures.append("memory reviewed recall-write authority capability missing")
        return
    expected_capability_fields = {
        "capability_id": MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_CAPABILITY_ID,
        "authority_domain_ref": MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_DOMAIN_REF,
        "authority_capability_ref": MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_CAPABILITY_REF,
        "required_mode_ref": MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_MODE_REF,
        "authority_lease_requirement_ref": (
            MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_LEASE_REQUIREMENT_REF
        ),
        "lease_scope": "session",
    }
    for field, expected in expected_capability_fields.items():
        if capability.get(field) != expected:
            failures.append(
                f"memory reviewed recall-write authority capability {field} drifted"
            )
    for posture_ref in MEMORY_REVIEWED_RECALL_WRITE_POSTURE_REFS:
        if posture_ref not in set(capability.get("rollback_or_safe_disable_refs", [])):
            failures.append(
                "memory reviewed recall-write authority capability missing "
                f"posture ref {posture_ref}"
            )
    if set(capability.get("policy_decisions", [])) != EXPECTED_POLICY_DECISIONS:
        failures.append(
            "memory reviewed recall-write authority capability policy decisions drifted"
        )
    capability_routes = set(capability.get("backend_routes", []))
    for route_ref in MEMORY_REVIEWED_RECALL_WRITE_ROUTES:
        if route_ref not in capability_routes:
            failures.append(
                "memory reviewed recall-write authority capability missing "
                f"route {route_ref}"
            )
    if capability.get("cli_parity_ref") != MEMORY_REVIEWED_RECALL_WRITE_CLI_REF:
        failures.append(
            "memory reviewed recall-write authority capability CLI parity ref drifted"
        )
    capability_tests = set(capability.get("focused_test_refs", []))
    for test_ref in MEMORY_REVIEWED_RECALL_WRITE_TEST_REFS:
        if test_ref not in capability_tests:
            failures.append(
                "memory reviewed recall-write authority capability missing "
                f"focused test {test_ref}"
            )
def _append_patch_workbench_manifest_failures(
    failures: list[str],
    module: dict[str, Any],
) -> None:
    module_id = str(module.get("module_id"))
    rank = int(module.get("current_rank", -1))
    honest_status = str(module.get("honest_status", "")).lower()
    blocked_authorities = set(module.get("blocked_authorities", []))
    missing_contracts = set(module.get("missing_contracts", []))
    backend_routes = set(module.get("backend_routes", []))
    if rank <= 2:
        if "apply_blocked" not in honest_status:
            failures.append(
                f"{module_id} rank 2 patch workbench must keep apply_blocked honest_status"
            )
        for contract_ref in PATCH_WORKBENCH_REQUIRED_MISSING_CONTRACTS:
            if contract_ref not in missing_contracts:
                failures.append(
                    f"{module_id} rank 2 patch workbench missing blocker contract {contract_ref}"
                )
        for authority in PATCH_WORKBENCH_REQUIRED_BLOCKED_AUTHORITIES:
            if authority not in blocked_authorities:
                failures.append(
                    f"{module_id} rank 2 patch workbench must block {authority}"
                )
        if module.get("real_local_mutation") is not False:
            failures.append(
                f"{module_id} rank 2 patch workbench must not claim real_local_mutation"
            )
        if module.get("durable_receipt") is not False:
            failures.append(
                f"{module_id} rank 2 patch workbench must not claim durable_receipt"
            )
        if module.get("evidence_timeline_event") is not False:
            failures.append(
                f"{module_id} rank 2 patch workbench must not claim evidence_timeline_event"
            )
        return

    if rank >= 4:
        if PATCH_WORKBENCH_APPLY_ROUTE not in backend_routes:
            failures.append(
                f"{module_id} rank 4+ patch apply claim requires {PATCH_WORKBENCH_APPLY_ROUTE}"
            )
        if missing_contracts & PATCH_WORKBENCH_REQUIRED_MISSING_CONTRACTS:
            failures.append(
                f"{module_id} rank 4+ patch apply claim still has missing apply contracts"
            )
        for field in [
            "exact_scope_required",
            "idempotency_required",
            "rollback_or_safe_disable_required",
            "backend_owned_receipts",
        ]:
            if module.get(field) is not True:
                failures.append(
                    f"{module_id} rank 4+ patch apply claim requires {field}"
                )
        if not module.get("receipt_refs"):
            failures.append(
                f"{module_id} rank 4+ patch apply claim requires receipt_refs"
            )
        if not module.get("evidence_refs"):
            failures.append(
                f"{module_id} rank 4+ patch apply claim requires evidence_refs"
            )
        if not module.get("cli_or_script_refs"):
            failures.append(
                f"{module_id} rank 4+ patch apply claim requires CLI parity"
            )
        if not module.get("test_refs"):
            failures.append(
                f"{module_id} rank 4+ patch apply claim requires focused tests"
            )
        if not module.get("verifier_refs"):
            failures.append(
                f"{module_id} rank 4+ patch apply claim requires verifier refs"
            )


def _append_local_model_manifest_failures(
    failures: list[str],
    module: dict[str, Any],
) -> None:
    if LOCAL_MODEL_CLI_REF not in set(module.get("cli_or_script_refs", [])):
        failures.append(
            f"local_models must use path-backed CLI/script ref {LOCAL_MODEL_CLI_REF}"
        )


def _append_authority_capability_failures(
    failures: list[str],
    module_id: str,
    module: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
) -> None:
    capabilities = {
        str(capability.get("capability_id")): capability
        for capability in module.get("authority_capabilities", [])
    }
    for capability_id, capability in capabilities.items():
        if int(capability.get("rank", -1)) < 5:
            failures.append(
                f"{module_id}:{capability_id} authority capability must be rank 5+"
            )
        if set(capability.get("policy_decisions", [])) != EXPECTED_POLICY_DECISIONS:
            failures.append(
                f"{module_id}:{capability_id} authority capability policy decisions drifted"
            )
        for field in [
            "active_lease_required",
            "exact_approval_required",
            "idempotency_required",
            "receipts_required",
            "audit_required",
            "redaction_required",
        ]:
            if capability.get(field) is not True:
                failures.append(
                    f"{module_id}:{capability_id} authority capability requires {field}"
                )
        if capability.get("lease_scope") not in {"session", "mission"}:
            failures.append(
                f"{module_id}:{capability_id} authority capability lease_scope drifted"
            )
        if "AuthorityLease" not in str(capability.get("operator_copy", "")):
            failures.append(
                f"{module_id}:{capability_id} authority capability operator copy must name AuthorityLease"
            )
        posture_refs = set(capability.get("rollback_or_safe_disable_refs", []))
        if not posture_refs:
            failures.append(
                f"{module_id}:{capability_id} authority capability requires posture refs"
            )
        for route_ref in capability.get("backend_routes", []):
            route = routes_by_ref.get(route_ref)
            if route is None:
                failures.append(
                    f"{module_id}:{capability_id} authority capability references missing route {route_ref}"
                )
                continue
            if route.get("route_classification") != "mutating_requires_authority":
                failures.append(
                    f"{module_id}:{capability_id} authority capability route must be authority gated"
                )
            if route.get("idempotency_required") is not True:
                failures.append(
                    f"{module_id}:{capability_id} authority capability route must require idempotency"
                )


def _append_first_lane_failures(
    failures: list[str],
    manifest: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
    root: Path,
) -> None:
    modules = {
        str(module.get("module_id")): module for module in manifest.get("modules", [])
    }
    action_inbox = modules.get("action_inbox")
    if action_inbox is None:
        failures.append("action_inbox module missing")
        return
    if action_inbox.get("current_rank") != 3:
        failures.append("Action Inbox module must remain rank 3 overall")
    if action_inbox.get("next_target_rank") != 5:
        failures.append("Action Inbox target rank must be 5")
    capabilities_by_id = {
        str(capability.get("capability_id")): capability
        for capability in action_inbox.get("authority_capabilities", [])
    }
    capabilities_by_legacy_lane = {
        str(capability.get("legacy_lane_id")): capability
        for capability in action_inbox.get("authority_capabilities", [])
        if capability.get("legacy_lane_id")
    }
    capability = capabilities_by_id.get(
        LOCAL_TASK_AUTHORITY_CAPABILITY_ID
    ) or capabilities_by_legacy_lane.get(LOCAL_TASK_LANE_ID)
    if capability is None:
        failures.append("Action Inbox local_task_create authority capability missing")
    else:
        expected_capability_fields = {
            "capability_id": LOCAL_TASK_AUTHORITY_CAPABILITY_ID,
            "authority_domain_ref": LOCAL_TASK_AUTHORITY_DOMAIN_REF,
            "authority_capability_ref": LOCAL_TASK_AUTHORITY_CAPABILITY_REF,
            "required_mode_ref": LOCAL_TASK_AUTHORITY_MODE_REF,
            "authority_lease_requirement_ref": LOCAL_TASK_AUTHORITY_LEASE_REQUIREMENT_REF,
            "lease_scope": "session",
        }
        for field, expected in expected_capability_fields.items():
            if capability.get(field) != expected:
                failures.append(
                    f"local_task_create authority capability {field} drifted"
                )
        for expected_ref in [LOCAL_TASK_ROLLBACK_REF, LOCAL_TASK_SAFE_DISABLE_REF]:
            if expected_ref not in set(
                capability.get("rollback_or_safe_disable_refs", [])
            ):
                failures.append(
                    f"local_task_create authority capability missing {expected_ref}"
                )
        if set(capability.get("policy_decisions", [])) != EXPECTED_POLICY_DECISIONS:
            failures.append(
                "local_task_create authority capability policy decisions drifted"
            )
        if LOCAL_TASK_ROUTE not in set(capability.get("backend_routes", [])):
            failures.append(
                f"local_task_create authority capability missing {LOCAL_TASK_ROUTE}"
            )
        if "rollback_execution" not in set(capability.get("blocked_authorities", [])):
            failures.append(
                "local_task_create authority capability must keep rollback_execution blocked"
            )
        _append_local_task_repeatability_gate_failures(failures, capability, root)
    route = routes_by_ref.get(LOCAL_TASK_ROUTE)
    if route is None:
        failures.append("local_task_create route missing from API manifest")
        return
    if route.get("path") != LOCAL_TASK_PATH:
        failures.append("local_task_create path drifted")
    if (
        route.get("operation_id")
        != "post_control_center_actions_action_id_local_task_commit"
    ):
        failures.append("local_task_create operation_id drifted")
    if route.get("rate_limit_group") != "action_decision":
        failures.append(
            "local_task_create route must use action_decision rate limit group"
        )
    declared = set(build_api_manifest(app).capabilities_declared)
    for capability in [
        "control_center_action_local_task_commit",
        "control_center_action_decision_state_machine",
    ]:
        if capability not in declared:
            failures.append(f"API manifest missing declared capability {capability}")


def _append_local_task_repeatability_gate_failures(
    failures: list[str],
    capability: dict[str, Any],
    root: Path,
) -> None:
    if capability.get("repeatability_gate_ref") != LOCAL_TASK_REPEATABILITY_GATE_REF:
        failures.append(
            "local_task_create authority capability must declare "
            f"{LOCAL_TASK_REPEATABILITY_GATE_REF}"
        )

    focused_test_refs = set(capability.get("focused_test_refs", []))
    for ref in sorted(LOCAL_TASK_REPEATABILITY_REQUIRED_FOCUSED_TEST_REFS):
        if ref not in focused_test_refs:
            failures.append(f"local_task_create repeatability gate missing {ref}")
        _append_repo_ref_failure(
            failures,
            root,
            ref,
            "local_task_create.repeatability.focused_test_refs",
        )

    frontend_refs = set(capability.get("frontend_repeatability_test_refs", []))
    for ref in sorted(LOCAL_TASK_REPEATABILITY_REQUIRED_FRONTEND_TEST_REFS):
        if ref not in frontend_refs:
            failures.append(
                f"local_task_create repeatability gate missing frontend test {ref}"
            )
        _append_source_ref_failure(
            failures,
            root,
            ref,
            "local_task_create.repeatability.frontend_repeatability_test_refs",
        )

    verifier_refs = set(capability.get("verifier_repeatability_refs", []))
    for ref in sorted(LOCAL_TASK_REPEATABILITY_REQUIRED_VERIFIER_REFS):
        if ref not in verifier_refs:
            failures.append(
                f"local_task_create repeatability gate missing verifier ref {ref}"
            )
        _append_source_ref_failure(
            failures,
            root,
            ref,
            "local_task_create.repeatability.verifier_repeatability_refs",
        )

    frontend = root / "apps/control-center/src/components/FounderLoopPanels.tsx"
    if frontend.exists():
        frontend_text = frontend.read_text(encoding="utf-8")
        for marker in [
            "refresh_pending_backend_read_model",
            "refresh_failed",
            "Backend read model refreshed; receipt visibility now comes from the Action Inbox API.",
        ]:
            if marker not in frontend_text:
                failures.append(
                    f"local_task_create repeatability UI missing marker {marker}"
                )


def _append_public_request_schema_failures(failures: list[str]) -> None:
    openapi = app.openapi()
    schemas = openapi.get("components", {}).get("schemas", {})
    for schema_name in [
        "FounderLoopLocalTaskCommitRequest",
        "MemoryContextPackActionProposalRequest",
    ]:
        properties = schemas.get(schema_name, {}).get("properties", {})
        if "approval_grants" in properties:
            failures.append(
                f"{schema_name} must not expose caller-supplied approval_grants"
            )
    frontend = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
    if "approval_grants" in frontend.read_text(encoding="utf-8"):
        failures.append(
            "Control Center Founder Loop panels must not send approval_grants"
        )


def _append_ref_resolution_failures(
    failures: list[str],
    manifest: dict[str, Any],
    root: Path,
) -> None:
    for module in manifest.get("modules", []):
        module_id = str(module.get("module_id"))
        for field in ["test_refs", "verifier_refs", "route_metadata_refs"]:
            for ref in module.get(field, []):
                _append_repo_ref_failure(
                    failures, root, str(ref), f"{module_id}.{field}"
                )
        binding = module.get("ui_status_binding")
        if isinstance(binding, dict):
            for field in [
                "frontend_endpoint_ref",
                "frontend_client_ref",
                "frontend_type_ref",
                "backend_only_doc_ref",
                "backend_only_blocker_ref",
            ]:
                ref = binding.get(field)
                if ref:
                    _append_source_ref_failure(
                        failures,
                        root,
                        str(ref),
                        f"{module_id}.ui_status_binding.{field}",
                    )
            for field in [
                "frontend_component_refs",
                "frontend_test_refs",
                "stale_language_scan_refs",
            ]:
                for ref in binding.get(field, []):
                    _append_source_ref_failure(
                        failures,
                        root,
                        str(ref),
                        f"{module_id}.ui_status_binding.{field}",
                    )
        for ref in module.get("cli_or_script_refs", []):
            _append_cli_or_script_ref_failure(
                failures, root, str(ref), f"{module_id}.cli_or_script_refs"
            )
        for capability in module.get("authority_capabilities", []):
            capability_id = str(capability.get("capability_id"))
            for ref in capability.get("focused_test_refs", []):
                _append_repo_ref_failure(
                    failures,
                    root,
                    str(ref),
                    f"{module_id}:{capability_id}.focused_test_refs",
                )
            cli_ref = capability.get("cli_parity_ref")
            if cli_ref:
                _append_cli_or_script_ref_failure(
                    failures,
                    root,
                    str(cli_ref),
                    f"{module_id}:{capability_id}.cli_parity_ref",
                )
            for ref in capability.get("frontend_repeatability_test_refs", []):
                _append_source_ref_failure(
                    failures,
                    root,
                    str(ref),
                    f"{module_id}:{capability_id}.frontend_repeatability_test_refs",
                )
            for ref in capability.get("verifier_repeatability_refs", []):
                _append_source_ref_failure(
                    failures,
                    root,
                    str(ref),
                    f"{module_id}:{capability_id}.verifier_repeatability_refs",
                )


def _append_repo_ref_failure(
    failures: list[str],
    root: Path,
    ref: str,
    owner: str,
) -> None:
    path_ref, _, selector = ref.partition("::")
    path = root / path_ref
    if not path.exists():
        failures.append(f"{owner} references missing path {ref}")
        return
    if selector:
        test_name = selector.split("[", 1)[0]
        if f"def {test_name}(" not in path.read_text(encoding="utf-8"):
            failures.append(f"{owner} references missing test {ref}")


def _append_source_ref_failure(
    failures: list[str],
    root: Path,
    ref: str,
    owner: str,
) -> None:
    path_ref, _, selector = ref.partition("::")
    path = root / path_ref
    if not path.exists():
        failures.append(f"{owner} references missing path {ref}")
        return
    if selector and selector not in path.read_text(encoding="utf-8"):
        failures.append(f"{owner} references missing selector {ref}")


def _append_authority_ref_failure(
    failures: list[str],
    root: Path,
    routes_by_ref: dict[str, dict[str, Any]],
    ref: str,
    owner: str,
) -> None:
    method, _, path = ref.partition(" ")
    if method in {"GET", "POST", "PUT", "PATCH", "DELETE"} and path.startswith("/"):
        if ref not in routes_by_ref:
            failures.append(f"{owner} references missing route {ref}")
        return
    path_ref, _, selector = ref.partition("::")
    path_obj = root / path_ref
    if not path_obj.exists():
        failures.append(f"{owner} references missing path {ref}")
        return
    if not selector:
        return
    text = path_obj.read_text(encoding="utf-8")
    if path_obj.suffix == ".py" and selector.startswith("test_"):
        test_name = selector.split("[", 1)[0]
        if f"def {test_name}(" not in text:
            failures.append(f"{owner} references missing test {ref}")
        return
    if selector not in text:
        failures.append(f"{owner} references missing selector {ref}")


def _append_cli_or_script_ref_failure(
    failures: list[str],
    root: Path,
    ref: str,
    owner: str,
) -> None:
    path_ref = ref.split(" ", 1)[0]
    if "/" not in path_ref:
        return
    path = root / path_ref
    if not path.exists():
        failures.append(f"{owner} references missing CLI/script {ref}")


def _append_ui_status_binding_failures(
    failures: list[str],
    module: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
    root: Path,
) -> None:
    module_id = str(module.get("module_id"))
    rank = int(module.get("current_rank", -1))
    target_rank = int(module.get("next_target_rank", -1))
    backend_status_routes = [
        str(route_ref)
        for route_ref in module.get("backend_routes", [])
        if _is_backend_status_route(str(route_ref))
    ]
    if (rank < 2 and target_rank < 2) or not backend_status_routes:
        return

    binding = module.get("ui_status_binding")
    if not isinstance(binding, dict):
        failures.append(
            f"{module_id} rank 2+ backend status route requires ui_status_binding"
        )
        return

    status_route_ref = str(binding.get("status_route_ref", ""))
    if status_route_ref not in backend_status_routes:
        failures.append(
            f"{module_id} ui_status_binding status_route_ref must match a backend status route"
        )
        return
    route = routes_by_ref.get(status_route_ref)
    if route is None:
        failures.append(
            f"{module_id} ui_status_binding references missing route {status_route_ref}"
        )
        return
    if route.get("method") != "GET":
        failures.append(f"{module_id} status route must be GET")
    if route.get("route_classification") != "local_readonly":
        failures.append(f"{module_id} status route must be local_readonly")
    if route.get("side_effect_class") != "validation_only":
        failures.append(f"{module_id} status route must be validation_only")
    if route.get("protected_route") is not True:
        failures.append(f"{module_id} status route must stay protected")
    if route.get("idempotency_required") is not False:
        failures.append(
            f"{module_id} read-only status route must not require idempotency"
        )

    backend_only = binding.get("backend_only_status")
    if backend_only is True:
        for field in [
            "backend_only_reason",
            "backend_only_doc_ref",
            "backend_only_blocker_ref",
        ]:
            if not binding.get(field):
                failures.append(
                    f"{module_id} backend-only status binding requires {field}"
                )
        return
    if backend_only is not False:
        failures.append(
            f"{module_id} ui_status_binding backend_only_status must be boolean"
        )
        return

    for field in [
        "frontend_endpoint_ref",
        "frontend_client_ref",
        "frontend_type_ref",
    ]:
        if not binding.get(field):
            failures.append(f"{module_id} surfaced status binding requires {field}")
    for field in ["frontend_component_refs", "frontend_test_refs"]:
        if not binding.get(field):
            failures.append(f"{module_id} surfaced status binding requires {field}")
    scan_refs = binding.get("stale_language_scan_refs")
    if not scan_refs:
        failures.append(
            f"{module_id} surfaced status binding requires stale_language_scan_refs"
        )
    else:
        _append_stale_language_scan_failures(failures, root, module_id, scan_refs)


def _is_backend_status_route(route_ref: str) -> bool:
    method, _, path = route_ref.partition(" ")
    return (
        method == "GET"
        and path.startswith("/control-center/")
        and path.endswith("/status")
    )


def _append_stale_language_scan_failures(
    failures: list[str],
    root: Path,
    module_id: str,
    scan_refs: list[str],
) -> None:
    for ref in scan_refs:
        path_ref, _, selector = str(ref).partition("::")
        path = root / path_ref
        if not path.exists():
            failures.append(f"{module_id} stale language scan missing path {ref}")
            continue
        text = _scoped_compact_text(path, selector)
        for phrase in STALE_UI_STATUS_PHRASES:
            if phrase in text:
                failures.append(
                    f"{module_id} stale UI/backend status language in {path_ref}: {phrase}"
                )


def _scoped_compact_text(path: Path, selector: str) -> str:
    raw = path.read_text(encoding="utf-8")
    if not selector:
        return _compact_string(raw)
    start = raw.find(selector)
    if start < 0:
        return _compact_string(raw)
    scoped = raw[start:]
    end_candidates = [
        index
        for marker in ["\n  },\n", "\n};", "\nexport function "]
        if (index := scoped.find(marker, 1)) > 0
    ]
    if end_candidates:
        scoped = scoped[: min(end_candidates)]
    return _compact_string(scoped)


def _append_mock_fallback_fixture_failures(failures: list[str], root: Path) -> None:
    fixture_path = root / CONTROL_CENTER_MOCK_DATA_PATH.relative_to(ROOT)
    if not fixture_path.exists():
        failures.append(
            f"Control Center mock fallback fixture missing {fixture_path.relative_to(root)}"
        )
        return
    fixture = fixture_path.read_text(encoding="utf-8")
    forbidden_source_markers = [
        'source: "python_core_action_inbox_read_model"',
        "source: 'python_core_action_inbox_read_model'",
        'source: "python_core_action_inbox_read_model" as const',
        "source: 'python_core_action_inbox_read_model' as const",
    ]
    if any(marker in fixture for marker in forbidden_source_markers):
        failures.append(
            "Control Center mock fallback must not claim python_core_action_inbox_read_model"
        )
    source_readiness_markers = [
        'source: "python_core_morning_briefing_read_model"',
        "source: 'python_core_morning_briefing_read_model'",
        'source: "python_core_morning_briefing_read_model" as const',
        "source: 'python_core_morning_briefing_read_model' as const",
        'source: "python_core_source_readiness_read_model"',
        "source: 'python_core_source_readiness_read_model'",
        'source: "python_core_source_readiness_read_model" as const',
        "source: 'python_core_source_readiness_read_model' as const",
    ]
    if any(marker in fixture for marker in source_readiness_markers):
        failures.append(
            "Control Center mock fallback must not claim backend-owned source readiness read models"
        )
    if "local_task_commit_eligible: true" in fixture:
        failures.append(
            "Control Center mock fallback must not claim local_task_commit_eligible true"
        )
    committed_mock_markers = {
        'local_task_commit_receipt_ref: "receipt:': (
            "Control Center mock fallback must not claim committed local task receipt refs"
        ),
        "local_task_commit_receipt_ref: 'receipt:": (
            "Control Center mock fallback must not claim committed local task receipt refs"
        ),
        'status: "receipt_recorded"': (
            "Control Center mock fallback must not claim receipt_recorded local task state"
        ),
        "status: 'receipt_recorded'": (
            "Control Center mock fallback must not claim receipt_recorded local task state"
        ),
        'action_group_id: "receipt_recorded"': (
            "Control Center mock fallback must not claim receipt_recorded local task lanes"
        ),
        "action_group_id: 'receipt_recorded'": (
            "Control Center mock fallback must not claim receipt_recorded local task lanes"
        ),
        'replay_posture: "idempotency_replay_available"': (
            "Control Center mock fallback must not claim backend local task replay posture"
        ),
        "replay_posture: 'idempotency_replay_available'": (
            "Control Center mock fallback must not claim backend local task replay posture"
        ),
        'conflict_posture: "conflicting_idempotency_payload_rejected"': (
            "Control Center mock fallback must not claim backend local task conflict posture"
        ),
        "conflict_posture: 'conflicting_idempotency_payload_rejected'": (
            "Control Center mock fallback must not claim backend local task conflict posture"
        ),
        'evidence_timeline_event_ref: "evidence-timeline-event:local-task:': (
            "Control Center mock fallback must not claim local task Evidence Timeline events"
        ),
        "evidence_timeline_event_ref: 'evidence-timeline-event:local-task:": (
            "Control Center mock fallback must not claim local task Evidence Timeline events"
        ),
    }
    for marker, message in committed_mock_markers.items():
        if marker in fixture:
            failures.append(message)
    source_readiness_fixture = ""
    source_start = fixture.find("const sourceReadinessPosture")
    if source_start >= 0:
        source_readiness_fixture = fixture[source_start:]
        source_end_candidates = [
            index
            for marker in [
                "\nconst crmLiteFollowups",
                "\nexport const mockControlCenterData",
            ]
            if (index := source_readiness_fixture.find(marker, 1)) > 0
        ]
        if source_end_candidates:
            source_readiness_fixture = source_readiness_fixture[
                : min(source_end_candidates)
            ]
        source_readiness_fixture = _compact_string(source_readiness_fixture)
    if (
        "backend_owned: true" in source_readiness_fixture
        or "backend_owned:true" in source_readiness_fixture
    ):
        failures.append(
            "Control Center mock fallback source readiness posture must not claim backend_owned true"
        )
    proposal_start = fixture.find("const sourceReadinessProposalCandidates")
    proposal_end = fixture.find("const sourceReadiness:", proposal_start)
    if proposal_start >= 0:
        if proposal_end <= proposal_start:
            proposal_end_candidates = [
                index
                for marker in [
                    "\nexport const mockControlCenterData",
                    "\nconst crmLiteFollowups",
                ]
                if (index := fixture.find(marker, proposal_start + 1)) > proposal_start
            ]
            proposal_end = (
                min(proposal_end_candidates)
                if proposal_end_candidates
                else len(fixture)
            )
        proposal_fixture = fixture[proposal_start:proposal_end]
        if "backend_owned: true" in proposal_fixture:
            failures.append(
                "Control Center mock fallback source readiness proposals must not be backend-owned"
            )
        if "python_core_source_readiness_read_model" in proposal_fixture:
            failures.append(
                "Control Center mock fallback source readiness proposals must not claim python_core_source_readiness_read_model"
            )


def _append_behavior_probe_failures(failures: list[str], root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="uaa-operational-maturity-") as tmp:
        state_dir = Path(tmp) / "founder_loop"
        repo = FounderLoopRepository(state_dir)
        action = _probe_local_task_action(repo)
        try:
            repo.commit_local_task(
                action_id="local-task-create-scorecard",
                request=FounderLoopLocalTaskCommitRequest(
                    approval_ref="approval-ref:probe-missing"
                ),
                idempotency_key_ref="idempotency-ref:probe-missing-approval",
            )
            failures.append("behavior probe: missing approval unexpectedly committed")
        except FounderLoopStorageError:
            pass

        repo = FounderLoopRepository(
            state_dir,
            active_authority_leases=[_probe_workspace_write_lease()],
        )
        action = _probe_local_task_action(repo)
        action = _approve_probe_local_task_action(repo, action)
        if action.get("local_task_commit_eligible") is not True:
            failures.append(
                "behavior probe: approved local task with workspace/write lease is not commit eligible"
            )
            return
        if not action.get("local_task_commit_approval_ref"):
            failures.append(
                "behavior probe: approved local task lacks backend approval ref"
            )
            return
        if action.get("safe_disable_ref") != LOCAL_TASK_SAFE_DISABLE_REF:
            failures.append(
                "behavior probe: approved local task safe_disable_ref drifted"
            )
        if action.get("rollback_ref") != LOCAL_TASK_ROLLBACK_REF:
            failures.append("behavior probe: approved local task rollback_ref drifted")
        if action.get("local_task_safe_disable_ref") != LOCAL_TASK_SAFE_DISABLE_REF:
            failures.append(
                "behavior probe: local task posture safe_disable_ref drifted"
            )
        if action.get("local_task_rollback_ref") != LOCAL_TASK_ROLLBACK_REF:
            failures.append("behavior probe: local task posture rollback_ref drifted")
        if action.get("local_task_safe_disable_active") is not False:
            failures.append(
                "behavior probe: local task posture is unexpectedly disabled"
            )
        if action.get("local_task_rollback_execution_enabled") is not False:
            failures.append("behavior probe: rollback execution unexpectedly enabled")
        if any(
            str(reason).endswith("-missing")
            for reason in action.get("local_task_commit_blocked_reasons", [])
        ):
            failures.append(
                "behavior probe: approved local task has missing posture refs"
            )
        request = FounderLoopLocalTaskCommitRequest(
            approval_ref=str(action["local_task_commit_approval_ref"]),
            decision_reason_ref="decision-reason-ref:operational-maturity-probe",
            metadata_refs=["metadata-ref:operational-maturity-probe"],
        )
        before_counts = repo.storage_status()["counts"]
        receipt = repo.commit_local_task(
            action_id="local-task-create-scorecard",
            request=request,
            idempotency_key_ref="idempotency-ref:operational-maturity-probe",
        )
        after_counts = repo.storage_status()["counts"]
        if after_counts["local_tasks"] != before_counts["local_tasks"] + 1:
            failures.append("behavior probe: local task count did not change")
        if (
            after_counts["local_task_commit_receipts"]
            != before_counts["local_task_commit_receipts"] + 1
        ):
            failures.append("behavior probe: local task receipt count did not change")
        if receipt.get("safe_disable_ref") != LOCAL_TASK_SAFE_DISABLE_REF:
            failures.append("behavior probe: receipt safe_disable_ref drifted")
        if receipt.get("rollback_ref") != LOCAL_TASK_ROLLBACK_REF:
            failures.append("behavior probe: receipt rollback_ref drifted")
        if receipt.get("rollback_execution_enabled") is not False:
            failures.append("behavior probe: receipt enabled rollback execution")
        replay = repo.commit_local_task(
            action_id="local-task-create-scorecard",
            request=request,
            idempotency_key_ref="idempotency-ref:operational-maturity-probe",
        )
        if (
            replay.get("receipt_ref") != receipt.get("receipt_ref")
            or replay.get("replayed") is not True
        ):
            failures.append(
                "behavior probe: idempotency replay did not return prior receipt"
            )
        try:
            repo.commit_local_task(
                action_id="local-task-create-scorecard",
                request=request.model_copy(
                    update={
                        "metadata_refs": ["metadata-ref:operational-maturity-conflict"]
                    }
                ),
                idempotency_key_ref="idempotency-ref:operational-maturity-probe",
            )
            failures.append(
                "behavior probe: idempotency conflict unexpectedly committed"
            )
        except FounderLoopStorageDuplicateError:
            pass
        timeline = repo.evidence_timeline()
        if "local_task_created" not in timeline.get("event_types", []):
            failures.append("behavior probe: local_task_created evidence event missing")
        serialized_receipt = json.dumps(receipt, sort_keys=True).lower()
        for forbidden in [
            "raw_prompt",
            "raw path",
            "raw_log",
            "credential",
            "password",
            "secret",
        ]:
            if forbidden in serialized_receipt:
                failures.append(
                    f"behavior probe: receipt leaks forbidden content {forbidden}"
                )
        disabled_repo = FounderLoopRepository(
            Path(tmp) / "disabled_founder_loop",
            active_authority_leases=[_probe_workspace_write_lease()],
        )
        disabled_action = _approve_probe_local_task_action(
            disabled_repo,
            _probe_local_task_action(disabled_repo),
        )
        disabled_repo._disable_local_task_create_lane_for_test(
            disabled_reason_refs=["safe-disable-reason:operational-maturity-probe"],
        )
        disabled_action = _probe_local_task_action(disabled_repo)
        if disabled_action.get("local_task_commit_eligible") is not False:
            failures.append(
                "behavior probe: safe-disabled local task remained eligible"
            )
        if FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF not in disabled_action.get(
            "local_task_commit_blocked_reasons",
            [],
        ):
            failures.append("behavior probe: safe-disabled blocker missing")
        try:
            disabled_repo.commit_local_task(
                action_id="local-task-create-scorecard",
                request=FounderLoopLocalTaskCommitRequest(
                    approval_ref=str(disabled_action["local_task_commit_approval_ref"]),
                    decision_reason_ref="decision-reason-ref:operational-maturity-disabled-probe",
                ),
                idempotency_key_ref="idempotency-ref:operational-maturity-disabled-probe",
            )
            failures.append(
                "behavior probe: safe-disabled local task unexpectedly committed"
            )
        except FounderLoopStorageError as exc:
            if str(exc) != "FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED":
                failures.append(
                    "behavior probe: safe-disabled local task returned wrong code"
                )
        if disabled_repo.storage_status()["counts"]["local_tasks"] != 0:
            failures.append("behavior probe: safe-disabled local task mutated state")
        _append_cli_probe_failures(failures, root, state_dir)


def _append_read_only_status_probe_failures(failures: list[str]) -> None:
    local_models = build_control_center_local_models_status(env={}).model_dump(
        mode="json"
    )
    if local_models.get("status") != "read_only_status":
        failures.append("read-only probe: local models status is not read_only_status")
    if local_models.get("proposal_review_only") is not True:
        failures.append("read-only probe: local models must stay proposal-review only")
    if any(local_models.get("lifecycle_actions", {}).values()):
        failures.append("read-only probe: local models lifecycle action enabled")
    for authority in [
        "model_download",
        "model_pull",
        "provider_model_authority",
        "runtime_adapter_execution",
        "ollama_runtime_call",
        "mlx_lm_runtime_call",
    ]:
        if authority not in set(local_models.get("blocked_authorities", [])):
            failures.append(
                f"read-only probe: local models missing blocked authority {authority}"
            )
    adapter_readiness = local_models.get("adapter_readiness")
    if not isinstance(adapter_readiness, list):
        failures.append("read-only probe: local model adapter readiness missing")
    else:
        adapters = {
            item.get("adapter_id"): item
            for item in adapter_readiness
            if isinstance(item, dict)
        }
        for adapter_id in ["ollama", "mlx_lm"]:
            adapter = adapters.get(adapter_id)
            if not isinstance(adapter, dict):
                failures.append(
                    f"read-only probe: local models missing {adapter_id} readiness"
                )
                continue
            for field in [
                "runtime_calls_enabled",
                "model_pulls_enabled",
                "model_downloads_enabled",
                "lifecycle_start_stop_switch_enabled",
                "provider_model_authority_enabled",
                "control_center_subprocess_execution_enabled",
            ]:
                if adapter.get(field) is not False:
                    failures.append(
                        f"read-only probe: {adapter_id} enabled forbidden field {field}"
                    )
            blocked_refs = set(adapter.get("blocked_authority_refs", []))
            for ref in [
                "blocked-authority:model-call",
                "blocked-authority:model-pull-download",
                "blocked-authority:lifecycle-start-stop-switch",
                "blocked-authority:provider-model-authority",
            ]:
                if ref not in blocked_refs:
                    failures.append(
                        f"read-only probe: {adapter_id} missing blocked ref {ref}"
                    )
    serialized_local_models = json.dumps(local_models, sort_keys=True).lower()
    for forbidden in [
        "/users/",
        "/home/",
        "raw_prompt",
        "raw_response",
        "provider_payload",
        "ollama generate",
        "ollama chat",
        "mlx_lm.generate",
    ]:
        if forbidden in serialized_local_models:
            failures.append(
                f"read-only probe: local models status leaks forbidden content {forbidden}"
            )

    with tempfile.TemporaryDirectory(prefix="uaa-readonly-status-probe-") as tmp:
        repo = FounderLoopRepository(Path(tmp) / "founder_loop")
        routes_by_ref = {
            f"{route.method} {route.path}": route.model_dump(mode="json")
            for route in build_api_manifest(app).routes
        }
        source_route = routes_by_ref.get("GET /control-center/sources/readiness")
        if not source_route:
            failures.append("read-only probe: source readiness route missing")
        else:
            if source_route.get("route_classification") != "local_readonly":
                failures.append(
                    "read-only probe: source readiness route is not local_readonly"
                )
            if source_route.get("side_effect_class") != "local_dev_workspace_only":
                failures.append(
                    "read-only probe: source readiness route side effect drifted"
                )
            if source_route.get("protected_route") is not True:
                failures.append("read-only probe: source readiness route not protected")
            if source_route.get("idempotency_required") is not False:
                failures.append(
                    "read-only probe: source readiness route requires idempotency"
                )
            if source_route.get("approval_posture") != (
                "not_required_for_route_classification"
            ):
                failures.append(
                    "read-only probe: source readiness route approval posture drifted"
                )
        source_readiness = repo.source_readiness()
        if source_readiness.get("schema_version") != "founder_loop_source_readiness.v1":
            failures.append("read-only probe: source readiness schema drifted")
        if source_readiness.get("source") != "python_core_source_readiness_read_model":
            failures.append("read-only probe: source readiness source drifted")
        if source_readiness.get("backend_owned") is not True:
            failures.append(
                "read-only probe: source readiness route data is not backend-owned"
            )
        if source_readiness.get("route_ref") != "/control-center/sources/readiness":
            failures.append("read-only probe: source readiness route_ref drifted")
        for field in [
            "connector_runtime_enabled",
            "source_refresh_enabled",
            "notification_delivery_enabled",
            "account_auth_enabled",
            "raw_source_ingestion_enabled",
            "write_authority_enabled",
        ]:
            if source_readiness.get(field) is not False:
                failures.append(
                    f"read-only probe: source readiness route enabled {field}"
                )
        for ref in [
            "blocked-state:no-connector-write",
            "blocked-state:no-account-auth",
            "blocked-state:no-background-polling",
        ]:
            if ref not in set(source_readiness.get("blocked_authority_refs", [])):
                failures.append(
                    f"read-only probe: source readiness missing blocked authority {ref}"
                )
        source_proposals = source_readiness.get("source_readiness_proposal_candidates")
        if not isinstance(source_proposals, list) or len(source_proposals) < 3:
            failures.append(
                "read-only probe: source readiness proposal candidates missing"
            )
            source_proposals = []
        expected_proposal_titles = {
            "Define email read-only metadata contract",
            "Define calendar read-only metadata contract",
            "Resolve missing account-auth boundary",
        }
        actual_proposal_titles = {
            str(proposal.get("title"))
            for proposal in source_proposals
            if isinstance(proposal, dict)
        }
        if not expected_proposal_titles.issubset(actual_proposal_titles):
            failures.append("read-only probe: source readiness proposal titles drifted")
        for proposal in source_proposals:
            if not isinstance(proposal, dict):
                continue
            if proposal.get("source") != "python_core_source_readiness_read_model":
                failures.append(
                    "read-only probe: source readiness proposal source drifted"
                )
            if proposal.get("backend_owned") is not True:
                failures.append(
                    "read-only probe: source readiness proposal is not backend-owned"
                )
            if (
                proposal.get("proposal_classification")
                != "proposal_only_no_execution_path"
            ):
                failures.append(
                    "read-only probe: source readiness proposal classification drifted"
                )
            for field in [
                "connector_runtime_enabled",
                "source_refresh_enabled",
                "account_auth_enabled",
                "raw_source_ingestion_enabled",
                "write_authority_enabled",
                "local_task_commit_eligible",
            ]:
                if proposal.get(field) is not False:
                    failures.append(
                        f"read-only probe: source readiness proposal enabled {field}"
                    )
        today = repo.today_summary(limit=6)
        source_posture = today.get("source_readiness_posture", {})
        if source_posture.get("backend_owned") is not True:
            failures.append("read-only probe: source readiness is not backend-owned")
        if (
            today.get("source_readiness_route_ref")
            != "/control-center/sources/readiness"
        ):
            failures.append("read-only probe: Today source readiness route ref missing")
        if source_readiness.get("source_readiness_posture") != source_posture:
            failures.append(
                "read-only probe: dedicated source readiness posture is not shared with Today"
            )
        for field in [
            "connector_runtime_enabled",
            "source_refresh_enabled",
            "notification_delivery_enabled",
            "account_auth_enabled",
            "raw_source_ingestion_enabled",
            "write_authority_enabled",
        ]:
            if source_posture.get(field) is not False:
                failures.append(f"read-only probe: source readiness enabled {field}")
        for ref in [
            "contract-ref:email-read-only-missing",
            "contract-ref:calendar-read-only-missing",
        ]:
            if ref not in set(source_posture.get("missing_contract_refs", [])):
                failures.append(
                    f"read-only probe: source readiness missing contract ref {ref}"
                )

        actions = repo.actions_inbox(limit=10)
        action_execution_enabled = actions.get("dogfood_capture", {}).get(
            "action_execution_enabled"
        )
        if action_execution_enabled is not False:
            failures.append("read-only probe: Action Inbox enabled execution")
        if not actions.get("review_queue_groups"):
            failures.append("read-only probe: Action Inbox queue groups missing")
        action_proposals = [
            item
            for item in actions.get("items", [])
            if item.get("action_kind") == "source_readiness_contract_proposal"
        ]
        if len(action_proposals) < 3:
            failures.append(
                "read-only probe: source readiness Action Inbox proposals missing"
            )
        for item in action_proposals:
            if item.get("action_group_id") != "proposal_only_no_execution_path":
                failures.append(
                    "read-only probe: source readiness Action proposal is executable"
                )
            if item.get("local_task_commit_eligible") is not False:
                failures.append(
                    "read-only probe: source readiness Action proposal is local-task eligible"
                )
            if item.get("approval_required") is not False:
                failures.append(
                    "read-only probe: source readiness Action proposal requires approval"
                )
            if item.get("source_readiness_backend_owned") is not True:
                failures.append(
                    "read-only probe: source readiness Action proposal is not backend-owned"
                )
        for facet in actions.get("review_filter_facets", []):
            if facet.get("backend_owned") is not True:
                failures.append("read-only probe: Action Inbox facet not backend-owned")
        for item in actions.get("items", []):
            envelope = item.get("approval_envelope", {})
            receipt_visibility = item.get("receipt_visibility", {})
            for label, payload in [
                ("approval envelope", envelope),
                ("receipt visibility", receipt_visibility),
            ]:
                if payload.get("source") != "python_core_action_inbox_read_model":
                    failures.append(
                        f"read-only probe: Action Inbox {label} source drifted"
                    )
                if payload.get("backend_owned") is not True:
                    failures.append(
                        f"read-only probe: Action Inbox {label} not backend-owned"
                    )
            if (
                item.get("local_task_commit_eligible") is True
                and receipt_visibility.get("backend_owned") is not True
            ):
                failures.append(
                    "read-only probe: local task eligibility lacks backend receipt visibility"
                )

        evidence = repo.evidence_timeline(limit=10)
        if evidence.get("read_only") is not True:
            failures.append("read-only probe: evidence timeline is not read-only")
        for field in [
            "approval_ref_authority",
            "rollback_execution_enabled",
            "memory_truth_authority",
            "context_injection_authorized",
            "action_execution_enabled",
            "connector_write_enabled",
            "production_authority_enabled",
        ]:
            if evidence.get(field) is not False:
                failures.append(f"read-only probe: evidence timeline enabled {field}")
        if evidence.get("safe_refs_only") is not True:
            failures.append("read-only probe: evidence timeline is not safe-ref only")


def _probe_local_task_action(repo: FounderLoopRepository) -> dict[str, Any]:
    return next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )


def _probe_workspace_write_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:operational-maturity-workspace-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary=(
            "Operational maturity probe lease grants Workspace write for exact "
            "approved local task commit receipts."
        ),
    )


def _approve_probe_local_task_action(
    repo: FounderLoopRepository,
    action: dict[str, Any],
) -> dict[str, Any]:
    repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=str(action["action_revision_ref"]),
            decision_reason_ref="decision-reason-ref:operational-maturity-action-approval",
        ),
        idempotency_key_ref="idempotency-ref:operational-maturity-action-approval",
    )
    return _probe_local_task_action(repo)


def _append_cli_probe_failures(
    failures: list[str],
    root: Path,
    state_dir: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/dev/uaa_founder_loop.py"),
            "--state-dir",
            str(state_dir),
            "commit-local-task",
            "--action-id",
            "local-task-create-scorecard",
            "--approval-ref",
            "approval-ref:cli-probe-missing",
            "--idempotency-ref",
            "idempotency-ref:cli-probe-missing",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        failures.append("behavior probe: CLI missing approval unexpectedly succeeded")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        failures.append("behavior probe: CLI did not emit parseable JSON")
        return
    if payload.get("safe_refs_only") is not True:
        failures.append("behavior probe: CLI output does not declare safe refs only")
    serialized = json.dumps(payload, sort_keys=True).lower()
    for forbidden in ["/users/", "/home/", "credential", "password", "secret"]:
        if forbidden in serialized:
            failures.append(
                f"behavior probe: CLI output leaks forbidden content {forbidden}"
            )


def _append_status_doc_failures(
    failures: list[str],
    gap_map_text: str,
    board_text: str,
) -> None:
    for label, text in [
        ("Operator Shell gap map", gap_map_text),
        ("Founder Command Center board", board_text),
    ]:
        for snippet in [
            "docs/control_center/operational_maturity_manifest.json",
            "docs/control_center/operationalization_ladder.md",
            "docs/control_center/authority_candidate_scorecard.json",
            "docs/control_center/authority_ramp_conveyor.md",
            "authoritylease capability",
        ]:
            if snippet not in text:
                failures.append(
                    f"{label} missing operational maturity gate snippet {snippet}"
                )
    unsupported_claims = [
        "files operational",
        "patch workbench operational",
        "local models operational",
        "settings operational",
        "connectors operational",
        "inbox sources operational",
    ]
    for claim in unsupported_claims:
        if claim in gap_map_text or claim in board_text:
            failures.append(
                f"status docs claim unsupported operational behavior: {claim}"
            )


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print(SUCCESS_MESSAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
