from pathlib import Path

import pytest

from ultimate_ai_agent.core.memory import (
    BUSINESS_MEMORY_CANDIDATE_KINDS,
    BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
    BUSINESS_MEMORY_QUALITY_STATES,
    BUSINESS_MEMORY_REQUIRED_BLOCKED_STATE_REFS,
    BUSINESS_MEMORY_REQUIRED_REF_FIELDS,
    BusinessMemoryQualityEnvelope,
    business_memory_authority_posture,
    business_memory_candidate_kind_rows,
    business_memory_quality_ref,
    business_memory_quality_state_rows,
    business_memory_surface_bindings,
    validate_business_memory_quality_envelope,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


DENIED_FLAGS = [
    "memory_write_authorized",
    "memory_delete_authorized",
    "memory_export_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "external_crm_write_authorized",
    "account_sync_authorized",
    "connector_runtime_enabled",
    "account_auth_enabled",
    "provider_or_model_authority_allowed",
    "source_truth_authority",
    "accepted_as_recall",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]


def _quality(**overrides: object) -> BusinessMemoryQualityEnvelope:
    data: dict[str, object] = {
        "review_ref": "memory-review:test",
        "candidate_ref": "business-memory-candidate:preference:test",
        "candidate_kind": "preference",
        "safe_summary": "Business memory quality envelope for a safe candidate.",
        "source_refs": ["source-ref:manual-note:test"],
        "provenance_refs": ["provenance-ref:manual-note:test"],
        "evidence_refs": ["evidence-ref:memory-review:test"],
        "related_entity_refs": ["business-memory-entity:preference:test"],
    }
    data.update(overrides)
    return BusinessMemoryQualityEnvelope(**data)


def test_business_memory_contract_covers_candidate_kinds_and_quality_states() -> None:
    assert BUSINESS_MEMORY_QUALITY_CONTRACT_REF == (
        "contract-ref:business-memory-quality-controls:v1"
    )
    assert BUSINESS_MEMORY_CANDIDATE_KINDS == [
        "profile",
        "project",
        "relationship",
        "organization",
        "deal",
        "opportunity",
        "promise",
        "follow_up",
        "preference",
        "decision",
        "commitment",
    ]
    assert BUSINESS_MEMORY_QUALITY_STATES == [
        "duplicate",
        "conflict",
        "stale_expired",
        "low_confidence",
        "source_missing",
        "evidence_missing",
        "blocked",
        "reviewed",
    ]
    assert BUSINESS_MEMORY_REQUIRED_REF_FIELDS == [
        "review_ref",
        "candidate_ref",
        "source_refs",
        "provenance_refs",
        "evidence_refs",
        "quality_state_refs",
        "related_entity_refs",
        "blocker_refs",
    ]

    kind_rows = business_memory_candidate_kind_rows()
    assert [row["candidate_kind"] for row in kind_rows] == (
        BUSINESS_MEMORY_CANDIDATE_KINDS
    )
    for row in kind_rows:
        assert row["review_required"] is True
        assert row["safe_summary_only"] is True
        assert row["source_refs_required"] is True
        assert row["provenance_refs_required"] is True
        assert row["evidence_refs_required"] is True
        assert row["quality_posture_required"] is True
        assert row["crm_write_authorized"] is False
        assert row["account_sync_authorized"] is False
        assert row["accepted_as_recall"] is False

    quality_rows = business_memory_quality_state_rows()
    assert [
        row["quality_state"] for row in quality_rows
    ] == BUSINESS_MEMORY_QUALITY_STATES
    for row in quality_rows:
        assert row["blocks_unreviewed_recall"] is True
        assert row["requires_operator_review"] is True
        assert row["requires_safe_refs"] is True
        assert row["authorizes_memory_write"] is False
        assert row["authorizes_crm_write"] is False
        assert row["authorizes_context_injection"] is False


def test_business_memory_quality_envelope_is_safe_refs_only() -> None:
    envelope = _quality()

    assert validate_business_memory_quality_envelope(envelope) is True
    assert envelope.safe_refs_only is True
    assert envelope.review_required_before_recall is True
    assert envelope.quality_state_refs == [
        business_memory_quality_ref("low_confidence"),
        business_memory_quality_ref("blocked"),
    ]
    for blocked_ref in BUSINESS_MEMORY_REQUIRED_BLOCKED_STATE_REFS:
        assert blocked_ref in envelope.blocker_refs
    for flag in DENIED_FLAGS:
        assert getattr(envelope, flag) is False


@pytest.mark.parametrize("flag", DENIED_FLAGS)
def test_business_memory_quality_envelope_rejects_authority_creep(flag: str) -> None:
    with pytest.raises(ValueError):
        _quality(**{flag: True})


@pytest.mark.parametrize(
    "missing_field",
    ["source_refs", "provenance_refs", "evidence_refs", "blocker_refs"],
)
def test_business_memory_quality_envelope_requires_safe_refs(
    missing_field: str,
) -> None:
    with pytest.raises(ValueError):
        _quality(**{missing_field: []})


def test_business_memory_quality_envelope_requires_candidate_kind_ref_binding() -> None:
    with pytest.raises(ValueError):
        _quality(
            candidate_ref="business-memory-candidate:relationship:test",
            candidate_kind="preference",
        )


def test_business_memory_quality_envelope_binds_source_kind_to_refs() -> None:
    with pytest.raises(ValueError):
        _quality(
            source_kind="local_chat_summary",
            source_refs=["source-ref:manual-note:test"],
            provenance_refs=["provenance-ref:local-chat-summary:test"],
        )
    with pytest.raises(ValueError):
        _quality(
            source_kind="local_chat_summary",
            source_refs=["source-ref:local-chat-summary:test"],
            provenance_refs=["provenance-ref:manual-note:test"],
        )


def test_business_memory_quality_envelope_requires_state_specific_refs() -> None:
    with pytest.raises(ValueError):
        _quality(quality_state_refs=[business_memory_quality_ref("duplicate")])
    with pytest.raises(ValueError):
        _quality(quality_state_refs=[business_memory_quality_ref("conflict")])
    with pytest.raises(ValueError):
        _quality(quality_state_refs=[business_memory_quality_ref("source_missing")])
    with pytest.raises(ValueError):
        _quality(quality_state_refs=[business_memory_quality_ref("evidence_missing")])

    duplicate = _quality(
        quality_state_refs=[business_memory_quality_ref("duplicate")],
        duplicate_of_refs=["business-memory-candidate:preference:older"],
    )
    assert validate_business_memory_quality_envelope(duplicate) is True
    conflict = _quality(
        quality_state_refs=[business_memory_quality_ref("conflict")],
        conflict_with_refs=["business-memory-candidate:preference:other"],
    )
    assert validate_business_memory_quality_envelope(conflict) is True


@pytest.mark.parametrize(
    "field_name, unsafe_value",
    [
        ("review_ref", "memory-review:raw_prompt"),
        ("candidate_ref", "business-memory-candidate:preference:raw-response"),
        ("source_refs", ["source-ref:raw-log:test"]),
        ("provenance_refs", ["provenance-ref:provider-payload:test"]),
        ("evidence_refs", ["evidence-ref:account-identifier:test"]),
        ("related_entity_refs", ["business-memory-entity:preference:credential"]),
        ("blocker_refs", ["blocked-state:raw-private-content"]),
    ],
)
def test_business_memory_quality_envelope_rejects_unsafe_ref_markers(
    field_name: str,
    unsafe_value: object,
) -> None:
    with pytest.raises(ValueError):
        _quality(**{field_name: unsafe_value})


@pytest.mark.parametrize(
    "unsafe_summary",
    [
        "raw prompt material",
        "raw response material",
        "provider payload body",
        "raw path marker",
        "raw log marker",
        "account identifier marker",
        "username: private actor",
        "hostname: private host",
        "credential material",
        "raw private content marker",
    ],
)
def test_business_memory_quality_envelope_rejects_raw_private_markers(
    unsafe_summary: str,
) -> None:
    with pytest.raises(ValueError):
        _quality(safe_summary=unsafe_summary)


def test_founder_loop_today_exposes_business_memory_quality_contract(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    today = repo.today_summary()

    assert (
        today["business_memory_quality_contract_ref"]
        == BUSINESS_MEMORY_QUALITY_CONTRACT_REF
    )
    assert [
        row["candidate_kind"] for row in today["business_memory_candidate_kinds"]
    ] == (BUSINESS_MEMORY_CANDIDATE_KINDS)
    assert [
        row["quality_state"] for row in today["business_memory_quality_states"]
    ] == (BUSINESS_MEMORY_QUALITY_STATES)
    assert today["business_memory_required_ref_fields"] == (
        BUSINESS_MEMORY_REQUIRED_REF_FIELDS
    )
    assert (
        today["business_memory_surface_bindings"] == business_memory_surface_bindings()
    )
    assert today["business_memory_authority_posture"] == (
        business_memory_authority_posture()
    )
    assert today["business_memory_status"] == (
        "implemented_review_queue_safe_ref_quality_metadata_contract"
    )
    assert (
        "contract-ref:business-memory-quality-controls-missing"
        not in (today["memory_review_missing_contract_refs"])
    )
    assert "no_external_crm_write" in today["memory_review_blocked_states"]
    assert "no_account_sync" in today["memory_review_blocked_states"]
    assert "no_automatic_recall" in today["memory_review_blocked_states"]

    memory_item = today["memory_review_queue"][0]
    assert memory_item["candidate_kind"] == "preference"
    assert memory_item["business_memory_quality_contract_ref"] == (
        BUSINESS_MEMORY_QUALITY_CONTRACT_REF
    )
    assert memory_item["business_memory_candidate_ref"] == (
        "business-memory-candidate:preference:memory-review-founder-loop-preferences"
    )
    assert memory_item["business_memory_candidate_kind"] == "preference"
    assert memory_item["business_memory_source_provenance_contract_ref"] == (
        "contract-ref:memory-source-provenance:v1"
    )
    assert memory_item["business_memory_source_kind"] == "manual_note"
    assert memory_item["business_memory_source_trust_posture"] == (
        "untrusted_until_reviewed"
    )
    assert memory_item["business_memory_redaction_status"] == "redacted_summary_only"
    assert memory_item["business_memory_quality_state_refs"] == [
        business_memory_quality_ref("blocked"),
        business_memory_quality_ref("low_confidence"),
    ]
    assert memory_item["business_memory_safe_refs_only"] is True
    assert memory_item["business_memory_review_required_before_recall"] is True
    assert memory_item["business_memory_accepted_as_recall"] is False
    assert memory_item["business_memory_crm_write_authorized"] is False
    assert memory_item["business_memory_account_sync_authorized"] is False
    assert memory_item["business_memory_context_injection_authorized"] is False
    for blocked_ref in BUSINESS_MEMORY_REQUIRED_BLOCKED_STATE_REFS:
        assert blocked_ref in memory_item["business_memory_blocker_refs"]
