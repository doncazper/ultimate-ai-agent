from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.connectors import (
    ConnectorDraftProposalItem,
    ConnectorDraftProposalReadModel,
    build_connector_draft_proposal_read_model,
)


ROOT = Path(__file__).resolve().parents[1]


def test_connector_draft_proposals_are_backend_owned_safe_refs_only() -> None:
    read_model = build_connector_draft_proposal_read_model()

    assert read_model.schema_version == "connector_draft_proposal_read_model.v1"
    assert read_model.source == "python_core_connector_draft_proposal_read_model"
    assert read_model.backend_owned is True
    assert read_model.proposal_count == 2
    assert {proposal.draft_kind for proposal in read_model.proposals} == {
        "email_response",
        "calendar_event_hold",
    }
    assert read_model.safe_refs_only is True
    assert read_model.draft_only is True
    assert read_model.metadata_only is True
    assert read_model.raw_payloads_persisted is False
    assert read_model.connector_runtime_enabled is False
    assert read_model.account_auth_enabled is False
    assert read_model.oauth_enabled is False
    assert read_model.connector_writes_enabled is False
    assert read_model.connector_sends_enabled is False
    assert read_model.provider_model_calls_enabled is False
    assert read_model.memory_write_enabled is False
    assert read_model.context_injection_enabled is False

    for proposal in read_model.proposals:
        assert proposal.status == "draft_proposal_ready"
        assert proposal.approval_required_to_draft is False
        assert proposal.approval_required_to_send is True
        assert proposal.outbound_approval_ref_grants_authority is False
        assert proposal.target_session_ref_grants_authority is False
        assert proposal.connector_write_enabled is False
        assert proposal.connector_send_enabled is False
        assert proposal.delivery_execution_performed is False
        assert proposal.connector_write_performed is False
        assert proposal.connector_send_performed is False
        assert proposal.account_sync_performed is False
        assert proposal.raw_payloads_persisted is False
        assert proposal.raw_body_persisted is False
        assert proposal.raw_draft_body_persisted is False
        assert proposal.blocked_send_write_reason_refs
        assert proposal.evidence_refs
        assert proposal.proof_refs


def test_connector_draft_proposals_reject_authority_and_raw_values() -> None:
    read_model = build_connector_draft_proposal_read_model()
    proposal = read_model.proposals[0]

    with pytest.raises(ValidationError, match="CONNECTOR_DRAFT_PROPOSAL_AUTHORITY_DENIED"):
        ConnectorDraftProposalItem.model_validate(
            {**proposal.model_dump(mode="json"), "connector_send_enabled": True}
        )

    with pytest.raises(ValidationError, match="CONNECTOR_DRAFT_PROPOSAL_AUTHORITY_DENIED"):
        ConnectorDraftProposalItem.model_validate(
            {**proposal.model_dump(mode="json"), "connector_write_performed": True}
        )

    with pytest.raises(ValidationError, match="CONNECTOR_DRAFT_PROPOSAL_RAW_CONTENT_DENIED"):
        ConnectorDraftProposalItem.model_validate(
            {
                **proposal.model_dump(mode="json"),
                "redacted_outline": ["send this to founder@example.com"],
            }
        )

    with pytest.raises(ValidationError, match="CONNECTOR_DRAFT_PROPOSALS_AUTHORITY_DENIED"):
        ConnectorDraftProposalReadModel(
            proposal_count=read_model.proposal_count,
            proposals=read_model.proposals,
            connector_sends_enabled=True,
        )


def test_connector_draft_proposals_cli_safe_refs_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/inspect_connector_draft_proposals.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    output_text = result.stdout.lower()
    assert payload["status"] == "draft_proposals_ready_no_send_write"
    assert payload["proposal_count"] == 2
    assert payload["real_connector_runtime_performed"] is False
    assert payload["connector_send_or_write_performed"] is False
    assert payload["connector_writes_enabled"] is False
    assert payload["connector_sends_enabled"] is False
    assert "founder@example" not in output_text
    assert "api_key" not in output_text
    assert "token" not in output_text
    assert "cookie" not in output_text
