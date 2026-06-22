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
    append_missing_doc_snippets,
    load_json,
    print_failures_or_success,
)
from ultimate_ai_agent.api.local_auth import LOCAL_API_BEARER_ENV  # noqa: E402
from ultimate_ai_agent.core.chat import CHAT_DURABLE_RECEIPT_CONTRACT_REF  # noqa: E402


SUCCESS_MESSAGE = "FCC-V1-004 Chat durable receipt and handoff verification passed."
DOC_PATH = "docs/control_center/FCC_V1_004_CHAT_DURABLE_RECEIPT_HANDOFF.md"
RELEASE_SURFACE_PATH = "docs/control_center/release_surface_manifest.json"
ROUTE_STATUS_PATH = "docs/control_center/route_status_manifest.json"
MILESTONE_STATUS_PATH = "docs/verification/milestone_status_manifest.json"
CHAT_TURN_ROUTE = ("POST", "/control-center/chat/turns")
CHAT_RECEIPT_ROUTE = ("GET", "/control-center/chat/turns/{turn_ref}/receipt")
CHAT_HANDOFF_ROUTE = ("POST", "/control-center/chat/turns/{turn_ref}/handoff")
FOUNDER_LOOP_V1_PROOF_REF = "scripts/verify_founder_loop_v1.py"
FOUNDER_LOOP_V1_PROOFED_STATUS = "founder_loop_v1_proofed"
ROUTES = {
    CHAT_TURN_ROUTE: {
        "operation_id": "post_control_center_chat_turns",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "chat_durable_receipt",
    },
    CHAT_RECEIPT_ROUTE: {
        "operation_id": "get_control_center_chat_turns_turn_ref_receipt",
        "route_classification": "local_sensitive",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": False,
        "rate_limit_group": None,
    },
    CHAT_HANDOFF_ROUTE: {
        "operation_id": "post_control_center_chat_turns_turn_ref_handoff",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "chat_durable_receipt",
    },
}
FORBIDDEN_CLAIMS = [
    "chat durable receipts are shipped",
    "chat is production ready",
    "chat handoff executes",
    "model output is authority",
    "memory write enabled",
    "public beta ready",
    "production authority enabled",
]
DENIED_RESPONSE_FIELDS = [
    "response_visible",
    "prompt_body_visible",
    "completion_body_visible",
    "model_output_authority",
    "tool_execution_enabled",
    "memory_write_authorized",
    "context_injection_authorized",
    "provider_sdk_call_enabled",
    "web_fetch_enabled",
    "connector_write_enabled",
    "shell_subprocess_execution_enabled",
    "action_execution_enabled",
    "approval_grant_capture_enabled",
    "production_authority_enabled",
    "action_executed",
    "plan_executed",
    "connector_write_performed",
    "memory_write_performed",
]
DENIED_RAW_FRAGMENTS = [
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider_payload",
    "full transcript",
    "credential",
    "password",
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
        _append_behavior_failures(failures, context)
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
        "scripts/verify_fcc_v1_004_chat_durable_receipt_handoff.py",
        "tests/test_fcc_v1_004_chat_durable_receipt_handoff.py",
        "apps/control-center/src/components/OperatorFlowPanels.tsx",
    ]:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-V1-004 file: {rel_path}")


def _append_manifest_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    for key, expected in ROUTES.items():
        route = context.routes_by_key.get(key)
        if route is None:
            failures.append(f"missing Chat durable receipt route metadata {key}")
            continue
        for field, value in expected.items():
            if route.get(field) != value:
                failures.append(f"Chat durable receipt route {key} {field} drifted")
        if key[0] == "POST" and route.get("approval_posture") != "required_before_mutation_authority":
            failures.append(f"Chat durable receipt route {key} must keep approval posture")
    forbidden_routes = [
        ("POST", "/control-center/chat" + "/execute"),
        ("POST", "/control-center/chat/turns/{turn_ref}/execute"),
        ("POST", "/control-center/chat/turns/{turn_ref}/memory-write"),
    ]
    for key in forbidden_routes:
        if key in context.routes_by_key:
            failures.append(f"forbidden Chat authority route exists: {key}")


