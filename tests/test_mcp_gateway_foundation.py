from __future__ import annotations

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.capabilities import (
    CapabilityApprovalGrant,
    CapabilityRegistry,
    LocalApprovalAuthority,
    MCP_REVIEW_AUTH_SCOPE,
    McpAuthPosture,
    McpDiscoveryToolMetadata,
    McpExactApprovalBinding,
    McpTransportPosture,
    PolicyEngine,
    SideEffectLevel,
    TaskEnvelope,
    build_mcp_blocked_receipt,
    build_mcp_preview_contract,
    build_mcp_replay_audit_record,
    evaluate_mcp_exact_approval_binding,
    mcp_tool_metadata_to_capability_candidate,
)
from ultimate_ai_agent.core.capabilities.enums import CapabilityAuthorityLevel, CoordinationMode, RiskLevel


def _metadata(**overrides: object) -> McpDiscoveryToolMetadata:
    data = {
        "server_ref": "mcp-server-ref:email-fixture",
        "tool_ref": "mcp-tool-ref:email.send",
        "name": "email.send",
        "description": "Declared MCP email send tool metadata.",
        "input_schema": {
            "type": "object",
            "required": ["draft_ref"],
            "properties": {"draft_ref": {"type": "string"}},
            "additionalProperties": False,
        },
        "output_schema": {"type": "object", "properties": {"receipt_ref": {"type": "string"}}},
        "provenance_ref": "provenance-ref:mcp:fixture",
        "transport_posture": McpTransportPosture.unknown_blocked,
        "auth_posture": McpAuthPosture.unknown_blocked,
        "audit_ref": "audit-ref:mcp:email-send",
        "replay_ref": "replay-ref:mcp:email-send",
        "revocation_ref": "revocation-ref:mcp:email-send",
        "safe_disable_ref": "safe-disable-ref:mcp:email-send",
        "expected_receipt_ref": "receipt-ref:mcp:email-send-blocked",
    }
    data.update(overrides)
    return McpDiscoveryToolMetadata(**data)


def test_unknown_mcp_tool_import_defaults_to_blocked_review_required_not_read_only() -> None:
    metadata = _metadata(declared_side_effects=None)
    manifest = mcp_tool_metadata_to_capability_candidate(metadata)

    assert manifest.kind.value == "mcp_tool"
    assert manifest.side_effects == SideEffectLevel.none
    assert manifest.risk_level == RiskLevel.high
    assert manifest.approval_required == "mcp_exact_approval_required"
    assert manifest.auth_scopes == [MCP_REVIEW_AUTH_SCOPE]
    assert CoordinationMode.direct_tool not in manifest.allowed_coordination_modes
    assert manifest.metadata["mcp_tools_call_allowed"] is False
    assert manifest.metadata["network_transport_allowed"] is False
    assert manifest.provider_runtime_allowed is False
    assert manifest.connector_write_allowed is False

    decision = PolicyEngine().can_select(manifest, {})
    assert decision.allowed is False
    assert "AUTH_SCOPE_MISSING" in decision.reason_codes


def test_mcp_send_email_metadata_requires_policy_scope_and_exact_approval() -> None:
    metadata = _metadata(
        declared_side_effects=SideEffectLevel.external,
        risk_level=RiskLevel.critical,
        credential_ref_required=True,
        credential_refs=["credential-ref:mcp:email-fixture"],
    )
    manifest = mcp_tool_metadata_to_capability_candidate(metadata)
    task = TaskEnvelope(user_request="Send the draft", objective="Review MCP send-email metadata")

    assert manifest.authority_level == CapabilityAuthorityLevel.external
    assert manifest.single_writer_required is True
    assert manifest.safety.require_single_writer is True
    assert manifest.connector_write_allowed is False

    missing_approval = PolicyEngine().can_execute(manifest, task, {"auth_scopes": [MCP_REVIEW_AUTH_SCOPE]})
    assert missing_approval.allowed is False
    assert missing_approval.requires_approval is True
    assert "CAPABILITY_APPROVAL_REQUIRED" in missing_approval.reason_codes

    grant = CapabilityApprovalGrant(
        approval_ref="approval-ref:mcp:wrong-tool",
        capability_id="capability-ref:mcp:other-tool",
        granted_by="human-reviewer",
    )
    mismatched = PolicyEngine(approval_authority=LocalApprovalAuthority([grant])).can_execute(
        manifest,
        task,
        {"auth_scopes": [MCP_REVIEW_AUTH_SCOPE], "approval_ref": "approval-ref:mcp:wrong-tool"},
    )
    assert mismatched.allowed is False
    assert "APPROVAL_CAPABILITY_MISMATCH" in mismatched.reason_codes


