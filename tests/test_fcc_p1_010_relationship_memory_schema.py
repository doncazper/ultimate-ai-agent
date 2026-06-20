from importlib import import_module

import pytest


def _memory():
    try:
        return import_module("ultimate_ai_agent.core.memory")
    except ModuleNotFoundError as exc:
        pytest.fail(f"FCC relationship memory schema package missing: {exc}")


def test_fcc_p1_010_builds_relationship_memory_candidate_contract() -> None:
    memory = _memory()
    candidate = memory.build_fcc_relationship_memory_candidate(
        memory.FCCRelationshipMemoryCandidateKind.relationship
    )

    assert candidate.candidate_ref == "fcc-memory-candidate-ref:fcc-p1-010:relationship"
    assert candidate.candidate_kind == memory.FCCRelationshipMemoryCandidateKind.relationship
    assert candidate.contract_only is True
    assert candidate.review_only is True
    assert candidate.safe_refs_required is True
    assert candidate.memory_is_recall_not_truth is True
    assert candidate.review_state == memory.FCCRelationshipMemoryReviewState.review_needed
    assert candidate.provenance_refs
    assert candidate.source_refs
    assert candidate.evidence_refs
    assert candidate.related_person_refs
    assert candidate.related_org_refs
    assert candidate.related_project_refs
    assert candidate.related_deal_refs
    assert candidate.related_follow_up_refs
    assert "Memory remains recall, not truth" in candidate.redacted_summary
    assert "not truth, approval" in candidate.authority_boundary
    assert candidate.confidence_posture == "safe_summary_unverified_until_review"
    assert candidate.correction_posture == (
        "correction_requires_scoped_memory_write_contract"
    )
    assert candidate.rejection_posture == (
        "rejection_is_review_state_only_until_capture_contract"
    )
    assert candidate.retention_posture == "retention_policy_not_bound"
    assert candidate.delete_posture == "delete_execution_not_scoped"
    assert candidate.export_posture == "export_is_redacted_review_posture_only"
    assert candidate.stale_state == "recheck_source_refs_before_memory_use"
    assert "contract-ref:fcc-p1-010:memory-write-policy-missing" in (
        candidate.missing_contract_refs
    )
    assert "blocked-state-ref:fcc-p1-010:no-automatic-memory-write" in (
        candidate.blocked_states
    )
    assert "blocked-state-ref:fcc-p1-010:no-context-injection" in (
        candidate.blocked_states
    )
    assert candidate.side_effects_performed == []

    for reason_code in [
        "FCC_P1_010_RELATIONSHIP_MEMORY_SCHEMA",
        "FCC_MEMORY_RECALL_NOT_TRUTH",
        "FCC_MEMORY_SAFE_REFS_ONLY",
        "FCC_MEMORY_REVIEW_ONLY_NO_WRITES",
        "FCC_MEMORY_CONTEXT_INJECTION_BLOCKED",
    ]:
        assert reason_code in candidate.reason_codes


def test_fcc_p1_010_builds_follow_up_memory_candidate_contract() -> None:
    memory = _memory()
    candidate = memory.build_fcc_relationship_memory_candidate("follow-up")

    assert candidate.candidate_kind == memory.FCCRelationshipMemoryCandidateKind.follow_up
    assert candidate.candidate_ref == "fcc-memory-candidate-ref:fcc-p1-010:follow_up"
    assert candidate.related_follow_up_refs == [
        "follow-up-ref:fcc-p1-010:reviewed-safe-follow-up"
    ]
    assert candidate.automatic_memory_write_enabled is False
    assert candidate.memory_delete_execution_enabled is False
    assert candidate.memory_export_execution_enabled is False
    assert candidate.context_injection_enabled is False


def test_fcc_p1_010_supports_all_candidate_kinds() -> None:
    memory = _memory()

    for candidate_kind in memory.FCCRelationshipMemoryCandidateKind:
        candidate = memory.build_fcc_relationship_memory_candidate(candidate_kind)
        assert candidate.candidate_kind == candidate_kind
        assert candidate.candidate_ref.startswith("fcc-memory-candidate-ref:")
        assert candidate.provenance_refs[0].startswith("provenance-ref:")
        assert candidate.source_refs[0].startswith("source-ref:")
        assert candidate.evidence_refs[0].startswith("evidence-ref:")


