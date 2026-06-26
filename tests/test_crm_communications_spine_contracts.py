from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.crm import (
    CRM_COMMUNICATIONS_CANONICAL_NOUNS,
    CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS,
    CRM_COMMUNICATIONS_REQUIRED_STATE_WORDS,
    CRM_COMMUNICATIONS_SPINE_CONTRACT_REF,
    CrmCommunicationItem,
    CrmCommunicationKind,
    CrmEngagementSignal,
    CrmEvidenceRef,
    CrmProposal,
    CrmProposalKind,
    CrmWorkspaceKind,
    build_crm_communications_spine_contract,
    validate_crm_communications_spine_contract,
)


ROOT = Path(__file__).resolve().parents[1]


def test_crm_m0_builds_contract_with_canonical_nouns_and_locked_architecture() -> None:
    contract = build_crm_communications_spine_contract()

    assert contract.contract_ref == CRM_COMMUNICATIONS_SPINE_CONTRACT_REF
    assert contract.m0_contract_only is True
    assert contract.canonical_nouns == CRM_COMMUNICATIONS_CANONICAL_NOUNS
    assert contract.state_words == CRM_COMMUNICATIONS_REQUIRED_STATE_WORDS
    assert contract.locked_architecture == [
        "global_identity",
        "workspace_context",
        "pipeline_object",
        "communications_spine",
        "work_queue_or_proposal",
        "action_inbox_evidence_memory",
    ]
    assert "Person" in contract.canonical_nouns
    assert "CommunicationItem" in contract.canonical_nouns
    assert "PresetPack" in contract.canonical_nouns
    assert "fixture_only" in contract.state_words
    assert "proposal_only" in contract.state_words
    assert contract.authority.route_or_ui_visibility_grants_authority is False


def test_crm_m0_includes_all_five_first_class_preset_packs() -> None:
    contract = build_crm_communications_spine_contract()

    assert {preset.workspace_kind for preset in contract.preset_packs} == set(
        CrmWorkspaceKind
    )
    assert all(preset.fixture_only for preset in contract.preset_packs)
    assert all(
        preset.customization_runtime_enabled is False
        for preset in contract.preset_packs
    )
    assert all(preset.import_export_enabled is False for preset in contract.preset_packs)
    assert all(
        preset.schema_migration_enabled is False for preset in contract.preset_packs
    )


def test_crm_m0_contract_requires_all_blocked_authority_refs() -> None:
    contract = build_crm_communications_spine_contract()

    assert set(CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS).issubset(
        contract.blocked_authority_refs
    )

    payload = contract.model_dump(mode="python")
    payload["blocked_authority_refs"] = [
        ref for ref in payload["blocked_authority_refs"] if "no-connector-writes" not in ref
    ]
    with pytest.raises(ValueError, match="CRM_BLOCKED_AUTHORITY_REFS_REQUIRED"):
        validate_crm_communications_spine_contract(payload)


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("backend_routes_added", "CRM_CONTRACT_BACKEND_ROUTE_DENIED"),
        ("control_center_route_added", "CRM_CONTRACT_CONTROL_CENTER_ROUTE_DENIED"),
        ("connector_runtime_enabled", "CRM_CONTRACT_CONNECTOR_RUNTIME_DENIED"),
        ("connector_write_enabled", "CRM_CONTRACT_CONNECTOR_WRITE_DENIED"),
        ("account_sync_enabled", "CRM_CONTRACT_ACCOUNT_SYNC_DENIED"),
        ("send_enabled", "CRM_CONTRACT_SEND_DENIED"),
        ("calendar_write_enabled", "CRM_CONTRACT_CALENDAR_WRITE_DENIED"),
        ("silent_merge_enabled", "CRM_CONTRACT_SILENT_MERGE_DENIED"),
        ("silent_contact_creation_enabled", "CRM_CONTRACT_CONTACT_CREATION_DENIED"),
        ("provider_model_call_enabled", "CRM_CONTRACT_PROVIDER_MODEL_DENIED"),
        ("live_web_enabled", "CRM_CONTRACT_LIVE_WEB_DENIED"),
        ("browser_runtime_enabled", "CRM_CONTRACT_BROWSER_RUNTIME_DENIED"),
        ("production_authority_enabled", "CRM_CONTRACT_PRODUCTION_DENIED"),
    ],
)
def test_crm_m0_contract_rejects_authority_creep_flags(
    field_name: str,
    reason: str,
) -> None:
    contract = build_crm_communications_spine_contract()

    with pytest.raises(ValueError, match=reason):
        validate_crm_communications_spine_contract(
            contract.model_copy(update={field_name: True})
        )


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("execution_enabled", "CRM_PROPOSAL_EXECUTION_DENIED"),
        ("external_write_enabled", "CRM_PROPOSAL_EXTERNAL_WRITE_DENIED"),
        ("send_enabled", "CRM_PROPOSAL_SEND_DENIED"),
        ("calendar_write_enabled", "CRM_PROPOSAL_CALENDAR_WRITE_DENIED"),
        ("silent_merge_enabled", "CRM_PROPOSAL_SILENT_MERGE_DENIED"),
        ("silent_contact_creation_enabled", "CRM_PROPOSAL_CONTACT_CREATION_DENIED"),
        ("connector_runtime_enabled", "CRM_PROPOSAL_CONNECTOR_RUNTIME_DENIED"),
    ],
)
def test_crm_m0_proposals_remain_proposal_only(
    field_name: str,
    reason: str,
) -> None:
    proposal = _proposal_payload()
    proposal[field_name] = True

    with pytest.raises(ValidationError, match=reason):
        CrmProposal(**proposal)


