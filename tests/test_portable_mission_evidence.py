from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.core.execution.portable_mission_evidence import (
    PortableMissionEvidenceEnvelope,
    _entry_hash,
    _stable_ref,
    build_portable_mission_evidence_bundle,
    verify_portable_mission_evidence_bundle,
)


def _sources(tmp_path: Path):  # type: ignore[no-untyped-def]
    orchestrator, dispatcher, _, lease, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="portable-evidence",
    )
    result = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:portable-evidence",
    )
    assert result.status == "succeeded"
    manifests = orchestrator.completion_store.list_manifests()
    receipts = [item for item in dispatcher.list_receipts() if item.status == "succeeded"]
    bundle = build_portable_mission_evidence_bundle(
        manifests,
        leases=[lease],
        dispatch_receipts=receipts,
    )
    return manifests, [lease], receipts, bundle


def _bundle(tmp_path: Path):  # type: ignore[no-untyped-def]
    return _sources(tmp_path)[-1]


def _rehash_payload(payload: dict[str, object]) -> None:
    envelopes = payload["envelopes"]
    assert isinstance(envelopes, list)
    predecessor = None
    for envelope_payload in envelopes:
        assert isinstance(envelope_payload, dict)
        envelope_payload["predecessor_entry_hash_ref"] = predecessor
        envelope_payload["entry_hash_ref"] = "portable-evidence-entry-hash-ref:pending"
        parsed = PortableMissionEvidenceEnvelope.model_validate(envelope_payload)
        envelope_payload["entry_hash_ref"] = _entry_hash(parsed)
        predecessor = envelope_payload["entry_hash_ref"]
    payload["genesis_entry_hash_ref"] = envelopes[0]["entry_hash_ref"]
    payload["terminal_entry_hash_ref"] = envelopes[-1]["entry_hash_ref"]
    payload["bundle_ref"] = _stable_ref(
        "portable-mission-evidence-bundle-ref",
        {key: value for key, value in payload.items() if key != "bundle_ref"},
    )


def test_portable_bundle_is_deterministic_content_free_and_non_authoritative(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path)
    verified = verify_portable_mission_evidence_bundle(
        bundle,
        expected_bundle_ref=bundle.bundle_ref,
        expected_envelope_count=bundle.envelope_count,
    )

    assert verified.valid is True
    assert verified.chain_verified is True
    assert verified.caller_expected_binding_matched is True
    assert verified.external_anchor_verified is False
    assert verified.signature_verified is False
    assert verified.cryptographic_authenticity_verified is False
    assert verified.execution_authority_granted is False
    assert bundle.signature_present is False
    assert bundle.signing_status == "blocked_signing_lifecycle_not_implemented"
    assert bundle.source_ledgers_verified is False
    assert bundle.execution_evidence_grants_authority is False
    assert all(
        item.provider_ref == "provider-ref:unknown:not-declared-by-adapter"
        for item in bundle.envelopes
    )
    assert all(item.target_binding_ref.startswith("target-binding-ref:") for item in bundle.envelopes)
    assert all(
        item.approval_scope_fingerprint_ref
        for item in bundle.envelopes
        if item.approval_ref is not None
    )
    unanchored = verify_portable_mission_evidence_bundle(bundle)
    assert unanchored.valid is True
    assert unanchored.caller_expected_binding_matched is False
    assert unanchored.external_anchor_verified is False

    manifests, leases, receipts, _ = _sources(tmp_path / "repeat")
    repeated = build_portable_mission_evidence_bundle(
        manifests,
        leases=leases,
        dispatch_receipts=receipts,
    )
    assert repeated == build_portable_mission_evidence_bundle(
        manifests,
        leases=leases,
        dispatch_receipts=receipts,
    )