def _append_release_surface_failures(
    failures: list[str],
    release_surface: dict[str, Any],
) -> None:
    chat = _route_by_path(release_surface, "/chat")
    if chat is None:
        failures.append("release surface missing /chat")
        return
    status = chat.get("status")
    if status not in {"partial", "ship"}:
        failures.append("/chat release status must remain partial or FCC-V1-007 proofed ship")
    if status == "ship" and FOUNDER_LOOP_V1_PROOF_REF not in set(chat.get("proof_lanes", [])):
        failures.append("/chat ship status requires FCC-V1-007 proof lane")
    for route in ROUTES:
        _append_route_present(failures, chat.get("backend_routes", []), route, "/chat")
    proof_refs = set(chat.get("proof_lanes", []))
    for proof_ref in [
        __file__.removeprefix(str(ROOT) + "/"),
        "tests/test_fcc_v1_004_chat_durable_receipt_handoff.py",
    ]:
        if proof_ref not in proof_refs:
            failures.append(f"/chat release surface missing proof ref {proof_ref}")
    blocked = set(chat.get("blocked_capabilities", []))
    if status == "partial":
        for capability in [
            "chat_model_output_authority",
            "chat_handoff_execution",
            "memory_write",
            "plan_execution",
            "action_execution",
            "production_authority",
        ]:
            if capability not in blocked:
                failures.append(f"/chat release surface missing blocked capability {capability}")


def _append_route_status_failures(
    failures: list[str],
    route_status: dict[str, Any],
) -> None:
    for label, item, key in [
        ("Chat Local Operator surface", _surface(route_status, "Chat Local Operator"), "current_backend_routes"),
        ("Navigate Chat visible action", _action(route_status, "navigate-chat-shell"), "backend_routes"),
    ]:
        if item is None:
            failures.append(f"route status missing {label}")
            continue
        for route in ROUTES:
            _append_route_present(failures, item.get(key, []), route, label)
        release_status = item.get("release_status")
        if release_status not in {"partial_backend_not_product_ready", FOUNDER_LOOP_V1_PROOFED_STATUS}:
            failures.append(f"{label} must remain partial or FCC-V1-007 proofed")
        if release_status == FOUNDER_LOOP_V1_PROOFED_STATUS and item.get("missing_backend_routes"):
            failures.append(f"{label} proofed status cannot list missing backend routes")
        lowered = str(item).lower()
        for fragment in ["durable", "handoff", "model output is not authority"]:
            if fragment not in lowered:
                failures.append(f"{label} missing Chat durable receipt posture {fragment}")


def _append_milestone_status_failures(
    failures: list[str],
    milestone_status: dict[str, Any],
) -> None:
    milestone = next(
        (
            item
            for item in milestone_status.get("milestones", [])
            if item.get("id") == "FCC-V1-004"
        ),
        None,
    )
    if milestone is None:
        failures.append("milestone status manifest missing FCC-V1-004")
        return
    if milestone.get("status") != "implemented":
        failures.append("FCC-V1-004 milestone status must be implemented")
    proof_refs = set(milestone.get("proof_refs", []))
    for required in {
        DOC_PATH,
        __file__.removeprefix(str(ROOT) + "/"),
        "tests/test_fcc_v1_004_chat_durable_receipt_handoff.py",
    }:
        if required not in proof_refs:
            failures.append(f"FCC-V1-004 missing proof ref {required}")


def _append_doc_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(
        failures,
        {
            DOC_PATH: [
                "Status: implemented for durable Chat receipts and reviewable handoffs",
                CHAT_DURABLE_RECEIPT_CONTRACT_REF,
                "POST /control-center/chat/turns",
                "GET /control-center/chat/turns/{turn_ref}/receipt",
                "POST /control-center/chat/turns/{turn_ref}/handoff",
                "Raw prompt content, raw response content, raw provider payloads",
                "Handoffs create proposals only",
                "scripts/verify_fcc_v1_004_chat_durable_receipt_handoff.py",
            ],
        },
    )


