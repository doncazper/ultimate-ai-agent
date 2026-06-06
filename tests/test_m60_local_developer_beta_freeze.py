import pytest

from ultimate_ai_agent.core.beta_freeze import (
    LocalDeveloperBetaFreezePolicy,
    LocalDeveloperBetaFreezeRequest,
    LocalDeveloperBetaFreezeStatus,
    build_local_developer_beta_freeze_report,
    validate_local_developer_beta_freeze_policy,
    validate_local_developer_beta_freeze_request,
)


def _request(**overrides):
    data = {
        "request_ref": "beta-freeze-request:m60",
        "freeze_ref": "beta-freeze:m60",
        "baseline_ref": "baseline:v0.64.0",
        "actor_ref": "actor:local-reviewer",
        "checklist_refs": [
            "beta-freeze:validation-green",
            "beta-freeze:docs-current",
            "beta-freeze:route-stable",
            "beta-freeze:dependency-stable",
            "beta-freeze:artifact-clean",
            "beta-freeze:authority-frozen",
        ],
        "release_candidate_refs": ["release:v0.64.0"],
        "safe_summary": "Freeze the local developer beta without adding authority.",
    }
    data.update(overrides)
    return LocalDeveloperBetaFreezeRequest(**data)


def test_local_developer_beta_freeze_report_is_review_only_and_no_effect() -> None:
    report = build_local_developer_beta_freeze_report(_request())

    assert report.status == LocalDeveloperBetaFreezeStatus.frozen
    assert report.freeze_only is True
    assert report.local_developer_beta_only is True
    assert report.production_authority_granted is False
    assert report.public_release_performed is False
    assert report.execution_performed is False
    assert report.post_m60_autonomy_enabled is False
    assert report.side_effects_performed == []
    assert report.reason_codes == ["M60_LOCAL_DEVELOPER_BETA_FREEZE_REVIEW_ONLY"]
    assert report.receipt_plan is not None
    assert report.receipt_plan.side_effects_performed == []
    assert "private key" not in str(report.model_dump()).lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("public_release_requested", "PUBLIC_RELEASE_DENIED"),
        ("external_distribution_requested", "EXTERNAL_DISTRIBUTION_DENIED"),
        ("post_m60_autonomy_requested", "POST_M60_AUTONOMY_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
        ("execution_requested", "EXECUTION_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("network_tool_requested", "NETWORK_TOOL_DENIED"),
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("mobile_sensor_requested", "MOBILE_SENSOR_DENIED"),
        ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
        ("credential_handling_requested", "CREDENTIAL_HANDLING_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("model_provider_call_requested", "MODEL_PROVIDER_CALL_DENIED"),
    ],
)
def test_local_developer_beta_freeze_denies_authority_request_flags(
    field: str, reason: str
) -> None:
    request = _request(**{field: True})

    with pytest.raises(ValueError, match=reason):
        validate_local_developer_beta_freeze_request(request)


def test_local_developer_beta_freeze_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "post_m60_autonomy_requested": True,
            "contains_secret": True,
        }
    )

    with pytest.raises(ValueError, match="POST_M60_AUTONOMY_DENIED"):
        build_local_developer_beta_freeze_report(request)


def test_local_developer_beta_freeze_requires_stable_checklist_refs() -> None:
    with pytest.raises(ValueError, match="BETA_FREEZE_CHECKLIST_REFS_REQUIRED"):
        validate_local_developer_beta_freeze_request(_request(checklist_refs=[]))

    with pytest.raises(ValueError, match="BETA_FREEZE_CHECKLIST_REF_DUPLICATE"):
        validate_local_developer_beta_freeze_request(
            _request(checklist_refs=["beta-freeze:docs-current", "beta-freeze:docs-current"])
        )


def test_local_developer_beta_freeze_denies_secret_like_metadata() -> None:
    request = _request(metadata={"token": "abcde12345678901234"})

    with pytest.raises(ValueError, match="SECRET_LIKE_BETA_FREEZE_CONTENT_DENIED"):
        build_local_developer_beta_freeze_report(request)


def test_local_developer_beta_freeze_policy_denies_post_m60_authority() -> None:
    policy = LocalDeveloperBetaFreezePolicy(
        public_release_enabled=True,
        post_m60_autonomy_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="PUBLIC_RELEASE_DENIED"):
        validate_local_developer_beta_freeze_policy(policy)
