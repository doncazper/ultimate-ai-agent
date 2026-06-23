#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402


SUCCESS_MESSAGE = "Operational maturity manifest verification passed."
MANIFEST_PATH = ROOT / "docs/control_center/operational_maturity_manifest.json"
SCHEMA_PATH = ROOT / "docs/schemas/operational_maturity_manifest.schema.json"
LADDER_DOC_PATH = ROOT / "docs/control_center/OPERATIONALIZATION_LADDER.md"
GAP_MAP_PATH = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
FOUNDER_BOARD_PATH = ROOT / "docs/kanban/founder_command_center_board.md"

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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _compact_text(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    manifest = _load_json(root / MANIFEST_PATH.relative_to(ROOT))
    schema = _load_json(root / SCHEMA_PATH.relative_to(ROOT))
    ladder_text = _compact_text(root / LADDER_DOC_PATH.relative_to(ROOT))
    gap_map_text = _compact_text(root / GAP_MAP_PATH.relative_to(ROOT))
    board_text = _compact_text(root / FOUNDER_BOARD_PATH.relative_to(ROOT))
    api_manifest = build_api_manifest(app).model_dump(mode="json")
    routes_by_ref = {
        f"{route['method']} {route['path']}": route
        for route in api_manifest["routes"]
    }

    _append_schema_shape_failures(failures, schema)
    _append_manifest_shape_failures(failures, manifest)
    _append_ladder_doc_failures(failures, ladder_text)
    _append_module_failures(failures, manifest, routes_by_ref)
    _append_first_lane_failures(failures, manifest, routes_by_ref)
    _append_status_doc_failures(failures, gap_map_text, board_text)
    return failures


def _append_schema_shape_failures(
    failures: list[str],
    schema: dict[str, Any],
) -> None:
    if schema.get("title") != "Control Center Operational Maturity Manifest":
        failures.append("operational maturity schema title drifted")
    module_required = set(
        schema.get("$defs", {}).get("module", {}).get("required", [])
    )
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


def _append_manifest_shape_failures(
    failures: list[str],
    manifest: dict[str, Any],
) -> None:
    if manifest.get("schema_version") != "uaa-control-center-operational-maturity.v1":
        failures.append("operational maturity manifest schema_version drifted")
    if manifest.get("status") != "active operational maturity manifest":
        failures.append("operational maturity manifest status drifted")
    if manifest.get("ladder_doc_ref") != "docs/control_center/OPERATIONALIZATION_LADDER.md":
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
            failures.append(f"{module_id} current_rank_label does not match rank {rank}")
        if int(module.get("next_target_rank", -1)) < int(rank):
            failures.append(f"{module_id} next_target_rank is behind current_rank")
        if not module.get("honest_status"):
            failures.append(f"{module_id} missing honest_status")
        if not module.get("smallest_next_operational_action"):
            failures.append(f"{module_id} missing smallest_next_operational_action")
        for route_ref in module.get("backend_routes", []):
            if route_ref not in routes_by_ref:
                failures.append(f"{module_id} references missing backend route {route_ref}")
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
    for route_ref in lane.get("backend_routes", []):
        route = routes_by_ref.get(route_ref)
        if route is None:
            failures.append(f"{module_id}:{lane_id} references missing route {route_ref}")
            continue
        if route.get("route_classification") != "mutating_requires_authority":
            failures.append(f"{module_id}:{lane_id} route must be mutating authority gated")
        if route.get("side_effect_class") != "local_dev_workspace_only":
            failures.append(f"{module_id}:{lane_id} route must stay local_dev_workspace_only")
        if route.get("idempotency_required") is not True:
            failures.append(f"{module_id}:{lane_id} route must require idempotency")


def _append_first_lane_failures(
    failures: list[str],
    manifest: dict[str, Any],
    routes_by_ref: dict[str, dict[str, Any]],
) -> None:
    modules = {
        str(module.get("module_id")): module
        for module in manifest.get("modules", [])
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
    ]:
        if expected not in set(lane.get(field, [])):
            failures.append(f"local_task_create lane missing {expected}")
    route = routes_by_ref.get(LOCAL_TASK_ROUTE)
    if route is None:
        failures.append("local_task_create route missing from API manifest")
        return
    if route.get("path") != LOCAL_TASK_PATH:
        failures.append("local_task_create path drifted")
    if route.get("operation_id") != "post_control_center_actions_action_id_local_task_commit":
        failures.append("local_task_create operation_id drifted")
    if route.get("rate_limit_group") != "action_decision":
        failures.append("local_task_create route must use action_decision rate limit group")
    declared = set(build_api_manifest(app).capabilities_declared)
    for capability in [
        "control_center_action_local_task_commit",
        "control_center_action_decision_state_machine",
    ]:
        if capability not in declared:
            failures.append(f"API manifest missing declared capability {capability}")


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
            "promotion gate",
        ]:
            if snippet not in text:
                failures.append(f"{label} missing operational maturity gate snippet {snippet}")
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