def test_portable_bundle_rejects_tamper_target_and_unknown_fields(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    payload = bundle.model_dump(mode="json")
    payload["envelopes"][0]["target_binding_ref"] = "target-binding-ref:substituted"
    assert verify_portable_mission_evidence_bundle(payload).valid is False

    payload = bundle.model_dump(mode="json")
    payload["raw_prompt"] = "must never be accepted"
    assert verify_portable_mission_evidence_bundle(payload).valid is False


def test_portable_bundle_rejects_reorder_replay_and_truncation(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    assert bundle.envelope_count >= 2

    reordered = bundle.model_dump(mode="json")
    reordered["envelopes"][0], reordered["envelopes"][1] = (
        reordered["envelopes"][1],
        reordered["envelopes"][0],
    )
    assert verify_portable_mission_evidence_bundle(reordered).valid is False

    replayed = bundle.model_dump(mode="json")
    replayed["envelopes"].append(replayed["envelopes"][-1])
    replayed["envelope_count"] += 1
    assert verify_portable_mission_evidence_bundle(replayed).valid is False

    truncated = bundle.model_dump(mode="json")
    truncated["envelopes"] = truncated["envelopes"][:-1]
    truncated["envelope_count"] -= 1
    assert (
        verify_portable_mission_evidence_bundle(
            truncated,
            expected_bundle_ref=bundle.bundle_ref,
            expected_envelope_count=bundle.envelope_count,
        ).valid
        is False
    )


def test_portable_bundle_rejects_cross_run_and_missing_binding(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    cross_run = bundle.model_dump(mode="json")
    cross_run["envelopes"][0]["run_ref"] = "run-ref:substituted"
    assert verify_portable_mission_evidence_bundle(cross_run).valid is False

    missing = bundle.model_dump(mode="json")
    del missing["envelopes"][0]["authority_decision_ref"]
    assert verify_portable_mission_evidence_bundle(missing).valid is False


def test_portable_builder_rejects_unverified_source_bindings(tmp_path: Path) -> None:
    manifests, leases, receipts, _ = _sources(tmp_path)
    forged_receipts = [
        receipts[0].model_copy(
            update={"target_binding_ref": "target-binding-ref:forged"}
        ),
        *receipts[1:],
    ]
    with pytest.raises(
        ValueError,
        match="PORTABLE_EVIDENCE_DISPATCH_SOURCE_MISMATCH",
    ):
        build_portable_mission_evidence_bundle(
            manifests,
            leases=leases,
            dispatch_receipts=forged_receipts,
        )

    wrong_lease = leases[0].model_copy(
        update={"domains": {**leases[0].domains, "shell": ["execute"]}}
    )
    with pytest.raises(ValueError, match="PORTABLE_EVIDENCE_LEASE_SCOPE_MISSING"):
        build_portable_mission_evidence_bundle(
            manifests,
            leases=[wrong_lease],
            dispatch_receipts=receipts,
        )

    revoked_lease = leases[0].model_copy(
        update={
            "status": "revoked",
            "constraints": {
                **leases[0].constraints,
                "revocation_reason_ref": "reason-ref:test-revocation",
                "revocation_idempotency_ref": "idempotency-ref:test-revocation",
            },
        }
    )
    before_revoke = build_portable_mission_evidence_bundle(
        manifests,
        leases=leases,
        dispatch_receipts=receipts,
    )
    after_revoke = build_portable_mission_evidence_bundle(
        manifests,
        leases=[revoked_lease],
        dispatch_receipts=receipts,
    )
    assert after_revoke == before_revoke


def test_portable_verifier_rejects_rehashed_cross_run_substitution(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path)
    payload = bundle.model_dump(mode="json")
    payload["envelopes"][1]["run_ref"] = "run-ref:substituted"
    _rehash_payload(payload)
    assert verify_portable_mission_evidence_bundle(payload).valid is False

    target_substitution = bundle.model_dump(mode="json")
    target_substitution["envelopes"][0]["target_binding_ref"] = (
        "target-binding-ref:substituted"
    )
    _rehash_payload(target_substitution)
    self_consistent_only = verify_portable_mission_evidence_bundle(
        target_substitution
    )
    assert self_consistent_only.valid is True
    assert self_consistent_only.caller_expected_binding_matched is False
    assert self_consistent_only.external_anchor_verified is False
    assert self_consistent_only.signature_verified is False
    assert self_consistent_only.cryptographic_authenticity_verified is False
    verification = verify_portable_mission_evidence_bundle(
        target_substitution,
        expected_bundle_ref=bundle.bundle_ref,
        expected_envelope_count=bundle.envelope_count,
    )
    assert verification.valid is False
    assert verification.external_anchor_verified is False
