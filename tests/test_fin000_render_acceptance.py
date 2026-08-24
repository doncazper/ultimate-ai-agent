from __future__ import annotations

import base64
import copy
import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from scripts import verify_fin000_render_acceptance as verifier


def _sign_all_roles(payload: dict[str, object]) -> dict[str, object]:
    trusted: list[dict[str, str]] = []
    for index, reviewer in enumerate(payload["reviewers"], start=1):
        private_key = Ed25519PrivateKey.generate()
        public_bytes = private_key.public_key().public_bytes_raw()
        reviewer["decision"] = "accepted"
        reviewer["reviewer_ref"] = f"reviewer-ref:fin000:independent-{index}"
        reviewer["trusted_key_ref"] = f"key-ref:fin000:independent-{index}"
        reviewer["receipt_ref"] = f"receipt-ref:fin000:review-{index}"
        reviewer["candidate_pack_digest"] = payload["candidate_pack_digest"]
        reviewer["acceptance_subject_digest"] = payload["acceptance_subject_digest"]
        reviewer["signature_base64url"] = (
            base64.urlsafe_b64encode(
                private_key.sign(
                    verifier.review_decision_message(
                        payload["ledger_ref"], payload["candidate_author_ref"], reviewer
                    )
                )
            )
            .decode()
            .rstrip("=")
        )
        trusted.append(
            {
                "role_ref": reviewer["role_ref"],
                "reviewer_ref": reviewer["reviewer_ref"],
                "key_ref": reviewer["trusted_key_ref"],
                "public_key_base64url": base64.urlsafe_b64encode(public_bytes)
                .decode()
                .rstrip("="),
                "public_key_fingerprint_ref": (
                    "sha256:" + hashlib.sha256(public_bytes).hexdigest()
                ),
            }
        )
    return {
        "registry_ref": "registry-ref:fin000:trusted-reviewers:v1",
        "candidate_pack_ref": "render-pack-ref:finance-compliance-v1",
        "status": "active",
        "reviewers": trusted,
    }


def test_fin000_pending_acceptance_ledger_is_consistent() -> None:
    failures, state = verifier.verify()

    assert failures == []
    assert state == "PENDING"
    assert verifier._load()["candidate_pack_digest"] == (
        "sha256:95c90c25855f6408ee22f9f050a07e373b79404de37c2f3c91a0005ac532fc72"
    )


def test_fin000_verifier_rejects_manifest_drift() -> None:
    payload = verifier._load()
    payload["assets"][0]["sha256"] = "0" * 64

    failures, state = verifier.verify(payload)

    assert state == "PENDING"
    assert any("manifest digest mismatch" in failure for failure in failures)


def test_fin000_verifier_enforces_exact_inventory_and_minimum_dimensions(
    monkeypatch,
) -> None:
    payload = verifier._load()
    payload["assets"][0]["filename"] = "replacement-desktop.png"

    failures, state = verifier.verify(payload)

    assert state == "PENDING"
    assert any("exact required filenames" in failure for failure in failures)

    payload = verifier._load()
    original = verifier._png_metadata

    def undersized(path):
        data, width, height = original(path)
        if path.name == "01-finance-command-desktop.png":
            return data, 100, 100
        return data, width, height

    monkeypatch.setattr(verifier, "_png_metadata", undersized)
    failures, state = verifier.verify(payload)

    assert state == "PENDING"
    assert any("dimensions below minimum" in failure for failure in failures)


def test_fin000_verifier_rejects_false_promotion() -> None:
    payload = verifier._load()
    payload["status"] = "accepted"
    payload["promotion_ready"] = True

    failures, state = verifier.verify(payload)

    assert state == "PENDING"
    assert (
        "promotion_ready does not match all integrity, checklist, and reviewer gates"
        in failures
    )
    assert "status must be pending_independent_review" in failures


