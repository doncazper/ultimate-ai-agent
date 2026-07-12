from pathlib import Path

import pytest

from ultimate_ai_agent.core.memory import (
    MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
    MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_REVIEW_DECISION_REQUIRED_BLOCKED_STATE_REFS,
    MEMORY_REVIEW_DECISION_REQUIRED_REF_FIELDS,
    MEMORY_REVIEW_DECISION_STATES,
    MemoryReviewDecisionEnvelope,
    build_memory_review_decision_envelope,
    memory_review_decision_authority_posture,
    memory_review_decision_state_rows,
    validate_memory_review_decision_envelope,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


DENIED_FLAGS = [
    "memory_write_authorized",
    "memory_delete_authorized",
    "memory_export_authorized",
    "context_injection_authorized",
    "connector_runtime_enabled",
    "account_auth_enabled",
    "provider_or_model_authority_allowed",
    "source_truth_authority",
    "accepted_as_recall",
    "retention_execution_authorized",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]


def _decision(**overrides: object) -> MemoryReviewDecisionEnvelope:
    data: dict[str, object] = {
        "decision_ref": "memory-review-decision:test",
        "review_ref": "memory-review:test",
        "decision_state": "accept",
        "actor_ref": "actor-ref:local-operator",
        "safe_summary": "Review decision envelope for a safe memory candidate.",
        "source_refs": ["source-ref:manual-note:test"],
        "provenance_refs": ["provenance-ref:manual-note:test"],
        "evidence_refs": ["evidence-ref:memory-review:test"],
        "audit_refs": ["audit-plan:memory-review:test"],
        "receipt_refs": ["receipt-plan:memory-review:test"],
    }
    data.update(overrides)
    return MemoryReviewDecisionEnvelope(**data)


def test_memory_review_decision_contract_covers_required_states() -> None:
    assert MEMORY_REVIEW_DECISION_CONTRACT_REF == (
        "contract-ref:memory-review-decision:v1"
    )
    assert MEMORY_REVIEW_DECISION_STATES == [
        "accept",
        "correct",
        "reject",
        "defer",
        "merge",
        "supersede",
        "expire",
        "forget_request",
    ]
    assert MEMORY_REVIEW_DECISION_REQUIRED_REF_FIELDS == [
        "actor_ref",
        "source_refs",
        "provenance_refs",
        "evidence_refs",
        "stale_state",
        "retention_posture",
        "audit_refs",
        "receipt_refs",
        "blocked_state_refs",
    ]

    rows = memory_review_decision_state_rows()
    assert [row["decision_state"] for row in rows] == MEMORY_REVIEW_DECISION_STATES
    for row in rows:
        expected_reviewed_recall_write = row["decision_state"] in {"accept", "correct"}
        assert row["review_required"] is True
        assert row["actor_ref_required"] is True
        assert row["source_refs_required"] is True
        assert row["provenance_refs_required"] is True
        assert row["evidence_refs_required"] is True
        assert row["audit_refs_required"] is True
        assert row["receipt_refs_required"] is True
        assert row["blocked_state_refs_required"] is True
        assert row["writes_authorized"] is expected_reviewed_recall_write
        assert row["write_scope_ref"] == (
            MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
            if expected_reviewed_recall_write
            else "blocked-state:no-memory-write"
        )
        assert row["deletes_authorized"] is False
        assert row["exports_authorized"] is False
        assert row["context_injection_authorized"] is False
        assert row["accepted_as_recall"] is expected_reviewed_recall_write


def test_memory_review_decision_envelopes_are_review_only() -> None:
    for decision_state in MEMORY_REVIEW_DECISION_STATES:
        envelope = build_memory_review_decision_envelope(
            decision_ref=f"memory-review-decision:{decision_state.replace('_', '-')}",
            review_ref="memory-review:test",
            decision_state=decision_state,
            actor_ref="actor-ref:local-operator",
            safe_summary="Review decision envelope for a safe memory candidate.",
            source_refs=["source-ref:manual-note:test"],
            provenance_refs=["provenance-ref:manual-note:test"],
            evidence_refs=["evidence-ref:memory-review:test"],
            audit_refs=["audit-plan:memory-review:test"],
            receipt_refs=["receipt-plan:memory-review:test"],
        )
        assert validate_memory_review_decision_envelope(envelope) is True
        assert envelope.review_only is True
        for flag in DENIED_FLAGS:
            assert getattr(envelope, flag) is False


@pytest.mark.parametrize("flag", DENIED_FLAGS)
def test_memory_review_decision_envelope_rejects_authority_creep(flag: str) -> None:
    with pytest.raises(ValueError):
        _decision(**{flag: True})


@pytest.mark.parametrize(
    "missing_field",
    [
        "source_refs",
        "provenance_refs",
        "evidence_refs",
        "audit_refs",
        "receipt_refs",
        "blocked_state_refs",
    ],
)
def test_memory_review_decision_envelope_requires_refs(missing_field: str) -> None:
    with pytest.raises(ValueError):
        _decision(**{missing_field: []})


def test_memory_review_decision_envelope_requires_core_blocked_states() -> None:
    with pytest.raises(ValueError):
        _decision(blocked_state_refs=["blocked-state:no-memory-write"])

    envelope = _decision()
    for blocked_ref in MEMORY_REVIEW_DECISION_REQUIRED_BLOCKED_STATE_REFS:
        assert blocked_ref in envelope.blocked_state_refs


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("decision_ref", "memory-review-decision:raw_prompt:test"),
        ("review_ref", "memory-review:provider_payload:test"),
        ("actor_ref", "actor-ref:username:test"),
        ("source_refs", ["source-ref:raw-prompt:test"]),
        ("provenance_refs", ["provenance-ref:raw-response:test"]),
        ("evidence_refs", ["evidence-ref:raw-log:test"]),
        ("audit_refs", ["audit-plan:account-identifier:test"]),
        ("receipt_refs", ["receipt-plan:credential:test"]),
        ("blocked_state_refs", ["blocked-state:raw-private-content"]),
    ],
)
def test_memory_review_decision_envelope_rejects_unsafe_ref_markers(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(ValueError):
        _decision(**{field_name: value})


def test_memory_review_decision_envelope_binds_source_kind_to_refs() -> None:
    _decision(
        source_kind="local_chat_summary",
        source_refs=["source-ref:local-chat-summary:test"],
        provenance_refs=["provenance-ref:local-chat-summary:test"],
    )

    with pytest.raises(ValueError):
        _decision(
            source_kind="local_chat_summary",
            source_refs=["source-ref:manual-note:test"],
            provenance_refs=["provenance-ref:local-chat-summary:test"],
        )
    with pytest.raises(ValueError):
        _decision(
            source_kind="local_chat_summary",
            source_refs=["source-ref:local-chat-summary:test"],
            provenance_refs=["provenance-ref:manual-note:test"],
        )


@pytest.mark.parametrize(
    "unsafe_summary",
    [
        "raw_prompt material",
        "raw_response material",
        "provider_payload body",
        "raw path marker",
        "raw log marker",
        "account identifier marker",
        "username: private actor",
        "hostname: private host",
        "credential material",
        "raw_private_content marker",
    ],
)
def test_memory_review_decision_envelope_rejects_raw_private_markers(
    unsafe_summary: str,
) -> None:
    with pytest.raises(ValueError):
        _decision(safe_summary=unsafe_summary)


def test_founder_loop_today_exposes_memory_review_decision_contract(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    today = repo.today_summary()

    assert today["memory_review_decision_contract_ref"] == (
        MEMORY_REVIEW_DECISION_CONTRACT_REF
    )
    assert [row["decision_state"] for row in today["memory_review_decision_states"]] == (
        MEMORY_REVIEW_DECISION_STATES
    )
    assert today["memory_review_decision_required_ref_fields"] == (
        MEMORY_REVIEW_DECISION_REQUIRED_REF_FIELDS
    )
    assert today["memory_review_decision_authority_posture"] == (
        memory_review_decision_authority_posture()
    )

    item = today["memory_review_queue"][0]
    assert item["decision_contract_ref"] == MEMORY_REVIEW_DECISION_CONTRACT_REF
    assert item["available_decision_states"] == MEMORY_REVIEW_DECISION_STATES
    assert item["decision_capture_status"] == "review_needed_no_decision_captured"
    assert item["decision_actor_ref"] == "actor-ref:local-operator-review-required"
    assert item["decision_source_provenance_contract_ref"] == (
        "contract-ref:memory-source-provenance:v1"
    )
    assert item["decision_source_kind"] == "manual_note"
    assert item["decision_source_trust_posture"] == "untrusted_until_reviewed"
    assert item["decision_redaction_status"] == "redacted_summary_only"
    assert item["decision_audit_refs"]
    assert item["decision_receipt_refs"]
    assert "blocked-state:no-memory-write" in item["decision_blocked_state_refs"]
    assert "blocked-state:no-memory-delete" in item["decision_blocked_state_refs"]
    assert "blocked-state:no-memory-export" in item["decision_blocked_state_refs"]
    assert item["decision_review_only"] is True
    assert item["memory_write_authorized"] is False
    assert item["memory_delete_authorized"] is False
    assert item["memory_export_authorized"] is False
    assert item["retention_execution_authorized"] is False
    assert item["accepted_as_truth"] is False
