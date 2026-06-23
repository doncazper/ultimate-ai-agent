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
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority  # noqa: E402
from ultimate_ai_agent.core.control_center.action_decisions import (  # noqa: E402
    FounderLoopActionDecisionRequest,
    action_approval_request,
)
from ultimate_ai_agent.core.control_center.local_tasks import (  # noqa: E402
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF,
    FounderLoopLocalTaskCommitRequest,
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
LOCAL_TASK_ROUTE = "POST /control-center/actions/{action_id}/local-task/commit"
LOCAL_TASK_PATH = "/control-center/actions/{action_id}/local-task/commit"
LOCAL_TASK_LANE_ID = "local_task_create"
LOCAL_TASK_RECEIPT_REF = "receipt:founder-loop-local-task:*"
LOCAL_TASK_EVENT_REF = "evidence-event-type:local_task_created"
LOCAL_TASK_ROLLBACK_REF = FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF
LOCAL_TASK_SAFE_DISABLE_REF = FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF
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
AUTHORITY_CANDIDATE_STATUSES = {
    "not_ready",
    "proposal_only_ready",
    "contract_ready",
    "micro_lane_candidate",
    "blocked_by_policy",
}
MICRO_LANE_REQUIRED_PREREQUISITE_FIELDS = [
    "backend_core_owner_ref",
    "route_side_effect_ref",
    "exact_scope_ref",
    "approval_plan_ref",
    "idempotency_plan_ref",
    "receipt_evidence_plan_ref",
    "rollback_safe_disable_plan_ref",
    "redaction_plan_ref",
]
MICRO_LANE_REQUIRED_PREREQUISITE_LIST_FIELDS = [
    "cli_api_core_parity_refs",
    "focused_test_refs",
    "verifier_refs",
]


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
    _append_authority_scorecard_failures(
        failures,
        scorecard,
        routes_by_ref,
        root,
        conveyor_text,
    )
    _append_ladder_doc_failures(failures, ladder_text)
    _append_module_failures(failures, manifest, routes_by_ref, root)
    _append_first_lane_failures(failures, manifest, routes_by_ref)
    _append_public_request_schema_failures(failures)
    _append_ref_resolution_failures(failures, manifest, root)
    _append_mock_fallback_fixture_failures(failures, root)
    _append_behavior_probe_failures(failures, root)
    _append_status_doc_failures(failures, gap_map_text, board_text)
    return failures


def _append_schema_shape_failures(
    failures: list[str],
    schema: dict[str, Any],
) -> None:
    if schema.get("title") != "Control Center Operational Maturity Manifest":
        failures.append("operational maturity schema title drifted")
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
    ]:
        if field not in module_required:
            failures.append(f"operational maturity schema missing module field {field}")
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
        "conveyor_doc_ref",
        "verifier_ref",
        "operational_maturity_manifest_ref",
        "proposal_foundation",
        "authority_candidates",
        "first_micro_lane_decision",
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
    prerequisite_required = set(
        schema.get("$defs", {})
        .get("authority_candidate", {})
        .get("properties", {})
        .get("prerequisite_refs", {})
        .get("required", [])
    )
    for field in (
        MICRO_LANE_REQUIRED_PREREQUISITE_FIELDS
        + MICRO_LANE_REQUIRED_PREREQUISITE_LIST_FIELDS
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


def _append_authority_scorecard_failures(
    failures: list[str],
    scorecard: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
    root: Path,
    conveyor_text: str,
) -> None:
    if (
        scorecard.get("schema_version")
        != "uaa-control-center-authority-candidate-scorecard.v1"
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
        "at most one candidate may be selected",
        "no new authority candidate is selected",
        "local_task_create",
    ]:
        if snippet not in conveyor_text:
            failures.append(f"authority ramp conveyor doc missing '{snippet}'")

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
    selected = [
        candidate
        for candidate in candidates
        if candidate.get("selected_for_micro_lane") is True
    ]
    if len(selected) > 1:
        failures.append(
            "authority scorecard must select at most one micro-lane candidate"
        )
    for candidate in candidates:
        _append_authority_candidate_failures(
            failures,
            candidate,
            routes_by_ref,
            root,
        )
    _append_first_micro_lane_decision_failures(
        failures,
        scorecard.get("first_micro_lane_decision"),
        selected,
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
        "route_refs",
        "surface_refs",
        "test_refs",
        "blocked_authorities",
        "next_safe_action",
    ]:
        if not foundation.get(field):
            failures.append(f"{foundation_id} authority foundation requires {field}")
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
    if (
        candidate.get("selected_for_micro_lane") is True
        and status != "micro_lane_candidate"
    ):
        failures.append(
            f"{candidate_id} selected micro-lane must be micro_lane_candidate"
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
    if status != "micro_lane_candidate":
        return
    for field in MICRO_LANE_REQUIRED_PREREQUISITE_FIELDS:
        ref = prerequisite_refs.get(field)
        if not ref:
            failures.append(f"{candidate_id} micro-lane candidate requires {field}")
            continue
        _append_authority_ref_failure(
            failures,
            root,
            routes_by_ref,
            str(ref),
            f"{candidate_id}.prerequisite_refs.{field}",
        )
    for field in MICRO_LANE_REQUIRED_PREREQUISITE_LIST_FIELDS:
        refs = prerequisite_refs.get(field)
        if not refs:
            failures.append(f"{candidate_id} micro-lane candidate requires {field}")
            continue
        for ref in refs:
            _append_authority_ref_failure(
                failures,
                root,
                routes_by_ref,
                str(ref),
                f"{candidate_id}.prerequisite_refs.{field}",
            )


def _append_first_micro_lane_decision_failures(
    failures: list[str],
    decision: Any,
    selected: list[dict[str, Any]],
) -> None:
    if not isinstance(decision, dict):
        failures.append("authority scorecard requires first_micro_lane_decision")
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
        for lane in module.get("graduated_lanes", []):
            _append_lane_failures(failures, module_id, lane, routes_by_ref)


def _append_lane_failures(
    failures: list[str],
    module_id: str,
    lane: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
) -> None:
    lane_id = str(lane.get("lane_id"))
    rank = int(lane.get("rank", -1))
    if rank < 5:
        failures.append(f"{module_id}:{lane_id} graduated lane must be rank 5+")
    for field in ["real_local_mutation", "durable_receipt", "evidence_timeline_event"]:
        if lane.get(field) is not True:
            failures.append(f"{module_id}:{lane_id} rank 5 lane requires {field}")
    if not lane.get("receipt_refs"):
        failures.append(f"{module_id}:{lane_id} rank 5 lane requires receipt_refs")
    if not lane.get("evidence_refs"):
        failures.append(f"{module_id}:{lane_id} rank 5 lane requires evidence_refs")
    if not lane.get("cli_parity_ref"):
        failures.append(f"{module_id}:{lane_id} rank 5 lane requires cli_parity_ref")
    if not lane.get("focused_test_refs"):
        failures.append(f"{module_id}:{lane_id} rank 5 lane requires focused_test_refs")
    if lane.get("rollback_or_safe_disable_required") is not True:
        failures.append(
            f"{module_id}:{lane_id} rank 5 lane requires rollback_or_safe_disable_required"
        )
    posture_refs = set(lane.get("rollback_or_safe_disable_refs", []))
    if not posture_refs:
        failures.append(f"{module_id}:{lane_id} rank 5 lane requires posture refs")
    if lane_id == LOCAL_TASK_LANE_ID:
        for expected_ref in [LOCAL_TASK_ROLLBACK_REF, LOCAL_TASK_SAFE_DISABLE_REF]:
            if expected_ref not in posture_refs:
                failures.append(
                    f"{module_id}:{lane_id} rank 5 lane missing posture ref {expected_ref}"
                )
    if "rollback_execution" not in set(lane.get("blocked_authorities", [])):
        failures.append(
            f"{module_id}:{lane_id} rank 5 lane must block rollback_execution"
        )
    for route_ref in lane.get("backend_routes", []):
        route = routes_by_ref.get(route_ref)
        if route is None:
            failures.append(
                f"{module_id}:{lane_id} references missing route {route_ref}"
            )
            continue
        if route.get("route_classification") != "mutating_requires_authority":
            failures.append(
                f"{module_id}:{lane_id} route must be mutating authority gated"
            )
        if route.get("side_effect_class") != "local_dev_workspace_only":
            failures.append(
                f"{module_id}:{lane_id} route must stay local_dev_workspace_only"
            )
        if route.get("idempotency_required") is not True:
            failures.append(f"{module_id}:{lane_id} route must require idempotency")


def _append_first_lane_failures(
    failures: list[str],
    manifest: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
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
    lanes = {
        str(lane.get("lane_id")): lane
        for lane in action_inbox.get("graduated_lanes", [])
    }
    lane = lanes.get(LOCAL_TASK_LANE_ID)
    if lane is None:
        failures.append("Action Inbox local_task_create graduated lane missing")
        return
    if lane.get("rank") != 5:
        failures.append("local_task_create lane must be rank 5")
    for expected, field in [
        (LOCAL_TASK_ROUTE, "backend_routes"),
        (LOCAL_TASK_RECEIPT_REF, "receipt_refs"),
        (LOCAL_TASK_EVENT_REF, "evidence_refs"),
        (LOCAL_TASK_ROLLBACK_REF, "rollback_or_safe_disable_refs"),
        (LOCAL_TASK_SAFE_DISABLE_REF, "rollback_or_safe_disable_refs"),
    ]:
        if expected not in set(lane.get(field, [])):
            failures.append(f"local_task_create lane missing {expected}")
    if lane.get("rollback_or_safe_disable_required") is not True:
        failures.append("local_task_create lane must require rollback or safe-disable")
    if "rollback_execution" not in set(lane.get("blocked_authorities", [])):
        failures.append("local_task_create lane must keep rollback_execution blocked")
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
        for lane in module.get("graduated_lanes", []):
            lane_id = str(lane.get("lane_id"))
            for ref in lane.get("focused_test_refs", []):
                _append_repo_ref_failure(
                    failures,
                    root,
                    str(ref),
                    f"{module_id}:{lane_id}.focused_test_refs",
                )
            cli_ref = lane.get("cli_parity_ref")
            if cli_ref:
                _append_cli_or_script_ref_failure(
                    failures,
                    root,
                    str(cli_ref),
                    f"{module_id}:{lane_id}.cli_parity_ref",
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
    if "local_task_commit_eligible: true" in fixture:
        failures.append(
            "Control Center mock fallback must not claim local_task_commit_eligible true"
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

        action = _approve_probe_local_task_action(repo, action)
        if action.get("local_task_commit_eligible") is not True:
            failures.append(
                "behavior probe: approved local task is not commit eligible"
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
        disabled_repo = FounderLoopRepository(Path(tmp) / "disabled_founder_loop")
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


def _probe_local_task_action(repo: FounderLoopRepository) -> dict[str, Any]:
    return next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )


def _approve_probe_local_task_action(
    repo: FounderLoopRepository,
    action: dict[str, Any],
) -> dict[str, Any]:
    request = FounderLoopActionDecisionRequest(
        decision_reason_ref="decision-reason-ref:operational-maturity-action-approval"
    )
    approval_request = action_approval_request(
        item_ref=str(action["item_ref"]),
        actor_context=request.actor_context,
        risk_class=str(action["risk_class"]),
        resource_refs=[
            str(action["item_ref"]),
            str(action["action_envelope_ref"]),
            str(action["action_scope_ref"]),
            str(action["action_approval_requirement_ref"]),
        ],
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    grant = authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="local_operational_maturity_probe",
        approval_ref="approval-ref:operational-maturity-action-approve",
    )
    repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            approval_ref=grant.approval_ref,
            approval_grants=[grant],
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
            "promotion gate",
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
