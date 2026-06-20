from importlib import import_module

import pytest


def _connectors():
    try:
        return import_module("ultimate_ai_agent.core.connectors")
    except ModuleNotFoundError as exc:
        pytest.fail(f"FCC draft email proposal connector contract missing: {exc}")


def test_fcc_p1_009_builds_draft_only_email_response_proposal_contract() -> None:
    connectors = _connectors()
    proposal = connectors.build_fcc_draft_email_response_proposal_envelope()

    assert (
        proposal.status
        == connectors.FCCDraftEmailResponseProposalStatus.draft_email_response_proposal_contract
    )
    assert proposal.draft_proposal_contract_ref == (
        "fcc-draft-email-response-proposal-contract:fcc-p1-009"
    )
    assert proposal.contract_only is True
    assert proposal.read_only is True
    assert proposal.draft_only is True
    assert proposal.safe_refs_required is True
    assert proposal.connector_runtime_missing is True
    assert proposal.side_effects_performed == []
    assert proposal.proposal_ref.startswith("draft-email-response-proposal-ref:")
    assert proposal.source_email_metadata_refs
    assert proposal.thread_ref.startswith("thread-ref:")
    assert proposal.sender_identity_ref.startswith("sender-identity-ref:")
    assert proposal.recipient_identity_refs
    assert proposal.account_identity_ref.startswith("account-identity-ref:")
    assert proposal.time_window_ref.startswith("time-window-ref:")
    assert proposal.follow_up_refs
    assert proposal.purpose_label == "follow_up_review"
    assert proposal.intent_label == "operator_reviewed_reply_outline"
    assert proposal.tone_label == "concise_professional"
    assert proposal.style_label == "safe_outline_only"
    assert proposal.draft_summary_ref.startswith("draft-summary-ref:")
    assert proposal.response_outline_ref.startswith("response-outline-ref:")
    assert proposal.redacted_response_outline
    assert proposal.evidence_refs
    assert proposal.source_readiness_refs
    assert proposal.audit_ref.startswith("audit-ref:")
    assert proposal.replay_ref.startswith("replay-ref:")
    assert proposal.approval_posture == (
        "approval_refs_are_identifiers_only_not_send_authority"
    )
    assert proposal.blocked_send_write_states == [
        "blocked-state-ref:fcc-p1-009:no-email-send",
        "blocked-state-ref:fcc-p1-009:no-email-write",
        "blocked-state-ref:fcc-p1-009:no-account-action",
    ]
    assert proposal.send_enabled is False
    assert proposal.reply_enabled is False
    assert proposal.forward_enabled is False
    assert proposal.account_auth_enabled is False
    assert proposal.account_write_enabled is False
    assert proposal.email_fetch_runtime_enabled is False
    assert proposal.email_search_runtime_enabled is False
    assert proposal.connector_runtime_enabled is False
    assert proposal.model_call_enabled is False
    assert proposal.memory_write_enabled is False
    assert proposal.context_injection_enabled is False
    assert proposal.backend_route_added is False
    assert proposal.control_center_control_added is False
    assert proposal.production_authority_enabled is False

    for reason_code in [
        "FCC_P1_009_DRAFT_ONLY_EMAIL_RESPONSE_PROPOSAL",
        "FCC_DRAFT_ONLY_EMAIL_PROPOSAL_CONTRACT",
        "FCC_DRAFT_PROPOSAL_SAFE_REFS_ONLY",
        "FCC_DRAFT_PROPOSAL_NO_SEND_WRITE_OR_ACCOUNT_AUTH",
        "FCC_DRAFT_PROPOSAL_CONNECTOR_RUNTIME_MISSING",
        "FCC_READ_ONLY_METADATA_CONTRACT_ONLY",
        "FCC_SAFE_REFS_ONLY",
        "FCC_CONNECTOR_RUNTIME_MISSING",
        "FCC_NO_AUTH_FETCH_WRITE_OR_BACKGROUND_COLLECTION",
    ]:
        assert reason_code in proposal.reason_codes