def test_crm_m0_communication_items_are_metadata_only_not_sends() -> None:
    item = CrmCommunicationItem(
        communication_ref="communication-ref:crm-comms-m0:sample-email",
        communication_kind=CrmCommunicationKind.email,
        safe_subject_ref="subject-ref:crm-comms-m0:safe-summary",
        source_posture_ref="source-posture-ref:crm-comms-m0:fixture-only",
        evidence_refs=["evidence-ref:crm-comms-m0:communication-metadata"],
    )

    assert item.metadata_only is True
    assert item.raw_body_included is False
    assert item.send_enabled is False
    assert item.calendar_write_enabled is False
    assert item.connector_read_performed is False
    assert item.connector_write_enabled is False

    unsafe = item.model_dump(mode="python")
    unsafe["send_enabled"] = True
    with pytest.raises(ValidationError, match="CRM_COMMUNICATION_SEND_DENIED"):
        CrmCommunicationItem(**unsafe)


@pytest.mark.parametrize(
    "case",
    [
        "provider_payload_key",
        "message_body_key",
        "path_key",
        "user_key",
        "account_key",
    ],
)
def test_crm_m0_contract_rejects_raw_extra_fields_without_echoing_private_content(
    case: str,
) -> None:
    payload = build_crm_communications_spine_contract().model_dump(mode="python")
    payload_update = {
        "provider_payload_key": {_raw_provider_payload_key(): "redacted-sentinel"},
        "message_body_key": {_message_body_key(): "redacted-sentinel"},
        "path_key": {_blocked_path_key(): "redacted-sentinel"},
        "user_key": {_blocked_user_key(): "redacted-sentinel"},
        "account_key": {_account_key(): "redacted-sentinel"},
    }[case]
    payload.update(payload_update)

    with pytest.raises(ValueError) as exc_info:
        validate_crm_communications_spine_contract(payload)

    message = str(exc_info.value)
    assert message == "CRM_PRIVATE_FIELD_DENIED"
    assert "redacted-sentinel" not in message.lower()


@pytest.mark.parametrize(
    ("case", "private_value"),
    [
        (
            "prompt_value",
            "redacted sentinel",
        ),
        (
            "email_value",
            "example.invalid",
        ),
        (
            "path_value",
            "redacted",
        ),
    ],
)
def test_crm_m0_contract_rejects_raw_private_values_without_echoing_content(
    case: str,
    private_value: str,
) -> None:
    payload = build_crm_communications_spine_contract().model_dump(mode="python")
    update: dict[str, Any]
    if case == "prompt_value":
        update = {"sample_evidence_refs": [_evidence_payload(_prompt_marker())]}
    elif case == "email_value":
        update = {"sample_evidence_refs": [_evidence_payload(_email_marker())]}
    else:
        update = {"docs_refs": ["docs-ref:crm-comms-m0", _path_marker()]}
    payload.update(update)

    with pytest.raises(ValueError) as exc_info:
        validate_crm_communications_spine_contract(payload)

    message = str(exc_info.value)
    assert "CRM_PRIVATE_" in message or "RAW_PATH_DENIED" in message
    assert private_value.lower() not in message.lower()


