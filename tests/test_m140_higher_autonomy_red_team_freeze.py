import pytest

from ultimate_ai_agent.core.autonomy import (
    REQUIRED_M140_ACCEPTED_CHECKPOINT_REFS,
    HigherAutonomyRedTeamFreezePolicy,
    HigherAutonomyRedTeamFreezeRequest,
    HigherAutonomyRedTeamFreezeStatus,
    build_higher_autonomy_red_team_freeze_report,
    validate_higher_autonomy_red_team_freeze_policy,
    validate_higher_autonomy_red_team_freeze_report,
    validate_higher_autonomy_red_team_freeze_request,
)


def _request(**overrides) -> HigherAutonomyRedTeamFreezeRequest:
    data = {
        "request_ref": "higher-autonomy-red-team-freeze-request:m140",
        "freeze_ref": "higher-autonomy-red-team-freeze:m140",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M140_ACCEPTED_CHECKPOINT_REFS),
        "red_team_checklist_refs": [
            "m140-freeze:m131-m139-covered",
            "m140-freeze:higher-autonomy-boundary-reviewed",
            "m140-freeze:red-team-runtime-absent",
            "m140-freeze:route-stable",
            "m140-freeze:dependency-stable",
            "m140-freeze:production-authority-blocked",
            "m140-freeze:m141-future",
        ],
        "audit_ref": "audit:m140:higher-autonomy-red-team-freeze",
        "replay_ref": "replay:m140:higher-autonomy-red-team-freeze",
        "revocation_ref": "revocation:m140:higher-autonomy-red-team-freeze",
        "kill_switch_ref": "kill-switch:m140:higher-autonomy-red-team-freeze",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m140:higher-autonomy-red-team-freeze:no-effect"
        ),
        "safe_summary": (
            "Freeze accepted M131-M139 higher-autonomy refs without adding runtime."
        ),
    }
    data.update(overrides)
    return HigherAutonomyRedTeamFreezeRequest(**data)


def test_m140_report_is_freeze_only_and_non_authoritative() -> None:
    report = build_higher_autonomy_red_team_freeze_report(_request())

    assert report.status == HigherAutonomyRedTeamFreezeStatus.frozen_for_review
    assert report.contract_only is True
    assert report.review_only is True
    assert report.freeze_only is True
    assert report.deterministic is True
    assert report.local_only is True
    assert report.safe_refs_only is True
    assert report.m131_m139_covered is True
    assert report.red_team_review_bound is True
    assert report.audit_replay_bound is True
    assert report.revocation_readiness_bound is True
    assert report.no_effect_receipt_required is True
    assert report.no_broad_unsandboxed_autonomy is True
    assert report.no_production_authority is True
    assert report.accepted_checkpoint_refs == list(REQUIRED_M140_ACCEPTED_CHECKPOINT_REFS)
    assert report.red_team_runtime_started is False
    assert report.red_team_harness_execution_performed is False
    assert report.adversarial_test_execution_performed is False
    assert report.autonomous_execution_performed is False
    assert report.broad_autonomy_granted is False
    assert report.global_autonomy_switch_enabled is False
    assert report.execution_performed is False
    assert report.tool_execution_performed is False
    assert report.shell_execution_performed is False
    assert report.browser_action_performed is False
    assert report.connector_action_performed is False
    assert report.network_access_performed is False
    assert report.plugin_execution_performed is False
    assert report.background_worker_started is False
    assert report.scheduler_started is False
    assert report.mobile_sensor_performed is False
    assert report.remote_execution_performed is False
    assert report.model_call_performed is False
    assert report.memory_write_performed is False
    assert report.context_injection_performed is False
    assert report.backend_route_added is False
    assert report.control_center_control_added is False
    assert report.dependency_added is False
    assert report.alpha_release_enabled is False
    assert report.beta_release_enabled is False
    assert report.production_authority_granted is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M140_HIGHER_AUTONOMY_RED_TEAM_FREEZE_REVIEW_ONLY",
        "M140_M131_M139_COVERED",
        "M140_NO_RED_TEAM_RUNTIME",
        "M140_NO_BROAD_UNSANDBOXED_AUTONOMY",
        "M140_NO_PRODUCTION_AUTHORITY",
        "M141_REMAINS_FUTURE",
    ]


