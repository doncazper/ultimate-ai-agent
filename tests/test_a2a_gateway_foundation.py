from __future__ import annotations

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.adapters import A2AAgentCardMinimal, A2AAgentCardV1, UAAA2AAgentCardMetadataImport
from ultimate_ai_agent.core.capabilities import (
    A2A_REVIEW_AUTH_SCOPE,
    A2AAgentMetadata,
    A2AAuthPosture,
    A2AExactDelegationApprovalContext,
    A2AExactDelegationApprovalBinding,
    A2ATrustPosture,
    CapabilityApprovalGrant,
    CapabilityRegistry,
    LocalApprovalAuthority,
    PolicyEngine,
    TaskEnvelope,
    a2a_agent_card_to_metadata,
    a2a_agent_metadata_to_capability_candidate,
    a2a_v1_agent_card_to_metadata,
    build_a2a_blocked_receipt,
    build_a2a_handoff_proposal,
    build_a2a_replay_audit_record,
    evaluate_a2a_exact_approval_binding,
)
from ultimate_ai_agent.core.capabilities.enums import CapabilityAuthorityLevel, CoordinationMode, RiskLevel, SideEffectLevel


def _card(**overrides: object) -> UAAA2AAgentCardMetadataImport:
    data = {
        "agent_id": "research-agent",
        "name": "Research Agent",
        "owner": "founder-local",
        "declared_capabilities": ["summarize", "crm.lookup"],
        "endpoint_url": "https://agent.example.invalid/a2a",
        "version": "0.1.0",
    }
    data.update(overrides)
    return UAAA2AAgentCardMetadataImport(**data)


def _a2a_v1_agent_card_fixture() -> dict[str, object]:
    return {
        "name": "GeoSpatial Route Planner Agent",
        "description": "Provides route planning and map generation services.",
        "supportedInterfaces": [
            {
                "url": "https://geo-agent.example.invalid/a2a/v1",
                "protocolBinding": "JSONRPC",
                "protocolVersion": "1.0",
            },
            {
                "url": "https://geo-agent.example.invalid/a2a/json",
                "protocolBinding": "HTTP+JSON",
                "protocolVersion": "1.0",
            },
        ],
        "provider": {
            "organization": "Example Geo Services",
            "url": "https://geo-services.example.invalid",
        },
        "iconUrl": "https://geo-agent.example.invalid/icon.png",
        "version": "1.2.0",
        "documentationUrl": "https://docs.example.invalid/georoute-agent/api",
        "capabilities": {
            "streaming": True,
            "pushNotifications": True,
            "extendedAgentCard": True,
        },
        "securitySchemes": {
            "openid": {
                "openIdConnectSecurityScheme": {
                    "openIdConnectUrl": "https://accounts.example.invalid/.well-known/openid-configuration",
                }
            }
        },
        "security": [{"openid": ["openid", "profile", "email"]}],
        "defaultInputModes": ["application/json", "text/plain"],
        "defaultOutputModes": ["application/json", "image/png"],
        "skills": [
            {
                "id": "route-optimizer-traffic",
                "name": "Traffic-Aware Route Optimizer",
                "description": "Calculates route candidates with redacted traffic context.",
                "tags": ["maps", "routing", "traffic"],
                "examples": ["Plan a redacted route with safe location refs."],
                "inputModes": ["application/json", "text/plain"],
                "outputModes": ["application/json", "text/html"],
            },
            {
                "id": "custom-map-generator",
                "name": "Personalized Map Generator",
                "description": "Creates map artifacts from safe refs only.",
                "tags": ["maps", "visualization"],
                "examples": ["Generate a map from reviewed point-of-interest refs."],
                "inputModes": ["application/json"],
                "outputModes": ["image/png", "application/json"],
            },
        ],
        "signatures": [
            {
                "protected": "signature-header-ref",
                "signature": "signature-value-ref",
            }
        ],
    }


def _metadata(**overrides: object):
    data = a2a_agent_card_to_metadata(_card()).model_dump(mode="python")
    data.update(overrides)
    return A2AAgentMetadata(**data)


def test_a2a_card_import_defaults_to_blocked_review_required_not_delegation() -> None:
    metadata = _metadata()
    manifest = a2a_agent_metadata_to_capability_candidate(metadata)

    assert manifest.kind.value == "a2a_agent"
    assert manifest.side_effects == SideEffectLevel.none
    assert manifest.risk_level == RiskLevel.high
    assert manifest.authority_level == CapabilityAuthorityLevel.metadata_only
    assert manifest.approval_required == "a2a_exact_delegation_approval_required"
    assert manifest.auth_scopes == [A2A_REVIEW_AUTH_SCOPE]
    assert CoordinationMode.agent_as_tool not in manifest.allowed_coordination_modes
    assert CoordinationMode.handoff not in manifest.allowed_coordination_modes
    assert manifest.metadata["remote_dispatch_allowed"] is False
    assert manifest.metadata["peer_auth_runtime_allowed"] is False
    assert manifest.metadata["remote_self_approval_allowed"] is False
    assert manifest.provider_runtime_allowed is False
    assert manifest.connector_write_allowed is False

    decision = PolicyEngine().can_select(manifest, {})
    assert decision.allowed is False
    assert "AUTH_SCOPE_MISSING" in decision.reason_codes


