from typing import Any
from importlib import import_module

import pytest


def _connectors() -> Any:
    try:
        return import_module("ultimate_ai_agent.core.connectors")
    except ModuleNotFoundError as exc:
        pytest.fail(f"FCC read-only connector contracts package missing: {exc}")


def test_fcc_p1_007_008_builds_paired_read_only_metadata_contracts() -> None:
    connectors = _connectors()
    pair = connectors.build_fcc_read_only_integration_contract_pair()

    assert (
        pair.status == connectors.FCCReadOnlyIntegrationPairStatus.paired_contracts
    )
    assert pair.contract_only is True
    assert pair.read_only is True
    assert pair.metadata_only is True
    assert pair.connector_runtime_missing is True
    assert pair.side_effects_performed == []
    assert pair.calendar.product_loop_ref == pair.product_loop_ref
    assert pair.email.product_loop_ref == pair.product_loop_ref

    for ref in pair.shared_source_readiness_refs:
        assert ref in pair.calendar.source_readiness_refs
        assert ref in pair.email.source_readiness_refs

    assert pair.calendar.calendar_contract_ref == (
        "fcc-calendar-read-only-contract:fcc-p1-007"
    )
    assert pair.email.email_contract_ref == (
        "fcc-email-metadata-read-only-contract:fcc-p1-008"
    )
    assert pair.calendar.event_ref.startswith("calendar-event-ref:")
    assert pair.calendar.time_window_ref.startswith("time-window-ref:")
    assert pair.calendar.attendee_identity_refs
    assert pair.calendar.account_identity_ref.startswith("account-identity-ref:")
    assert pair.calendar.meeting_prep_summary_ref.startswith(
        "meeting-prep-summary-ref:"
    )
    assert pair.email.sender_summary_ref.startswith("sender-summary-ref:")
    assert pair.email.thread_ref.startswith("thread-ref:")
    assert pair.email.time_window_ref.startswith("time-window-ref:")
    assert pair.email.label_summary_refs
    assert pair.email.inbox_summary_ref.startswith("inbox-summary-ref:")
    assert pair.email.follow_up_summary_ref.startswith("follow-up-summary-ref:")

    for reason_code in [
        "FCC_READ_ONLY_METADATA_CONTRACT_ONLY",
        "FCC_SAFE_REFS_ONLY",
        "FCC_CONNECTOR_RUNTIME_MISSING",
        "FCC_NO_AUTH_FETCH_WRITE_OR_BACKGROUND_COLLECTION",
    ]:
        assert reason_code in pair.reason_codes
        assert reason_code in pair.calendar.reason_codes
        assert reason_code in pair.email.reason_codes


