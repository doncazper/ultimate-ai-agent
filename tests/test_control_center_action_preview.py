import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center import (
    ControlCenterActionDecisionStatus,
    ControlCenterActionKind,
    ControlCenterRiskLevel,
    preview_control_center_action,
)


def preview_payload(**overrides):
    payload = {
        "request_id": "cc_preview_001",
        "actor_context": {"actor_type": "user", "actor_id": "local_operator"},
        "action_kind": ControlCenterActionKind.view_status,
        "target_ref": "dashboard",
        "purpose": "review current status",
        "risk_level": ControlCenterRiskLevel.safe,
        "data_classification": "system_internal",
        "consent_refs": [],
        "metadata": {"source": "test"},
    }
    payload.update(overrides)
    return payload


def test_control_center_action_preview_allows_safe_status_view():
    decision = preview_control_center_action(preview_payload())

    assert decision.allowed is True
    assert decision.status == ControlCenterActionDecisionStatus.allowed_preview
    assert decision.preview_summary == "Preview only; no action was executed."


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"action_kind": ControlCenterActionKind.disabled_execute}, "EXECUTION_ACTION_BLOCKED"),
        ({"target_ref": "remote-workers/dispatch/job"}, "REMOTE_EXECUTION_BLOCKED"),
        ({"target_ref": "plugins/enable/build-web-apps"}, "PLUGIN_ENABLEMENT_BLOCKED"),
        ({"target_ref": "mobile/sensors/camera"}, "MOBILE_SENSOR_BLOCKED"),
        ({"target_ref": "runtime/execute/model"}, "RUNTIME_EXECUTION_BLOCKED"),
        ({"metadata": {"claim": "provider invocation requested"}}, "MODEL_OR_PROVIDER_EXECUTION_BLOCKED"),
        ({"metadata": {"claim": "credential use requested"}}, "CREDENTIAL_USE_BLOCKED"),
        ({"metadata": {"claim": "mutate file requested"}}, "MUTATION_BLOCKED"),
        ({"approval_ref": "approval_any_string"}, "ARBITRARY_APPROVAL_REF_NOT_AUTHORITY"),
    ],
)
def test_control_center_action_preview_denies_unsafe_claims(overrides, reason):
    decision = preview_control_center_action(preview_payload(**overrides))

    assert decision.allowed is False
    assert reason in decision.reason_codes
    assert "abcdefghijklmnop" not in decision.safe_message


def test_control_center_high_risk_preview_requires_approval_without_execution():
    decision = preview_control_center_action(
        preview_payload(
            action_kind=ControlCenterActionKind.preview_action,
            risk_level=ControlCenterRiskLevel.high,
            target_ref="tool/request/high-risk-preview",
        )
    )

    assert decision.allowed is False
    assert decision.status == ControlCenterActionDecisionStatus.approval_required
    assert "APPROVAL_REQUIRED_FOR_HIGH_RISK_PREVIEW" in decision.reason_codes
    assert decision.preview_summary == "Preview only; no action was executed."


def test_control_center_action_preview_rejects_extra_raw_prompt_field():
    with pytest.raises(ValidationError):
        preview_control_center_action(preview_payload(raw_prompt="summarize private file"))
