from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.consent import (
    ConsentGrant,
    ConsentLedger,
    ConsentQuery,
    ConsentScopeType,
    ConsentSubjectType,
    PermissionAction,
)
from ultimate_ai_agent.core.consent.enums import DataBoundary
from ultimate_ai_agent.core.contracts import ContextPack, ExecutionContract
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.tools import (
    CapabilityFirewallPolicy,
    ToolCategory,
    ToolDecisionStatus,
    ToolExecutionMode,
    ToolManifest,
    ToolPermissionKind,
    ToolPermissionManifest,
    ToolRequest,
    ToolRiskLevel,
)
from ultimate_ai_agent.core.tools import ToolBroker, ToolRegistry


@pytest.fixture
def actor_context():
    return ActorContext(
        actor_type=ActorType.orchestrator,
        actor_id="test_actor",
        authority_source=AuthoritySource.explicit_user_request,
        created_at=datetime.now(UTC),
    )


def make_tool(
    tool_id: str = "mock_tool",
    *,
    risk_level: ToolRiskLevel = ToolRiskLevel.safe,
    requested_permissions: list[ToolPermissionKind] | None = None,
    permission_manifest: ToolPermissionManifest | None = None,
    execution_mode: ToolExecutionMode = ToolExecutionMode.dry_run,
    idempotency_required: bool = False,
    supports_dry_run: bool = False,
) -> ToolManifest:
    return ToolManifest(
        tool_id=tool_id,
        display_name="Mock Tool",
        category=ToolCategory.mock,
        description="Policy-only test tool",
        execution_mode=execution_mode,
        risk_level=risk_level,
        permissions_required=requested_permissions or [],
        permission_manifest=permission_manifest,
        idempotency_required=idempotency_required,
        supports_dry_run=supports_dry_run,
        capability_flag="mock_tool_active",
        owner="tests",
        source="tests",
        version="1.0.0",
    )


def make_request(
    actor_context: ActorContext,
    *,
    tool_id: str = "mock_tool",
    requested_action: str = "execute",
    approval_ref: str | None = None,
    idempotency_key: str | None = None,
) -> ToolRequest:
    return ToolRequest(
        request_id=f"req_{tool_id}_{requested_action}",
        run_id="run_stage_a",
        tool_id=tool_id,
        actor_context=actor_context,
        requested_action=requested_action,
        purpose="policy testing",
        data_classification=DataBoundary.public,
        approval_ref=approval_ref,
        idempotency_key=idempotency_key,
    )


def make_consent_ledger(action: PermissionAction = PermissionAction.execute) -> ConsentLedger:
    ledger = ConsentLedger()
    ledger.add_grant(
        ConsentGrant(
            consent_id="grant_stage_a",
            subject_type=ConsentSubjectType.tool,
            subject_id="mock_tool",
            granted_to_actor="test_actor",
            on_behalf_of_user_id="user_123",
            scope_type=ConsentScopeType.project,
            allowed_actions=[action],
            source="tests",
        )
    )
    return ledger


def evaluate_with_tool(
    request: ToolRequest,
    tool: ToolManifest,
    *,
    ledger: ConsentLedger | None = None,
    firewall: CapabilityFirewallPolicy | None = None,
    execution_contract: ExecutionContract | None = None,
    context_pack: ContextPack | None = None,
):
    registry = ToolRegistry()
    registry.register_tool(tool)
    broker = ToolBroker(
        registry=registry,
        firewall_policy=firewall or CapabilityFirewallPolicy(max_risk_level=ToolRiskLevel.high),
    )
    return broker.evaluate_request(
        request=request,
        consent_ledger=ledger or make_consent_ledger(),
        execution_contract=execution_contract,
        context_pack=context_pack,
    )


def test_tool_broker_denies_contract_forbidden_tool(actor_context):
    contract = ExecutionContract(
        contract_id="ec_stage_a_forbidden",
        run_id="run_stage_a",
        workspace_id="ws",
        user_id="user",
        request_summary="Test forbidden tool",
        goal="Test policy",
        deliverable="Decision",
        mode="answer",
        forbidden_tools=["mock_tool"],
        acceptance_criteria=["Decision returned"],
    )

    decision = evaluate_with_tool(make_request(actor_context), make_tool(), execution_contract=contract)

    assert decision.status == ToolDecisionStatus.denied
    assert decision.reason_codes == ["CONTRACT_FORBIDDEN_TOOL"]


