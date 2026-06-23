#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts import verify_uaa_p1_086_api_boundary_enforcement_tests as p1_086  # noqa: E402
from scripts.verification.api_lane import (  # noqa: E402
    ApiVerifierContext,
    default_api_verifier_context,
)
from scripts.verification.api_routes import (  # noqa: E402
    EXPECTED_APPROVAL_POSTURE_SUMMARY,
    EXPECTED_AUTH_POSTURE_SUMMARY,
    EXPECTED_MUTATING_ROUTES,
    EXPECTED_RATE_LIMIT_GROUPS,
    projected_routes,
    route_fixture,
)
from scripts.verification.repo import (  # noqa: E402
    load_json,
    print_failures_or_success,
    read_text,
)
from ultimate_ai_agent.api.idempotency import API_IDEMPOTENCY_AUDIT_POLICY_REF  # noqa: E402
from ultimate_ai_agent.api.rate_limits import API_TARGETED_RATE_LIMIT_POLICY_REF  # noqa: E402


SUCCESS_MESSAGE = "FCC-V1-001 API perimeter for real mutations verification passed."
PERIMETER_DOC = "docs/api/FCC_V1_001_API_PERIMETER_FOR_REAL_MUTATIONS.md"
PERIMETER_MANIFEST = "docs/control_center/founder_loop_api_perimeter_manifest.json"
PERIMETER_SCHEMA = "docs/schemas/founder_loop_api_perimeter.schema.json"
REQUIRED_POSTURE_FIELDS = {
    "route_classification",
    "side_effect_class",
    "auth_posture",
    "approval_posture",
    "idempotency_posture",
    "rate_limit_posture",
}
FALSE_FLAGS = {
    "runtime_authority_added",
    "routes_added",
    "durable_replay_runtime_added",
    "public_beta_claim_enabled",
    "production_readiness_claim_enabled",
    "manual_review_completion_claimed",
}
FORBIDDEN_DOC_SNIPPETS = [
    "duplicate replay runtime is implemented",
    "durable dedupe runtime is implemented",
    "manual review is complete",
    "manual review completed",
    "public beta ready",
    "production ready",
    "production auth enabled",
]
TARGETED_ROUTE_EXPECTATIONS = {
    ("POST", "/v1/chat/completions"): "model_chat",
    ("POST", "/files/review/approvals/capture"): "action_preview_proposal",
    ("POST", "/control-center/actions/preview"): "action_preview_proposal",
    ("POST", "/control-center/today/action-envelope"): "today_to_action_envelope",
    ("POST", "/control-center/chat/turns"): "chat_durable_receipt",
    ("POST", "/control-center/chat/turns/{turn_ref}/handoff"): "chat_durable_receipt",
    ("POST", "/control-center/memory/review/{candidate_ref}/accept"): "memory_review_decision",
    ("POST", "/control-center/actions/{action_id}/reject"): "action_decision",
    ("POST", "/task-decomposition/approval-requests"): "task_decomposition",
    ("POST", "/task-decomposition/approvals/grants/capture"): "task_decomposition",
    ("POST", "/task-decomposition/run"): "task_decomposition",
}
REQUIRED_FAMILY_REFS = {
    "today_to_action_envelope",
    "action_decision",
    "chat_receipt_handoff",
    "memory_review_decision",
    "evidence_timeline_mutation",
    "file_proposal_or_approval_capture",
}
REQUIRED_FAMILY_RECEIPT_REFS = {
    "today_to_action_envelope": "future-action-envelope-receipt",
    "action_decision": "future-action-decision-receipt",
    "chat_receipt_handoff": "future-chat-turn-or-handoff-receipt",
    "memory_review_decision": "future-memory-review-decision-receipt",
    "evidence_timeline_mutation": "future-evidence-timeline-receipt",
    "file_proposal_or_approval_capture": "future-file-proposal-or-approval-receipt",
}
REQUIRED_PROOF_LANES = {
    "scripts/verify_fcc_v1_001_api_perimeter.py",
    "tests/test_fcc_v1_001_api_perimeter.py",
    "scripts/verify_uaa_p1_086_api_boundary_enforcement_tests.py",
    "tests/test_api_boundary_enforcement.py",
    "tests/test_api_manifest.py",
    "tests/test_api_route_inventory_fixture.py",
}
REQUIRED_BLOCKED_CAPABILITIES = {
    "durable_duplicate_replay_runtime",
    "exactly_once_execution_claim",
    "action_execution_without_exact_approval",
    "memory_write_without_review_decision",
    "connector_write",
    "production_auth",
    "public_beta_claim",
    "production_readiness_claim",
}
REQUIRED_EVIDENCE_REFS = {
    "docs/api/FCC_V1_001_API_PERIMETER_FOR_REAL_MUTATIONS.md",
    "docs/control_center/founder_loop_api_perimeter_manifest.json",
    "docs/schemas/founder_loop_api_perimeter.schema.json",
    "src/ultimate_ai_agent/api/manifest.py",
    "src/ultimate_ai_agent/api/contracts.py",
    "tests/fixtures/api_route_inventory_128.json",
}