def _append_behavior_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    old_state_dir = os.environ.get("UAA_FOUNDER_LOOP_STATE_DIR")
    old_bearer = os.environ.get(LOCAL_API_BEARER_ENV)
    bearer = "fcc-v1-004-local-bearer"
    auth_headers = {"Authorization": f"Bearer {bearer}"}
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = str(Path(temp_dir) / "founder_loop")
        os.environ[LOCAL_API_BEARER_ENV] = bearer
        try:
            receipt = _exercise_chat_turn_receipt(failures, context, auth_headers)
            _exercise_chat_handoffs(failures, context, receipt, auth_headers)
            _append_today_summary_failures(failures, context, receipt, auth_headers)
        finally:
            if old_state_dir is None:
                os.environ.pop("UAA_FOUNDER_LOOP_STATE_DIR", None)
            else:
                os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = old_state_dir
            if old_bearer is None:
                os.environ.pop(LOCAL_API_BEARER_ENV, None)
            else:
                os.environ[LOCAL_API_BEARER_ENV] = old_bearer


def _exercise_chat_turn_receipt(
    failures: list[str],
    context: ApiVerifierContext,
    auth_headers: dict[str, str],
) -> dict[str, Any]:
    body = _chat_turn_body()
    missing = context.client.post("/control-center/chat/turns", json=body, headers=auth_headers)
    if missing.status_code != 428:
        failures.append("Chat turn receipt route must reject missing idempotency")
    first = context.client.post(
        "/control-center/chat/turns",
        json=body,
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-004-chat-turn",
        },
    )
    if first.status_code != 200:
        failures.append(f"Chat turn receipt route failed with {first.status_code}")
        return {"turn_ref": body["turn_ref"]}
    receipt = first.json().get("data", {})
    _append_receipt_shape_failures(failures, receipt, "Chat turn receipt")
    if receipt.get("contract_ref") != CHAT_DURABLE_RECEIPT_CONTRACT_REF:
        failures.append("Chat turn receipt contract ref drifted")
    replay = context.client.post(
        "/control-center/chat/turns",
        json=body,
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-004-chat-turn",
        },
    )
    if replay.status_code != 200 or replay.json().get("data", {}).get("replayed") is not True:
        failures.append("Chat turn receipt route must replay matching idempotency payload")
    conflict = context.client.post(
        "/control-center/chat/turns",
        json={**body, "model_ref": "model-ref:fcc-v1-004-other-local"},
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-004-chat-turn",
        },
    )
    if conflict.status_code != 409:
        failures.append("Chat turn receipt route must reject idempotency conflict")
    fetched = context.client.get(
        f"/control-center/chat/turns/{body['turn_ref']}/receipt",
        headers=auth_headers,
    )
    if fetched.status_code != 200 or fetched.json().get("data", {}).get("receipt_ref") != receipt.get("receipt_ref"):
        failures.append("Chat turn receipt GET route did not return the stored receipt")
    return receipt


