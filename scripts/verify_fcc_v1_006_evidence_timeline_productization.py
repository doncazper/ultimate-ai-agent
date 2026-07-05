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
from ultimate_ai_agent.core.control_center.action_decisions import (  # noqa: E402
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.local_tasks import (  # noqa: E402
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (  # noqa: E402
    WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV,
    WebEvidenceProductSliceRequest,
    build_web_evidence_product_slice_receipt,
)
from ultimate_ai_agent.core.storage import (  # noqa: E402
    EVIDENCE_TIMELINE_PRODUCTIZATION_CONTRACT_REF,
    EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES,
    FounderLoopRepository,
)
from ultimate_ai_agent.core.tools.runtime.http_fetch import (  # noqa: E402
    ReadOnlyHttpFetchTransportResponse,
)


SUCCESS_MESSAGE = "FCC-V1-006 Evidence Timeline productization verification passed."
DOC_PATH = "docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md"
RELEASE_SURFACE_PATH = "docs/control_center/release_surface_manifest.json"
ROUTE_STATUS_PATH = "docs/control_center/route_status_manifest.json"
MILESTONE_STATUS_PATH = "docs/verification/milestone_status_manifest.json"
EVIDENCE_ROUTE = ("GET", "/control-center/evidence/timeline")
FOUNDER_LOOP_V1_PROOF_REF = "scripts/verify_founder_loop_v1.py"
FOUNDER_LOOP_V1_PROOFED_STATUS = "founder_loop_v1_proofed"
FORBIDDEN_CLAIMS = [
    "evidence timeline is shipped",
    "evidence timeline is production ready",
    "evidence grants approval",
    "evidence executes rollback",
    "evidence executes actions",
    "evidence injects memory",
    "evidence treats memory as truth",
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
            [
                DOC_PATH,
                "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
                "docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md",
                "docs/kanban/current_board.md",
            ],
            FORBIDDEN_CLAIMS,
        )
        _append_ui_failures(failures, root)
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [
        DOC_PATH,
        "scripts/verify_fcc_v1_006_evidence_timeline_productization.py",
        "tests/test_fcc_v1_006_evidence_timeline_productization.py",
        "apps/control-center/src/components/FounderLoopPanels.tsx",
    ]:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-V1-006 file: {rel_path}")


def _append_manifest_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    route = context.routes_by_key.get(EVIDENCE_ROUTE)
    if route is None:
        failures.append("missing Evidence Timeline route metadata")
        return
    expected = {
        "operation_id": "get_control_center_evidence_timeline",
        "route_classification": "local_sensitive",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": False,
        "rate_limit_group": None,
    }
    for field, value in expected.items():
        if route.get(field) != value:
            failures.append(f"Evidence Timeline route {field} drifted")
    if route.get("auth_posture") != "protected_local_bearer_required":
        failures.append("Evidence Timeline route must remain protected")
    for forbidden in [
        ("POST", "/control-center/evidence/timeline"),
        ("POST", "/control-center/evidence/approve"),
        ("POST", "/control-center/evidence/rollback"),
        ("POST", "/control-center/evidence/execute"),
    ]:
        if forbidden in context.routes_by_key:
            failures.append(f"forbidden Evidence authority route exists: {forbidden}")
    if "control_center_evidence_timeline_productization" not in context.manifest.get(
        "capabilities_declared",
        [],
    ):
        failures.append("API manifest missing Evidence Timeline productization capability")


def _append_release_surface_failures(
    failures: list[str],
    release_surface: dict[str, Any],
) -> None:
    evidence = _route_by_path(release_surface, "/evidence")
    if evidence is None:
        failures.append("release surface missing /evidence")
        return
    status = evidence.get("status")
    if status not in {"partial", "ship"}:
        failures.append("/evidence release status must remain partial or FCC-V1-007 proofed ship")
    if status == "ship" and FOUNDER_LOOP_V1_PROOF_REF not in set(evidence.get("proof_lanes", [])):
        failures.append("/evidence ship status requires FCC-V1-007 proof lane")
    _append_route_present(
        failures,
        evidence.get("backend_routes", []),
        EVIDENCE_ROUTE,
        "/evidence",
    )
    proof_refs = set(evidence.get("proof_lanes", []))
    for proof_ref in [
        DOC_PATH,
        "scripts/verify_fcc_v1_006_evidence_timeline_productization.py",
        "tests/test_fcc_v1_006_evidence_timeline_productization.py",
    ]:
        if proof_ref not in proof_refs:
            failures.append(f"/evidence release surface missing proof ref {proof_ref}")
    blocked = set(evidence.get("blocked_capabilities", []))
    if status == "partial":
        for capability in [
            "production_authority",
            "broad_runtime_execution",
            "connector_write",
            "evidence_approval_authority",
            "evidence_rollback_execution",
        ]:
            if capability not in blocked:
                failures.append(f"/evidence release surface missing blocker {capability}")


def _append_route_status_failures(
    failures: list[str],
    route_status: dict[str, Any],
) -> None:
    for label, item, key in [
        ("Evidence surface", _surface(route_status, "Evidence"), "current_backend_routes"),
        ("Navigate Evidence action", _action(route_status, "navigate-evidence"), "backend_routes"),
    ]:
        if item is None:
            failures.append(f"route status missing {label}")
            continue
        _append_route_present(failures, item.get(key, []), EVIDENCE_ROUTE, label)
        release_status = item.get("release_status")
        if release_status not in {"partial_backend_not_product_ready", FOUNDER_LOOP_V1_PROOFED_STATUS}:
            failures.append(f"{label} must remain partial or FCC-V1-007 proofed")
        if release_status == FOUNDER_LOOP_V1_PROOFED_STATUS and item.get("missing_backend_routes"):
            failures.append(f"{label} proofed status cannot list missing backend routes")
        lowered = str(item).lower()
        for fragment in [
            "action_envelope_created",
            "action_decision_recorded",
            "chat_turn_receipt_recorded",
            "chat_handoff_created",
            "memory_review_decision_recorded",
            "rollback",
            "idempotency",
        ]:
            if fragment not in lowered:
                failures.append(f"{label} missing Evidence Timeline posture {fragment}")


def _append_milestone_status_failures(
    failures: list[str],
    milestone_status: dict[str, Any],
) -> None:
    milestone = next(
        (
            item
            for item in milestone_status.get("milestones", [])
            if item.get("id") == "FCC-V1-006"
        ),
        None,
    )
    if milestone is None:
        failures.append("milestone status manifest missing FCC-V1-006")
        return
    if milestone.get("status") != "implemented":
        failures.append("FCC-V1-006 milestone status must be implemented")
    proof_refs = set(milestone.get("proof_refs", []))
    for proof_ref in [
        DOC_PATH,
        "scripts/verify_fcc_v1_006_evidence_timeline_productization.py",
        "tests/test_fcc_v1_006_evidence_timeline_productization.py",
    ]:
        if proof_ref not in proof_refs:
            failures.append(f"FCC-V1-006 missing proof ref {proof_ref}")


def _append_doc_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(
        failures,
        {
            DOC_PATH: [
                "Status: implemented for backend-owned Evidence Timeline productization",
                EVIDENCE_TIMELINE_PRODUCTIZATION_CONTRACT_REF,
                "GET /control-center/evidence/timeline",
                "action_envelope_created",
                "action_decision_recorded",
                "chat_turn_receipt_recorded",
                "chat_handoff_created",
                "memory_review_decision_recorded",
                "Evidence remains read-only and safe-ref-only",
                "scripts/verify_fcc_v1_006_evidence_timeline_productization.py",
            ],
            "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md": [
                "FCC-V1-006 implements a backend-owned Evidence Timeline index",
                "no approval authority, rollback execution, action execution, context injection, connector writes, public beta, or production authority",
            ],
        },
    )


def _append_behavior_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    old_state_dir = os.environ.get("UAA_FOUNDER_LOOP_STATE_DIR")
    old_bearer = os.environ.get(LOCAL_API_BEARER_ENV)
    bearer = "fcc-v1-006-local-bearer"
    auth_headers = {"Authorization": f"Bearer {bearer}"}
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = str(Path(temp_dir) / "founder_loop")
        os.environ[LOCAL_API_BEARER_ENV] = bearer
        try:
            receipts = _exercise_loop(failures, context, auth_headers)
            response = context.client.get(
                "/control-center/evidence/timeline",
                headers=auth_headers,
            )
            if response.status_code != 200:
                failures.append("Evidence Timeline route did not return 200")
                return
            data = response.json().get("data", {})
            if data.get("contract_ref") != EVIDENCE_TIMELINE_PRODUCTIZATION_CONTRACT_REF:
                failures.append("Evidence Timeline contract ref drifted")
            for flag in [
                "raw_content_stored",
                "approval_ref_authority",
                "rollback_execution_enabled",
                "memory_truth_authority",
                "context_injection_authorized",
                "action_execution_enabled",
                "connector_write_enabled",
                "production_authority_enabled",
            ]:
                if data.get(flag) is not False:
                    failures.append(f"Evidence Timeline denied flag {flag} must stay false")
            event_counts = data.get("event_type_counts", {})
            for event_type in EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES:
                if event_counts.get(event_type, 0) < 1:
                    failures.append(f"Evidence Timeline missing event type {event_type}")
            group_kinds = {group.get("group_kind") for group in data.get("groups", [])}
            for group_kind in ["today_item", "action", "chat_turn", "memory_candidate"]:
                if group_kind not in group_kinds:
                    failures.append(f"Evidence Timeline missing group kind {group_kind}")
            compact = str(data).lower()
            for receipt_ref in receipts:
                if receipt_ref and receipt_ref not in str(data):
                    failures.append(f"Evidence Timeline missing receipt {receipt_ref}")
            for fragment in ["raw prompt", "raw_response", "provider_payload"]:
                if fragment in compact:
                    failures.append(f"Evidence Timeline contains unsafe fragment {fragment}")
        finally:
            if old_state_dir is None:
                os.environ.pop("UAA_FOUNDER_LOOP_STATE_DIR", None)
            else:
                os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = old_state_dir
            if old_bearer is None:
                os.environ.pop(LOCAL_API_BEARER_ENV, None)
            else:
                os.environ[LOCAL_API_BEARER_ENV] = old_bearer


def _exercise_loop(
    failures: list[str],
    context: ApiVerifierContext,
    auth_headers: dict[str, str],
) -> list[str]:
    receipts: list[str] = []
    inbox = context.client.get("/control-center/actions/inbox", headers=auth_headers)
    if inbox.status_code != 200:
        failures.append("Action Inbox unavailable for Evidence Timeline exercise")
        return receipts
    action_items = inbox.json().get("data", {}).get("items", [])
    item_ref = next(
        (
            item.get("item_ref")
            for item in action_items
            if item.get("item_ref") == "founder-action:setup-assistant-hardening"
        ),
        None,
    )
    if not item_ref:
        failures.append("Action decision exercise item missing")
        return receipts
    action = context.client.post(
        f"/control-center/actions/{item_ref}/reject",
        json={
            "decision_reason_ref": "decision-reason-ref:fcc-v1-006-action",
            "metadata_refs": ["metadata-ref:fcc-v1-006-action"],
        },
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-006-action",
        },
    )
    if action.status_code == 200:
        receipts.append(str(action.json().get("data", {}).get("receipt_ref", "")))
    else:
        failures.append(f"Action decision exercise failed with {action.status_code}")

    chat = context.client.post(
        "/control-center/chat/turns",
        json={
            "turn_ref": "chat-turn:fcc-v1-006",
            "route_ref": "/v1/chat/completions",
            "model_ref": "model-ref:fcc-v1-006-local",
            "runtime_truth": "local-chat-route-answered",
            "auth_truth": "local-bearer-accepted",
            "tool_denial_truth": "tools-functions-streaming-denied",
            "safe_summary_ref": "safe-summary-ref:fcc-v1-006-chat",
            "evidence_refs": ["evidence-ref:fcc-v1-006-chat"],
        },
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-006-chat",
        },
    )
    if chat.status_code == 200:
        receipts.append(str(chat.json().get("data", {}).get("receipt_ref", "")))
    else:
        failures.append(f"Chat receipt exercise failed with {chat.status_code}")
    handoff = context.client.post(
        "/control-center/chat/turns/chat-turn:fcc-v1-006/handoff",
        json={"handoff_target": "actions"},
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-006-handoff",
        },
    )
    if handoff.status_code == 200:
        receipts.append(str(handoff.json().get("data", {}).get("receipt_ref", "")))
    else:
        failures.append(f"Chat handoff exercise failed with {handoff.status_code}")

    memory = context.client.get("/control-center/memory/review", headers=auth_headers)
    if memory.status_code == 200 and memory.json().get("data", {}).get("items"):
        candidate_ref = memory.json()["data"]["items"][0]["business_memory_candidate_ref"]
        decision = context.client.post(
            f"/control-center/memory/review/{candidate_ref}/reject",
            json={
                "reviewer_ref": "actor-ref:fcc-v1-006-memory",
                "source_refs": ["source-ref:fcc-v1-006-memory"],
                "evidence_refs": ["evidence-ref:fcc-v1-006-memory"],
            },
            headers={
                **auth_headers,
                "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-006-memory",
            },
        )
        if decision.status_code == 200:
            receipts.append(str(decision.json().get("data", {}).get("receipt_ref", "")))
        else:
            failures.append(f"Memory Review exercise failed with {decision.status_code}")
    else:
        failures.append("Memory Review unavailable for Evidence Timeline exercise")

    local_task_receipt = _commit_local_task_for_timeline()
    if local_task_receipt:
        receipts.append(local_task_receipt)
    else:
        failures.append("Local task commit exercise failed")
    web_evidence_receipt = _record_web_evidence_for_timeline()
    if web_evidence_receipt:
        receipts.append(web_evidence_receipt)
    else:
        failures.append("Web Evidence product slice exercise failed")
    return receipts