def expected_mutating_inventory(context: ApiVerifierContext) -> list[dict[str, Any]]:
    routes = []
    for key, route in context.routes_by_key.items():
        if route["route_classification"] != "mutating_requires_authority":
            continue
        routes.append(
            {
                "method": key[0],
                "path": key[1],
                "operation_id": route["operation_id"],
                "side_effect_class": route["side_effect_class"],
                "route_classification": route["route_classification"],
                "auth_posture": route["auth_posture"],
                "approval_posture": route["approval_posture"],
                "idempotency_posture": route["idempotency_posture"],
                "idempotency_policy_ref": route["idempotency_policy_ref"],
                "rate_limit_posture": route["rate_limit_posture"],
                "rate_limit_group": route["rate_limit_group"],
            }
        )
    return sorted(routes, key=lambda item: (item["path"], item["method"]))


def verify(
    root: Path = ROOT,
    *,
    context: ApiVerifierContext | None = None,
    perimeter_manifest: dict[str, Any] | None = None,
    doc_text: str | None = None,
    check_files: bool = True,
) -> list[str]:
    failures: list[str] = []
    context = context or default_api_verifier_context()
    perimeter_manifest = (
        perimeter_manifest
        if perimeter_manifest is not None
        else load_json(PERIMETER_MANIFEST)
    )
    doc_text = doc_text if doc_text is not None else read_text(PERIMETER_DOC)

    if check_files:
        _append_required_file_failures(failures, root)

    _append_schema_failures(failures, perimeter_manifest)
    failures.extend(p1_086.verify(context))
    _append_api_posture_failures(failures, context)
    _append_perimeter_manifest_failures(failures, perimeter_manifest, context)
    _append_doc_claim_failures(failures, doc_text)
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [PERIMETER_DOC, PERIMETER_MANIFEST, PERIMETER_SCHEMA]:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-V1-001 file: {rel_path}")


def _append_schema_failures(failures: list[str], manifest: dict[str, Any]) -> None:
    schema = load_json(PERIMETER_SCHEMA)
    for error in sorted(
        Draft202012Validator(schema).iter_errors(manifest),
        key=lambda error: list(error.path),
    ):
        failures.append(f"Founder Loop API perimeter schema error: {error.message}")


def _append_api_posture_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    manifest = context.manifest
    if manifest.get("route_auth_posture_summary") != EXPECTED_AUTH_POSTURE_SUMMARY:
        failures.append("FCC-V1-001 auth posture summary drifted")
    if manifest.get("route_approval_posture_summary") != EXPECTED_APPROVAL_POSTURE_SUMMARY:
        failures.append("FCC-V1-001 approval posture summary drifted")
    if route_fixture()["routes"] != projected_routes(manifest):
        failures.append("FCC-V1-001 frozen route inventory does not match live manifest")

    mutating_routes = {
        key for key, route in context.routes_by_key.items()
        if route["route_classification"] == "mutating_requires_authority"
    }
    if mutating_routes != EXPECTED_MUTATING_ROUTES:
        failures.append(f"FCC-V1-001 mutating route inventory drifted: {sorted(mutating_routes)}")

    targeted_groups = {
        route["rate_limit_group"]
        for route in context.routes_by_key.values()
        if route["rate_limit_targeted"] is True
    }
    if targeted_groups != EXPECTED_RATE_LIMIT_GROUPS:
        failures.append(f"FCC-V1-001 targeted rate-limit groups drifted: {sorted(targeted_groups)}")

    for key, route in context.routes_by_key.items():
        expected_auth = (
            "public_metadata_no_auth"
            if route["route_classification"] == "public_metadata"
            else "protected_local_bearer_required"
        )
        expected_approval = (
            "required_before_mutation_authority"
            if route["route_classification"] == "mutating_requires_authority"
            else "not_required_for_route_classification"
        )
        if route.get("auth_posture") != expected_auth:
            failures.append(f"{key[0]} {key[1]} missing FCC-V1-001 auth posture")
        if route.get("approval_posture") != expected_approval:
            failures.append(f"{key[0]} {key[1]} missing FCC-V1-001 approval posture")
        if route["route_classification"] == "mutating_requires_authority":
            _append_mutating_route_failures(failures, key, route)

    for key, group in TARGETED_ROUTE_EXPECTATIONS.items():
        route = context.routes_by_key.get(key)
        if route is None:
            failures.append(f"FCC-V1-001 targeted route missing: {key[0]} {key[1]}")
            continue
        if route.get("rate_limit_group") != group:
            failures.append(f"{key[0]} {key[1]} targeted rate-limit group drifted")
        if route.get("rate_limit_policy_ref") != API_TARGETED_RATE_LIMIT_POLICY_REF:
            failures.append(f"{key[0]} {key[1]} targeted rate-limit policy ref drifted")


