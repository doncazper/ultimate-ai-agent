from typing import Any
import pytest

from ultimate_ai_agent.core.dry_run_audit import (
    DryRunExecutionAuditIntent,
    DryRunExecutionAuditPolicy,
    DryRunExecutionAuditRequest,
    DryRunExecutionAuditStatus,
    build_dry_run_execution_audit_report,
    validate_dry_run_execution_audit_policy,
    validate_dry_run_execution_audit_request,
)


def _intent(**overrides: Any) -> Any:
    data = {
        "intent_ref": "dry-run-intent:m58-safe-tool-preview",
        "operation_ref": "operation:tool-preview",
        "target_ref": "target:safe-local-contract",
        "requested_capability_refs": [
            "capability:preview-only",
            "capability:no-side-effects",
        ],
        "safe_summary": "Audit a declared preview-only operation without running it.",
    }
    data.update(overrides)
    return DryRunExecutionAuditIntent(**data)


def _request(**overrides: Any) -> Any:
    intent = overrides.pop("intent", _intent())
    data = {
        "request_ref": "dry-run-audit-request:m58-safe-tool-preview",
        "audit_ref": "dry-run-audit:m58-safe-tool-preview",
        "sandbox_review_ref": "sandbox-review:m57-runtime-boundary",
        "intent_refs": [intent.intent_ref],
        "intents": [intent],
        "actor_ref": "actor:local-reviewer",
        "replay_key_ref": "replay-key:m58-safe-tool-preview",
    }
    data.update(overrides)
    return DryRunExecutionAuditRequest(**data)


def test_dry_run_execution_audit_report_is_no_effect_and_deterministic() -> None:
    report = build_dry_run_execution_audit_report(_request())

    assert report.status == DryRunExecutionAuditStatus.reviewed
    assert report.dry_run_only is True
    assert report.execution_performed is False
    assert report.tool_execution_performed is False
    assert report.subprocess_performed is False
    assert report.shell_execution_performed is False
    assert report.side_effects_performed == []
    assert report.entries[0].reason_codes == ["M58_DRY_RUN_AUDIT_ONLY"]
    assert report.receipt_plan is not None
    assert report.receipt_plan.execution_performed is False
    assert report.receipt_plan.side_effects_performed == []
    assert "raw prompt body" not in str(report.model_dump()).lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("execution_requested", "EXECUTION_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
        ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
        ("network_access_requested", "NETWORK_ACCESS_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
        ("side_effects_requested", "SIDE_EFFECTS_DENIED"),
    ],
)
def test_dry_run_execution_intent_denies_runtime_authority_flags(field: str, reason: str) -> None:
    request = _request(intent=_intent(**{field: True}))

    with pytest.raises(ValueError, match=reason):
        validate_dry_run_execution_audit_request(request)


def test_dry_run_execution_audit_revalidates_model_copy_mutated_intent() -> None:
    request = _request()
    request = request.model_copy(
        update={
            "intents": [
                request.intents[0].model_copy(
                    update={
                        "execution_requested": True,
                        "contains_raw_prompt": True,
                    }
                )
            ]
        }
    )

    with pytest.raises(ValueError, match="EXECUTION_DENIED"):
        build_dry_run_execution_audit_report(request)


def test_dry_run_execution_audit_denies_duplicate_and_missing_intent_bindings() -> None:
    duplicate = _intent(operation_ref="operation:duplicate")
    with pytest.raises(ValueError, match="DRY_RUN_INTENT_REF_DUPLICATE"):
        validate_dry_run_execution_audit_request(
            _request(intent_refs=[duplicate.intent_ref, duplicate.intent_ref], intents=[duplicate])
        )

    with pytest.raises(ValueError, match="DRY_RUN_INTENT_MISSING"):
        validate_dry_run_execution_audit_request(_request(intent_refs=["dry-run-intent:missing"], intents=[]))


def test_dry_run_execution_audit_denies_secret_like_content() -> None:
    request = _request(intent=_intent(safe_summary="api_key='abcde12345678901234'"))

    with pytest.raises(ValueError, match="SECRET_LIKE_DRY_RUN_AUDIT_CONTENT_DENIED"):
        build_dry_run_execution_audit_report(request)


def test_dry_run_execution_audit_policy_denies_runtime_authority() -> None:
    policy = DryRunExecutionAuditPolicy(
        execution_enabled=True,
        shell_execution_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="EXECUTION_DENIED"):
        validate_dry_run_execution_audit_policy(policy)
