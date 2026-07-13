#!/usr/bin/env python3
from __future__ import annotations

import os
import json
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
from ultimate_ai_agent.core.authority import (  # noqa: E402
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (  # noqa: E402
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.memory import (  # noqa: E402
    FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
    MEMORY_REVIEW_LIFECYCLE_SCOPE_REF,
    MEMORY_REVIEW_RECEIPT_SCOPE_REF,
    MEMORY_REVIEW_WRITE_ROLLBACK_BLOCKED_REF,
    MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


SUCCESS_MESSAGE = "FCC-V1-005 Memory Review decision receipt verification passed."
DOC_PATH = "docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md"
RELEASE_SURFACE_PATH = "docs/control_center/release_surface_manifest.json"
ROUTE_STATUS_PATH = "docs/control_center/route_status_manifest.json"
MILESTONE_STATUS_PATH = "docs/verification/milestone_status_manifest.json"
MEMORY_REVIEW_GET_ROUTE = ("GET", "/control-center/memory/review")
MEMORY_REVIEW_RECEIPT_ROUTE = (
    "GET",
    "/control-center/memory/review/{candidate_ref}/receipt",
)
FOUNDER_LOOP_V1_PROOF_REF = "scripts/verify_founder_loop_v1.py"
FOUNDER_LOOP_V1_PROOFED_STATUS = "founder_loop_v1_proofed"
MEMORY_REVIEW_DECISION_ROUTES = {
    ("POST", "/control-center/memory/review/{candidate_ref}/accept"): {
        "operation_id": "post_control_center_memory_review_candidate_ref_accept",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "memory_review_decision",
    },
    ("POST", "/control-center/memory/review/{candidate_ref}/correct"): {
        "operation_id": "post_control_center_memory_review_candidate_ref_correct",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "memory_review_decision",
    },
    ("POST", "/control-center/memory/review/{candidate_ref}/reject"): {
        "operation_id": "post_control_center_memory_review_candidate_ref_reject",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "memory_review_decision",
    },
    ("POST", "/control-center/memory/review/{candidate_ref}/defer"): {
        "operation_id": "post_control_center_memory_review_candidate_ref_defer",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "memory_review_decision",
    },
    ("POST", "/control-center/memory/review/{candidate_ref}/merge"): {
        "operation_id": "post_control_center_memory_review_candidate_ref_merge",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "memory_review_decision",
    },
    ("POST", "/control-center/memory/review/{candidate_ref}/supersede"): {
        "operation_id": "post_control_center_memory_review_candidate_ref_supersede",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "memory_review_decision",
    },
    ("POST", "/control-center/memory/review/{candidate_ref}/expire"): {
        "operation_id": "post_control_center_memory_review_candidate_ref_expire",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "memory_review_decision",
    },
    ("POST", "/control-center/memory/review/{candidate_ref}/forget-request"): {
        "operation_id": "post_control_center_memory_review_candidate_ref_forget_request",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "memory_review_decision",
    },
    ("POST", "/control-center/memory/review/manual-candidate"): {
        "operation_id": "post_control_center_memory_review_manual_candidate",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "memory_review_decision",
    },
}
ROUTES = {
    MEMORY_REVIEW_GET_ROUTE: {
        "operation_id": "get_control_center_memory_review",
        "route_classification": "local_sensitive",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": False,
        "rate_limit_group": None,
    },
    MEMORY_REVIEW_RECEIPT_ROUTE: {
        "operation_id": "get_control_center_memory_review_candidate_ref_receipt",
        "route_classification": "local_sensitive",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": False,
        "rate_limit_group": None,
    },
    **MEMORY_REVIEW_DECISION_ROUTES,
}
FORBIDDEN_CLAIMS = [
    "memory review decisions are shipped",
    "memory review is production ready",
    "memory review grants context injection",
    "memory review writes crm",
    "memory review executes actions",
    "accept decision injects context",
    "accept decision is source truth",
]
DENIED_RECEIPT_FIELDS = [
    "context_injection_authorized",
    "connector_write_authorized",
    "external_crm_sync_authorized",
    "account_sync_authorized",
    "automatic_action_execution_authorized",
    "model_provider_authority_allowed",
    "source_truth_authority",
    "memory_truth_authority",
    "production_authority_enabled",
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
        _append_ui_label_failures(failures, root)
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [
        DOC_PATH,
        "scripts/verify_fcc_v1_005_memory_review_decisions.py",
        "tests/test_fcc_v1_005_memory_review_decisions.py",
        "apps/control-center/src/components/FounderLoopPanels.tsx",
    ]:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-V1-005 file: {rel_path}")


def _append_manifest_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    for key, expected in ROUTES.items():
        route = context.routes_by_key.get(key)
        if route is None:
            failures.append(f"missing Memory Review decision route metadata {key}")
            continue
        for field, value in expected.items():
            if route.get(field) != value:
                failures.append(f"Memory Review route {key} {field} drifted")
        if key[0] == "POST" and route.get("approval_posture") != "required_before_mutation_authority":
            failures.append(f"Memory Review route {key} must keep approval posture")
    forbidden_routes = [
        ("POST", "/control-center/memory/review/{candidate_ref}/write"),
        ("POST", "/control-center/memory/review/{candidate_ref}/inject"),
        ("POST", "/control-center/memory/review/{candidate_ref}/sync-crm"),
        ("POST", "/control-center/memory/review/{candidate_ref}/execute"),
    ]
    for key in forbidden_routes:
        if key in context.routes_by_key:
            failures.append(f"forbidden Memory Review authority route exists: {key}")


def _append_release_surface_failures(
    failures: list[str],
    release_surface: dict[str, Any],
) -> None:
    memory = _route_by_path(release_surface, "/memory")
    if memory is None:
        failures.append("release surface missing /memory")
        return
    status = memory.get("status")
    if status not in {"partial", "ship"}:
        failures.append("/memory release status must remain partial or FCC-V1-007 proofed ship")
    if status == "ship" and FOUNDER_LOOP_V1_PROOF_REF not in set(memory.get("proof_lanes", [])):
        failures.append("/memory ship status requires FCC-V1-007 proof lane")
    for route in ROUTES:
        _append_route_present(failures, memory.get("backend_routes", []), route, "/memory")
    proof_refs = set(memory.get("proof_lanes", []))
    for proof_ref in [
        DOC_PATH,
        __file__.removeprefix(str(ROOT) + "/"),
        "tests/test_fcc_v1_005_memory_review_decisions.py",
    ]:
        if proof_ref not in proof_refs:
            failures.append(f"/memory release surface missing proof ref {proof_ref}")
    blocked = set(memory.get("blocked_capabilities", []))
    if status == "partial":
        for capability in [
            "memory_context_injection",
            "memory_truth_authority",
            "memory_connector_write",
            "memory_external_crm_sync",
            "memory_action_execution",
            "production_authority",
        ]:
            if capability not in blocked:
                failures.append(f"/memory release surface missing blocked capability {capability}")


def _append_route_status_failures(
    failures: list[str],
    route_status: dict[str, Any],
) -> None:
    for label, item, key in [
        ("Memory Review surface", _surface(route_status, "Memory Review"), "current_backend_routes"),
        ("Navigate Memory visible action", _action(route_status, "navigate-memory"), "backend_routes"),
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
        for fragment in ["receipt", "idempotency", "context injection", "crm sync"]:
            if fragment not in lowered:
                failures.append(f"{label} missing Memory Review decision posture {fragment}")


def _append_milestone_status_failures(
    failures: list[str],
    milestone_status: dict[str, Any],
) -> None:
    milestone = next(
        (
            item
            for item in milestone_status.get("milestones", [])
            if item.get("id") == "FCC-V1-005"
        ),
        None,
    )
    if milestone is None:
        failures.append("milestone status manifest missing FCC-V1-005")
        return
    if milestone.get("status") != "implemented":
        failures.append("FCC-V1-005 milestone status must be implemented")
    proof_refs = set(milestone.get("proof_refs", []))
    for required in {
        DOC_PATH,
        __file__.removeprefix(str(ROOT) + "/"),
        "tests/test_fcc_v1_005_memory_review_decisions.py",
    }:
        if required not in proof_refs:
            failures.append(f"FCC-V1-005 missing proof ref {required}")


def _append_doc_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(
        failures,
        {
            DOC_PATH: [
                "Status: implemented for backend-owned Memory Review decision receipts",
                FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
                "GET /control-center/memory/review",
                "GET /control-center/memory/review/{candidate_ref}/receipt",
                "POST /control-center/memory/review/{candidate_ref}/accept",
                "POST /control-center/memory/review/{candidate_ref}/correct",
                "POST /control-center/memory/review/{candidate_ref}/reject",
                "POST /control-center/memory/review/{candidate_ref}/expire",
                "reviewed_recall_record_ref",
                "LocalMemoryStore",
                "Correct stores corrected_summary_ref; correction receipts remain content-free",
                "Accept records reviewed recall only; it is not truth authority",
                "scripts/verify_fcc_v1_005_memory_review_decisions.py",
            ],
            "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md": [
                "Memory Review decisions are backend-owned and receipt-backed",
                "no context injection, truth authority, CRM/account sync, connector writes, action execution, provider/model calls, public beta, or production authority",
            ],
        },
    )


def _append_behavior_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    old_state_dir = os.environ.get("UAA_FOUNDER_LOOP_STATE_DIR")
    old_authority_state_dir = os.environ.get(AUTHORITY_STATE_DIR_ENV)
    old_bearer = os.environ.get(LOCAL_API_BEARER_ENV)
    bearer = "fcc-v1-005-local-bearer"
    auth_headers = {"Authorization": f"Bearer {bearer}"}
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = str(Path(temp_dir) / "founder_loop")
        authority_state_dir = Path(temp_dir) / "authority"
        _issue_memory_write_lease(authority_state_dir)
        os.environ[AUTHORITY_STATE_DIR_ENV] = str(authority_state_dir)
        os.environ[LOCAL_API_BEARER_ENV] = bearer
        try:
            candidate_ref = _candidate_ref(context, auth_headers)
            accept = _exercise_decision(
                failures,
                context,
                candidate_ref,
                "accept",
                auth_headers,
            )
            _exercise_correction(failures, context, candidate_ref, auth_headers)
            reject = _exercise_decision(
                failures,
                context,
                candidate_ref,
                "reject",
                auth_headers,
            )
            _append_recall_record_failures(failures, accept)
            _append_receipt_lookup_failures(
                failures,
                context,
                candidate_ref,
                reject,
                auth_headers,
            )
            _append_today_summary_failures(failures, context, reject or accept, auth_headers)
            _append_memory_review_failures(failures, context, reject or accept, auth_headers)
            _append_cli_parity_failures(failures)
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


def _issue_memory_write_lease(state_dir: Path) -> None:
    issue_authority_lease_with_test_approval(
        AuthorityLeaseStore(state_dir),
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={AuthorityDomain.memory: [AuthorityCapability.write]},
            decision_reason_ref="decision-reason-ref:fcc-v1-005-authority",
            safe_summary=(
                "Verifier session lease grants Memory write for exact Memory Review "
                "accept/correct behavior checks."
            ),
        ),
        idempotency_ref="idempotency-ref:fcc-v1-005-authority",
        approval_ref="approval-ref:verifier:fcc-v1-005-authority",
    )


def _candidate_ref(context: ApiVerifierContext, auth_headers: dict[str, str]) -> str:
    response = context.client.get("/control-center/memory/review", headers=auth_headers)
    data = response.json().get("data", {}) if response.status_code == 200 else {}
    items = data.get("items") or []
    if not items:
        return "business-memory-candidate:preference:memory-review-founder-loop-preferences"
    return str(
        items[0].get("business_memory_candidate_ref")
        or items[0].get("review_ref")
        or "business-memory-candidate:preference:memory-review-founder-loop-preferences"
    )


def _exercise_decision(
    failures: list[str],
    context: ApiVerifierContext,
    candidate_ref: str,
    decision: str,
    auth_headers: dict[str, str],
) -> dict[str, Any]:
    body = _decision_body(decision)
    route = f"/control-center/memory/review/{candidate_ref}/{decision}"
    missing = context.client.post(route, json=body, headers=auth_headers)
    if missing.status_code != 428:
        failures.append(f"Memory Review {decision} must reject missing idempotency")
    key = f"idempotency-ref:fcc-v1-005-memory-{decision}"
    first = context.client.post(
        route,
        json=body,
        headers={**auth_headers, "x-uaa-idempotency-key": key},
    )
    if first.status_code != 200:
        failures.append(f"Memory Review {decision} failed with {first.status_code}")
        return {}
    receipt = first.json().get("data", {})
    _append_receipt_shape_failures(failures, receipt, f"Memory Review {decision}")
    if receipt.get("contract_ref") != FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF:
        failures.append(f"Memory Review {decision} contract ref drifted")
    if receipt.get("decision") != decision:
        failures.append(f"Memory Review {decision} receipt decision drifted")
    if decision in {"accept", "correct"} and not receipt.get("reviewed_recall_record_ref"):
        failures.append(f"Memory Review {decision} must create reviewed recall record ref")
    if decision in {"accept", "correct"} and receipt.get("reviewed_recall_write_performed") is not True:
        failures.append(f"Memory Review {decision} must prove reviewed recall write")
    if decision == "reject" and receipt.get("reviewed_recall_record_ref"):
        failures.append("Memory Review reject must not create reviewed recall record ref")
    if decision == "reject" and receipt.get("reviewed_recall_write_performed") is not False:
        failures.append("Memory Review reject must not claim reviewed recall write")
    replay = context.client.post(
        route,
        json=body,
        headers={**auth_headers, "x-uaa-idempotency-key": key},
    )
    replay_data = replay.json().get("data", {}) if replay.status_code == 200 else {}
    if (
        replay.status_code != 200
        or replay_data.get("receipt_ref") != receipt.get("receipt_ref")
        or replay_data.get("replayed") is not False
    ):
        failures.append(
            f"Memory Review {decision} must return the stored receipt for matching replay"
        )
    conflict = context.client.post(
        route,
        json={**body, "reviewer_ref": f"actor-ref:fcc-v1-005-{decision}-changed"},
        headers={**auth_headers, "x-uaa-idempotency-key": key},
    )
    if conflict.status_code != 409:
        failures.append(f"Memory Review {decision} must reject idempotency conflict")
    return receipt


def _exercise_correction(
    failures: list[str],
    context: ApiVerifierContext,
    candidate_ref: str,
    auth_headers: dict[str, str],
) -> None:
    route = f"/control-center/memory/review/{candidate_ref}/correct"
    missing_ref = context.client.post(
        route,
        json=_decision_body("correct", corrected_summary_ref=None),
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": "idempotency-ref:fcc-v1-005-correct-missing",
        },
    )
    if missing_ref.status_code != 400:
        failures.append("Memory Review correction must require corrected_summary_ref")
    receipt = _exercise_decision(failures, context, candidate_ref, "correct", auth_headers)
    if "corrected_safe_summary" in receipt:
        failures.append("Memory Review correction receipt must remain content-free")
    if receipt.get("corrected_summary_ref") != "safe-summary-ref:fcc-v1-005-correction":
        failures.append("Memory Review correction must store corrected_summary_ref")
    if not receipt.get("reviewed_recall_record_ref"):
        failures.append("Memory Review correction must create reviewed recall record ref")


def _decision_body(
    decision: str,
    *,
    corrected_summary_ref: str | None = "safe-summary-ref:fcc-v1-005-correction",
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "reviewer_ref": f"actor-ref:fcc-v1-005-{decision}",
        "source_refs": ["source-ref:manual-note:fcc-v1-005"],
        "evidence_refs": ["evidence-ref:memory-review:fcc-v1-005"],
        "metadata_refs": [f"metadata-ref:memory-review:fcc-v1-005-{decision}"],
    }
    if decision == "correct" and corrected_summary_ref is not None:
        body["corrected_summary_ref"] = corrected_summary_ref
        body["corrected_safe_summary"] = "Corrected bounded safe summary for FCC-V1-005."
    return body


def _append_receipt_shape_failures(
    failures: list[str],
    receipt: dict[str, Any],
    label: str,
) -> None:
    for field in [
        "candidate_ref",
        "decision_ref",
        "receipt_ref",
        "idempotency_key_ref",
        "payload_fingerprint_ref",
        "evidence_timeline_event_ref",
        "approval_ref",
        "approval_scope_ref",
        "approval_status",
        "approval_reason_refs",
        "safe_disable_ref",
        "rollback_ref",
        "safe_disable_posture_ref",
        "rollback_execution_enabled",
        "rollback_blocker_refs",
        "reviewer_ref",
        "source_refs",
        "evidence_refs",
        "blocked_state_refs",
        "created_at",
    ]:
        if field not in receipt:
            failures.append(f"{label} missing receipt field {field}")
    for field in DENIED_RECEIPT_FIELDS:
        if receipt.get(field) is not False:
            failures.append(f"{label} denied field {field} must stay false")
    lifecycle_suppression = bool(receipt.get("suppressed_recall_record_refs"))
    expected_scope_ref = (
        MEMORY_REVIEW_LIFECYCLE_SCOPE_REF
        if lifecycle_suppression
        else MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
        if receipt.get("decision") in {"accept", "correct"}
        else MEMORY_REVIEW_RECEIPT_SCOPE_REF
    )
    if receipt.get("approval_scope_ref") != expected_scope_ref:
        failures.append(f"{label} approval scope ref drifted")
    if receipt.get("decision") in {"accept", "correct"} or lifecycle_suppression:
        for field in [
            "authority_decision_ref",
            "authority_decision_outcome",
            "authority_lease_ref",
            "authority_domain_ref",
            "authority_capability_ref",
        ]:
            if not receipt.get(field):
                failures.append(f"{label} missing authority field {field}")
        if receipt.get("authority_domain_ref") != "authority-domain-ref:memory":
            failures.append(f"{label} authority domain ref drifted")
        if receipt.get("authority_capability_ref") != "authority-capability-ref:write":
            failures.append(f"{label} authority capability ref drifted")
    else:
        for field in [
            "authority_decision_ref",
            "authority_decision_outcome",
            "authority_lease_ref",
        ]:
            if receipt.get(field):
                failures.append(f"{label} receipt-only decision claimed {field}")
    if receipt.get("safe_disable_ref") != MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF:
        failures.append(f"{label} safe-disable ref drifted")
    if receipt.get("rollback_execution_enabled") is not False:
        failures.append(f"{label} rollback execution must stay blocked")
    if MEMORY_REVIEW_WRITE_ROLLBACK_BLOCKED_REF not in set(
        receipt.get("rollback_blocker_refs") or []
    ):
        failures.append(f"{label} missing rollback blocker ref")
    if "raw" in str(receipt).lower() or "provider payload" in str(receipt).lower():
        failures.append(f"{label} receipt contains unsafe raw/provider wording")


def _append_cli_parity_failures(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        state_dir = Path(temp_dir) / "founder_loop_cli"
        authority_state_dir = Path(temp_dir) / "authority"
        _issue_memory_write_lease(authority_state_dir)
        env = {**os.environ, AUTHORITY_STATE_DIR_ENV: str(authority_state_dir)}
        repo = FounderLoopRepository(state_dir)
        queue = repo.list_memory_review_queue(limit=1)
        candidate_ref = str(
            queue[0].get("business_memory_candidate_ref")
            or queue[0].get("review_ref")
        )
        decision = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/dev/uaa_founder_loop.py"),
                "--state-dir",
                str(state_dir),
                "record-memory-decision",
                "--candidate-ref",
                candidate_ref,
                "--decision",
                "accept",
                "--idempotency-ref",
                "idempotency-ref:fcc-v1-005-cli-accept",
                "--reviewer-ref",
                "actor-ref:fcc-v1-005-cli-reviewer",
                "--source-ref",
                "source-ref:fcc-v1-005-cli",
                "--evidence-ref",
                "evidence-ref:fcc-v1-005-cli",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if decision.returncode != 0:
            failures.append("Memory Review CLI accept command failed")
            return
        try:
            decision_payload = json.loads(decision.stdout)
        except json.JSONDecodeError:
            failures.append("Memory Review CLI accept did not return JSON")
            return
        receipt = dict(decision_payload.get("receipt") or {})
        if receipt.get("reviewed_recall_write_performed") is not True:
            failures.append("Memory Review CLI accept must prove reviewed recall write")
        if receipt.get("authority_domain_ref") != "authority-domain-ref:memory":
            failures.append("Memory Review CLI accept authority domain drifted")
        if receipt.get("authority_capability_ref") != "authority-capability-ref:write":
            failures.append("Memory Review CLI accept authority capability drifted")
        if receipt.get("approval_scope_ref") != MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF:
            failures.append("Memory Review CLI accept approval scope drifted")
        if str(state_dir) in decision.stdout:
            failures.append("Memory Review CLI accept leaked state path")

        inspect = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/dev/uaa_founder_loop.py"),
                "--state-dir",
                str(state_dir),
                "memory-receipts",
                "--limit",
                "5",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if inspect.returncode != 0:
            failures.append("Memory Review CLI receipt inspection failed")
            return
        try:
            inspect_payload = json.loads(inspect.stdout)
        except json.JSONDecodeError:
            failures.append("Memory Review CLI receipt inspection did not return JSON")
            return
        if inspect_payload.get("exact_write_scope_ref") != MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF:
            failures.append("Memory Review CLI inspection exact scope drifted")
        if inspect_payload.get("reviewed_recall_record_count") != 1:
            failures.append("Memory Review CLI inspection must show one recall record")
        posture = dict(inspect_payload.get("write_safe_disable_posture") or {})
        if posture.get("rollback_execution_enabled") is not False:
            failures.append("Memory Review CLI inspection must block rollback execution")
        serialized = json.dumps(inspect_payload).lower()
        for fragment in ["raw_prompt", "raw_response", "provider_payload"]:
            if fragment in serialized:
                failures.append(f"Memory Review CLI inspection leaked {fragment}")
        if str(state_dir).lower() in serialized:
            failures.append("Memory Review CLI inspection leaked state path")


def _append_recall_record_failures(
    failures: list[str],
    receipt: dict[str, Any],
) -> None:
    if not receipt:
        return
    repo = FounderLoopRepository.from_env()
    records = repo.list_memory_review_recall_records()
    if not records:
        failures.append("Memory Review accept/correct must create LocalMemoryStore recall records")
        return
    receipt_ref = receipt.get("receipt_ref")
    matching = [
        record
        for record in records
        if receipt_ref in set(record.get("receipt_refs") or [])
    ]
    if not matching:
        failures.append("Memory Review recall records must include decision receipt refs")
        return
    record = matching[0]
    if record.get("authority_level") != "recall_only":
        failures.append("Memory Review recall record must remain recall_only")
    if record.get("review_state") != "user_reviewed":
        failures.append("Memory Review recall record must be user_reviewed")
    recall_metadata = record.get("recall_metadata") or {}
    if recall_metadata.get("context_pack_eligible") is not False:
        failures.append("Memory Review recall record must not be context-pack eligible")
    if recall_metadata.get("injection_priority") != 0:
        failures.append("Memory Review recall record must keep zero injection priority")
    metadata = record.get("metadata") or {}
    for field in [
        "context_injection_authorized",
        "source_truth_authority",
        "connector_write_authorized",
        "automatic_action_execution_authorized",
    ]:
        if metadata.get(field) is not False:
            failures.append(f"Memory Review recall record metadata {field} must be false")


def _append_receipt_lookup_failures(
    failures: list[str],
    context: ApiVerifierContext,
    candidate_ref: str,
    receipt: dict[str, Any],
    auth_headers: dict[str, str],
) -> None:
    response = context.client.get(
        f"/control-center/memory/review/{candidate_ref}/receipt",
        headers=auth_headers,
    )
    if response.status_code != 200:
        failures.append("Memory Review receipt lookup route must return latest receipt")
        return
    data = response.json().get("data", {})
    if receipt and data.get("receipt_ref") != receipt.get("receipt_ref"):
        failures.append("Memory Review receipt lookup must return latest candidate receipt")
    missing = context.client.get(
        "/control-center/memory/review/business-memory-candidate:missing/receipt",
        headers=auth_headers,
    )
    if missing.status_code != 404:
        failures.append("Memory Review receipt lookup must return 404 when absent")


def _append_today_summary_failures(
    failures: list[str],
    context: ApiVerifierContext,
    receipt: dict[str, Any],
    auth_headers: dict[str, str],
) -> None:
    response = context.client.get("/control-center/today/summary", headers=auth_headers)
    if response.status_code != 200:
        failures.append("Today summary failed after Memory Review decision")
        return
    today = response.json().get("data", {})
    if receipt and receipt.get("receipt_ref") not in today.get("memory_review_decision_receipt_refs", []):
        failures.append("Today summary missing Memory Review decision receipt ref")
    timeline = [
        item
        for item in today.get("evidence_timeline", [])
        if item.get("item_kind") == "memory_review_evidence_ref"
    ]
    if not timeline:
        failures.append("Evidence Timeline missing Memory Review decision event")
    elif receipt and receipt.get("receipt_ref") not in str(timeline):
        failures.append("Evidence Timeline missing Memory Review receipt ref")


def _append_memory_review_failures(
    failures: list[str],
    context: ApiVerifierContext,
    receipt: dict[str, Any],
    auth_headers: dict[str, str],
) -> None:
    response = context.client.get("/control-center/memory/review", headers=auth_headers)
    if response.status_code != 200:
        failures.append("Memory Review GET failed after decisions")
        return
    data = response.json().get("data", {})
    if receipt and receipt.get("receipt_ref") not in data.get("decision_receipt_refs", []):
        failures.append("Memory Review GET missing decision receipt ref")
    if data.get("context_injection_authorized") is not False:
        failures.append("Memory Review GET must keep context injection blocked")
    if data.get("raw_content_stored") is not False:
        failures.append("Memory Review GET must report raw content omitted")
    rejected = [
        item
        for item in data.get("items", [])
        if item.get("review_state") == "rejected"
    ]
    if not rejected:
        failures.append("Rejected Memory Review candidates must stay preserved")


def _append_ui_label_failures(failures: list[str], root: Path) -> None:
    path = root / "apps/control-center/src/components/FounderLoopPanels.tsx"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for required in [
        "Record accept receipt",
        "Record correction receipt",
        "Record reject receipt",
    ]:
        if required not in text:
            failures.append(f"Memory Review UI missing safe label {required}")
    for forbidden in [
        ">Approve<",
        ">Run<",
        ">Execute<",
        ">Save memory<",
        ">Write memory<",
        ">Learn this<",
    ]:
        if forbidden.lower() in text.lower():
            failures.append(f"Memory Review UI contains unsafe label {forbidden}")


def _route_by_path(
    release_surface: dict[str, Any],
    path: str,
) -> dict[str, Any] | None:
    return next(
        (
            route
            for route in release_surface.get("routes", [])
            if route.get("path") == path
        ),
        None,
    )


def _surface(route_status: dict[str, Any], surface: str) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in route_status.get("surfaces", [])
            if item.get("surface") == surface
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


def _append_route_present(
    failures: list[str],
    routes: list[dict[str, Any]],
    route: tuple[str, str],
    label: str,
) -> None:
    method, path = route
    if not any(
        item.get("method") == method and item.get("path") == path
        for item in routes
    ):
        failures.append(f"{label} missing route {method} {path}")


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