def test_m140_report_uses_safe_refs_only() -> None:
    report = build_higher_autonomy_red_team_freeze_report(_request())

    assert report.report_ref == "higher-autonomy-red-team-freeze-report:m140"
    assert report.freeze_ref == "higher-autonomy-red-team-freeze:m140"
    assert report.audit_ref.startswith("audit:")
    assert report.replay_ref.startswith("replay:")
    assert report.revocation_ref.startswith("revocation:")
    assert report.kill_switch_ref.startswith("kill-switch:")
    assert report.no_effect_receipt_plan_ref.startswith("receipt-plan:")
    assert "secret" not in report.safe_summary.lower()
    assert "token" not in report.safe_summary.lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("red_team_runtime_enabled", "M140_RED_TEAM_RUNTIME_DENIED"),
        (
            "red_team_harness_execution_enabled",
            "M140_RED_TEAM_HARNESS_EXECUTION_DENIED",
        ),
        (
            "adversarial_test_execution_enabled",
            "M140_ADVERSARIAL_TEST_EXECUTION_DENIED",
        ),
        ("autonomous_execution_enabled", "M140_AUTONOMOUS_EXECUTION_DENIED"),
        ("broad_autonomy_enabled", "M140_BROAD_AUTONOMY_DENIED"),
        ("global_autonomy_switch_enabled", "M140_GLOBAL_AUTONOMY_SWITCH_DENIED"),
        ("execution_enabled", "M140_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M140_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M140_SHELL_EXECUTION_DENIED"),
        ("browser_action_enabled", "M140_BROWSER_ACTION_DENIED"),
        ("connector_action_enabled", "M140_CONNECTOR_ACTION_DENIED"),
        ("network_access_enabled", "M140_NETWORK_ACCESS_DENIED"),
        ("plugin_execution_enabled", "M140_PLUGIN_EXECUTION_DENIED"),
        ("background_worker_enabled", "M140_BACKGROUND_WORKER_DENIED"),
        ("scheduler_enabled", "M140_SCHEDULER_DENIED"),
        ("mobile_sensor_enabled", "M140_MOBILE_SENSOR_DENIED"),
        ("remote_execution_enabled", "M140_REMOTE_EXECUTION_DENIED"),
        ("model_call_enabled", "M140_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M140_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M140_CONTEXT_INJECTION_DENIED"),
        (
            "raw_prompt_payload_exposure_enabled",
            "M140_RAW_PROMPT_PAYLOAD_DENIED",
        ),
        (
            "credential_cookie_access_enabled",
            "M140_CREDENTIAL_COOKIE_ACCESS_DENIED",
        ),
        ("backend_route_enabled", "M140_BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "M140_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M140_DEPENDENCY_DENIED"),
        ("alpha_release_enabled", "M140_ALPHA_RELEASE_DENIED"),
        ("beta_release_enabled", "M140_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M140_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m140_policy_denies_authority_expansion(field, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_higher_autonomy_red_team_freeze_policy(
            HigherAutonomyRedTeamFreezePolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("red_team_runtime_requested", "M140_RED_TEAM_RUNTIME_DENIED"),
        (
            "red_team_harness_execution_requested",
            "M140_RED_TEAM_HARNESS_EXECUTION_DENIED",
        ),
        (
            "adversarial_test_execution_requested",
            "M140_ADVERSARIAL_TEST_EXECUTION_DENIED",
        ),
        ("autonomous_execution_requested", "M140_AUTONOMOUS_EXECUTION_DENIED"),
        ("broad_autonomy_requested", "M140_BROAD_AUTONOMY_DENIED"),
        ("global_autonomy_switch_requested", "M140_GLOBAL_AUTONOMY_SWITCH_DENIED"),
        ("execution_requested", "M140_EXECUTION_DENIED"),
        ("tool_execution_requested", "M140_TOOL_EXECUTION_DENIED"),
        ("shell_execution_requested", "M140_SHELL_EXECUTION_DENIED"),
        ("browser_action_requested", "M140_BROWSER_ACTION_DENIED"),
        ("connector_action_requested", "M140_CONNECTOR_ACTION_DENIED"),
        ("network_access_requested", "M140_NETWORK_ACCESS_DENIED"),
        ("plugin_execution_requested", "M140_PLUGIN_EXECUTION_DENIED"),
        ("model_call_requested", "M140_MODEL_CALL_DENIED"),
        ("memory_write_requested", "M140_MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "M140_CONTEXT_INJECTION_DENIED"),
        ("backend_route_requested", "M140_BACKEND_ROUTE_DENIED"),
        ("dependency_requested", "M140_DEPENDENCY_DENIED"),
        ("alpha_release_requested", "M140_ALPHA_RELEASE_DENIED"),
        ("beta_release_requested", "M140_BETA_RELEASE_DENIED"),
        ("production_authority_requested", "M140_PRODUCTION_AUTHORITY_DENIED"),
        ("contains_raw_prompt", "M140_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M140_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M140_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M140_SECRET_DENIED"),
    ],
)
def test_m140_request_denies_unsafe_inputs(field, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_higher_autonomy_red_team_freeze_request(
            _request().model_copy(update={field: True})
        )


def test_m140_requires_exact_accepted_checkpoints_and_unique_checklists() -> None:
    with pytest.raises(ValueError, match="M140_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_higher_autonomy_red_team_freeze_request(
            _request(accepted_checkpoint_refs=[])
        )

    with pytest.raises(ValueError, match="M140_CHECKPOINT_REF_REQUIRED"):
        validate_higher_autonomy_red_team_freeze_request(
            _request(accepted_checkpoint_refs=["checkpoint:m131"])
        )

    with pytest.raises(ValueError, match="M140_CHECKPOINT_REF_UNEXPECTED"):
        validate_higher_autonomy_red_team_freeze_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M140_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m140",
                ]
            )
        )

    with pytest.raises(ValueError, match="M140_CHECKPOINT_REF_DUPLICATE"):
        validate_higher_autonomy_red_team_freeze_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M140_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m139",
                ]
            )
        )

    with pytest.raises(ValueError, match="M140_REF_DUPLICATE"):
        validate_higher_autonomy_red_team_freeze_request(
            _request(
                red_team_checklist_refs=[
                    "m140-freeze:route-stable",
                    "m140-freeze:route-stable",
                ]
            )
        )


