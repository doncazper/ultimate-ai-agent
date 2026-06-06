import pytest

from ultimate_ai_agent.core.autonomy import (
    AutonomyAuthorityMode,
    AutonomyPolicyDecision,
    AutonomyPolicyEnginePolicy,
    AutonomyPolicyEvaluationRequest,
    AutonomyPolicyRule,
    AutonomyRiskClass,
    AutonomousPlanSimulationRequest,
    AutonomousPlanSimulationStep,
    ScopedAutonomySessionRequest,
    ScopedAutonomySessionScope,
    build_autonomous_plan_simulation_result,
    build_autonomy_policy_decision,
    validate_autonomous_plan_simulation_request,
    validate_autonomous_plan_simulation_step,
)


def _scope(**overrides):
    data = {
        "scope_ref": "autonomy-session-scope:m64-local-review",
        "actor_ref": "actor:local-reviewer",
        "resource_refs": ["resource:local-prototype"],
        "capability_refs": ["capability:observe-only-review"],
        "allowlist_refs": ["allowlist:m64-local-review"],
        "max_duration_seconds": 900,
        "risk_class": AutonomyRiskClass.low,
        "revocation_ref": "revocation:m64-local-review",
        "audit_ref": "audit:m64-local-review",
        "replay_ref": "replay:m64-local-review",
    }
    data.update(overrides)
    return ScopedAutonomySessionScope(**data)


def _session_request(**overrides):
    data = {
        "session_request_ref": "autonomy-session-request:m64-local-review",
        "requested_mode": AutonomyAuthorityMode.dry_run_plan,
        "scope": _scope(),
    }
    data.update(overrides)
    return ScopedAutonomySessionRequest(**data)


def _rule(**overrides):
    data = {
        "rule_ref": "autonomy-policy-rule:m64-local-review",
        "allowed_actor_refs": ["actor:local-reviewer"],
        "allowed_resource_refs": ["resource:local-prototype"],
        "allowed_capability_refs": ["capability:observe-only-review"],
        "required_allowlist_refs": ["allowlist:m64-local-review"],
        "max_mode": AutonomyAuthorityMode.dry_run_plan,
        "max_risk_class": AutonomyRiskClass.low,
        "max_duration_seconds": 900,
    }
    data.update(overrides)
    return AutonomyPolicyRule(**data)


def _policy(**overrides):
    data = {
        "policy_ref": "autonomy-policy:m64-local-review",
        "policy_version_ref": "autonomy-policy-version:m64-v1",
        "rules": [_rule()],
    }
    data.update(overrides)
    return AutonomyPolicyEnginePolicy(**data)


def _policy_decision(**overrides):
    request = AutonomyPolicyEvaluationRequest(
        evaluation_request_ref="autonomy-policy-evaluation:m64-local-review",
        policy=_policy(),
        session_request=_session_request(),
    )
    decision = build_autonomy_policy_decision(request)
    if overrides:
        decision = decision.model_copy(update=overrides)
    return decision


def _step(step_ref: str = "autonomy-simulation-step:inspect-plan", **overrides):
    data = {
        "step_ref": step_ref,
        "intent_ref": "intent:inspect-redacted-review-packet",
        "capability_ref": "capability:observe-only-review",
        "resource_ref": "resource:local-prototype",
        "simulated_outcome_ref": "simulation-outcome:redacted-review-only",
        "risk_class": AutonomyRiskClass.low,
        "depends_on_step_refs": [],
    }
    data.update(overrides)
    return AutonomousPlanSimulationStep(**data)


def _simulation_request(**overrides):
    data = {
        "simulation_request_ref": "autonomy-plan-simulation-request:m64-local-review",
        "policy_decision": _policy_decision(),
        "steps": [_step()],
        "actor_ref": "actor:local-reviewer",
        "resource_refs": ["resource:local-prototype"],
        "capability_refs": ["capability:observe-only-review"],
        "allowlist_refs": ["allowlist:m64-local-review"],
        "audit_ref": "audit:m64-local-review",
        "replay_ref": "replay:m64-local-review",
    }
    data.update(overrides)
    return AutonomousPlanSimulationRequest(**data)