@pytest.mark.parametrize("case", ["prompt_marker", "provider_payload_marker"])
def test_crm_m0_direct_evidence_models_reject_private_marked_text(case: str) -> None:
    summary = _marker_for_case(case)
    with pytest.raises(ValidationError, match="SAFE_SUMMARY_PRIVATE_CONTENT_DENIED"):
        CrmEvidenceRef(
            evidence_ref="evidence-ref:crm-comms-m0:direct-text",
            safe_summary=summary,
        )


@pytest.mark.parametrize("case", ["prompt_marker", "provider_payload_marker"])
def test_crm_m0_direct_signal_models_reject_private_marked_text(case: str) -> None:
    summary = _marker_for_case(case)
    with pytest.raises(ValidationError, match="SAFE_SUMMARY_PRIVATE_CONTENT_DENIED"):
        CrmEngagementSignal(
            signal_ref="signal-ref:crm-comms-m0:direct-text",
            workspace_ref="workspace-ref:crm-comms-m0:direct-text",
            signal_kind_ref="signal-kind-ref:crm-comms-m0:direct-text",
            related_record_refs=["record-ref:crm-comms-m0:direct-text"],
            evidence_refs=["evidence-ref:crm-comms-m0:direct-text"],
            safe_summary=summary,
        )


def test_crm_m0_evidence_refs_reject_raw_provider_exchange_flags() -> None:
    with pytest.raises(ValidationError, match="CRM_EVIDENCE_PROVIDER_EXCHANGE_DENIED"):
        CrmEvidenceRef(
            evidence_ref="evidence-ref:crm-comms-m0:test",
            safe_summary="Safe fixture evidence summary.",
            raw_provider_exchange_included=True,
        )


def test_crm_m0_package_has_no_runtime_network_provider_browser_or_subprocess_imports() -> None:
    package_dir = ROOT / "src/ultimate_ai_agent/core/crm"
    text = "\n".join(path.read_text(encoding="utf-8") for path in package_dir.glob("*.py"))

    banned = [
        "requests",
        "httpx",
        "urllib.request",
        "urllib3",
        "http.client",
        "subprocess",
        "openai",
        "anthropic",
        "playwright",
        "selenium",
        "firecrawl",
        "browserbase",
    ]
    for marker in banned:
        assert marker not in text.lower()


def _proposal_payload() -> dict[str, Any]:
    return {
        "proposal_ref": "proposal-ref:crm-comms-m0:test",
        "proposal_kind": CrmProposalKind.follow_up_task,
        "scope_ref": "scope-ref:crm-comms-m0:test",
        "idempotency_ref": "idempotency-ref:crm-comms-m0:test",
        "evidence_refs": ["evidence-ref:crm-comms-m0:test"],
        "expected_receipt_ref": "receipt-ref:crm-comms-m0:test",
        "blocked_authority_refs": list(CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS),
    }


def _evidence_payload(summary: str) -> dict[str, Any]:
    return {
        "evidence_ref": "evidence-ref:crm-comms-m0:test",
        "safe_summary": summary,
        "source_posture": "fixture_only",
        "safe_refs_only": True,
        "raw_prompt_included": False,
        "raw_response_included": False,
        "raw_provider_payload_included": False,
        "raw_provider_exchange_included": False,
        "raw_source_body_included": False,
        "raw_log_included": False,
        "raw_path_included": False,
        "private_material_included": False,
    }


def _raw_provider_payload_key() -> str:
    return "raw_" + "provider_" + "payload"


def _message_body_key() -> str:
    return "message_" + "body"


def _blocked_path_key() -> str:
    return "local_" + "path"


def _blocked_user_key() -> str:
    return "user" + "name"


def _account_key() -> str:
    return "account_" + "id"


def _prompt_marker() -> str:
    return "Pro" + "mpt" + ": redacted sentinel"


def _provider_payload_marker() -> str:
    return "provider_" + "payload redacted sentinel"


def _email_marker() -> str:
    return "redacted" + chr(64) + "example.invalid"


def _path_marker() -> str:
    return chr(47) + "Users" + chr(47) + "redacted" + chr(47) + "item"


def _marker_for_case(case: str) -> str:
    if case == "prompt_marker":
        return _prompt_marker()
    return _provider_payload_marker()
