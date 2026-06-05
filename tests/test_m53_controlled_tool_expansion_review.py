import pytest

from ultimate_ai_agent.core.tools import (
    ControlledToolExpansionCandidate,
    ControlledToolExpansionPolicy,
    ControlledToolExpansionReviewStatus,
    ToolExpansionCapabilityKind,
    evaluate_controlled_tool_expansion_candidate,
    validate_controlled_tool_expansion_candidate,
    validate_controlled_tool_expansion_policy,
)


def _candidate(**overrides):
    data = {
        "candidate_ref": "tool-expansion-candidate:m53-safe",
        "safe_name": "Metadata-only review candidate",
        "capability_kind": ToolExpansionCapabilityKind.safe_metadata_review,
        "safe_summary": "Review a future tool capability without enabling it.",
    }
    data.update(overrides)
    return ControlledToolExpansionCandidate(**data)


def test_controlled_tool_expansion_review_allows_metadata_review_only() -> None:
    decision = evaluate_controlled_tool_expansion_candidate(_candidate())

    assert decision.status == ControlledToolExpansionReviewStatus.review_ready
    assert decision.review_allowed is True
    assert decision.execution_allowed is False
    assert decision.tool_enablement_allowed is False
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.execution_performed is False
    assert decision.receipt_plan.tool_enabled is False
    assert decision.receipt_plan.side_effects_performed == []
    assert decision.no_network_call_performed is True
    assert decision.no_model_call_performed is True
    assert decision.no_memory_write_performed is True
    assert decision.no_context_injection_performed is True


@pytest.mark.parametrize(
    "capability_kind",
    [
        ToolExpansionCapabilityKind.shell_execution,
        ToolExpansionCapabilityKind.subprocess_execution,
        ToolExpansionCapabilityKind.unrestricted_network_tool,
        ToolExpansionCapabilityKind.provider_model_call,
        ToolExpansionCapabilityKind.browser_automation_execution,
        ToolExpansionCapabilityKind.plugin_enablement,
        ToolExpansionCapabilityKind.mobile_sensor_access,
        ToolExpansionCapabilityKind.remote_execution,
        ToolExpansionCapabilityKind.raw_file_browsing,
        ToolExpansionCapabilityKind.raw_file_export,
        ToolExpansionCapabilityKind.full_file_read,
        ToolExpansionCapabilityKind.file_mutation,
        ToolExpansionCapabilityKind.memory_write,
        ToolExpansionCapabilityKind.context_injection,
        ToolExpansionCapabilityKind.credentials_cookie_handling,
        ToolExpansionCapabilityKind.external_saas_analytics_sdk,
        ToolExpansionCapabilityKind.production_authority,
    ],
)
def test_effectful_tool_expansion_candidates_are_future_review_only(
    capability_kind: ToolExpansionCapabilityKind,
) -> None:
    decision = evaluate_controlled_tool_expansion_candidate(
        _candidate(
            candidate_ref=f"tool-expansion-candidate:m53-{capability_kind.value}",
            capability_kind=capability_kind,
            safe_name=f"Future {capability_kind.value} review",
        )
    )

    assert decision.status == ControlledToolExpansionReviewStatus.future_milestone
    assert decision.review_allowed is True
    assert decision.execution_allowed is False
    assert decision.tool_enablement_allowed is False
    assert decision.future_milestone_required is True
    assert "M53_REVIEW_ONLY" in decision.reason_codes
    assert "FUTURE_MILESTONE_REQUIRED" in decision.reason_codes


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("execution_requested", "TOOL_EXPANSION_EXECUTION_DENIED"),
        ("tool_enablement_requested", "TOOL_ENABLEMENT_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
        ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_DENIED"),
        ("contains_raw_tool_payload", "RAW_TOOL_PAYLOAD_DENIED"),
        ("contains_secret_like_content", "SECRET_LIKE_CONTENT_DENIED"),
    ],
)
def test_controlled_tool_expansion_candidate_rejects_authority_or_raw_fields(
    field: str,
    reason: str,
) -> None:
    candidate = _candidate(**{field: True})

    with pytest.raises(ValueError, match=reason):
        validate_controlled_tool_expansion_candidate(candidate)


def test_controlled_tool_expansion_revalidates_model_copy_mutated_fields() -> None:
    candidate = _candidate().model_copy(
        update={
            "contains_raw_prompt": True,
            "execution_requested": True,
            "tool_enablement_requested": True,
        }
    )

    with pytest.raises(ValueError, match="TOOL_EXPANSION_EXECUTION_DENIED"):
        evaluate_controlled_tool_expansion_candidate(candidate)


def test_approval_ref_cannot_authorize_controlled_tool_expansion() -> None:
    candidate = _candidate(approval_ref="approval:m53-tool-expansion")

    with pytest.raises(ValueError, match="APPROVAL_REF_NOT_AUTHORITY"):
        evaluate_controlled_tool_expansion_candidate(candidate)


def test_unknown_tool_expansion_candidate_is_denied() -> None:
    decision = evaluate_controlled_tool_expansion_candidate(
        _candidate(capability_kind=ToolExpansionCapabilityKind.unknown)
    )

    assert decision.status == ControlledToolExpansionReviewStatus.denied
    assert decision.review_allowed is False
    assert decision.execution_allowed is False
    assert decision.tool_enablement_allowed is False
    assert "UNKNOWN_TOOL_EXPANSION_DENIED" in decision.reason_codes


def test_controlled_tool_expansion_policy_rejects_runtime_flags() -> None:
    policy = ControlledToolExpansionPolicy(
        shell_execution_enabled=True,
        unrestricted_network_tools_enabled=True,
        provider_model_calls_enabled=True,
        browser_automation_execution_enabled=True,
        plugin_enablement_enabled=True,
        memory_write_enabled=True,
        context_injection_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="SHELL_EXECUTION_DENIED"):
        validate_controlled_tool_expansion_policy(policy)