def test_tool_broker_denies_tool_not_in_contract_allowed_list(actor_context):
    contract = ExecutionContract(
        contract_id="ec_stage_a_allowed",
        run_id="run_stage_a",
        workspace_id="ws",
        user_id="user",
        request_summary="Test allowed tools",
        goal="Test policy",
        deliverable="Decision",
        mode="answer",
        allowed_tools=["other_tool"],
        acceptance_criteria=["Decision returned"],
    )

    decision = evaluate_with_tool(make_request(actor_context), make_tool(), execution_contract=contract)

    assert decision.status == ToolDecisionStatus.denied
    assert decision.reason_codes == ["CONTRACT_TOOL_NOT_ALLOWED"]


def test_tool_broker_denies_tool_not_in_context_permissions(actor_context):
    context_pack = ContextPack(
        context_pack_id="cp_stage_a",
        contract_id="ec_stage_a",
        run_id="run_stage_a",
        workspace_id="ws",
        user_id="user",
        active_goal="Test context tool boundary",
        tool_permissions=["other_tool"],
        token_budget=1000,
    )

    decision = evaluate_with_tool(make_request(actor_context), make_tool(), context_pack=context_pack)

    assert decision.status == ToolDecisionStatus.denied
    assert decision.reason_codes == ["CONTEXT_TOOL_NOT_ALLOWED"]


def test_tool_broker_allows_when_contract_and_context_permit_then_checks_next_policy(actor_context):
    contract = ExecutionContract(
        contract_id="ec_stage_a_permitted",
        run_id="run_stage_a",
        workspace_id="ws",
        user_id="user",
        request_summary="Test permitted tool",
        goal="Test policy",
        deliverable="Decision",
        mode="answer",
        allowed_tools=["mock_tool"],
        acceptance_criteria=["Decision returned"],
    )
    context_pack = ContextPack(
        context_pack_id="cp_stage_a_permitted",
        contract_id="ec_stage_a_permitted",
        run_id="run_stage_a",
        workspace_id="ws",
        user_id="user",
        active_goal="Test context tool boundary",
        tool_permissions=["mock_tool"],
        token_budget=1000,
    )

    decision = evaluate_with_tool(
        make_request(actor_context),
        make_tool(),
        execution_contract=contract,
        context_pack=context_pack,
    )

    assert decision.status == ToolDecisionStatus.allowed
    assert decision.reason_codes == ["AUTHORIZED"]


def test_high_risk_tool_with_unvalidated_approval_ref_stays_approval_required(actor_context):
    decision = evaluate_with_tool(
        make_request(actor_context, approval_ref="human_approved_ref_123"),
        make_tool(risk_level=ToolRiskLevel.high),
    )

    assert decision.status == ToolDecisionStatus.approval_required
    assert decision.approval_required is True
    assert "APPROVAL_REF_UNVALIDATED" in decision.reason_codes


def test_high_risk_tool_with_test_approval_ref_can_pass_in_mock_mode(actor_context):
    decision = evaluate_with_tool(
        make_request(actor_context, approval_ref="approval_test_123"),
        make_tool(risk_level=ToolRiskLevel.high, execution_mode=ToolExecutionMode.mock),
    )

    assert decision.status == ToolDecisionStatus.allowed
    assert decision.reason_codes == ["AUTHORIZED"]


def test_external_action_without_valid_approval_is_approval_required(actor_context):
    decision = evaluate_with_tool(
        make_request(actor_context, requested_action="send", approval_ref="approval_prod_123"),
        make_tool(risk_level=ToolRiskLevel.low),
        ledger=make_consent_ledger(PermissionAction.send),
    )

    assert decision.status == ToolDecisionStatus.approval_required
    assert "APPROVAL_REF_UNVALIDATED" in decision.reason_codes
    assert "EXTERNAL_ACTION_REQUIRES_APPROVAL" in decision.reason_codes


