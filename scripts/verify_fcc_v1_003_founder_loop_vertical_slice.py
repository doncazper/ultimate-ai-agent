#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
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
    append_missing_doc_snippets,
    load_json,
    print_failures_or_success,
)
from ultimate_ai_agent.api.local_auth import LOCAL_API_BEARER_ENV  # noqa: E402
from ultimate_ai_agent.core.authority import AUTHORITY_STATE_DIR_ENV  # noqa: E402
from ultimate_ai_agent.core.control_center.action_decisions import (  # noqa: E402
    FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
    FounderLoopActionDecisionRequest,
)


SUCCESS_MESSAGE = "FCC-V1-003 Founder Loop vertical slice verification passed."
DOC_PATH = "docs/control_center/FCC_V1_003_FOUNDER_LOOP_VERTICAL_SLICE.md"
RELEASE_SURFACE_PATH = "docs/control_center/release_surface_manifest.json"
ROUTE_STATUS_PATH = "docs/control_center/route_status_manifest.json"
MILESTONE_STATUS_PATH = "docs/verification/milestone_status_manifest.json"
CLI_PATH = "scripts/dev/uaa_founder_loop.py"
TODAY_ITEM_REF = "briefing:storage-state-first-loop"
TODAY_ROUTE = ("POST", "/control-center/today/action-envelope")
FOUNDER_LOOP_V1_PROOF_REF = "scripts/verify_founder_loop_v1.py"
FOUNDER_LOOP_V1_PROOFED_STATUS = "founder_loop_v1_proofed"
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
    check_files: bool = True,
    check_behavior: bool = True,
) -> list[str]:
    failures: list[str] = []
    context = context or default_api_verifier_context()
    release_surface = release_surface or load_json(RELEASE_SURFACE_PATH)
    route_status = route_status or load_json(ROUTE_STATUS_PATH)
    milestone_status = milestone_status or load_json(MILESTONE_STATUS_PATH)
    if check_files:
        _append_required_file_failures(failures, root)
    _append_manifest_failures(failures, context)
    _append_release_surface_failures(failures, release_surface)
    _append_route_status_failures(failures, route_status)
    _append_milestone_status_failures(failures, milestone_status)
    _append_doc_failures(failures)
    if check_behavior:
        _append_behavior_failures(failures, context, root)
    if check_files:
        append_forbidden_claims(
            failures,
            [DOC_PATH, "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"],
            FORBIDDEN_CLAIMS,
        )
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [
        DOC_PATH,
        CLI_PATH,
        "tests/test_fcc_v1_003_founder_loop_vertical_slice.py",
        "apps/control-center/src/components/FounderLoopPanels.tsx",
    ]:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-V1-003 file: {rel_path}")


def _append_manifest_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    route = context.routes_by_key.get(TODAY_ROUTE)
    if route is None:
        failures.append("missing Today-to-Action envelope route metadata")
        return
    expected = {
        "operation_id": "post_control_center_today_action_envelope",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "rate_limit_group": "today_to_action_envelope",
    }
    for key, value in expected.items():
        if route.get(key) != value:
            failures.append(f"Today-to-Action route {key} drifted")
    if route.get("idempotency_required") is not True:
        failures.append("Today-to-Action route must require idempotency")
    if route.get("approval_posture") != "required_before_mutation_authority":
        failures.append("Today-to-Action route must keep approval posture")
    if ("POST", "/control-center/actions/{action_id}/execute") in context.routes_by_key:
        failures.append("Action execution route must not exist")


def _append_release_surface_failures(
    failures: list[str],
    release_surface: dict[str, Any],
) -> None:
    today = _route_by_path(release_surface, "/today")
    actions = _route_by_path(release_surface, "/actions")
    for label, item in [("/today", today), ("/actions", actions)]:
        if item is None:
            failures.append(f"release surface missing {label}")
            continue
        if label == "/today" and item.get("status") != "partial":
            failures.append("/today release status must remain partial")
        if label == "/actions":
            status = item.get("status")
            if status not in {"partial", "ship"}:
                failures.append("/actions release status must remain partial or FCC-V1-007 proofed ship")
            if status == "ship" and FOUNDER_LOOP_V1_PROOF_REF not in set(item.get("proof_lanes", [])):
                failures.append("/actions ship status requires FCC-V1-007 proof lane")
        _append_route_present(failures, item.get("backend_routes", []), TODAY_ROUTE, label)
    if today and "missing_backend:today-action-mutation-contract" in set(
        today.get("blocked_capabilities", [])
    ):
        failures.append("/today still claims missing Today action mutation contract")
    if actions and "missing_backend:today-action-envelope-creation-contract" in set(
        actions.get("blocked_capabilities", [])
    ):
        failures.append("/actions still claims missing Today-to-Action envelope creation")