def _append_mutating_route_failures(
    failures: list[str],
    key: tuple[str, str],
    route: dict[str, Any],
) -> None:
    if route.get("protected_route") is not True:
        failures.append(f"{key[0]} {key[1]} mutating route is not protected")
    if route.get("auth_posture") != "protected_local_bearer_required":
        failures.append(f"{key[0]} {key[1]} mutating route lacks local bearer posture")
    if route.get("approval_posture") != "required_before_mutation_authority":
        failures.append(f"{key[0]} {key[1]} mutating route lacks approval posture")
    if route.get("idempotency_required") is not True:
        failures.append(f"{key[0]} {key[1]} mutating route lacks idempotency requirement")
    if route.get("idempotency_posture") != "required_before_mutation_authority":
        failures.append(f"{key[0]} {key[1]} mutating route lacks FCC-V1-001 idempotency posture")
    if route.get("idempotency_policy_ref") != API_IDEMPOTENCY_AUDIT_POLICY_REF:
        failures.append(f"{key[0]} {key[1]} mutating idempotency policy ref drifted")


def _append_perimeter_manifest_failures(
    failures: list[str],
    manifest: dict[str, Any],
    context: ApiVerifierContext,
) -> None:
    if manifest.get("schema_version") != "uaa-founder-loop-api-perimeter.v1":
        failures.append("Founder Loop API perimeter manifest schema_version drifted")
    if manifest.get("milestone_ref") != "FCC-V1-001":
        failures.append("Founder Loop API perimeter manifest milestone_ref must be FCC-V1-001")
    for flag in FALSE_FLAGS:
        if manifest.get(flag) is not False:
            failures.append(f"Founder Loop API perimeter manifest overclaims {flag}")
    if manifest.get("manual_review_status") != "deferred_until_later_local_review":
        failures.append("manual review status must remain deferred")
    if manifest.get("rate_limits_are_auth") is not False:
        failures.append("Founder Loop API perimeter must say rate limits are not auth")
    if set(manifest.get("proof_lanes", [])) != REQUIRED_PROOF_LANES:
        failures.append("Founder Loop API perimeter proof_lanes drifted")
    if set(manifest.get("blocked_capabilities", [])) != REQUIRED_BLOCKED_CAPABILITIES:
        failures.append("Founder Loop API perimeter blocked_capabilities drifted")
    if set(manifest.get("evidence_refs", [])) != REQUIRED_EVIDENCE_REFS:
        failures.append("Founder Loop API perimeter evidence_refs drifted")
    if manifest.get("current_mutating_routes") != expected_mutating_inventory(context):
        failures.append("Founder Loop API perimeter current_mutating_routes drifted")

    duplicate_replay = manifest.get("duplicate_replay_contract", {})
    if duplicate_replay.get("current_runtime_status") != "blocked_until_route_owner_append_first_receipts":
        failures.append("duplicate replay runtime status must remain blocked until route-owner receipts")
    if duplicate_replay.get("same_key_same_payload") != "required_future_return_prior_receipt":
        failures.append("duplicate replay same-key contract drifted")
    if duplicate_replay.get("same_key_conflicting_payload") != "required_future_reject_conflict":
        failures.append("duplicate replay conflict contract drifted")

    families = manifest.get("founder_loop_mutation_families", [])
    family_refs = {family.get("family_ref") for family in families}
    if family_refs != REQUIRED_FAMILY_REFS:
        failures.append(f"Founder Loop mutation family refs drifted: {sorted(family_refs)}")
    for family in families:
        family_ref = family.get("family_ref")
        posture_fields = set(family.get("required_manifest_posture", []))
        if posture_fields != REQUIRED_POSTURE_FIELDS:
            failures.append(f"{family_ref} posture fields drifted: {sorted(posture_fields)}")
        if family.get("duplicate_replay_required_before_runtime") is not True:
            failures.append(f"{family_ref} must require duplicate replay before runtime")
        if family.get("status") not in {"planned", "blocked_until_route_owner_storage"}:
            failures.append(f"{family_ref} has unsafe status {family.get('status')}")
        if family.get("receipt_requirement_ref") != REQUIRED_FAMILY_RECEIPT_REFS.get(family_ref):
            failures.append(f"{family_ref} receipt requirement ref drifted")


def _append_doc_claim_failures(failures: list[str], doc_text: str) -> None:
    compact = " ".join(doc_text.lower().split())
    required = [
        "status: implemented as contract and verifier coverage",
        "duplicate replay behavior is defined here as a required route-owner contract",
        "fcc-v1-002 implements it for action inbox decision routes",
        "manual review remains deferred",
        "rate limits are local-first backpressure, not authentication",
    ]
    for snippet in required:
        if snippet not in compact:
            failures.append(f"FCC-V1-001 doc missing '{snippet}'")
    for snippet in FORBIDDEN_DOC_SNIPPETS:
        if snippet in compact:
            failures.append(f"FCC-V1-001 doc contains forbidden claim '{snippet}'")


def main() -> int:
    return print_failures_or_success(
        failures=verify(),
        success_message=SUCCESS_MESSAGE,
    )


if __name__ == "__main__":
    raise SystemExit(main())