def test_idempotency_required_for_mutable_tool(actor_context):
    decision = evaluate_with_tool(
        make_request(actor_context, requested_action="write"),
        make_tool(idempotency_required=True),
        ledger=make_consent_ledger(PermissionAction.write),
    )

    assert decision.status == ToolDecisionStatus.denied
    assert decision.reason_codes == ["IDEMPOTENCY_KEY_REQUIRED"]


def test_idempotency_key_allows_mutable_policy_to_proceed(actor_context):
    decision = evaluate_with_tool(
        make_request(actor_context, requested_action="write", idempotency_key="idem_123456"),
        make_tool(idempotency_required=True),
        ledger=make_consent_ledger(PermissionAction.write),
    )

    assert decision.status == ToolDecisionStatus.allowed


def test_firewall_denies_filesystem_when_no_roots_allowlisted():
    manifest = make_tool(
        requested_permissions=[ToolPermissionKind.filesystem_read],
        permission_manifest=ToolPermissionManifest(
            required_permissions=[ToolPermissionKind.filesystem_read],
            filesystem_roots=["/workspace/project"],
        ),
    )

    passed, reasons = CapabilityFirewallPolicy().check_firewall(manifest)

    assert passed is False
    assert "FILESYSTEM_ACCESS_NOT_ALLOWLISTED" in reasons


def test_firewall_allows_requested_root_under_allowlisted_root():
    manifest = make_tool(
        requested_permissions=[ToolPermissionKind.filesystem_read],
        permission_manifest=ToolPermissionManifest(
            required_permissions=[ToolPermissionKind.filesystem_read],
            filesystem_roots=["/workspace/project"],
        ),
    )

    passed, reasons = CapabilityFirewallPolicy(
        allowed_filesystem_roots=["/workspace"],
    ).check_firewall(manifest)

    assert passed is True
    assert reasons == []


def test_firewall_denies_requested_root_outside_allowlist():
    manifest = make_tool(
        requested_permissions=[ToolPermissionKind.filesystem_read],
        permission_manifest=ToolPermissionManifest(
            required_permissions=[ToolPermissionKind.filesystem_read],
            filesystem_roots=["/etc"],
        ),
    )

    passed, reasons = CapabilityFirewallPolicy(
        allowed_filesystem_roots=["/workspace"],
    ).check_firewall(manifest)

    assert passed is False
    assert "FILESYSTEM_ACCESS_NOT_ALLOWLISTED" in reasons


def test_firewall_denies_network_when_no_domains_allowlisted():
    manifest = make_tool(
        requested_permissions=[ToolPermissionKind.network],
        permission_manifest=ToolPermissionManifest(
            required_permissions=[ToolPermissionKind.network],
            network_domains=["api.example.com"],
        ),
    )

    passed, reasons = CapabilityFirewallPolicy().check_firewall(manifest)

    assert passed is False
    assert "NETWORK_ACCESS_NOT_ALLOWLISTED" in reasons


def test_firewall_allows_explicitly_allowlisted_network_domain():
    manifest = make_tool(
        requested_permissions=[ToolPermissionKind.network],
        permission_manifest=ToolPermissionManifest(
            required_permissions=[ToolPermissionKind.network],
            network_domains=["api.example.com"],
        ),
    )

    passed, reasons = CapabilityFirewallPolicy(
        allowed_network_domains=["api.example.com"],
    ).check_firewall(manifest)

    assert passed is True
    assert reasons == []


def test_firewall_denies_unallowlisted_network_domain():
    manifest = make_tool(
        requested_permissions=[ToolPermissionKind.network],
        permission_manifest=ToolPermissionManifest(
            required_permissions=[ToolPermissionKind.network],
            network_domains=["evil.example.com"],
        ),
    )

    passed, reasons = CapabilityFirewallPolicy(
        allowed_network_domains=["api.example.com"],
    ).check_firewall(manifest)

    assert passed is False
    assert "NETWORK_ACCESS_NOT_ALLOWLISTED" in reasons


