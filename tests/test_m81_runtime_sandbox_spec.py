from typing import Any
import pytest

from ultimate_ai_agent.core.sandbox import (
    RuntimeSandboxSpecPolicy,
    RuntimeSandboxSpecRequest,
    RuntimeSandboxSpecStatus,
    build_runtime_sandbox_spec,
    validate_runtime_sandbox_spec_policy,
    validate_runtime_sandbox_spec_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "runtime-sandbox-spec-request:m81",
        "spec_ref": "runtime-sandbox-spec:m81",
        "baseline_ref": "baseline:v0.84.1",
        "actor_ref": "actor:local-reviewer",
        "prior_milestone_refs": ["milestone:M57", "milestone:M58", "milestone:M80"],
        "boundary_refs": [
            "sandbox-boundary:m57-architecture-review",
            "sandbox-boundary:m58-dry-run-audit",
            "sandbox-boundary:m80-freeze",
        ],
        "threat_model_refs": [
            "threat-model:no-process-spawn",
            "threat-model:no-network-runtime",
        ],
        "audit_requirement_refs": [
            "audit-requirement:deterministic-spec",
            "audit-requirement:no-side-effects",
        ],
        "safe_summary": (
            "M81 defines a runtime sandbox spec only; it does not start a sandbox, "
            "create command proposals, execute commands, spawn processes, mutate files, "
            "access networks, call models, write memory, inject context, add routes, "
            "or grant production authority."
        ),
    }
    data.update(overrides)
    return RuntimeSandboxSpecRequest(**data)


def test_m81_runtime_sandbox_spec_is_spec_only_and_no_authority() -> None:
    spec = build_runtime_sandbox_spec(_request())

    assert spec.status == RuntimeSandboxSpecStatus.specified
    assert spec.spec_only is True
    assert spec.review_only is True
    assert spec.deterministic is True
    assert spec.local_only is True
    assert spec.runtime_sandbox_started is False
    assert spec.command_proposal_created is False
    assert spec.command_execution_performed is False
    assert spec.subprocess_execution_performed is False
    assert spec.shell_execution_performed is False
    assert spec.process_spawn_performed is False
    assert spec.filesystem_mutation_performed is False
    assert spec.network_access_performed is False
    assert spec.tool_execution_performed is False
    assert spec.browser_automation_performed is False
    assert spec.plugin_execution_performed is False
    assert spec.remote_execution_performed is False
    assert spec.model_call_performed is False
    assert spec.memory_write_performed is False
    assert spec.context_injection_performed is False
    assert spec.background_worker_started is False
    assert spec.backend_route_added is False
    assert spec.control_center_control_added is False
    assert spec.dependency_added is False
    assert spec.production_authority_granted is False
    assert spec.side_effects_performed == []
    assert spec.reason_codes == [
        "M81_RUNTIME_SANDBOX_SPEC_ONLY",
        "M81_NO_RUNTIME_SANDBOX_EXECUTION",
        "M82_REMAINS_FUTURE",
    ]
    assert "private key" not in str(spec.model_dump()).lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_sandbox_requested", "RUNTIME_SANDBOX_EXECUTION_DENIED"),
        ("command_proposal_requested", "COMMAND_PROPOSAL_DENIED"),
        ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
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
        ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
        ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
        ("contains_secret", "SECRET_LIKE_SANDBOX_SPEC_CONTENT_DENIED"),
    ],
)
def test_m81_runtime_sandbox_spec_denies_runtime_authority_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_runtime_sandbox_spec_request(_request(**{field: True}))


def test_m81_runtime_sandbox_spec_requires_prior_milestone_refs_and_unique_boundaries() -> None:
    with pytest.raises(ValueError, match="M81_PRIOR_MILESTONE_REFS_REQUIRED"):
        validate_runtime_sandbox_spec_request(_request(prior_milestone_refs=[]))

    with pytest.raises(ValueError, match="M81_PRIOR_MILESTONE_REF_REQUIRED"):
        validate_runtime_sandbox_spec_request(
            _request(prior_milestone_refs=["milestone:M57", "milestone:M58"])
        )

    with pytest.raises(ValueError, match="M81_BOUNDARY_REF_DUPLICATE"):
        validate_runtime_sandbox_spec_request(
            _request(
                boundary_refs=[
                    "sandbox-boundary:m80-freeze",
                    "sandbox-boundary:m80-freeze",
                ]
            )
        )


def test_m81_runtime_sandbox_spec_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "runtime_sandbox_requested": True,
            "contains_secret": True,
        }
    )

    with pytest.raises(ValueError, match="RUNTIME_SANDBOX_EXECUTION_DENIED"):
        build_runtime_sandbox_spec(request)


def test_m81_runtime_sandbox_spec_denies_secret_like_metadata() -> None:
    request = _request(metadata={"token": "abcde12345678901234"})

    with pytest.raises(ValueError, match="SECRET_LIKE_SANDBOX_SPEC_CONTENT_DENIED"):
        build_runtime_sandbox_spec(request)


def test_m81_runtime_sandbox_spec_policy_denies_enablement() -> None:
    policy = RuntimeSandboxSpecPolicy(
        runtime_sandbox_enabled=True,
        command_execution_enabled=True,
        shell_execution_enabled=True,
        network_access_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="RUNTIME_SANDBOX_EXECUTION_DENIED"):
        validate_runtime_sandbox_spec_policy(policy)