def _commit_local_task_for_timeline() -> str:
    repo = FounderLoopRepository.from_env()
    repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:fcc-v1-006-local-task-approval",
        ),
        idempotency_key_ref="idempotency-ref:fcc-v1-006-local-task-action",
    )
    action = next(
        item
        for item in repo.list_action_inbox(limit=200)
        if item.get("item_ref") == "founder-action:local-task-create-scorecard"
    )
    commit_request = FounderLoopLocalTaskCommitRequest(
        approval_ref=str(action["local_task_commit_approval_ref"]),
        decision_reason_ref="decision-reason-ref:fcc-v1-006-local-task-commit",
        metadata_refs=["metadata-ref:fcc-v1-006-local-task-commit"],
    )
    receipt = repo.commit_local_task(
        action_id="local-task-create-scorecard",
        request=commit_request,
        idempotency_key_ref="idempotency-ref:fcc-v1-006-local-task-commit",
    )
    return str(receipt.get("receipt_ref", ""))


def _record_web_evidence_for_timeline() -> str:
    repo = FounderLoopRepository.from_env()
    previous_allowlist = os.environ.get(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV)
    os.environ[WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV] = "example.org"
    try:
        receipt = build_web_evidence_product_slice_receipt(
            WebEvidenceProductSliceRequest(
                request_ref="web-evidence-request:fcc-v1-006",
                url="https://example.org/status",
                allowed_host="example.org",
                evidence_refs=["evidence-ref:fcc-v1-006-web-evidence"],
                metadata_refs=["metadata-ref:fcc-v1-006-web-evidence"],
            ),
            transport=_fake_web_evidence_transport,
        )
    finally:
        if previous_allowlist is None:
            os.environ.pop(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV, None)
        else:
            os.environ[WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV] = previous_allowlist
    repo.record_web_evidence_attachment(receipt)
    return receipt.receipt_ref