def _append_route_status_failures(
    failures: list[str],
    route_status: dict[str, Any],
) -> None:
    for label, item, key in [
        ("Today surface", _surface(route_status, "Today"), "current_backend_routes"),
        ("Action Inbox surface", _surface(route_status, "Action Inbox"), "current_backend_routes"),
        ("Today visible action", _action(route_status, "navigate-today"), "backend_routes"),
    ]:
        if item is None:
            failures.append(f"route status missing {label}")
            continue
        _append_route_present(failures, item.get(key, []), TODAY_ROUTE, label)
        release_status = item.get("release_status")
        if label == "Action Inbox surface":
            if release_status not in {"partial_backend_not_product_ready", FOUNDER_LOOP_V1_PROOFED_STATUS}:
                failures.append(f"{label} must remain partial or FCC-V1-007 proofed")
            if release_status == FOUNDER_LOOP_V1_PROOFED_STATUS and item.get("missing_backend_routes"):
                failures.append(f"{label} proofed status cannot list missing backend routes")
        elif release_status != "partial_backend_not_product_ready":
            failures.append(f"{label} must remain partial")


def _append_milestone_status_failures(
    failures: list[str],
    milestone_status: dict[str, Any],
) -> None:
    milestone = next(
        (
            item
            for item in milestone_status.get("milestones", [])
            if item.get("id") == "FCC-V1-003"
        ),
        None,
    )
    if milestone is None:
        failures.append("milestone status manifest missing FCC-V1-003")
        return
    if milestone.get("status") != "implemented":
        failures.append("FCC-V1-003 milestone status must be implemented")
    proof_refs = set(milestone.get("proof_refs", []))
    for required in {DOC_PATH, CLI_PATH, __file__.removeprefix(str(ROOT) + "/")}:
        if required not in proof_refs:
            failures.append(f"FCC-V1-003 missing proof ref {required}")


def _append_doc_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(
        failures,
        {
            DOC_PATH: [
                "Status: implemented for the first receipt-bearing vertical slice",
                FOUNDER_LOOP_VERTICAL_SLICE_CONTRACT_REF,
                "Today item -> Action envelope -> exact approval/edit/reject/defer receipt -> Evidence Timeline",
                "`workspace/draft` AuthorityLease",
                "authority decision refs",
                "does not execute the approved action",
                "scripts/dev/uaa_founder_loop.py",
            ],
        },
    )


def _append_behavior_failures(
    failures: list[str],
    context: ApiVerifierContext,
    root: Path,
) -> None:
    old_state_dir = os.environ.get("UAA_FOUNDER_LOOP_STATE_DIR")
    old_authority_state_dir = os.environ.get(AUTHORITY_STATE_DIR_ENV)
    old_bearer = os.environ.get(LOCAL_API_BEARER_ENV)
    bearer = "fcc-v1-003-local-bearer"
    auth_headers = {"Authorization": f"Bearer {bearer}"}
    with tempfile.TemporaryDirectory() as temp_dir:
        state_dir = str(Path(temp_dir) / "founder_loop")
        os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = state_dir
        os.environ[AUTHORITY_STATE_DIR_ENV] = str(Path(temp_dir) / "authority")
        os.environ[LOCAL_API_BEARER_ENV] = bearer
        try:
            item_ref = _exercise_promotion_api(failures, context, auth_headers)
            _exercise_cli(failures, root, state_dir)
            _exercise_decisions(failures, context, state_dir, item_ref, auth_headers)
            _append_timeline_failures(failures, context, item_ref, auth_headers)
        finally:
            if old_state_dir is None:
                os.environ.pop("UAA_FOUNDER_LOOP_STATE_DIR", None)
            else:
                os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = old_state_dir
            if old_authority_state_dir is None:
                os.environ.pop(AUTHORITY_STATE_DIR_ENV, None)
            else:
                os.environ[AUTHORITY_STATE_DIR_ENV] = old_authority_state_dir
            if old_bearer is None:
                os.environ.pop(LOCAL_API_BEARER_ENV, None)
            else:
                os.environ[LOCAL_API_BEARER_ENV] = old_bearer


def _exercise_promotion_api(
    failures: list[str],
    context: ApiVerifierContext,
    auth_headers: dict[str, str],
) -> str:
    body = {"today_item_ref": TODAY_ITEM_REF}
    missing = context.client.post(
        "/control-center/today/action-envelope",
        json=body,
        headers=auth_headers,
    )
    if missing.status_code != 428:
        failures.append("Today-to-Action route must reject missing idempotency")
    first = context.client.post(
        "/control-center/today/action-envelope",
        json=body,
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-003-promote",
        },
    )
    if first.status_code != 200:
        failures.append("Today-to-Action route did not create first receipt")
        return "founder-action:today-promotion:missing"
    receipt = first.json().get("data", {})
    _append_no_authority_flag_failures(failures, receipt, "promotion receipt")
    if receipt.get("action_envelope_ref") is None:
        failures.append("Today-to-Action receipt missing action_envelope_ref")
    if receipt.get("authority_decision_outcome") != "allow":
        failures.append("Today-to-Action receipt missing allowed authority decision")
    if not receipt.get("authority_lease_ref"):
        failures.append("Today-to-Action receipt missing authority lease ref")
    if "authority_decision_refs_only" not in first.json().get(
        "redactions_applied",
        [],
    ):
        failures.append("Today-to-Action route missing authority redaction posture")
    replay = context.client.post(
        "/control-center/today/action-envelope",
        json=body,
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-003-promote",
        },
    )
    if replay.status_code != 200 or replay.json().get("data", {}).get("replayed") is not True:
        failures.append("Today-to-Action route must replay matching idempotency payload")
    conflict = context.client.post(
        "/control-center/today/action-envelope",
        json={**body, "priority": "high"},
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-003-promote",
        },
    )
    if conflict.status_code != 409:
        failures.append("Today-to-Action route must reject idempotency conflict")
    return str(receipt.get("item_ref", "founder-action:today-promotion:missing"))


