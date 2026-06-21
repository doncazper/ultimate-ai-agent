from ultimate_ai_agent.core.consent import (
    ConsentLedger,
    ConsentGrant,
    ConsentQuery,
    ConsentScopeType,
    ConsentSubjectType,
    PermissionAction,
    DataBoundary,
)

def test_consent_policy_deny_overrides_allow() -> None:
    ledger = ConsentLedger()
    # Allow grant
    g_allow = ConsentGrant(
        consent_id="g_allow",
        subject_type=ConsentSubjectType.tool,
        subject_id="tool_file",
        granted_to_actor="orchestrator",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[PermissionAction.write],
        source="test"
    )
    # Deny grant
    g_deny = ConsentGrant(
        consent_id="g_deny",
        subject_type=ConsentSubjectType.tool,
        subject_id="tool_file",
        granted_to_actor="orchestrator",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[],
        denied_actions=[PermissionAction.write],
        source="test"
    )
    ledger.add_grant(g_allow)
    ledger.add_grant(g_deny)
    
    query = ConsentQuery(
        actor_id="orchestrator",
        action=PermissionAction.write,
        resource="tool_file",
        purpose="file editing"
    )
    
    decision = ledger.evaluate(query)
    assert decision.allowed is False
    assert "EXPLICIT_DENY_ACTION" in decision.reason_codes

def test_consent_policy_sensitive_personal_data() -> None:
    ledger = ConsentLedger()
    # Allow grant that does NOT specify sensitive personal boundary
    g1 = ConsentGrant(
        consent_id="g1",
        subject_type=ConsentSubjectType.tool,
        subject_id="tool_analytics",
        granted_to_actor="orchestrator",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[PermissionAction.read],
        source="test"
    )
    ledger.add_grant(g1)
    
    query = ConsentQuery(
        actor_id="orchestrator",
        action=PermissionAction.read,
        resource="tool_analytics",
        data_classification=DataBoundary.sensitive_personal,
        purpose="analytics"
    )
    
    decision = ledger.evaluate(query)
    # Denied because explicit data classification is required for sensitive_personal
    assert decision.allowed is False
    
    # Add grant that explicitly allows sensitive personal data boundary
    g2 = ConsentGrant(
        consent_id="g2",
        subject_type=ConsentSubjectType.tool,
        subject_id="tool_analytics",
        granted_to_actor="orchestrator",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[PermissionAction.read],
        allowed_data_boundaries=[DataBoundary.sensitive_personal],
        source="test"
    )
    ledger.add_grant(g2)
    
    decision2 = ledger.evaluate(query)
    assert decision2.allowed is True
    assert "g2" in decision2.matched_grants


def test_consent_policy_denied_purpose_overrides_allow() -> None:
    ledger = ConsentLedger()
    ledger.add_grant(
        ConsentGrant(
            consent_id="g_purpose_deny",
            subject_type=ConsentSubjectType.tool,
            subject_id="tool_file",
            granted_to_actor="orchestrator",
            on_behalf_of_user_id="user_123",
            scope_type=ConsentScopeType.project,
            allowed_actions=[PermissionAction.read],
            denied_purposes=["training"],
            source="test",
        )
    )

    decision = ledger.evaluate(
        ConsentQuery(
            actor_id="orchestrator",
            action=PermissionAction.read,
            resource="tool_file",
            data_classification=DataBoundary.project_private,
            purpose="training",
        )
    )

    assert decision.allowed is False
    assert "EXPLICIT_DENY_PURPOSE" in decision.reason_codes


def test_consent_policy_denied_resource_prefix_overrides_broad_allow() -> None:
    ledger = ConsentLedger()
    ledger.add_grant(
        ConsentGrant(
            consent_id="g_resource_deny",
            subject_type=ConsentSubjectType.tool,
            subject_id="tool_messages",
            granted_to_actor="orchestrator",
            on_behalf_of_user_id="user_123",
            scope_type=ConsentScopeType.project,
            allowed_actions=[PermissionAction.read],
            allowed_resources=["messages/*"],
            denied_resources=["messages/family/*"],
            source="test",
        )
    )

    decision = ledger.evaluate(
        ConsentQuery(
            actor_id="orchestrator",
            action=PermissionAction.read,
            resource="messages/family/thread_1",
            data_classification=DataBoundary.user_private,
            purpose="summary",
        )
    )

    assert decision.allowed is False
    assert "EXPLICIT_DENY_RESOURCE" in decision.reason_codes


def test_consent_policy_regulated_data_requires_explicit_boundary() -> None:
    ledger = ConsentLedger()
    ledger.add_grant(
        ConsentGrant(
            consent_id="g_broad",
            subject_type=ConsentSubjectType.tool,
            subject_id="tool_records",
            granted_to_actor="orchestrator",
            on_behalf_of_user_id="user_123",
            scope_type=ConsentScopeType.project,
            allowed_actions=[PermissionAction.read],
            allowed_resources=["records/*"],
            source="test",
        )
    )

    query = ConsentQuery(
        actor_id="orchestrator",
        action=PermissionAction.read,
        resource="records/case_1",
        data_classification=DataBoundary.regulated,
        purpose="review",
    )

    denied = ledger.evaluate(query)
    assert denied.allowed is False
    assert "NO_MATCHING_GRANT" in denied.reason_codes

    ledger.add_grant(
        ConsentGrant(
            consent_id="g_regulated",
            subject_type=ConsentSubjectType.tool,
            subject_id="tool_records",
            granted_to_actor="orchestrator",
            on_behalf_of_user_id="user_123",
            scope_type=ConsentScopeType.project,
            allowed_actions=[PermissionAction.read],
            allowed_resources=["records/*"],
            allowed_data_boundaries=[DataBoundary.regulated],
            source="test",
        )
    )

    allowed = ledger.evaluate(query)
    assert allowed.allowed is True
    assert "g_regulated" in allowed.matched_grants