def test_a2a_metadata_requires_scope_and_exact_approval_before_execution() -> None:
    metadata = _metadata(
        requested_grant_refs=["grant-ref:a2a:crm-read"],
        credential_ref_required=True,
        credential_refs=["credential-ref:a2a:peer-token"],
    )
    manifest = a2a_agent_metadata_to_capability_candidate(metadata)
    task = TaskEnvelope(user_request="Delegate research", objective="Review A2A metadata")

    missing_approval = PolicyEngine().can_execute(manifest, task, {"auth_scopes": [A2A_REVIEW_AUTH_SCOPE]})
    assert missing_approval.allowed is False
    assert missing_approval.requires_approval is True
    assert "CAPABILITY_APPROVAL_REQUIRED" in missing_approval.reason_codes

    grant = CapabilityApprovalGrant(
        approval_ref="approval-ref:a2a:wrong-agent",
        capability_id="capability-ref:a2a:other-agent",
        granted_by="human-reviewer",
    )
    mismatched = PolicyEngine(approval_authority=LocalApprovalAuthority([grant])).can_execute(
        manifest,
        task,
        {"auth_scopes": [A2A_REVIEW_AUTH_SCOPE], "approval_ref": "approval-ref:a2a:wrong-agent"},
    )
    assert mismatched.allowed is False
    assert "APPROVAL_CAPABILITY_MISMATCH" in mismatched.reason_codes


def test_a2a_manifest_presence_is_not_callable_delegation_authority() -> None:
    registry = CapabilityRegistry()
    manifest = registry.manifest_from_a2a_agent_card(_card())

    with pytest.raises(KeyError):
        registry.load_manifest(manifest.id)
    assert manifest.auth_scopes == [A2A_REVIEW_AUTH_SCOPE]
    assert manifest.side_effects == SideEffectLevel.none
    assert manifest.metadata["source"] == "a2a_agent_card_metadata"
    assert manifest.metadata["endpoint_ref"] == "endpoint-ref:a2a:declared-redacted"
    assert "https://" not in str(manifest.model_dump(mode="json"))
    with pytest.raises(ValueError, match="requires an adapter"):
        registry.register(manifest)


def test_official_a2a_v1_agent_card_fixture_imports_as_safe_refs_without_dispatch() -> None:
    card = A2AAgentCardV1.model_validate(_a2a_v1_agent_card_fixture())
    metadata = a2a_v1_agent_card_to_metadata(card)
    manifest = a2a_agent_metadata_to_capability_candidate(metadata)

    assert card.supported_interfaces[0].protocol_binding == "JSONRPC"
    assert card.supported_interfaces[0].protocol_version == "1.0"
    assert metadata.schema_version_ref == "schema-version-ref:a2a:1.0"
    assert metadata.endpoint_declared is True
    assert metadata.endpoint_ref == "endpoint-ref:a2a:v1:supported-interface-redacted"
    assert metadata.auth_posture == A2AAuthPosture.peer_auth_blocked
    assert metadata.trust_posture == A2ATrustPosture.untrusted_metadata
    assert "grant-ref:a2a:peer-auth-review-required" in metadata.requested_grant_refs
    assert "capability-ref:a2a-declared:route-optimizer-traffic" in metadata.declared_capability_refs
    assert "interface-ref:a2a:JSONRPC:1.0" in metadata.evidence_refs
    assert manifest.metadata["remote_dispatch_allowed"] is False
    assert manifest.metadata["peer_auth_runtime_allowed"] is False
    assert manifest.metadata["remote_self_approval_allowed"] is False
    assert manifest.side_effects == SideEffectLevel.none
    assert manifest.authority_level == CapabilityAuthorityLevel.metadata_only

    persisted = f"{metadata.model_dump(mode='json')} {manifest.model_dump(mode='json')}"
    assert "https://" not in persisted
    assert "openid-configuration" not in persisted


