from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from scripts import verify_fcc_v1_001_api_perimeter as verifier
from scripts.verification import api_lane
from scripts.verification.api_lane import ApiVerifierContext


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs/control_center/founder_loop_api_perimeter_manifest.json"


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_fcc_v1_001_api_perimeter_verifier_passes_current_repo() -> None:
    assert verifier.verify(ROOT) == []


def test_fcc_v1_001_manifest_inventory_matches_api_manifest() -> None:
    context = api_lane.default_api_verifier_context()
    manifest = load_manifest()

    assert manifest["runtime_authority_added"] is False
    assert manifest["routes_added"] is False
    assert manifest["manual_review_completion_claimed"] is False
    assert manifest["current_mutating_route_count"] == 31
    assert manifest["current_mutating_routes"] == verifier.expected_mutating_inventory(context)
    assert {family["family_ref"] for family in manifest["founder_loop_mutation_families"]} == (
        verifier.REQUIRED_FAMILY_REFS
    )


def test_fcc_v1_001_verifier_flags_mutating_route_without_idempotency() -> None:
    context = api_lane.default_api_verifier_context()
    mutated_manifest = copy.deepcopy(context.manifest)
    route = next(
        route for route in mutated_manifest["routes"]
        if route["path"] == "/v1/chat/completions"
    )
    route["idempotency_required"] = False
    route["idempotency_posture"] = "not_required_for_route_classification"
    route["idempotency_policy_ref"] = None
    route["approval_posture"] = "not_required_for_route_classification"
    mutated_context = ApiVerifierContext(
        app=context.app,
        manifest=mutated_manifest,
        routes_by_key={
            (route["method"], route["path"]): route
            for route in mutated_manifest["routes"]
        },
        client=context.client,
        https_client=context.https_client,
    )

    failures = verifier.verify(
        ROOT,
        context=mutated_context,
        perimeter_manifest=load_manifest(),
        check_files=False,
    )

    assert any("mutating route lacks FCC-V1-001 idempotency posture" in failure for failure in failures)
    assert any("mutating route lacks approval posture" in failure for failure in failures)


def test_fcc_v1_001_verifier_flags_replay_and_manual_review_overclaims() -> None:
    doc_text = (
        "Status: implemented as contract and verifier coverage. "
        "Duplicate replay behavior is defined here as a required future route-owner contract. "
        "Manual review remains deferred. "
        "Rate limits are local-first backpressure, not authentication. "
        "Duplicate replay runtime is implemented. "
        "Manual review completed."
    )

    failures = verifier.verify(
        ROOT,
        perimeter_manifest=load_manifest(),
        doc_text=doc_text,
        check_files=False,
    )

    assert any("duplicate replay runtime is implemented" in failure for failure in failures)
    assert any("manual review completed" in failure for failure in failures)


def test_fcc_v1_001_verifier_flags_manifest_authority_overclaims() -> None:
    manifest = load_manifest()
    manifest["durable_replay_runtime_added"] = True
    manifest["public_beta_claim_enabled"] = True
    manifest["rate_limits_are_auth"] = True
    manifest["manual_review_status"] = "complete"
    manifest["proof_lanes"] = []
    manifest["blocked_capabilities"] = []
    manifest["evidence_refs"] = []
    manifest["unexpected_authority"] = True

    failures = verifier.verify(
        ROOT,
        perimeter_manifest=manifest,
        check_files=False,
    )

    assert any("overclaims durable_replay_runtime_added" in failure for failure in failures)
    assert any("overclaims public_beta_claim_enabled" in failure for failure in failures)
    assert any("rate limits are not auth" in failure for failure in failures)
    assert any("manual review status must remain deferred" in failure for failure in failures)
    assert any("proof_lanes drifted" in failure for failure in failures)
    assert any("blocked_capabilities drifted" in failure for failure in failures)
    assert any("evidence_refs drifted" in failure for failure in failures)
    assert any("Additional properties are not allowed" in failure for failure in failures)


def test_fcc_v1_001_verifier_flags_nested_family_contract_drift() -> None:
    manifest = load_manifest()
    family = manifest["founder_loop_mutation_families"][0]
    family["required_manifest_posture"].append("production_authority")
    family["receipt_requirement_ref"] = "future-memory-review-decision-receipt"

    failures = verifier.verify(
        ROOT,
        perimeter_manifest=manifest,
        check_files=False,
    )

    assert any("production_authority" in failure for failure in failures)
    assert any("posture fields drifted" in failure for failure in failures)
    assert any("receipt requirement ref drifted" in failure for failure in failures)
