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
from ultimate_ai_agent.core.authority import (  # noqa: E402
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (  # noqa: E402
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.storage import (  # noqa: E402
    EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES,
    FounderLoopRepository,
)
from ultimate_ai_agent.core.tools.runtime.http_fetch import (  # noqa: E402
    ReadOnlyHttpFetchTransportResponse,
)


SUCCESS_MESSAGE = "FCC-V1-007 Founder Loop V1 promotion proof verification passed."
DOC_PATH = "docs/control_center/FCC_V1_007_PROMOTION_AND_PROOF_LANE.md"
RELEASE_SURFACE_PATH = "docs/control_center/release_surface_manifest.json"
ROUTE_STATUS_PATH = "docs/control_center/route_status_manifest.json"
MILESTONE_STATUS_PATH = "docs/verification/milestone_status_manifest.json"
PROOF_SCRIPT = "scripts/verify_founder_loop_v1.py"
PROOF_TEST = "tests/test_founder_loop_v1_proof_lane.py"
PROOFED_ROUTE_STATUS = "founder_loop_v1_proofed"
PROMOTED_ROUTES = {"/actions", "/chat", "/memory", "/evidence"}
BLOCKED_OR_PARTIAL_ROUTES = {"/inbox": "partial", "/settings": "partial", "/models": "partial"}
PROMOTED_SURFACES = {"Action Inbox", "Chat Local Operator", "Memory Review", "Evidence"}
PROMOTED_ACTIONS = {
    "navigate-actions-inbox",
    "navigate-chat-shell",
    "navigate-memory",
    "navigate-evidence",
}
MUTATING_ROUTE_RATE_LIMITS = {
    ("POST", "/control-center/today/action-envelope"): "today_to_action_envelope",
    ("POST", "/control-center/actions/{action_id}/approve"): "action_decision",
    ("POST", "/control-center/actions/{action_id}/edit"): "action_decision",
    ("POST", "/control-center/actions/{action_id}/reject"): "action_decision",
    ("POST", "/control-center/actions/{action_id}/defer"): "action_decision",
    ("POST", "/control-center/actions/{action_id}/local-task/commit"): "action_decision",
    ("POST", "/control-center/chat/turns"): "chat_durable_receipt",
    ("POST", "/control-center/chat/turns/{turn_ref}/handoff"): "chat_durable_receipt",
    ("POST", "/control-center/memory/review/{candidate_ref}/accept"): "memory_review_decision",
    ("POST", "/control-center/memory/review/{candidate_ref}/correct"): "memory_review_decision",
    ("POST", "/control-center/memory/review/{candidate_ref}/reject"): "memory_review_decision",
}
READ_ROUTE_KEYS = {
    ("GET", "/control-center/actions/inbox"),
    ("GET", "/control-center/actions/{action_id}/receipt"),
    ("GET", "/control-center/chat/turns/{turn_ref}/receipt"),
    ("GET", "/control-center/memory/review"),
    ("GET", "/control-center/evidence/timeline"),
}
FORBIDDEN_CLAIMS = [
    "public beta ready",
    "public release ready",
    "production ready",
    "ready for production",
    "broad runtime execution enabled",
    "connector writes enabled",
    "memory context injection enabled",
    "model output is authority",
    "evidence grants approval",
    "approved actions execute",
]
UNSAFE_TIMELINE_FRAGMENTS = [
    "raw prompt",
    "raw response",
    "provider_payload",
    "raw_provider",
    "credential",
    "secret",
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
    _append_release_surface_failures(failures, release_surface)
    _append_route_status_failures(failures, route_status)
    _append_route_metadata_failures(failures, context)
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
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [DOC_PATH, PROOF_SCRIPT, PROOF_TEST, RELEASE_SURFACE_PATH, ROUTE_STATUS_PATH]:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-V1-007 file: {rel_path}")


def _append_release_surface_failures(
    failures: list[str], release_surface: dict[str, Any]
) -> None:
    for flag in [
        "release_claims_enabled",
        "runtime_authority_added",
        "public_beta_claim_enabled",
        "production_readiness_claim_enabled",
    ]:
        if release_surface.get(flag) is not False:
            failures.append(f"release surface must keep denied flag false: {flag}")
    routes = {
        route.get("path"): route
        for route in release_surface.get("routes", [])
        if isinstance(route, dict)
    }
    for path in sorted(PROMOTED_ROUTES):
        route = routes.get(path)
        if route is None:
            failures.append(f"release surface missing promoted route {path}")
            continue
        if route.get("status") != "ship":
            failures.append(f"{path} must be ship only for FCC-V1-007 proofed route behavior")
        if route.get("blocked_capabilities"):
            failures.append(f"{path} ship route cannot list blocked capabilities")
        if not route.get("backend_routes"):
            failures.append(f"{path} ship route must list backend route refs")
        proof_lanes = set(route.get("proof_lanes", []))
        for proof in {PROOF_SCRIPT, PROOF_TEST, DOC_PATH}:
            if proof not in proof_lanes:
                failures.append(f"{path} missing FCC-V1-007 proof lane {proof}")
    for path, expected in BLOCKED_OR_PARTIAL_ROUTES.items():
        route = routes.get(path)
        if route is None:
            failures.append(f"release surface missing route {path}")
            continue
        if route.get("status") != expected:
            failures.append(f"{path} must remain {expected} during FCC-V1-007")
    today = routes.get("/today")
    if today and today.get("status") != "partial":
        failures.append("/today must remain partial; FCC-V1-007 promotes only proven route surfaces")


def _append_route_status_failures(
    failures: list[str], route_status: dict[str, Any]
) -> None:
    if route_status.get("release_status_taxonomy_map", {}).get(PROOFED_ROUTE_STATUS) != "shipped":
        failures.append("route status manifest must map founder_loop_v1_proofed to shipped")
    if PROOFED_ROUTE_STATUS not in set(route_status.get("allowed_release_statuses", [])):
        failures.append("route status manifest missing founder_loop_v1_proofed status")
    for surface_name in PROMOTED_SURFACES:
        surface = _surface(route_status, surface_name)
        if surface is None:
            failures.append(f"route status missing promoted surface {surface_name}")
            continue
        if surface.get("release_status") != PROOFED_ROUTE_STATUS:
            failures.append(f"{surface_name} must use founder_loop_v1_proofed")
        if surface.get("missing_backend_routes"):
            failures.append(f"{surface_name} proofed status cannot list missing backend routes")
        _append_no_overclaim_text(failures, str(surface), surface_name)
    for action_id in PROMOTED_ACTIONS:
        action = _action(route_status, action_id)
        if action is None:
            failures.append(f"route status missing promoted action {action_id}")
            continue
        if action.get("release_status") != PROOFED_ROUTE_STATUS:
            failures.append(f"{action_id} must use founder_loop_v1_proofed")
        if action.get("missing_backend_routes"):
            failures.append(f"{action_id} proofed status cannot list missing backend routes")
        _append_no_overclaim_text(failures, str(action), action_id)
    for surface_name in ["Inbox"]:
        surface = _surface(route_status, surface_name)
        if surface and surface.get("release_status") != "status_available_not_completion":
            failures.append(f"{surface_name} must remain status-only")
    settings = _surface(route_status, "Settings")
    if settings and settings.get("release_status") != "status_available_not_completion":
        failures.append("Settings must remain status-only")
    models = _surface(route_status, "Models")
    if models and models.get("release_status") == PROOFED_ROUTE_STATUS:
        failures.append("Models must not be promoted by FCC-V1-007")


def _append_route_metadata_failures(
    failures: list[str], context: ApiVerifierContext
) -> None:
    for key, rate_group in MUTATING_ROUTE_RATE_LIMITS.items():
        route = context.routes_by_key.get(key)
        if route is None:
            failures.append(f"missing promoted mutating route metadata: {key}")
            continue
        if route.get("route_classification") != "mutating_requires_authority":
            failures.append(f"{key} must remain mutating_requires_authority")
        if route.get("auth_posture") != "protected_local_bearer_required":
            failures.append(f"{key} must remain bearer protected")
        if route.get("approval_posture") != "required_before_mutation_authority":
            failures.append(f"{key} must keep approval posture")
        if route.get("idempotency_required") is not True:
            failures.append(f"{key} must require idempotency")
        if route.get("rate_limit_group") != rate_group:
            failures.append(f"{key} rate-limit group drifted")
    for key in READ_ROUTE_KEYS:
        route = context.routes_by_key.get(key)
        if route is None:
            failures.append(f"missing promoted read route metadata: {key}")
            continue
        if route.get("route_classification") != "local_sensitive":
            failures.append(f"{key} must remain local_sensitive")
        if route.get("auth_posture") != "protected_local_bearer_required":
            failures.append(f"{key} must remain bearer protected")
        if route.get("idempotency_required") is not False:
            failures.append(f"{key} must not require idempotency")
    for forbidden in [
        ("POST", "/control-center/actions/{action_id}/execute"),
        ("POST", "/control-center/chat/turns/{turn_ref}/execute"),
        ("POST", "/control-center/memory/review/{candidate_ref}/write"),
        ("POST", "/control-center/evidence/rollback"),
    ]:
        if forbidden in context.routes_by_key:
            failures.append(f"forbidden promoted-surface authority route exists: {forbidden}")


def _append_milestone_status_failures(
    failures: list[str], milestone_status: dict[str, Any]
) -> None:
    milestone = next(
        (
            item
            for item in milestone_status.get("milestones", [])
            if item.get("id") == "FCC-V1-007"
        ),
        None,
    )
    if milestone is None:
        failures.append("milestone status manifest missing FCC-V1-007")
        return
    if milestone.get("status") != "implemented":
        failures.append("FCC-V1-007 milestone status must be implemented")
    proof_refs = set(milestone.get("proof_refs", []))
    for proof in {DOC_PATH, PROOF_SCRIPT, PROOF_TEST}:
        if proof not in proof_refs:
            failures.append(f"FCC-V1-007 milestone status missing proof ref {proof}")


def _append_doc_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(
        failures,
        {
            DOC_PATH: [
                "Status: implemented for Founder Loop V1 promotion proof",
                "founder_loop_v1_proofed",
                "not public release or production readiness",
                "no action execution",
                "no context injection",
                "no connector writes",
            ],
            "docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md": [
                "FCC-V1-007 - Promotion And Proof Lane",
                "Status: Implemented",
                "scripts/verify_founder_loop_v1.py",
            ],
        },
    )


def _append_behavior_failures(
    failures: list[str], context: ApiVerifierContext
) -> None:
    old_state_dir = os.environ.get("UAA_FOUNDER_LOOP_STATE_DIR")
    old_authority_state_dir = os.environ.get(AUTHORITY_STATE_DIR_ENV)
    old_bearer = os.environ.get(LOCAL_API_BEARER_ENV)
    bearer = "fcc-v1-007-local-bearer"
    auth_headers = {"Authorization": f"Bearer {bearer}"}
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = str(Path(temp_dir) / "founder_loop")
        os.environ[AUTHORITY_STATE_DIR_ENV] = str(Path(temp_dir) / "authority")
        os.environ[LOCAL_API_BEARER_ENV] = bearer
        try:
            receipts = _exercise_founder_loop(failures, context, auth_headers)
            _append_timeline_failures(failures, context, receipts, auth_headers)
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


def _exercise_founder_loop(
    failures: list[str], context: ApiVerifierContext, auth_headers: dict[str, str]
) -> list[str]:
    receipts: list[str] = []
    inbox = context.client.get("/control-center/actions/inbox", headers=auth_headers)
    items = inbox.json().get("data", {}).get("items", []) if inbox.status_code == 200 else []
    if not items:
        failures.append("Action Inbox proof exercise found no action candidates")
        return receipts
    item_ref = next(
        (
            item.get("item_ref")
            for item in items
            if item.get("item_ref") != "founder-action:local-task-create-scorecard"
        ),
        items[0].get("item_ref"),
    )
    action = context.client.post(
        f"/control-center/actions/{item_ref}/reject",
        json={"decision_reason_ref": "decision-reason-ref:fcc-v1-007-action"},
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-007-action",
        },
    )
    _append_receipt_from_response(failures, action, receipts, "Action decision")
    chat = context.client.post(
        "/control-center/chat/turns",
        json={
            "turn_ref": "chat-turn:fcc-v1-007",
            "route_ref": "/v1/chat/completions",
            "model_ref": "model-ref:fcc-v1-007-local",
            "runtime_truth": "local-chat-route-answered",
            "auth_truth": "local-bearer-accepted",
            "tool_denial_truth": "tools-functions-streaming-denied",
            "safe_summary_ref": "safe-summary-ref:fcc-v1-007-chat",
            "evidence_refs": ["evidence-ref:fcc-v1-007-chat"],
        },
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-007-chat",
        },
    )
    _append_receipt_from_response(failures, chat, receipts, "Chat turn")
    handoff = context.client.post(
        "/control-center/chat/turns/chat-turn:fcc-v1-007/handoff",
        json={"handoff_target": "actions"},
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-007-handoff",
        },
    )
    _append_receipt_from_response(failures, handoff, receipts, "Chat handoff")
    memory = context.client.get("/control-center/memory/review", headers=auth_headers)
    memory_items = (
        memory.json().get("data", {}).get("items", []) if memory.status_code == 200 else []
    )
    if not memory_items:
        failures.append("Memory Review proof exercise found no candidates")
        return receipts
    candidate_ref = memory_items[0]["business_memory_candidate_ref"]
    decision = context.client.post(
        f"/control-center/memory/review/{candidate_ref}/reject",
        json={
            "reviewer_ref": "actor-ref:fcc-v1-007-memory",
            "source_refs": ["source-ref:fcc-v1-007-memory"],
            "evidence_refs": ["evidence-ref:fcc-v1-007-memory"],
        },
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-007-memory",
        },
    )
    _append_receipt_from_response(failures, decision, receipts, "Memory Review")
    _issue_workspace_write_lease_for_proof()
    local_task_action = _approve_local_task_for_proof()
    local_task = context.client.post(
        "/control-center/actions/local-task-create-scorecard/local-task/commit",
        json=FounderLoopLocalTaskCommitRequest(
            approval_ref=str(local_task_action["local_task_commit_approval_ref"]),
            decision_reason_ref="decision-reason-ref:fcc-v1-007-local-task-commit",
            metadata_refs=["metadata-ref:fcc-v1-007-local-task-commit"],
        ).model_dump(mode="json"),
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-007-local-task-commit",
        },
    )
    _append_receipt_from_response(failures, local_task, receipts, "Local task commit")
    web_evidence_receipt = _record_web_evidence_for_proof()
    if web_evidence_receipt:
        receipts.append(web_evidence_receipt)
    else:
        failures.append("Web Evidence proof exercise failed")
    return receipts