def test_autonomous_plan_simulation_is_deterministic_review_only() -> None:
    result = build_autonomous_plan_simulation_result(_simulation_request())

    assert result.contract_valid_for_review is True
    assert result.review_only is True
    assert result.dry_run_only is True
    assert result.deterministic is True
    assert result.simulation_performed is True
    assert result.authority_granted is False
    assert result.session_started is False
    assert result.execution_performed is False
    assert result.side_effects_performed == []
    assert result.simulated_step_refs == ["autonomy-simulation-step:inspect-plan"]
    assert result.reason_codes == ["M64_AUTONOMOUS_PLAN_SIMULATION_REVIEW_ONLY"]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("execution_requested", "EXECUTION_DENIED"),
        ("execution_performed", "EXECUTION_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
        ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
        ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
        ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
        ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
        ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_autonomous_plan_simulation_denies_runtime_flags(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_autonomous_plan_simulation_request(_simulation_request(**{field: True}))


def test_autonomous_plan_simulation_step_denies_runtime_flags() -> None:
    with pytest.raises(ValueError, match="TOOL_EXECUTION_DENIED"):
        validate_autonomous_plan_simulation_step(_step(tool_execution_enabled=True))

    with pytest.raises(ValueError, match="CONTEXT_INJECTION_DENIED"):
        validate_autonomous_plan_simulation_step(_step(context_injection_enabled=True))


def test_autonomous_plan_simulation_revalidates_mutated_policy_decisions() -> None:
    for update, reason in [
        ({"authority_granted": True}, "AUTONOMY_POLICY_AUTHORITY_DENIED"),
        ({"session_started": True}, "AUTONOMY_SESSION_START_DENIED"),
        ({"execution_performed": True}, "EXECUTION_DENIED"),
        ({"side_effects_performed": ["tool:unsafe"]}, "AUTONOMY_SIDE_EFFECTS_DENIED"),
        ({"policy_allows_review": False}, "POLICY_REVIEW_ALLOWANCE_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_autonomous_plan_simulation_request(
                _simulation_request(policy_decision=_policy_decision(**update))
            )


def test_autonomous_plan_simulation_dependencies_are_stable_and_acyclic() -> None:
    first = _step("autonomy-simulation-step:first")
    second = _step(
        "autonomy-simulation-step:second",
        depends_on_step_refs=["autonomy-simulation-step:first"],
    )
    result = build_autonomous_plan_simulation_result(_simulation_request(steps=[second, first]))

    assert result.simulated_step_refs == [
        "autonomy-simulation-step:first",
        "autonomy-simulation-step:second",
    ]

    with pytest.raises(ValueError, match="SIMULATION_STEP_DUPLICATE_REF_DENIED"):
        validate_autonomous_plan_simulation_request(_simulation_request(steps=[first, first]))

    with pytest.raises(ValueError, match="SIMULATION_STEP_MISSING_DEPENDENCY_DENIED"):
        validate_autonomous_plan_simulation_request(
            _simulation_request(
                steps=[_step(depends_on_step_refs=["autonomy-simulation-step:missing"])]
            )
        )

    with pytest.raises(ValueError, match="SIMULATION_STEP_SELF_DEPENDENCY_DENIED"):
        validate_autonomous_plan_simulation_request(
            _simulation_request(
                steps=[
                    _step(
                        "autonomy-simulation-step:self",
                        depends_on_step_refs=["autonomy-simulation-step:self"],
                    )
                ]
            )
        )

    with pytest.raises(ValueError, match="SIMULATION_STEP_CYCLE_DENIED"):
        validate_autonomous_plan_simulation_request(
            _simulation_request(
                steps=[
                    _step(
                        "autonomy-simulation-step:a",
                        depends_on_step_refs=["autonomy-simulation-step:b"],
                    ),
                    _step(
                        "autonomy-simulation-step:b",
                        depends_on_step_refs=["autonomy-simulation-step:a"],
                    ),
                ]
            )
        )


def test_autonomous_plan_simulation_denies_approval_tests_and_secret_like_metadata() -> None:
    with pytest.raises(ValueError, match="APPROVAL_TEST_REF_DENIED"):
        validate_autonomous_plan_simulation_request(
            _simulation_request(approval_test_ref="approval_test_:m64")
        )

    result = build_autonomous_plan_simulation_result(
        _simulation_request(approval_ref="approval:m64-identifier-only")
    )

    assert result.authority_granted is False
    assert "APPROVAL_REF_IDENTIFIER_ONLY" in result.reason_codes

    with pytest.raises(ValueError, match="SECRET_LIKE_AUTONOMOUS_PLAN_SIMULATION_CONTENT_DENIED"):
        validate_autonomous_plan_simulation_request(
            _simulation_request(metadata={"api_key": "abcde12345678901234"})
        )


def test_autonomous_plan_simulation_revalidates_model_copy_mutated_steps() -> None:
    request = _simulation_request()
    mutated_step = request.steps[0].model_copy(
        update={
            "execution_performed": True,
            "metadata": {"token": "abcde12345678901234"},
        }
    )
    mutated_request = request.model_copy(update={"steps": [mutated_step]})

    with pytest.raises(ValueError, match="SECRET_LIKE_AUTONOMOUS_PLAN_SIMULATION_CONTENT_DENIED"):
        validate_autonomous_plan_simulation_request(mutated_request)


def test_autonomous_plan_simulation_result_model_denies_direct_authority_mutation() -> None:
    result = build_autonomous_plan_simulation_result(_simulation_request())
    with pytest.raises(ValueError, match="EXECUTION_DENIED"):
        type(result).model_validate(result.model_dump() | {"execution_performed": True})

    with pytest.raises(ValueError, match="AUTONOMY_POLICY_AUTHORITY_DENIED"):
        AutonomyPolicyDecision.model_validate(result.policy_decision.model_dump() | {"authority_granted": True})