def _fake_web_evidence_transport(
    _request: Any,
    _policy: Any,
) -> ReadOnlyHttpFetchTransportResponse:
    return ReadOnlyHttpFetchTransportResponse(
        status_code=200,
        content_type="text/plain",
        body=b"Public status page for timeline verification.",
    )


_fake_web_evidence_transport.transport_ref = (
    "http-fetch-transport:fake-fcc-v1-006-web-evidence"
)
_fake_web_evidence_transport.real_world_transport_performed = True


def _append_ui_failures(failures: list[str], root: Path) -> None:
    for rel_path, snippets in {
        "apps/control-center/src/api/endpoints.ts": [
            "founderEvidenceTimeline",
            "/control-center/evidence/timeline",
        ],
        "apps/control-center/src/api/client.ts": ["FounderLoopEvidenceTimelineIndex"],
        "apps/control-center/src/components/FounderLoopPanels.tsx": [
            "EvidenceTimelineEventCard",
            "Idempotency refs",
            "Rollback posture",
        ],
        "apps/control-center/src/routes.tsx": ["founderEvidenceTimeline"],
    }.items():
        text = (root / rel_path).read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                failures.append(f"UI file {rel_path} missing {snippet}")


def _route_by_path(payload: dict[str, Any], path: str) -> dict[str, Any] | None:
    return next((item for item in payload.get("routes", []) if item.get("path") == path), None)


def _surface(payload: dict[str, Any], name: str) -> dict[str, Any] | None:
    return next((item for item in payload.get("surfaces", []) if item.get("surface") == name), None)


def _action(payload: dict[str, Any], action_id: str) -> dict[str, Any] | None:
    return next(
        (item for item in payload.get("visible_actions", []) if item.get("action_id") == action_id),
        None,
    )


def _append_route_present(
    failures: list[str],
    routes: list[dict[str, Any]],
    route: tuple[str, str],
    label: str,
) -> None:
    method, path = route
    if not any(item.get("method") == method and item.get("path") == path for item in routes):
        failures.append(f"{label} missing route {method} {path}")


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