def test_m140_revalidates_model_copy_mutations() -> None:
    report = build_higher_autonomy_red_team_freeze_report(_request())

    for update, reason in [
        ({"review_only": False}, "M140_REVIEW_ONLY_REQUIRED"),
        ({"freeze_only": False}, "M140_FREEZE_ONLY_REQUIRED"),
        ({"safe_refs_only": False}, "M140_SAFE_REFS_ONLY_REQUIRED"),
        ({"m131_m139_covered": False}, "M140_M131_M139_COVERAGE_REQUIRED"),
        ({"red_team_review_bound": False}, "M140_RED_TEAM_REVIEW_REQUIRED"),
        ({"red_team_runtime_started": True}, "M140_RED_TEAM_RUNTIME_DENIED"),
        (
            {"red_team_harness_execution_performed": True},
            "M140_RED_TEAM_HARNESS_EXECUTION_DENIED",
        ),
        (
            {"adversarial_test_execution_performed": True},
            "M140_ADVERSARIAL_TEST_EXECUTION_DENIED",
        ),
        (
            {"autonomous_execution_performed": True},
            "M140_AUTONOMOUS_EXECUTION_DENIED",
        ),
        ({"tool_execution_performed": True}, "M140_TOOL_EXECUTION_DENIED"),
        ({"browser_action_performed": True}, "M140_BROWSER_ACTION_DENIED"),
        ({"connector_action_performed": True}, "M140_CONNECTOR_ACTION_DENIED"),
        ({"backend_route_added": True}, "M140_BACKEND_ROUTE_DENIED"),
        ({"alpha_release_enabled": True}, "M140_ALPHA_RELEASE_DENIED"),
        ({"beta_release_enabled": True}, "M140_BETA_RELEASE_DENIED"),
        (
            {"production_authority_granted": True},
            "M140_PRODUCTION_AUTHORITY_DENIED",
        ),
        ({"side_effects_performed": ["ran red-team harness"]}, "M140_SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_higher_autonomy_red_team_freeze_report(
                report.model_copy(update=update)
            )


def test_m140_denies_secret_like_metadata_and_requires_reason_code() -> None:
    with pytest.raises(ValueError, match="M140_SECRET_LIKE_RED_TEAM_FREEZE_CONTENT_DENIED"):
        build_higher_autonomy_red_team_freeze_report(
            _request(metadata={"api_token": "abcde12345678901234567890"})
        )

    report = build_higher_autonomy_red_team_freeze_report(_request())
    with pytest.raises(ValueError, match="M140_REASON_CODE_REQUIRED"):
        validate_higher_autonomy_red_team_freeze_report(
            report.model_copy(update={"reason_codes": ["M141_REMAINS_FUTURE"]})
        )