def test_fin000_distinct_key_signatures_cannot_self_certify_human_independence() -> (
    None
):
    payload = copy.deepcopy(verifier._load())
    for check in payload["checklist"]:
        if check["decision"] == "pending_independent_review":
            check["decision"] = "accepted"
            check["evidence_refs"] = ["evidence-ref:fin000:independent-review"]
    trust_payload = _sign_all_roles(payload)

    failures, state = verifier.verify(payload, trusted_reviewers_payload=trust_payload)

    assert state == "PENDING"
    assert any(
        "identity authority is not externally configured" in item for item in failures
    )


def test_fin000_changes_requested_cannot_promote() -> None:
    payload = copy.deepcopy(verifier._load())
    payload["checklist"][2]["decision"] = "changes_requested"
    payload["checklist"][2]["evidence_refs"] = ["finding-ref:fin000:fixture-story"]
    payload["status"] = "changes_requested"

    failures, state = verifier.verify(payload)

    assert failures == []
    assert state == "PENDING"


def test_fin000_verifier_rejects_stale_or_self_review() -> None:
    payload = copy.deepcopy(verifier._load())
    reviewer = payload["reviewers"][0]
    reviewer["decision"] = "accepted"
    reviewer["reviewer_ref"] = payload["candidate_author_ref"]
    reviewer["trusted_key_ref"] = "key-ref:fin000:self-review"
    reviewer["receipt_ref"] = "receipt-ref:fin000:self-review"
    reviewer["candidate_pack_digest"] = "sha256:" + "0" * 64
    reviewer["acceptance_subject_digest"] = payload["acceptance_subject_digest"]
    reviewer["signature_base64url"] = "a" * 86

    failures, state = verifier.verify(payload)

    assert state == "PENDING"
    assert any("must be independent" in failure for failure in failures)


def test_fin000_verifier_rejects_fabricated_or_reused_reviewer_identity() -> None:
    payload = copy.deepcopy(verifier._load())
    for check in payload["checklist"]:
        if check["decision"] == "pending_independent_review":
            check["decision"] = "accepted"
            check["evidence_refs"] = ["evidence-ref:fin000:independent-review"]
    trust_payload = _sign_all_roles(payload)
    payload["reviewers"][1]["reviewer_ref"] = payload["reviewers"][0]["reviewer_ref"]
    payload["status"] = "accepted"
    payload["promotion_ready"] = True

    failures, state = verifier.verify(payload, trusted_reviewers_payload=trust_payload)

    assert state == "PENDING"
    assert any("identities must be distinct" in failure for failure in failures)
    assert any(
        "not enrolled for the exact role and key" in failure for failure in failures
    )


def test_fin000_verifier_rejects_stale_acceptance_subject_signature() -> None:
    payload = copy.deepcopy(verifier._load())
    trust_payload = _sign_all_roles(payload)
    payload["reviewers"][0]["acceptance_subject_digest"] = "sha256:" + "0" * 64

    failures, state = verifier.verify(payload, trusted_reviewers_payload=trust_payload)

    assert state == "PENDING"
    assert any("not bound to the acceptance subject" in failure for failure in failures)


def test_fin000_accepted_reviewer_cannot_retain_open_findings() -> None:
    payload = copy.deepcopy(verifier._load())
    trust_payload = _sign_all_roles(payload)
    payload["reviewers"][0]["finding_refs"] = ["finding-ref:fin000:unresolved"]

    failures, state = verifier.verify(payload, trusted_reviewers_payload=trust_payload)

    assert state == "PENDING"
    assert any("cannot retain open findings" in failure for failure in failures)


def test_fin000_verifier_rejects_unsafe_durable_content() -> None:
    payload = copy.deepcopy(verifier._load())
    payload["next_safe_action"] = "Inspect /Users/example/private material."

    failures, state = verifier.verify(payload)

    assert state == "PENDING"
    assert any("forbidden durable marker" in failure for failure in failures)

    for unsafe_ref in (
        "evidence-ref:sk_live_abc123",
        "evidence-ref:ghp_abcdef123456",
        "evidence-ref:tokenvalue",
    ):
        payload = copy.deepcopy(verifier._load())
        payload["checklist"][0]["evidence_refs"] = [unsafe_ref]

        failures, state = verifier.verify(payload)

        assert state == "PENDING"
        assert any(
            "evidence_refs must contain only safe refs" in item for item in failures
        )