def test_fcc_p1_010_requires_safe_refs_and_review_posture() -> None:
    memory = _memory()
    candidate = memory.build_fcc_relationship_memory_candidate()

    for update, reason in [
        ({"provenance_refs": []}, "PROVENANCE_REFS_REQUIRED"),
        ({"source_refs": []}, "SOURCE_REFS_REQUIRED"),
        ({"evidence_refs": []}, "EVIDENCE_REFS_REQUIRED"),
        ({"missing_contract_refs": []}, "MISSING_CONTRACT_REFS_REQUIRED"),
        ({"blocked_states": []}, "BLOCKED_STATES_REQUIRED"),
        ({"contract_only": False}, "CONTRACT_ONLY_REQUIRED"),
        ({"review_only": False}, "REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "SAFE_REFS_REQUIRED"),
        ({"memory_is_recall_not_truth": False}, "MEMORY_RECALL_NOT_TRUTH_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            memory.validate_fcc_relationship_memory_candidate(
                candidate.model_copy(update=update)
            )


def test_fcc_p1_010_denies_authority_runtime_and_mutation_flags() -> None:
    memory = _memory()
    candidate = memory.build_fcc_relationship_memory_candidate()

    for field, reason in [
        ("approval_authority_enabled", "APPROVAL_AUTHORITY_DENIED"),
        ("automatic_memory_write_enabled", "AUTOMATIC_MEMORY_WRITE_DENIED"),
        ("memory_delete_execution_enabled", "MEMORY_DELETE_EXECUTION_DENIED"),
        ("memory_export_execution_enabled", "MEMORY_EXPORT_EXECUTION_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("model_provider_authority_enabled", "MODEL_PROVIDER_AUTHORITY_DENIED"),
        ("connector_runtime_enabled", "CONNECTOR_RUNTIME_DENIED"),
        ("connector_write_enabled", "CONNECTOR_WRITE_DENIED"),
        ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
        ("email_calendar_fetch_enabled", "EMAIL_CALENDAR_FETCH_DENIED"),
        ("background_sync_enabled", "BACKGROUND_SYNC_DENIED"),
        ("backend_route_added", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
        ("public_beta_claim_enabled", "PUBLIC_BETA_CLAIM_DENIED"),
        ("public_distribution_claim_enabled", "PUBLIC_DISTRIBUTION_CLAIM_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("raw_transcript_enabled", "RAW_TRANSCRIPT_DENIED"),
        ("raw_prompt_enabled", "RAW_PROMPT_DENIED"),
        ("raw_source_content_enabled", "RAW_SOURCE_CONTENT_DENIED"),
        ("private_connector_content_enabled", "PRIVATE_CONNECTOR_CONTENT_DENIED"),
        ("private_material_enabled", "PRIVATE_MATERIAL_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            memory.validate_fcc_relationship_memory_candidate(
                candidate.model_copy(update={field: True})
            )

    with pytest.raises(ValueError, match="SIDE_EFFECTS_DENIED"):
        memory.validate_fcc_relationship_memory_candidate(
            candidate.model_copy(update={"side_effects_performed": ["write-memory"]})
        )


@pytest.mark.parametrize(
    ("update", "private_value"),
    [
        ({"metadata": {"raw_transcript": "private transcript"}}, "private transcript"),
        ({"metadata": {"prompt": "private prompt"}}, "private prompt"),
        ({"metadata": {"source_text": "private source"}}, "private source"),
        (
            {"metadata": {"private_connector_content": "private connector note"}},
            "private connector note",
        ),
        ({"metadata": {"participant": "founder@example.com"}}, "founder@example"),
        ({"metadata": {"person_name": "Private Person"}}, "Private Person"),
        ({"metadata": {"account_id": "mailbox-primary"}}, "mailbox-primary"),
        ({"metadata": {"local_path": "/Users/example/private.txt"}}, "/Users/example"),
        ({"metadata": {"log": "private log line"}}, "private log line"),
        ({"metadata": {"environment_dump": "PRIVATE_ENV=1"}}, "PRIVATE_ENV"),
        ({"metadata": {"password": "private-password"}}, "private-password"),
        ({"metadata": {"access_token": "private-token"}}, "private-token"),
        ({"metadata": {"cookie": "private-cookie"}}, "private-cookie"),
        ({"metadata": {"secret": "private-secret"}}, "private-secret"),
        (
            {"metadata": {"provider_payload": "private provider payload"}},
            "private provider payload",
        ),
        ({"redacted_summary": "Prompt: private memory"}, "private memory"),
    ],
)
def test_fcc_p1_010_redaction_regressions_do_not_echo_private_content(
    update: dict[str, object], private_value: str
) -> None:
    memory = _memory()
    candidate = memory.build_fcc_relationship_memory_candidate()

    with pytest.raises(ValueError) as exc_info:
        memory.validate_fcc_relationship_memory_candidate(
            candidate.model_copy(update=update)
        )

    message = str(exc_info.value)
    assert "FCC_MEMORY_PRIVATE_" in message
    assert private_value.lower() not in message.lower()


def test_fcc_p1_010_rejects_raw_extra_fields_without_echoing_content() -> None:
    memory = _memory()
    candidate = memory.build_fcc_relationship_memory_candidate()
    payload = candidate.model_dump(mode="python")
    payload["raw_source_text"] = "Private relationship detail."

    with pytest.raises(ValueError) as exc_info:
        memory.validate_fcc_relationship_memory_candidate(payload)

    assert str(exc_info.value) == "FCC_MEMORY_PRIVATE_FIELD_DENIED"
    assert "relationship detail" not in str(exc_info.value).lower()