def _approve_local_task_for_proof() -> dict[str, Any]:
    repo = FounderLoopRepository.from_env()
    repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:fcc-v1-007-local-task-approval",
        ),
        idempotency_key_ref="idempotency-ref:fcc-v1-007-local-task-action",
    )
    return next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )


def _record_web_evidence_for_proof() -> str:
    repo = FounderLoopRepository.from_env()
    previous_allowlist = os.environ.get(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV)
    os.environ[WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV] = "example.org"
    try:
        receipt = build_web_evidence_product_slice_receipt(
            WebEvidenceProductSliceRequest(
                request_ref="web-evidence-request:fcc-v1-007",
                url="https://example.org/status",
                allowed_host="example.org",
                evidence_refs=["evidence-ref:fcc-v1-007-web-evidence"],
                metadata_refs=["metadata-ref:fcc-v1-007-web-evidence"],
            ),
            transport=_fake_web_evidence_transport,
            active_authority_leases=[_browser_read_lease()],
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
        body=b"Public status page for proof verification.",
    )


_fake_web_evidence_transport.transport_ref = (
    "http-fetch-transport:fake-fcc-v1-007-web-evidence"
)
_fake_web_evidence_transport.real_world_transport_performed = True


def _issue_workspace_write_lease_for_proof() -> None:
    issue_authority_lease_with_test_approval(
        AuthorityLeaseStore(),
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={
                AuthorityDomain.workspace: [AuthorityCapability.write]
            },
            decision_reason_ref="reason-ref:fcc-v1-007-local-task-authority",
            safe_summary=(
                "Verifier lease grants Workspace write for exact local task commit."
            ),
        ),
        idempotency_ref="idempotency-ref:fcc-v1-007-local-task-authority",
        approval_ref="approval-ref:verifier:fcc-v1-007-local-task-authority",
    )


