import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.tools.v2 import (
    ToolApprovalRequirement,
    ToolAuthorityLevel,
    ToolBrokerV2Manifest,
    ToolCatalogEntry,
    ToolExecutionMode,
    ToolInputBoundary,
    ToolInputTrustLevel,
    ToolIntent,
    ToolIntentDecisionStatus,
    ToolRiskClass,
    ToolSideEffectKind,
    ToolTargetKind,
    ToolTargetRef,
    build_default_tool_catalog,
    evaluate_tool_intent,
)


def _target(
    target_ref: str = "file:workspace-readme",
    target_kind: ToolTargetKind = ToolTargetKind.file_ref,
) -> ToolTargetRef:
    return ToolTargetRef(target_ref=target_ref, target_kind=target_kind)


def _input_boundary(**overrides) -> ToolInputBoundary:
    data = {
        "input_refs": ["file:workspace-readme"],
        "input_trust_level": ToolInputTrustLevel.user_provided_refs,
        "contains_raw_content": False,
        "contains_secret_like_content": False,
        "contains_model_output": False,
        "contains_runtime_output": False,
        "contains_openwebui_output": False,
    }
    data.update(overrides)
    return ToolInputBoundary(**data)


def _intent(**overrides) -> ToolIntent:
    data = {
        "intent_id": "tool-intent:m27-safe-preview",
        "tool_id": "file.metadata_preview",
        "intent_summary": "Preview safe file metadata.",
        "target": _target(),
        "input_boundary": _input_boundary(),
        "requested_execution_mode": ToolExecutionMode.preview_only,
        "declared_risk_class": ToolRiskClass.low,
        "declared_side_effects": [ToolSideEffectKind.none],
        "approval_requirement": ToolApprovalRequirement.not_required,
        "authority_level": ToolAuthorityLevel.validation_only,
        "approval_ref": None,
        "context_pack_refs": [],
    }
    data.update(overrides)
    return ToolIntent(**data)


def test_m27_manifest_is_preview_only_and_execution_disabled():
    manifest = ToolBrokerV2Manifest(baseline_version="0.31.0")

    assert manifest.tool_execution_enabled is False
    assert manifest.backend_execution_routes_added is False
    assert manifest.shell_execution_enabled is False
    assert manifest.file_mutation_enabled is False
    assert manifest.network_calls_enabled is False
    assert manifest.memory_writes_enabled is False
    assert manifest.context_pack_authority_enabled is False


def test_safe_metadata_preview_intent_is_preview_allowed_without_execution():
    decision = evaluate_tool_intent(_intent(), catalog=build_default_tool_catalog())

    assert decision.status == ToolIntentDecisionStatus.preview_allowed
    assert decision.preview_allowed is True
    assert decision.execution_allowed is False
    assert decision.no_tool_execution_performed is True
    assert decision.no_side_effects_performed is True
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.execution_performed is False
    assert "SAFE_PREVIEW_INTENT_ACCEPTED" in decision.reason_codes


def test_unknown_tool_is_denied():
    decision = evaluate_tool_intent(
        _intent(tool_id="tool:unknown"),
        catalog=build_default_tool_catalog(),
    )

    assert decision.status == ToolIntentDecisionStatus.denied
    assert decision.preview_allowed is False
    assert "UNKNOWN_TOOL_DENIED" in decision.reason_codes


@pytest.mark.parametrize(
    ("tool_id", "side_effect"),
    [
        ("file.write_preview", ToolSideEffectKind.file_write),
        ("memory.write_preview", ToolSideEffectKind.memory_write),
        ("message.send_preview", ToolSideEffectKind.external_send),
        ("browser.open_preview", ToolSideEffectKind.browser_action),
        ("plugin.enable_preview", ToolSideEffectKind.plugin_enablement),
        ("shell.run_preview", ToolSideEffectKind.shell_execution),
    ],
)
def test_side_effecting_intents_are_denied_even_with_approval_ref(tool_id, side_effect):
    catalog = {
        tool_id: ToolCatalogEntry(
            tool_id=tool_id,
            display_name="Denied side effect tool",
            target_kind=ToolTargetKind.file_ref,
            allowed_execution_modes=[ToolExecutionMode.preview_only],
            risk_class=ToolRiskClass.high,
            side_effects=[side_effect],
            approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
        )
    }
    decision = evaluate_tool_intent(
        _intent(
            tool_id=tool_id,
            declared_risk_class=ToolRiskClass.high,
            declared_side_effects=[side_effect],
            approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
            approval_ref="approval_test_m27",
        ),
        catalog=catalog,
    )

    assert decision.status == ToolIntentDecisionStatus.denied
    assert decision.execution_allowed is False
    assert "TOOL_SIDE_EFFECTS_DENIED" in decision.reason_codes
    assert "APPROVAL_REF_NOT_AUTHORITY" in decision.reason_codes