def _exercise_chat_handoffs(
    failures: list[str],
    context: ApiVerifierContext,
    receipt: dict[str, Any],
    auth_headers: dict[str, str],
) -> None:
    turn_ref = str(receipt.get("turn_ref", "chat-turn:fcc-v1-004"))
    missing_receipt = context.client.post(
        "/control-center/chat/turns/chat-turn:fcc-v1-004-missing/handoff",
        json={"handoff_target": "actions"},
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-004-missing",
        },
    )
    if missing_receipt.status_code != 404:
        failures.append("Chat handoff must reject missing turn receipt with 404")
    missing_idempotency = context.client.post(
        f"/control-center/chat/turns/{turn_ref}/handoff",
        json={"handoff_target": "actions"},
        headers=auth_headers,
    )
    if missing_idempotency.status_code != 428:
        failures.append("Chat handoff route must reject missing idempotency")
    actions = context.client.post(
        f"/control-center/chat/turns/{turn_ref}/handoff",
        json={"handoff_target": "actions"},
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-004-handoff-actions",
        },
    )
    if actions.status_code != 200:
        failures.append(f"Chat actions handoff route failed with {actions.status_code}")
    else:
        action_receipt = actions.json().get("data", {})
        _append_receipt_shape_failures(failures, action_receipt, "Chat actions handoff")
        if not str(action_receipt.get("created_ref", "")).startswith("founder-action:"):
            failures.append("Chat actions handoff did not create a reviewable Action ref")
        if action_receipt.get("action_executed") is not False:
            failures.append("Chat actions handoff must not execute actions")
    replay = context.client.post(
        f"/control-center/chat/turns/{turn_ref}/handoff",
        json={"handoff_target": "actions"},
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-004-handoff-actions",
        },
    )
    if replay.status_code != 200 or replay.json().get("data", {}).get("replayed") is not True:
        failures.append("Chat actions handoff must replay matching idempotency payload")
    conflict = context.client.post(
        f"/control-center/chat/turns/{turn_ref}/handoff",
        json={"handoff_target": "plans"},
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-004-handoff-actions",
        },
    )
    if conflict.status_code != 409:
        failures.append("Chat handoff route must reject idempotency conflict")
    plans = context.client.post(
        f"/control-center/chat/turns/{turn_ref}/handoff",
        json={"handoff_target": "plans"},
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-004-handoff-plans",
        },
    )
    if plans.status_code != 200:
        failures.append(f"Chat plans handoff route failed with {plans.status_code}")
    else:
        plan_receipt = plans.json().get("data", {})
        _append_receipt_shape_failures(failures, plan_receipt, "Chat plans handoff")
        if not str(plan_receipt.get("created_ref", "")).startswith("plan-summary:"):
            failures.append("Chat plans handoff did not create a reviewable Plan ref")
        if plan_receipt.get("plan_executed") is not False:
            failures.append("Chat plans handoff must not execute plans")


def _append_today_summary_failures(
    failures: list[str],
    context: ApiVerifierContext,
    receipt: dict[str, Any],
    auth_headers: dict[str, str],
) -> None:
    response = context.client.get("/control-center/today/summary", headers=auth_headers)
    if response.status_code != 200:
        failures.append("Today summary did not return after Chat receipt")
        return
    summary = response.json().get("data", {})
    if receipt.get("receipt_ref") not in set(summary.get("chat_turn_receipt_refs", [])):
        failures.append("Today summary missing Chat turn receipt ref")
    if CHAT_DURABLE_RECEIPT_CONTRACT_REF != summary.get("chat_durable_receipt_contract_ref"):
        failures.append("Today summary missing Chat durable receipt contract ref")
    if not summary.get("chat_handoff_receipt_refs"):
        failures.append("Today summary missing Chat handoff receipt refs")
    timeline_text = str(summary.get("evidence_timeline", "")).lower()
    for fragment in ["chat", "receipt", "handoff"]:
        if fragment not in timeline_text:
            failures.append(f"Evidence Timeline missing Chat {fragment} history")


def _append_receipt_shape_failures(
    failures: list[str],
    payload: dict[str, Any],
    label: str,
) -> None:
    for key in ["receipt_ref", "evidence_ref", "idempotency_key_ref", "payload_fingerprint_ref"]:
        if not payload.get(key):
            failures.append(f"{label} missing {key}")
    for key in DENIED_RESPONSE_FIELDS:
        if payload.get(key) is True:
            failures.append(f"{label} enabled denied authority flag {key}")
    compact = str(payload).lower()
    for fragment in DENIED_RAW_FRAGMENTS:
        if fragment in compact:
            failures.append(f"{label} contains denied raw-content fragment {fragment}")


def _chat_turn_body() -> dict[str, Any]:
    return {
        "turn_ref": "chat-turn:fcc-v1-004",
        "route_ref": "/v1/chat/completions",
        "model_ref": "model-ref:fcc-v1-004-local",
        "runtime_truth": "local-chat-route-answered",
        "auth_truth": "local-bearer-accepted",
        "tool_denial_truth": "tools-functions-streaming-denied",
        "safe_summary_ref": "safe-summary-ref:fcc-v1-004-chat",
        "evidence_refs": ["evidence-ref:fcc-v1-004-chat"],
        "metadata_refs": ["metadata-ref:fcc-v1-004-chat"],
    }


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
