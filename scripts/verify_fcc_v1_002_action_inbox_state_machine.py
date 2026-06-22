#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.verification.api_lane import (  # noqa: E402
    ApiVerifierContext,
    default_api_verifier_context,
)
from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    load_json,
    print_failures_or_success,
    read_text,
)
from ultimate_ai_agent.core.control_center.action_decisions import (  # noqa: E402
    FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
)


SUCCESS_MESSAGE = "FCC-V1-002 Action Inbox state machine verification passed."
DOC_PATH = "docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md"
RELEASE_SURFACE_PATH = "docs/control_center/release_surface_manifest.json"
ROUTE_STATUS_PATH = "docs/control_center/route_status_manifest.json"
PRODUCT_TRUTH_PATH = "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
MILESTONE_STATUS_PATH = "docs/verification/milestone_status_manifest.json"
ACTION_UI_PATH = "apps/control-center/src/components/FounderLoopPanels.tsx"
ACTION_ROUTES = {
    ("POST", "/control-center/actions/{action_id}/approve"): (
        "post_control_center_actions_action_id_approve",
        "mutating_requires_authority",
    ),
    ("POST", "/control-center/actions/{action_id}/edit"): (
        "post_control_center_actions_action_id_edit",
        "mutating_requires_authority",
    ),
    ("POST", "/control-center/actions/{action_id}/reject"): (
        "post_control_center_actions_action_id_reject",
        "mutating_requires_authority",
    ),
    ("POST", "/control-center/actions/{action_id}/defer"): (
        "post_control_center_actions_action_id_defer",
        "mutating_requires_authority",
    ),
    ("GET", "/control-center/actions/{action_id}/receipt"): (
        "get_control_center_actions_action_id_receipt",
        "local_sensitive",
    ),
}
FORBIDDEN_CLAIMS = [
    "action execution enabled",
    "approved actions execute",
    "connector writes enabled",
    "memory writes enabled",
    "public beta ready",
    "production ready",
    "production authority enabled",
]


def verify(
    root: Path = ROOT,
    *,
    context: ApiVerifierContext | None = None,
    release_surface: dict[str, Any] | None = None,
    route_status: dict[str, Any] | None = None,
    milestone_status: dict[str, Any] | None = None,
    doc_text: str | None = None,
    check_files: bool = True,
    check_api_behavior: bool = True,
) -> list[str]:
    failures: list[str] = []
    if check_files:
        _append_required_file_failures(failures, root)
    context = context or default_api_verifier_context()
    release_surface = release_surface or load_json(RELEASE_SURFACE_PATH)
    route_status = route_status or load_json(ROUTE_STATUS_PATH)
    milestone_status = milestone_status or load_json(MILESTONE_STATUS_PATH)
    doc_text = doc_text if doc_text is not None else read_text(DOC_PATH)

    _append_manifest_failures(failures, context)
    _append_release_surface_failures(failures, release_surface)
    _append_route_status_failures(failures, route_status)
    _append_milestone_status_failures(failures, milestone_status)
    _append_doc_failures(failures, doc_text)
    if check_api_behavior:
        _append_api_behavior_failures(failures, context)
    if check_files:
        append_forbidden_claims(
            failures,
            [DOC_PATH, PRODUCT_TRUTH_PATH, "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"],
            FORBIDDEN_CLAIMS,
        )
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [
        DOC_PATH,
        RELEASE_SURFACE_PATH,
        ROUTE_STATUS_PATH,
        MILESTONE_STATUS_PATH,
        ACTION_UI_PATH,
        "src/ultimate_ai_agent/core/control_center/action_decisions.py",
        "tests/test_fcc_v1_002_action_inbox_state_machine.py",
    ]:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-V1-002 file: {rel_path}")


def _append_manifest_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    manifest = context.manifest
    if manifest.get("route_count") != 125:
        failures.append("FCC-V1-002 expects current API route_count 125")
    if manifest.get("route_classification_summary", {}).get("mutating_requires_authority") != 23:
        failures.append("FCC-V1-002 expects 23 mutating routes")
    for key, (operation_id, route_classification) in ACTION_ROUTES.items():
        route = context.routes_by_key.get(key)
        if route is None:
            failures.append(f"missing Action Inbox route metadata: {key}")
            continue
        if route.get("operation_id") != operation_id:
            failures.append(f"{key} operation_id drifted")
        if route.get("route_classification") != route_classification:
            failures.append(f"{key} route_classification drifted")
        if route.get("side_effect_class") != "local_dev_workspace_only":
            failures.append(f"{key} side_effect_class drifted")
        if key[0] == "POST":
            if route.get("idempotency_required") is not True:
                failures.append(f"{key} must require idempotency")
            if route.get("approval_posture") != "required_before_mutation_authority":
                failures.append(f"{key} must require approval posture before mutation")
            if route.get("rate_limit_group") != "action_decision":
                failures.append(f"{key} must use action_decision rate-limit group")
    if ("POST", "/control-center/actions/{action_id}/execute") in context.routes_by_key:
        failures.append("Action Inbox execution route must not exist")


