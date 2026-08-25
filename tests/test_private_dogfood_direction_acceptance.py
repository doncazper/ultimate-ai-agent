from __future__ import annotations

import copy

from scripts import verify_private_dogfood_direction_acceptance as verifier


def test_checked_in_founder_direction_acceptance_is_valid() -> None:
    failures, advisories, current_match = verifier.verify()

    assert failures == []
    assert advisories == []
    assert current_match is True


def test_q25_recorded_asset_tampering_fails_closed() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["programs"]["q25"]["assets"][0]["sha256"] = "sha256:" + "0" * 64

    failures, _, _ = verifier.verify(payload)

    assert "Q25 accepted asset digest does not match its recorded assets" in failures

    payload["programs"]["q25"]["asset_digest"] = verifier._canonical_q25_digest(
        payload["programs"]["q25"]["assets"]
    )
    failures, _, _ = verifier.verify(payload)
    assert any("programs.q25.asset_digest" in item for item in failures)


def test_q25_extra_surface_inventory_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(
        verifier,
        "_current_q25_inventory",
        lambda root=verifier.ROOT: (
            verifier.EXPECTED_Q25_PATH_REFS
            | {
                "repo-path-ref:docs/design/control_center_north_star/renders/social-media-v1/05-extra.jpg"
            }
        ),
    )

    failures, _, _ = verifier.verify()

    assert "current Q25 surface inventory drifted" in failures


def test_q25_cosmetic_asset_drift_is_advisory(monkeypatch) -> None:
    original = verifier.hashlib.sha256

    class ChangedDigest:
        def hexdigest(self) -> str:
            return "1" * 64

    def changed_only_for_bytes(value=b""):
        if value.startswith(b"\xff\xd8"):
            return ChangedDigest()
        return original(value)

    monkeypatch.setattr(verifier.hashlib, "sha256", changed_only_for_bytes)
    failures, advisories, current_match = verifier.verify()

    assert failures == []
    assert current_match is False
    assert any("Q25 surface bytes changed" in item for item in advisories)


def test_q26_pack_integrity_stays_fail_closed() -> None:
    fin_ledger = copy.deepcopy(verifier._load(verifier.FIN_LEDGER_PATH))
    fin_ledger["candidate_pack_digest"] = "sha256:" + "0" * 64

    failures, advisories, _ = verifier.verify(fin_ledger_payload=fin_ledger)

    assert "current FIN-000 candidate pack integrity check failed" in failures
    assert any(
        "Q26 independent candidate pack revision changed" in item for item in advisories
    )


def test_authority_cannot_be_granted_by_direction_acceptance() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["authority_posture"]["bank_connectivity_allowed"] = True

    failures, _, _ = verifier.verify(payload)

    assert any("bank_connectivity_allowed" in item for item in failures)


def test_required_remaining_gate_cannot_be_removed() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["programs"]["q25"]["remaining_gate_refs"].pop()

    failures, _, _ = verifier.verify(payload)

    assert "Q25 remaining gates drifted from the exact accepted set" in failures


def test_secret_like_receipt_ref_is_rejected() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["decision_receipt_ref"] = "receipt-ref:sk_live_abc123"

    failures, _, _ = verifier.verify(payload)

    assert any("secret-like durable content" in item for item in failures)