def test_firewall_denies_credentials_before_secret_broker_phase():
    manifest = make_tool(
        requested_permissions=[ToolPermissionKind.credential],
        permission_manifest=ToolPermissionManifest(
            required_permissions=[ToolPermissionKind.credential],
            credentials_keys=["TEST_API_KEY"],
        ),
    )

    passed, reasons = CapabilityFirewallPolicy(
        allowed_credentials=["TEST_API_KEY"],
    ).check_firewall(manifest)

    assert passed is False
    assert "CREDENTIAL_ACCESS_NOT_PERMITTED" in reasons


def test_m3_boundary_models_reject_unexpected_fields(actor_context):
    with pytest.raises(ValidationError):
        ConsentGrant(
            consent_id="grant_extra",
            subject_type=ConsentSubjectType.tool,
            subject_id="mock_tool",
            granted_to_actor="test_actor",
            on_behalf_of_user_id="user_123",
            scope_type=ConsentScopeType.project,
            allowed_actions=[PermissionAction.read],
            source="tests",
            unexpected="blocked",
        )

    with pytest.raises(ValidationError):
        ToolManifest(
            tool_id="tool_extra",
            display_name="Tool Extra",
            category=ToolCategory.mock,
            description="extra field test",
            execution_mode=ToolExecutionMode.dry_run,
            risk_level=ToolRiskLevel.safe,
            capability_flag="tool_extra_active",
            owner="tests",
            source="tests",
            version="1.0.0",
            unexpected="blocked",
        )

    with pytest.raises(ValidationError):
        ToolRequest(
            request_id="req_extra",
            run_id="run_extra",
            tool_id="mock_tool",
            actor_context=actor_context,
            requested_action="read",
            purpose="policy testing",
            data_classification=DataBoundary.public,
            unexpected="blocked",
        )


def test_permission_action_any_allows_actions():
    ledger = ConsentLedger()
    ledger.add_grant(
        ConsentGrant(
            consent_id="grant_any",
            subject_type=ConsentSubjectType.tool,
            subject_id="mock_tool",
            granted_to_actor="actor",
            on_behalf_of_user_id="user",
            scope_type=ConsentScopeType.project,
            allowed_actions=[PermissionAction.any],
            source="tests",
        )
    )

    decision = ledger.evaluate(
        ConsentQuery(
            actor_id="actor",
            action=PermissionAction.write,
            resource="mock_tool",
            purpose="policy testing",
        )
    )

    assert decision.allowed is True


def test_permission_action_any_deny_overrides_allow_any():
    ledger = ConsentLedger()
    ledger.add_grant(
        ConsentGrant(
            consent_id="grant_allow_any",
            subject_type=ConsentSubjectType.tool,
            subject_id="mock_tool",
            granted_to_actor="actor",
            on_behalf_of_user_id="user",
            scope_type=ConsentScopeType.project,
            allowed_actions=[PermissionAction.any],
            source="tests",
        )
    )
    ledger.add_grant(
        ConsentGrant(
            consent_id="grant_deny_any",
            subject_type=ConsentSubjectType.tool,
            subject_id="mock_tool",
            granted_to_actor="actor",
            on_behalf_of_user_id="user",
            scope_type=ConsentScopeType.project,
            denied_actions=[PermissionAction.any],
            source="tests",
        )
    )

    decision = ledger.evaluate(
        ConsentQuery(
            actor_id="actor",
            action=PermissionAction.write,
            resource="mock_tool",
            purpose="policy testing",
        )
    )

    assert decision.allowed is False
    assert decision.reason_codes == ["EXPLICIT_DENY_ACTION"]


def test_specific_deny_overrides_allow_any():
    ledger = ConsentLedger()
    ledger.add_grant(
        ConsentGrant(
            consent_id="grant_allow_any",
            subject_type=ConsentSubjectType.tool,
            subject_id="mock_tool",
            granted_to_actor="actor",
            on_behalf_of_user_id="user",
            scope_type=ConsentScopeType.project,
            allowed_actions=[PermissionAction.any],
            denied_actions=[PermissionAction.delete],
            source="tests",
        )
    )

    decision = ledger.evaluate(
        ConsentQuery(
            actor_id="actor",
            action=PermissionAction.delete,
            resource="mock_tool",
            purpose="policy testing",
        )
    )

    assert decision.allowed is False
    assert decision.reason_codes == ["EXPLICIT_DENY_ACTION"]