def _browser_read_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:founder-loop-web-evidence-verify",
        mode=TrustMode.read_only,
        domains={AuthorityDomain.browser: [AuthorityCapability.read]},
        constraints={
            "web_evidence_lane_ref": "lane-ref:web-evidence-product-slice",
            "https_get_only": True,
            "browser_actions_allowed": False,
        },
        safe_summary=(
            "Verifier lease grants Browser read authority for one "
            "Founder Loop web evidence preview."
        ),
    )


def _append_receipt_from_response(
    failures: list[str], response: Any, receipts: list[str], label: str
) -> None:
    if response.status_code != 200:
        failures.append(f"{label} proof exercise failed with {response.status_code}")
        return
    receipt_ref = str(response.json().get("data", {}).get("receipt_ref", ""))
    if not receipt_ref:
        failures.append(f"{label} proof exercise did not return receipt_ref")
        return
    receipts.append(receipt_ref)


def _append_timeline_failures(
    failures: list[str],
    context: ApiVerifierContext,
    receipts: list[str],
    auth_headers: dict[str, str],
) -> None:
    response = context.client.get("/control-center/evidence/timeline", headers=auth_headers)
    if response.status_code != 200:
        failures.append(f"Evidence Timeline proof route failed with {response.status_code}")
        return
    data = response.json().get("data", {})
    events_text = str(data.get("events", [])).lower()
    if set(data.get("event_types", [])) != set(EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES):
        failures.append("Evidence Timeline proof event types drifted")
    for event_type in EVIDENCE_TIMELINE_PRODUCTIZED_EVENT_TYPES:
        if data.get("event_type_counts", {}).get(event_type, 0) < 1:
            failures.append(f"Evidence Timeline missing proof event type {event_type}")
    for receipt_ref in receipts:
        if receipt_ref and receipt_ref not in str(data.get("events", [])):
            failures.append(f"Evidence Timeline missing receipt ref {receipt_ref}")
    for fragment in UNSAFE_TIMELINE_FRAGMENTS:
        if fragment in events_text:
            failures.append(f"Evidence Timeline contains unsafe fragment {fragment!r}")
    for flag in [
        "approval_ref_authority",
        "rollback_execution_enabled",
        "context_injection_authorized",
        "action_execution_enabled",
        "production_authority_enabled",
    ]:
        if data.get(flag) is not False:
            failures.append(f"Evidence Timeline proof must keep {flag}=false")


def _append_no_overclaim_text(failures: list[str], text: str, label: str) -> None:
    compact = " ".join(text.lower().split())
    for forbidden in FORBIDDEN_CLAIMS:
        if forbidden in compact:
            failures.append(f"{label} contains forbidden proof overclaim {forbidden!r}")


def _surface(route_status: dict[str, Any], name: str) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in route_status.get("surfaces", [])
            if item.get("surface") == name
        ),
        None,
    )


def _action(route_status: dict[str, Any], action_id: str) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in route_status.get("visible_actions", [])
            if item.get("action_id") == action_id
        ),
        None,
    )


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