def _append_release_surface_failures(
    failures: list[str],
    release_surface: dict[str, Any],
) -> None:
    actions = _route_by_path(release_surface, "/actions")
    if actions is None:
        failures.append("release surface missing /actions route")
        return
    if actions.get("status") != "partial":
        failures.append("/actions release status must remain partial")
    if actions.get("approval_required") is not True:
        failures.append("/actions must require approval posture for mutating decision routes")
    _append_backend_route_set_failures(failures, actions.get("backend_routes", []), "release surface")
    blocked = set(actions.get("blocked_capabilities", []))
    for required in {
        "missing_backend:action-execution-contract",
        "production_authority",
        "connector_write",
    }:
        if required not in blocked:
            failures.append(f"/actions release surface missing blocked capability {required}")


def _append_route_status_failures(
    failures: list[str],
    route_status: dict[str, Any],
) -> None:
    surface = next(
        (
            item for item in route_status.get("surfaces", [])
            if item.get("surface") == "Action Inbox"
        ),
        None,
    )
    action = next(
        (
            item for item in route_status.get("visible_actions", [])
            if item.get("action_id") == "navigate-actions-inbox"
        ),
        None,
    )
    for label, item, key in [
        ("route status surface", surface, "current_backend_routes"),
        ("visible action", action, "backend_routes"),
    ]:
        if item is None:
            failures.append(f"missing Action Inbox {label}")
            continue
        if item.get("release_status") != "partial_backend_not_product_ready":
            failures.append(f"Action Inbox {label} must remain partial")
        _append_backend_route_set_failures(failures, item.get(key, []), label)


def _append_milestone_status_failures(
    failures: list[str],
    milestone_status: dict[str, Any],
) -> None:
    milestone = next(
        (
            item for item in milestone_status.get("milestones", [])
            if item.get("id") == "FCC-V1-002"
        ),
        None,
    )
    if milestone is None:
        failures.append("milestone status manifest missing FCC-V1-002")
        return
    if milestone.get("status") != "implemented":
        failures.append("FCC-V1-002 milestone status must be implemented")
    proof_refs = set(milestone.get("proof_refs", []))
    for required in {DOC_PATH, "scripts/verify_fcc_v1_002_action_inbox_state_machine.py"}:
        if required not in proof_refs:
            failures.append(f"FCC-V1-002 milestone status missing proof ref {required}")


def _append_doc_failures(failures: list[str], doc_text: str) -> None:
    compact = " ".join(doc_text.lower().split())
    for required in [
        "status: implemented for backend-owned action inbox decision state",
        FOUNDER_LOOP_ACTION_STATE_CONTRACT_REF,
        "does not execute the approved action",
        "reusing the same idempotency key with the same decision payload returns the prior receipt",
    ]:
        if required.lower() not in compact:
            failures.append(f"FCC-V1-002 doc missing required wording: {required}")


def _append_api_behavior_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    old_state_dir = os.environ.get("UAA_FOUNDER_LOOP_STATE_DIR")
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = str(Path(temp_dir) / "founder_loop")
        try:
            body = {"decision_reason_ref": "decision-reason-ref:verifier-reject"}
            missing = context.client.post(
                "/control-center/actions/setup-assistant-hardening/reject",
                json=body,
            )
            if missing.status_code != 428:
                failures.append("Action decision route must reject missing idempotency")
            first = context.client.post(
                "/control-center/actions/setup-assistant-hardening/reject",
                json=body,
                headers={"x-uaa-idempotency-key": "idempotency-ref:verifier-reject"},
            )
            if first.status_code != 200:
                failures.append("Action decision route did not return first receipt")
                return
            receipt = first.json().get("data", {})
            if receipt.get("status") != "rejected" or receipt.get("action_executed") is not False:
                failures.append("Action decision receipt must be rejected without execution")
            replay = context.client.post(
                "/control-center/actions/setup-assistant-hardening/reject",
                json=body,
                headers={"x-uaa-idempotency-key": "idempotency-ref:verifier-reject"},
            )
            if replay.status_code != 200 or replay.json().get("data", {}).get("replayed") is not True:
                failures.append("Action decision route must replay matching idempotency payload")
            conflict = context.client.post(
                "/control-center/actions/setup-assistant-hardening/reject",
                json={"decision_reason_ref": "decision-reason-ref:verifier-changed"},
                headers={"x-uaa-idempotency-key": "idempotency-ref:verifier-reject"},
            )
            if conflict.status_code != 409:
                failures.append("Action decision route must reject idempotency conflict")
            receipt_response = context.client.get(
                "/control-center/actions/setup-assistant-hardening/receipt"
            )
            if receipt_response.status_code != 200:
                failures.append("Action receipt route did not return stored receipt")
        finally:
            if old_state_dir is None:
                os.environ.pop("UAA_FOUNDER_LOOP_STATE_DIR", None)
            else:
                os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = old_state_dir


def _append_backend_route_set_failures(
    failures: list[str],
    routes: Any,
    label: str,
) -> None:
    route_keys = {
        (route.get("method"), route.get("path"))
        for route in routes
        if isinstance(route, dict)
    }
    missing = set(ACTION_ROUTES) | {("GET", "/control-center/actions/inbox")}
    missing -= route_keys
    if missing:
        failures.append(f"{label} missing Action Inbox backend routes: {sorted(missing)}")


def _route_by_path(manifest: dict[str, Any], path: str) -> dict[str, Any] | None:
    return next(
        (
            route for route in manifest.get("routes", [])
            if isinstance(route, dict) and route.get("path") == path
        ),
        None,
    )


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
