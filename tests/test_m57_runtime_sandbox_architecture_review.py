from typing import Any
import pytest

from ultimate_ai_agent.core.sandbox import (
    RuntimeSandboxArchitecturePolicy,
    RuntimeSandboxArchitectureRequest,
    RuntimeSandboxArchitectureStatus,
    build_runtime_sandbox_architecture_review,
    validate_runtime_sandbox_architecture_policy,
    validate_runtime_sandbox_architecture_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "sandbox-review-request:m57-runtime-boundary",
        "review_ref": "sandbox-review:m57-runtime-boundary",
        "architecture_ref": "sandbox-architecture:m57-contract",
        "boundary_refs": [
            "boundary:no-shell-execution",
            "boundary:no-subprocess",
            "boundary:no-side-effects",
        ],
        "threat_model_refs": [
            "threat:process-spawn",
            "threat:network-egress",
            "threat:filesystem-mutation",
        ],
        "audit_requirement_refs": ["audit:dry-run-before-execution"],
        "safe_summary": "Architecture review over declared sandbox boundaries only.",
    }
    data.update(overrides)
    return RuntimeSandboxArchitectureRequest(**data)


def test_runtime_sandbox_architecture_review_is_contract_only_and_no_effect() -> None:
    review = build_runtime_sandbox_architecture_review(_request())

    assert review.status == RuntimeSandboxArchitectureStatus.reviewed
    assert review.architecture_review_only is True
    assert review.runtime_sandbox_enabled is False
    assert review.execution_performed is False
    assert review.subprocess_performed is False
    assert review.shell_execution_performed is False
    assert review.side_effects_performed == []
    assert review.reason_codes == ["M57_RUNTIME_SANDBOX_ARCHITECTURE_REVIEW_ONLY"]
    assert review.receipt_plan is not None
    assert review.receipt_plan.side_effects_performed == []
    assert "raw provider payload" not in str(review.model_dump()).lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("sandbox_runtime_requested", "SANDBOX_RUNTIME_DENIED"),
        ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
        ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
        ("network_access_requested", "NETWORK_ACCESS_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("m58_dry_run_harness_requested", "M58_DRY_RUN_HARNESS_DENIED"),
    ],
)
def test_runtime_sandbox_architecture_request_denies_runtime_authority_flags(
    field: str, reason: str
) -> None:
    request = _request(**{field: True})

    with pytest.raises(ValueError, match=reason):
        validate_runtime_sandbox_architecture_request(request)


def test_runtime_sandbox_architecture_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "shell_execution_requested": True,
            "contains_raw_prompt": True,
        }
    )

    with pytest.raises(ValueError, match="SHELL_EXECUTION_DENIED"):
        build_runtime_sandbox_architecture_review(request)


def test_runtime_sandbox_architecture_policy_denies_enabled_runtime_flags() -> None:
    policy = RuntimeSandboxArchitecturePolicy(
        sandbox_runtime_enabled=True,
        subprocess_execution_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="SANDBOX_RUNTIME_DENIED"):
        validate_runtime_sandbox_architecture_policy(policy)


def test_runtime_sandbox_architecture_denies_secret_like_metadata() -> None:
    request = _request(metadata={"api_key": "abcde12345678901234"})

    with pytest.raises(ValueError, match="SECRET_LIKE_SANDBOX_METADATA_DENIED"):
        build_runtime_sandbox_architecture_review(request)