def _exercise_cli(failures: list[str], root: Path, state_dir: str) -> None:
    common = [sys.executable, str(root / CLI_PATH), "--state-dir", state_dir]
    inspect = subprocess.run(
        [*common, "inspect", "--limit", "4"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if inspect.returncode != 0 or "raw_paths_omitted" not in inspect.stdout:
        failures.append("Founder Loop CLI inspect path failed safe output check")
    promote = subprocess.run(
        [
            *common,
            "promote-action-envelope",
            "--today-item-ref",
            TODAY_ITEM_REF,
            "--idempotency-ref",
            "idempotency-ref:fcc-v1-003-cli-promote",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if promote.returncode != 0 or "action_envelope_ref" not in promote.stdout:
        failures.append("Founder Loop CLI promote path failed receipt output check")


def _exercise_decisions(
    failures: list[str],
    context: ApiVerifierContext,
    state_dir: str,
    item_ref: str,
    auth_headers: dict[str, str],
) -> None:
    approval = _approval_body(state_dir, item_ref)
    action_path = f"/control-center/actions/{item_ref}"
    checks = [
        ("approve", approval, "approved"),
        ("edit", {"edited_envelope_ref": "edited-envelope-ref:fcc-v1-003"}, "edited"),
        ("reject", {"decision_reason_ref": "decision-reason-ref:fcc-v1-003-reject"}, "rejected"),
        ("defer", {"defer_until_ref": "defer-until-ref:fcc-v1-003"}, "deferred"),
    ]
    for decision, body, expected_status in checks:
        response = context.client.post(
            f"{action_path}/{decision}",
            json=body,
            headers={
                **auth_headers,
                "x-uaa-idempotency-key": f"idempotency-ref:fcc-v1-003-{decision}",
            },
        )
        if response.status_code != 200:
            failures.append(f"Action {decision} did not return a receipt")
            continue
        receipt = response.json().get("data", {})
        if receipt.get("status") != expected_status:
            failures.append(f"Action {decision} receipt status drifted")
        _append_no_authority_flag_failures(failures, receipt, f"{decision} receipt")


def _approval_body(state_dir: str, item_ref: str) -> dict[str, Any]:
    request = FounderLoopActionDecisionRequest(
        decision_reason_ref="decision-reason-ref:fcc-v1-003-approve"
    )
    return {
        "decision_reason_ref": request.decision_reason_ref,
    }


def _append_timeline_failures(
    failures: list[str],
    context: ApiVerifierContext,
    item_ref: str,
    auth_headers: dict[str, str],
) -> None:
    response = context.client.get("/control-center/today/summary", headers=auth_headers)
    if response.status_code != 200:
        failures.append("Today summary did not return after vertical slice decisions")
        return
    timeline = response.json().get("data", {}).get("evidence_timeline", [])
    match = next((item for item in timeline if item_ref in str(item)), None)
    if match is None:
        failures.append("Evidence Timeline missing promoted Action item")
        return
    answers = match.get("history_answers", {})
    for key in ["proposed", "approved", "happened", "changed", "undoable"]:
        if key not in answers:
            failures.append(f"Evidence Timeline missing {key} history answer")


def _append_no_authority_flag_failures(
    failures: list[str],
    payload: dict[str, Any],
    label: str,
) -> None:
    for key in [
        "action_executed",
        "approval_grants_execution",
        "connector_write_performed",
        "memory_write_performed",
        "model_provider_authority_allowed",
        "production_authority_enabled",
    ]:
        if payload.get(key) is True:
            failures.append(f"{label} enabled denied authority flag {key}")


def _append_route_present(
    failures: list[str],
    routes: Any,
    key: tuple[str, str],
    label: str,
) -> None:
    route_keys = {
        (route.get("method"), route.get("path"))
        for route in routes
        if isinstance(route, dict)
    }
    if key not in route_keys:
        failures.append(f"{label} missing route {key}")


def _surface(route_status: dict[str, Any], surface: str) -> dict[str, Any] | None:
    return next((item for item in route_status.get("surfaces", []) if item.get("surface") == surface), None)


def _action(route_status: dict[str, Any], action_id: str) -> dict[str, Any] | None:
    return next((item for item in route_status.get("visible_actions", []) if item.get("action_id") == action_id), None)


def _route_by_path(manifest: dict[str, Any], path: str) -> dict[str, Any] | None:
    return next(
        (
            route
            for route in manifest.get("routes", [])
            if isinstance(route, dict) and route.get("path") == path
        ),
        None,
    )


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