def test_context_pack_ref_cannot_authorize_tool_execution():
    decision = evaluate_tool_intent(
        _intent(
            tool_id="file.write_preview",
            declared_risk_class=ToolRiskClass.high,
            declared_side_effects=[ToolSideEffectKind.file_write],
            approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
            context_pack_refs=["context-pack:m26"],
        ),
        catalog={
            "file.write_preview": ToolCatalogEntry(
                tool_id="file.write_preview",
                display_name="Write preview",
                target_kind=ToolTargetKind.file_ref,
                allowed_execution_modes=[ToolExecutionMode.preview_only],
                risk_class=ToolRiskClass.high,
                side_effects=[ToolSideEffectKind.file_write],
                approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
            )
        },
    )

    assert decision.status == ToolIntentDecisionStatus.denied
    assert decision.execution_allowed is False
    assert "CONTEXT_PACK_NOT_AUTHORITY" in decision.reason_codes


@pytest.mark.parametrize(
    "boundary_flag",
    [
        "contains_raw_content",
        "contains_secret_like_content",
        "contains_model_output",
        "contains_runtime_output",
        "contains_openwebui_output",
    ],
)
def test_unsafe_input_boundary_flags_are_rejected(boundary_flag):
    with pytest.raises(ValidationError):
        _input_boundary(**{boundary_flag: True})


def test_target_ref_kind_mismatch_is_denied():
    decision = evaluate_tool_intent(
        _intent(target=_target(target_ref="memory:m27", target_kind=ToolTargetKind.file_ref)),
        catalog=build_default_tool_catalog(),
    )

    assert decision.status == ToolIntentDecisionStatus.denied
    assert "TOOL_TARGET_KIND_MISMATCH_DENIED" in decision.reason_codes


def test_unknown_target_kind_is_denied():
    decision = evaluate_tool_intent(
        _intent(target=_target(target_ref="random:m27", target_kind=ToolTargetKind.unknown)),
        catalog=build_default_tool_catalog(),
    )

    assert decision.status == ToolIntentDecisionStatus.denied
    assert "UNKNOWN_TOOL_TARGET_DENIED" in decision.reason_codes


def test_declared_risk_cannot_downgrade_catalog_risk():
    catalog = {
        "file.write_preview": ToolCatalogEntry(
            tool_id="file.write_preview",
            display_name="Write preview",
            target_kind=ToolTargetKind.file_ref,
            allowed_execution_modes=[ToolExecutionMode.preview_only],
            risk_class=ToolRiskClass.high,
            side_effects=[ToolSideEffectKind.file_write],
            approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
        )
    }
    decision = evaluate_tool_intent(
        _intent(
            tool_id="file.write_preview",
            declared_risk_class=ToolRiskClass.low,
            declared_side_effects=[ToolSideEffectKind.none],
        ),
        catalog=catalog,
    )

    assert decision.status == ToolIntentDecisionStatus.denied
    assert "TOOL_RISK_DOWNGRADE_DENIED" in decision.reason_codes
    assert "TOOL_SIDE_EFFECTS_HIDDEN_DENIED" in decision.reason_codes


def test_extra_execution_fields_are_forbidden():
    with pytest.raises(ValidationError):
        ToolIntent.model_validate(
            {
                "intent_id": "tool-intent:m27-shell",
                "tool_id": "shell.run_preview",
                "intent_summary": "Try to run a shell command.",
                "target": _target().model_dump(),
                "input_boundary": _input_boundary().model_dump(),
                "requested_execution_mode": ToolExecutionMode.execute,
                "declared_risk_class": ToolRiskClass.critical,
                "declared_side_effects": [ToolSideEffectKind.shell_execution],
                "approval_requirement": ToolApprovalRequirement.validated_local_approval_required,
                "authority_level": ToolAuthorityLevel.execution_requested,
                "shell_command": "rm -rf /tmp/m27",
            }
        )