def test_mcp_metadata_is_not_callable_by_manifest_presence_alone() -> None:
    registry = CapabilityRegistry()
    manifest = registry.manifest_from_mcp_tool_spec(
        {
            "name": "email.send",
            "description": "MCP send metadata.",
            "inputSchema": {"type": "object", "properties": {"draft_ref": {"type": "string"}}},
            "outputSchema": {"type": "object"},
        }
    )

    with pytest.raises(KeyError):
        registry.load_manifest(manifest.id)
    assert manifest.auth_scopes == [MCP_REVIEW_AUTH_SCOPE]
    assert manifest.side_effects == SideEffectLevel.none
    assert manifest.metadata["source"] == "mcp_discovery_metadata"
    with pytest.raises(ValueError, match="requires an adapter"):
        registry.register(manifest)


def test_mcp_preview_contract_is_no_side_effect_and_uses_safe_refs_only() -> None:
    metadata = _metadata()
    manifest = mcp_tool_metadata_to_capability_candidate(metadata)
    preview = build_mcp_preview_contract(metadata, manifest)

    assert preview.status == "blocked_review_required"
    assert preview.execution_performed is False
    assert preview.side_effects_performed is False
    assert preview.broker_invocation_allowed is False
    assert preview.model_direct_call_allowed is False
    assert preview.provider_direct_call_allowed is False
    assert preview.react_direct_call_allowed is False
    assert preview.required_argument_refs == ["argument-ref:mcp:mcp-tool-ref:email.send:draft_ref"]


def test_mcp_exact_approval_binding_blocks_mismatched_refs() -> None:
    metadata = _metadata(credential_ref_required=True, credential_refs=["credential-ref:mcp:email-fixture"])
    manifest = mcp_tool_metadata_to_capability_candidate(metadata)
    binding = McpExactApprovalBinding(
        approval_ref="approval-ref:mcp:email-send",
        server_ref="mcp-server-ref:wrong",
        tool_ref=metadata.tool_ref,
        capability_id=manifest.id,
        argument_ref="argument-ref:mcp:email-send:draft",
        scope_ref="scope-ref:mcp:email-send",
        credential_refs=[],
        budget_ref="budget-ref:mcp:none",
        expires_ref="expires-ref:mcp:review-window",
        expected_receipt_ref=metadata.expected_receipt_ref,
        revocation_ref=metadata.revocation_ref,
    )

    decision = evaluate_mcp_exact_approval_binding(binding, metadata, manifest)

    assert decision.allowed is False
    assert decision.status == "blocked"
    assert "MCP_APPROVAL_SERVER_MISMATCH" in decision.reason_codes
    assert "MCP_APPROVAL_CREDENTIAL_REF_MISSING" in decision.reason_codes


def test_mcp_blocked_receipt_and_replay_audit_are_replayable_without_reexecution() -> None:
    metadata = _metadata()
    manifest = mcp_tool_metadata_to_capability_candidate(metadata)
    receipt = build_mcp_blocked_receipt(
        metadata,
        manifest,
        receipt_ref="receipt-ref:mcp:email-send-blocked-instance",
        reason_codes=["MCP_RUNTIME_BLOCKED", "MCP_EXACT_APPROVAL_REQUIRED"],
    )
    replay = build_mcp_replay_audit_record(
        metadata,
        manifest,
        receipt,
        selection_ref="selection-ref:mcp:email-send",
        policy_decision_ref="policy-decision-ref:mcp:email-send",
        approval_decision_ref="approval-decision-ref:mcp:email-send",
    )

    assert receipt.status == "blocked"
    assert receipt.execution_performed is False
    assert receipt.side_effects_performed is False
    assert receipt.approval_missing_ref == "approval-missing-ref:mcp:exact-approval-required"
    assert replay.reconstructable is True
    assert replay.reexecution_allowed is False
    assert replay.receipt_ref == receipt.receipt_ref


def test_mcp_metadata_rejects_raw_credentials_and_secret_like_payloads() -> None:
    with pytest.raises(ValidationError, match="raw MCP credential"):
        _metadata(auth_posture=McpAuthPosture.raw_credential_blocked)

    with pytest.raises(ValidationError, match="secret-like"):
        _metadata(description="api_key='abc12345678901234567890'")