def test_fcc_p1_009_policy_denies_runtime_write_auth_model_and_release_flags() -> None:
    connectors = _connectors()
    flag_reasons = [
        ("raw_body_enabled", "RAW_BODY_DENIED"),
        ("raw_draft_body_enabled", "RAW_DRAFT_BODY_DENIED"),
        ("subject_text_enabled", "SUBJECT_TEXT_DENIED"),
        ("participant_identifiers_enabled", "PARTICIPANT_IDENTIFIERS_DENIED"),
        ("attachment_names_enabled", "ATTACHMENT_NAMES_DENIED"),
        ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
        ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
        ("account_write_enabled", "ACCOUNT_WRITE_DENIED"),
        ("email_fetch_runtime_enabled", "EMAIL_FETCH_RUNTIME_DENIED"),
        ("email_search_runtime_enabled", "EMAIL_SEARCH_RUNTIME_DENIED"),
        ("reply_enabled", "EMAIL_REPLY_DENIED"),
        ("forward_enabled", "EMAIL_FORWARD_DENIED"),
        ("send_enabled", "EMAIL_SEND_DENIED"),
        ("delete_enabled", "EMAIL_DELETE_DENIED"),
        ("archive_enabled", "EMAIL_ARCHIVE_DENIED"),
        ("label_write_enabled", "EMAIL_LABEL_WRITE_DENIED"),
        ("move_enabled", "EMAIL_MOVE_DENIED"),
        ("connector_runtime_enabled", "CONNECTOR_RUNTIME_DENIED"),
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("background_sync_enabled", "BACKGROUND_SYNC_DENIED"),
        ("notification_delivery_enabled", "NOTIFICATION_DELIVERY_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
        ("public_beta_claim_enabled", "PUBLIC_BETA_CLAIM_DENIED"),
        ("public_distribution_claim_enabled", "PUBLIC_DISTRIBUTION_CLAIM_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]

    for field, reason in flag_reasons:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_fcc_draft_email_response_proposal_policy(
                connectors.FCCDraftEmailResponseProposalPolicy(**{field: True})
            )


def test_fcc_p1_009_envelope_denies_send_write_runtime_and_side_effect_flags() -> None:
    connectors = _connectors()
    proposal = connectors.build_fcc_draft_email_response_proposal_envelope()

    for field, reason in [
        ("raw_body_enabled", "RAW_BODY_DENIED"),
        ("raw_draft_body_enabled", "RAW_DRAFT_BODY_DENIED"),
        ("subject_text_enabled", "SUBJECT_TEXT_DENIED"),
        ("participant_identifiers_enabled", "PARTICIPANT_IDENTIFIERS_DENIED"),
        ("attachment_names_enabled", "ATTACHMENT_NAMES_DENIED"),
        ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
        ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
        ("account_write_enabled", "ACCOUNT_WRITE_DENIED"),
        ("email_fetch_runtime_enabled", "EMAIL_FETCH_RUNTIME_DENIED"),
        ("email_search_runtime_enabled", "EMAIL_SEARCH_RUNTIME_DENIED"),
        ("reply_enabled", "EMAIL_REPLY_DENIED"),
        ("forward_enabled", "EMAIL_FORWARD_DENIED"),
        ("send_enabled", "EMAIL_SEND_DENIED"),
        ("delete_enabled", "EMAIL_DELETE_DENIED"),
        ("archive_enabled", "EMAIL_ARCHIVE_DENIED"),
        ("label_write_enabled", "EMAIL_LABEL_WRITE_DENIED"),
        ("move_enabled", "EMAIL_MOVE_DENIED"),
        ("connector_runtime_enabled", "CONNECTOR_RUNTIME_DENIED"),
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("backend_route_added", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
        ("background_sync_enabled", "BACKGROUND_SYNC_DENIED"),
        ("notification_delivery_enabled", "NOTIFICATION_DELIVERY_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
        ("public_beta_claim_enabled", "PUBLIC_BETA_CLAIM_DENIED"),
        ("public_distribution_claim_enabled", "PUBLIC_DISTRIBUTION_CLAIM_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_fcc_draft_email_response_proposal_envelope(
                proposal.model_copy(update={field: True})
            )

    with pytest.raises(ValueError, match="SIDE_EFFECTS_DENIED"):
        connectors.validate_fcc_draft_email_response_proposal_envelope(
            proposal.model_copy(update={"side_effects_performed": ["email-send"]})
        )


@pytest.mark.parametrize(
    ("update", "private_value"),
    [
        ({"redacted_draft_summary": "Body: private note"}, "private note"),
        ({"metadata": {"subject": "Private reply"}}, "Private reply"),
        ({"metadata": {"participant": "founder@example.com"}}, "founder@example"),
        ({"metadata": {"account_id": "mailbox-primary"}}, "mailbox-primary"),
        ({"metadata": {"attachment_name": "proposal.pdf"}}, "proposal.pdf"),
        ({"metadata": {"password": "private-password"}}, "private-password"),
        ({"metadata": {"access_token": "token-private"}}, "token-private"),
        ({"metadata": {"secret": "secret-private"}}, "secret-private"),
        ({"metadata": {"provider_payload": "provider-private"}}, "provider-private"),
        ({"metadata": {"transcript": "private transcript"}}, "private transcript"),
        ({"metadata": {"source_content": "private source"}}, "private source"),
        ({"redacted_response_outline": ["Subject: private outline"]}, "private outline"),
    ],
)
def test_fcc_p1_009_redaction_regressions_do_not_echo_private_content(
    update: dict[str, object], private_value: str
) -> None:
    connectors = _connectors()
    proposal = connectors.build_fcc_draft_email_response_proposal_envelope()

    with pytest.raises(ValueError) as exc_info:
        connectors.validate_fcc_draft_email_response_proposal_envelope(
            proposal.model_copy(update=update)
        )

    message = str(exc_info.value)
    assert "FCC_DRAFT_EMAIL_PRIVATE_" in message
    assert private_value not in message


def test_fcc_p1_009_rejects_raw_extra_fields_without_echoing_content() -> None:
    connectors = _connectors()
    proposal = connectors.build_fcc_draft_email_response_proposal_envelope()
    payload = proposal.model_dump(mode="python")
    payload["raw_draft_body"] = "Reply with this private sentence."

    with pytest.raises(ValueError) as exc_info:
        connectors.validate_fcc_draft_email_response_proposal_envelope(payload)

    message = str(exc_info.value)
    assert message == "FCC_DRAFT_EMAIL_PRIVATE_FIELD_DENIED"
    assert "private sentence" not in message.lower()
