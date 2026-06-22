from pathlib import Path
import json

import pytest

from ultimate_ai_agent.core.memory import (
    MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
    MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS,
    MemorySourceProvenanceRef,
    MemorySourceRef,
    build_memory_source_provenance_ref,
    memory_source_provenance_policy_rows,
    memory_source_provenance_review_posture,
    validate_memory_source_provenance_ref,
)
from ultimate_ai_agent.core.memory.validation import validate_memory_source_ref
from ultimate_ai_agent.core.storage import FounderLoopRepository


DENIED_FLAGS = [
    "source_truth_authority",
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "connector_runtime_enabled",
    "account_auth_enabled",
    "provider_or_model_authority_allowed",
    "source_payload_storage_allowed",
    "private_content_storage_allowed",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]


def _safe_source_ref(source_kind: str) -> str:
    return f"source-ref:{source_kind.replace('_', '-')}:test"


def test_memory_source_provenance_contract_covers_required_source_kinds() -> None:
    assert MEMORY_SOURCE_PROVENANCE_CONTRACT_REF == (
        "contract-ref:memory-source-provenance:v1"
    )
    assert MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS == [
        "manual_note",
        "external_assistant_review_summary",
        "local_chat_summary",
        "local_coding_summary",
        "task_plan",
        "action_proposal",
        "evidence_timeline_ref",
        "read_only_calendar_metadata_ref",
        "read_only_email_metadata_ref",
        "crm_lite_business_record",
    ]

    policy_rows = memory_source_provenance_policy_rows()
    assert [row["source_kind"] for row in policy_rows] == (
        MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS
    )
    for row in policy_rows:
        assert row["review_required"] is True
        assert row["trusted_without_review"] is False
        assert row["source_payload_storage_allowed"] is False
        assert row["automatic_memory_write_allowed"] is False
        assert row["context_injection_allowed"] is False
        assert row["connector_runtime_allowed"] is False
        assert row["provider_or_model_authority_allowed"] is False
        assert row["account_auth_allowed"] is False


def test_memory_source_provenance_refs_are_review_only_and_safe() -> None:
    for source_kind in MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS:
        source = build_memory_source_provenance_ref(
            source_ref=_safe_source_ref(source_kind),
            source_kind=source_kind,
            provenance_ref=f"provenance-ref:{source_kind.replace('_', '-')}:test",
            safe_label=f"{source_kind.replace('_', ' ')} summary",
            evidence_refs=[f"evidence-ref:{source_kind.replace('_', '-')}:test"],
            source_readiness_refs=[
                f"source-readiness-ref:{source_kind.replace('_', '-')}:test"
            ],
        )
        assert validate_memory_source_provenance_ref(source) is True
        assert source.review_required is True
        assert source.trust_posture == "untrusted_until_reviewed"
        for flag in DENIED_FLAGS:
            assert getattr(source, flag) is False


@pytest.mark.parametrize("flag", DENIED_FLAGS)
def test_memory_source_provenance_rejects_authority_creep(flag: str) -> None:
    with pytest.raises(ValueError):
        MemorySourceProvenanceRef(
            source_ref="source-ref:manual-note:test",
            source_kind="manual_note",
            provenance_ref="provenance-ref:manual-note:test",
            safe_label="Manual note summary",
            **{flag: True},
        )


@pytest.mark.parametrize(
    "unsafe_update",
    [
        {"safe_label": "username: private actor"},
        {"safe_label": "provider_payload body"},
        {"redacted_summary_ref": "summary-ref:/Users/private"},
    ],
)
def test_memory_source_provenance_rejects_private_or_payload_markers(
    unsafe_update: dict[str, str],
) -> None:
    with pytest.raises(ValueError):
        MemorySourceProvenanceRef(
            source_ref="source-ref:manual-note:test",
            source_kind="manual_note",
            provenance_ref="provenance-ref:manual-note:test",
            **unsafe_update,
        )


def test_legacy_memory_source_validation_rejects_unsafe_provenance_markers() -> None:
    safe_source = MemorySourceRef(
        source_id="docs/canonical/09_roadmap.md",
        source_type="file",
        file_ref="file-ref:roadmap",
        locator="line:148",
    )
    assert validate_memory_source_ref(safe_source) is True

    with pytest.raises(ValueError):
        validate_memory_source_ref(
            MemorySourceRef(
                source_id="unsafe-source",
                source_type="file",
                file_ref="file-ref:unsafe",
                source_uri="/Users/private/workspace/source.txt",
            )
        )

    with pytest.raises(ValueError):
        validate_memory_source_ref(
            MemorySourceRef(
                source_id="unsafe-source",
                source_type="assistant",
                source_ref="source-ref:assistant-review:test",
                source_kind="external_assistant_review_summary",
                metadata={"provider_payload": "private-provider-body"},
            )
        )


def test_founder_loop_today_exposes_memory_source_provenance_contract(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    today = repo.today_summary()

    assert today["memory_source_provenance_contract_ref"] == (
        MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    )
    assert today["memory_source_required_kinds"] == (
        MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS
    )
    assert len(today["memory_source_policy"]) == len(
        MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS
    )
    posture = today["memory_source_review_posture"]
    assert posture == memory_source_provenance_review_posture()
    assert posture["review_required_before_recall"] is True
    assert posture["connector_runtime_enabled"] is False
    assert posture["account_auth_enabled"] is False
    assert posture["production_authority_enabled"] is False

    memory_item = today["memory_review_queue"][0]
    assert memory_item["source_policy_ref"] == MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    assert memory_item["source_kind"] == "manual_note"
    assert memory_item["source_trust_posture"] == "untrusted_until_reviewed"
    assert memory_item["source_review_required"] is True
    assert memory_item["safe_summary_only"] is True
    assert memory_item["accepted_as_truth"] is False
    assert memory_item["memory_write_authorized"] is False
    assert memory_item["context_injection_authorized"] is False
    assert memory_item["connector_runtime_allowed"] is False

    serialized = json.dumps(today, sort_keys=True).lower()
    for forbidden in [
        "raw_prompt",
        "raw_response",
        "provider_payload",
        "api_key",
        "authorization",
        "cookie",
        "password",
        "private_key",
        str(tmp_path).lower(),
    ]:
        assert forbidden not in serialized