def test_fcc_p1_calendar_contract_denies_runtime_write_auth_and_release_flags() -> None:
    connectors = _connectors()
    flag_reasons = [
        ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
        ("network_fetch_enabled", "NETWORK_FETCH_DENIED"),
        ("calendar_read_runtime_enabled", "CALENDAR_READ_RUNTIME_DENIED"),
        ("calendar_search_runtime_enabled", "CALENDAR_SEARCH_RUNTIME_DENIED"),
        ("event_create_enabled", "CALENDAR_EVENT_CREATE_DENIED"),
        ("event_update_enabled", "CALENDAR_EVENT_UPDATE_DENIED"),
        ("event_delete_enabled", "CALENDAR_EVENT_DELETE_DENIED"),
        ("invite_send_enabled", "CALENDAR_INVITE_SEND_DENIED"),
        ("meeting_link_exposure_enabled", "MEETING_LINK_EXPOSURE_DENIED"),
        ("location_exposure_enabled", "LOCATION_EXPOSURE_DENIED"),
        ("event_title_body_storage_enabled", "EVENT_TITLE_BODY_STORAGE_DENIED"),
        ("raw_invite_body_enabled", "RAW_INVITE_BODY_DENIED"),
        ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
        ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
        ("connector_runtime_enabled", "CONNECTOR_RUNTIME_DENIED"),
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
        ("public_beta_claim_enabled", "PUBLIC_BETA_CLAIM_DENIED"),
        ("public_distribution_claim_enabled", "PUBLIC_DISTRIBUTION_CLAIM_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]

    for field, reason in flag_reasons:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_fcc_calendar_read_only_policy(
                connectors.FCCCalendarReadOnlyPolicy(**{field: True})
            )

    record = connectors.build_fcc_calendar_event_metadata_envelope()
    for field, reason in [
        ("backend_route_added", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
        ("event_create_enabled", "CALENDAR_EVENT_CREATE_DENIED"),
        ("raw_invite_body_enabled", "RAW_INVITE_BODY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_fcc_calendar_event_metadata_envelope(
                record.model_copy(update={field: True})
            )


def test_fcc_p1_email_contract_denies_runtime_write_auth_and_release_flags() -> None:
    connectors = _connectors()
    flag_reasons = [
        ("raw_body_enabled", "RAW_BODY_DENIED"),
        ("subject_text_enabled", "SUBJECT_TEXT_DENIED"),
        ("participant_identifiers_enabled", "PARTICIPANT_IDENTIFIERS_DENIED"),
        ("attachment_names_enabled", "ATTACHMENT_NAMES_DENIED"),
        ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
        ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
        ("email_fetch_runtime_enabled", "EMAIL_FETCH_RUNTIME_DENIED"),
        ("email_search_runtime_enabled", "EMAIL_SEARCH_RUNTIME_DENIED"),
        ("send_enabled", "EMAIL_SEND_DENIED"),
        ("delete_enabled", "EMAIL_DELETE_DENIED"),
        ("archive_enabled", "EMAIL_ARCHIVE_DENIED"),
        ("label_write_enabled", "EMAIL_LABEL_WRITE_DENIED"),
        ("connector_runtime_enabled", "CONNECTOR_RUNTIME_DENIED"),
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "DEPENDENCY_DENIED"),
        ("public_beta_claim_enabled", "PUBLIC_BETA_CLAIM_DENIED"),
        ("public_distribution_claim_enabled", "PUBLIC_DISTRIBUTION_CLAIM_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ]

    for field, reason in flag_reasons:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_fcc_email_metadata_read_only_policy(
                connectors.FCCEmailMetadataReadOnlyPolicy(**{field: True})
            )

    record = connectors.build_fcc_email_metadata_envelope()
    for field, reason in [
        ("backend_route_added", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
        ("raw_body_enabled", "RAW_BODY_DENIED"),
        ("send_enabled", "EMAIL_SEND_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            connectors.validate_fcc_email_metadata_envelope(
                record.model_copy(update={field: True})
            )


@pytest.mark.parametrize(
    ("update", "private_value"),
    [
        ({"metadata": {"title": "Private board review"}}, "Private board review"),
        ({"metadata": {"safe_note": "Location: 123 Main Street"}}, "123 Main"),
        (
            {"redacted_meeting_prep_summary": "Join https://zoom.us/j/123"},
            "zoom.us",
        ),
        ({"metadata": {"attendee": "founder@example.com"}}, "founder@example"),
        ({"metadata": {"attachment_name": "agenda.pdf"}}, "agenda.pdf"),
        ({"metadata": {"api_key": "sk-test-private"}}, "sk-test-private"),
    ],
)
def test_fcc_p1_calendar_redaction_regressions_do_not_echo_private_content(
    update: dict[str, object], private_value: str
) -> None:
    connectors = _connectors()
    record = connectors.build_fcc_calendar_event_metadata_envelope()

    with pytest.raises(ValueError) as exc_info:
        connectors.validate_fcc_calendar_event_metadata_envelope(
            record.model_copy(update=update)
        )

    message = str(exc_info.value)
    assert "FCC_CALENDAR_PRIVATE_" in message
    assert private_value not in message


@pytest.mark.parametrize(
    ("update", "private_value"),
    [
        ({"metadata": {"subject": "Private term sheet"}}, "Private term sheet"),
        ({"metadata": {"safe_note": "Subject: Private update"}}, "Private update"),
        ({"metadata": {"participant": "founder@example.com"}}, "founder@example"),
        ({"metadata": {"attachment_name": "forecast.pdf"}}, "forecast.pdf"),
        ({"metadata": {"account_id": "mailbox-primary"}}, "mailbox-primary"),
        ({"metadata": {"password": "private-password"}}, "private-password"),
        ({"redacted_inbox_summary": "Body: private note"}, "private note"),
    ],
)
def test_fcc_p1_email_redaction_regressions_do_not_echo_private_content(
    update: dict[str, object], private_value: str
) -> None:
    connectors = _connectors()
    record = connectors.build_fcc_email_metadata_envelope()

    with pytest.raises(ValueError) as exc_info:
        connectors.validate_fcc_email_metadata_envelope(record.model_copy(update=update))

    message = str(exc_info.value)
    assert "FCC_EMAIL_PRIVATE_" in message
    assert private_value not in message


def test_fcc_p1_pair_requires_calendar_email_and_shared_product_loop_binding() -> None:
    connectors = _connectors()
    pair = connectors.build_fcc_read_only_integration_contract_pair()

    with pytest.raises(ValueError, match="FCC_CALENDAR_PRODUCT_LOOP_BINDING_MISMATCH"):
        connectors.validate_fcc_read_only_integration_contract_pair(
            pair.model_copy(update={"product_loop_ref": "founder-command-center-product-loop:other"})
        )

    broken_calendar = pair.calendar.model_copy(update={"source_readiness_refs": []})
    with pytest.raises(ValueError, match="SOURCE_READINESS_REF_REQUIRED"):
        connectors.validate_fcc_read_only_integration_contract_pair(
            pair.model_copy(update={"calendar": broken_calendar})
        )

    with pytest.raises(ValueError, match="SIDE_EFFECTS_DENIED"):
        connectors.validate_fcc_read_only_integration_contract_pair(
            pair.model_copy(update={"side_effects_performed": ["fetch-email"]})
        )