def test_a2a_handoff_proposal_is_preview_only_and_no_dispatch() -> None:
    metadata = _metadata()
    manifest = a2a_agent_metadata_to_capability_candidate(metadata)
    proposal = build_a2a_handoff_proposal(
        metadata,
        manifest,
        proposal_ref="proposal-ref:a2a:research",
        source_agent_ref="a2a-agent-ref:uaa-local",
        task_ref="task-ref:a2a:research",
        objective_ref="objective-ref:a2a:research",
    )

    assert proposal.status == "blocked_review_required"
    assert proposal.delegation_performed is False
    assert proposal.remote_dispatch_allowed is False
    assert proposal.remote_self_approval_allowed is False
    assert proposal.memory_write_allowed is False
    assert proposal.provider_call_allowed is False
    assert proposal.connector_write_allowed is False
    assert proposal.browser_shell_execution_allowed is False


def test_a2a_exact_approval_binding_blocks_mismatched_refs() -> None:
    metadata = _metadata(
        requested_grant_refs=["grant-ref:a2a:crm-read"],
        credential_ref_required=True,
        credential_refs=["credential-ref:a2a:peer-token"],
    )
    manifest = a2a_agent_metadata_to_capability_candidate(metadata)
    binding = A2AExactDelegationApprovalBinding(
        approval_ref="approval-ref:a2a:research",
        agent_ref="a2a-agent-ref:wrong",
        card_ref=metadata.card_ref,
        capability_id=manifest.id,
        task_ref="task-ref:a2a:wrong",
        handoff_ref="handoff-ref:a2a:wrong",
        requested_grant_refs=[],
        credential_refs=[],
        expires_ref="expires-ref:a2a:wrong-window",
        expected_receipt_ref=metadata.expected_receipt_ref,
        revocation_ref=metadata.revocation_ref,
    )
    context = A2AExactDelegationApprovalContext(
        task_ref="task-ref:a2a:research",
        handoff_ref="handoff-ref:a2a:research",
        expires_ref="expires-ref:a2a:review-window",
    )

    decision = evaluate_a2a_exact_approval_binding(binding, metadata, manifest, context)

    assert decision.allowed is False
    assert decision.status == "blocked"
    assert "A2A_APPROVAL_AGENT_MISMATCH" in decision.reason_codes
    assert "A2A_APPROVAL_TASK_MISMATCH" in decision.reason_codes
    assert "A2A_APPROVAL_HANDOFF_MISMATCH" in decision.reason_codes
    assert "A2A_APPROVAL_EXPIRES_MISMATCH" in decision.reason_codes
    assert "A2A_APPROVAL_REQUESTED_GRANT_MISSING" in decision.reason_codes
    assert "A2A_APPROVAL_CREDENTIAL_REF_MISSING" in decision.reason_codes


def test_a2a_legacy_agent_card_alias_remains_metadata_only() -> None:
    card = A2AAgentCardMinimal(
        agent_id="legacy-research-agent",
        name="Legacy Research Agent",
        owner="founder-local",
        version="0.1.0",
    )

    assert isinstance(card, UAAA2AAgentCardMetadataImport)
    assert card.schema_version == "uaa_a2a_agent_card_metadata_import.v1"


def test_a2a_blocked_receipt_and_replay_audit_do_not_redelegate() -> None:
    metadata = _metadata()
    manifest = a2a_agent_metadata_to_capability_candidate(metadata)
    receipt = build_a2a_blocked_receipt(
        metadata,
        manifest,
        receipt_ref="receipt-ref:a2a:research-blocked-instance",
        reason_codes=["A2A_REMOTE_DISPATCH_BLOCKED", "A2A_EXACT_APPROVAL_REQUIRED"],
    )
    replay = build_a2a_replay_audit_record(
        metadata,
        manifest,
        receipt,
        selection_ref="selection-ref:a2a:research",
        policy_decision_ref="policy-decision-ref:a2a:research",
        approval_decision_ref="approval-decision-ref:a2a:research",
    )

    assert receipt.status == "blocked"
    assert receipt.delegation_performed is False
    assert receipt.remote_dispatch_performed is False
    assert receipt.approval_missing_ref == "approval-missing-ref:a2a:exact-delegation-approval-required"
    assert replay.reconstructable is True
    assert replay.redelegation_allowed is False
    assert replay.receipt_ref == receipt.receipt_ref


def test_a2a_metadata_rejects_raw_credentials_secret_like_content_and_revoked_activation() -> None:
    with pytest.raises(ValidationError, match="raw A2A credential"):
        _metadata(auth_posture=A2AAuthPosture.raw_credential_blocked)

    with pytest.raises(ValidationError, match="secret-like"):
        _metadata(name="token='abc12345678901234567890'")

    with pytest.raises(ValidationError, match="revoked A2A"):
        _metadata(trust_posture=A2ATrustPosture.revoked, activation_posture="metadata_only")
