from typing import Any
import pytest

from ultimate_ai_agent.core.productization import (
    REQUIRED_M143_ACCEPTED_CHECKPOINT_REFS,
    AlphaUiAppReadinessPolicy,
    AlphaUiAppReadinessRequest,
    AlphaUiAppReadinessStatus,
    build_alpha_ui_app_readiness_record,
    validate_alpha_ui_app_readiness_policy,
    validate_alpha_ui_app_readiness_record,
    validate_alpha_ui_app_readiness_request,
)


def _request(**overrides: Any) -> AlphaUiAppReadinessRequest:
    data = {
        "request_ref": "alpha-ui-app-readiness-request:m143",
        "readiness_review_ref": "alpha-ui-app-readiness:m143",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M143_ACCEPTED_CHECKPOINT_REFS),
        "ui_readiness_refs": [
            "ui-readiness:m143:alpha-shell-safe",
            "ui-readiness:m143:no-runtime-start",
        ],
        "app_readiness_refs": [
            "app-readiness:m143:checklist-only",
            "app-readiness:m143:no-build",
        ],
        "privacy_review_refs": [
            "privacy-review:m142:safe-summary-only",
            "privacy-review:m143:no-raw-private-content",
        ],
        "accessibility_review_refs": [
            "accessibility-review:m143:keyboard-copy",
            "accessibility-review:m143:contrast-review",
        ],
        "release_blocker_refs": [
            "release-blocker:m143:no-alpha-release",
            "release-blocker:m143:no-beta-release",
        ],
        "audit_ref": "audit:m143:alpha-ui-app-readiness",
        "replay_ref": "replay:m143:alpha-ui-app-readiness",
        "revocation_ref": "revocation:m143:alpha-ui-app-readiness",
        "kill_switch_ref": "kill-switch:m143:alpha-ui-app-readiness",
        "no_effect_receipt_plan_ref": "receipt-plan:m143:alpha-ui-app-readiness:no-effect",
        "safe_summary": "Record alpha UI and app readiness refs without starting runtime.",
    }
    data.update(overrides)
    return AlphaUiAppReadinessRequest(**data)


def test_m143_record_is_contract_only_and_non_authoritative() -> None:
    record = build_alpha_ui_app_readiness_record(_request())

    assert record.status == AlphaUiAppReadinessStatus.readiness_review_recorded
    assert record.contract_only is True
    assert record.review_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.alpha_ui_app_readiness_only is True
    assert record.m101_m142_covered is True
    assert record.ui_readiness_bound is True
    assert record.app_readiness_bound is True
    assert record.privacy_review_bound is True
    assert record.accessibility_review_bound is True
    assert record.release_blocker_bound is True
    assert record.audit_replay_bound is True
    assert record.revocation_readiness_bound is True
    assert record.no_effect_receipt_required is True
    assert record.no_alpha_ui_runtime is True
    assert record.no_app_readiness_execution is True
    assert record.no_app_build is True
    assert record.no_app_store_connect is True
    assert record.no_alpha_release is True
    assert record.no_production_authority is True
    assert record.accepted_checkpoint_refs == list(
        REQUIRED_M143_ACCEPTED_CHECKPOINT_REFS
    )
    assert record.alpha_ui_runtime_started is False
    assert record.app_readiness_execution_performed is False
    assert record.app_build_performed is False
    assert record.app_signing_performed is False
    assert record.app_store_connect_performed is False
    assert record.testflight_upload_performed is False
    assert record.alpha_release_enabled is False
    assert record.beta_release_enabled is False
    assert record.production_authority_granted is False
    assert record.privacy_review_execution_performed is False
    assert record.raw_private_content_accessed is False
    assert record.auth_runtime_started is False
    assert record.login_enabled is False
    assert record.execution_performed is False
    assert record.tool_execution_performed is False
    assert record.shell_execution_performed is False
    assert record.browser_action_performed is False
    assert record.connector_action_performed is False
    assert record.network_access_performed is False
    assert record.plugin_execution_performed is False
    assert record.model_call_performed is False
    assert record.memory_write_performed is False
    assert record.context_injection_performed is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M143_ALPHA_UI_APP_READINESS_REVIEW_ONLY",
        "M143_M101_M142_COVERED",
        "M143_NO_ALPHA_UI_RUNTIME",
        "M143_NO_APP_READINESS_EXECUTION",
        "M143_NO_APP_BUILD",
        "M143_NO_APP_STORE_CONNECT",
        "M143_NO_ALPHA_RELEASE",
        "M143_NO_PRODUCTION_AUTHORITY",
        "M144_REMAINS_FUTURE",
    ]


def test_m143_record_uses_safe_refs_only() -> None:
    record = build_alpha_ui_app_readiness_record(_request())

    assert record.record_ref == "alpha-ui-app-readiness-record:m143"
    assert record.readiness_review_ref == "alpha-ui-app-readiness:m143"
    assert all(ref.startswith("ui-readiness:") for ref in record.ui_readiness_refs)
    assert all(ref.startswith("app-readiness:") for ref in record.app_readiness_refs)
    assert all(ref.startswith("privacy-review:") for ref in record.privacy_review_refs)
    assert all(
        ref.startswith("accessibility-review:")
        for ref in record.accessibility_review_refs
    )
    assert all(ref.startswith("release-blocker:") for ref in record.release_blocker_refs)
    assert record.audit_ref.startswith("audit:")
    assert record.replay_ref.startswith("replay:")
    assert record.revocation_ref.startswith("revocation:")
    assert record.kill_switch_ref.startswith("kill-switch:")
    assert record.no_effect_receipt_plan_ref.startswith("receipt-plan:")
    assert "secret" not in record.safe_summary.lower()
    assert "token" not in record.safe_summary.lower()
    assert "password" not in record.safe_summary.lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("alpha_ui_runtime_enabled", "M143_ALPHA_UI_RUNTIME_DENIED"),
        ("app_readiness_execution_enabled", "M143_APP_READINESS_EXECUTION_DENIED"),
        ("app_build_enabled", "M143_APP_BUILD_DENIED"),
        ("app_signing_enabled", "M143_APP_SIGNING_DENIED"),
        ("app_store_connect_enabled", "M143_APP_STORE_CONNECT_DENIED"),
        ("testflight_upload_enabled", "M143_TESTFLIGHT_UPLOAD_DENIED"),
        ("alpha_release_enabled", "M143_ALPHA_RELEASE_DENIED"),
        ("beta_release_enabled", "M143_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M143_PRODUCTION_AUTHORITY_DENIED"),
        ("privacy_review_execution_enabled", "M143_PRIVACY_REVIEW_EXECUTION_DENIED"),
        ("raw_private_content_access_enabled", "M143_RAW_PRIVATE_CONTENT_DENIED"),
        ("auth_runtime_enabled", "M143_AUTH_RUNTIME_DENIED"),
        ("login_enabled", "M143_LOGIN_DENIED"),
        ("execution_enabled", "M143_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M143_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M143_SHELL_EXECUTION_DENIED"),
        ("browser_action_enabled", "M143_BROWSER_ACTION_DENIED"),
        ("connector_action_enabled", "M143_CONNECTOR_ACTION_DENIED"),
        ("network_access_enabled", "M143_NETWORK_ACCESS_DENIED"),
        ("plugin_execution_enabled", "M143_PLUGIN_EXECUTION_DENIED"),
        ("backend_route_enabled", "M143_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M143_DEPENDENCY_DENIED"),
    ],
)
def test_m143_policy_denies_authority_expansion(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_alpha_ui_app_readiness_policy(
            AlphaUiAppReadinessPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("alpha_ui_runtime_requested", "M143_ALPHA_UI_RUNTIME_DENIED"),
        ("app_readiness_execution_requested", "M143_APP_READINESS_EXECUTION_DENIED"),
        ("app_build_requested", "M143_APP_BUILD_DENIED"),
        ("app_signing_requested", "M143_APP_SIGNING_DENIED"),
        ("app_store_connect_requested", "M143_APP_STORE_CONNECT_DENIED"),
        ("testflight_upload_requested", "M143_TESTFLIGHT_UPLOAD_DENIED"),
        ("alpha_release_requested", "M143_ALPHA_RELEASE_DENIED"),
        ("beta_release_requested", "M143_BETA_RELEASE_DENIED"),
        ("production_authority_requested", "M143_PRODUCTION_AUTHORITY_DENIED"),
        ("raw_private_content_access_requested", "M143_RAW_PRIVATE_CONTENT_DENIED"),
        ("contains_raw_private_content", "M143_RAW_PRIVATE_CONTENT_DENIED"),
        ("contains_raw_prompt", "M143_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M143_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M143_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M143_SECRET_DENIED"),
        ("backend_route_requested", "M143_BACKEND_ROUTE_DENIED"),
        ("dependency_requested", "M143_DEPENDENCY_DENIED"),
    ],
)
def test_m143_request_denies_unsafe_inputs(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_alpha_ui_app_readiness_request(
            _request().model_copy(update={field: True})
        )


def test_m143_requires_exact_checkpoint_and_readiness_refs() -> None:
    with pytest.raises(ValueError, match="M143_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_alpha_ui_app_readiness_request(_request(accepted_checkpoint_refs=[]))

    with pytest.raises(ValueError, match="M143_CHECKPOINT_REF_REQUIRED"):
        validate_alpha_ui_app_readiness_request(
            _request(accepted_checkpoint_refs=["checkpoint:m101"])
        )

    with pytest.raises(ValueError, match="M143_CHECKPOINT_REF_UNEXPECTED"):
        validate_alpha_ui_app_readiness_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M143_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m144",
                ]
            )
        )

    for field, reason in [
        ("ui_readiness_refs", "M143_UI_READINESS_REF_REQUIRED"),
        ("app_readiness_refs", "M143_APP_READINESS_REF_REQUIRED"),
        ("privacy_review_refs", "M143_PRIVACY_REVIEW_REF_REQUIRED"),
        ("accessibility_review_refs", "M143_ACCESSIBILITY_REVIEW_REF_REQUIRED"),
        ("release_blocker_refs", "M143_RELEASE_BLOCKER_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_alpha_ui_app_readiness_request(_request(**{field: []}))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"alpha_ui_runtime_started": True}, "M143_ALPHA_UI_RUNTIME_DENIED"),
        (
            {"app_readiness_execution_performed": True},
            "M143_APP_READINESS_EXECUTION_DENIED",
        ),
        ({"app_build_performed": True}, "M143_APP_BUILD_DENIED"),
        ({"app_signing_performed": True}, "M143_APP_SIGNING_DENIED"),
        ({"app_store_connect_performed": True}, "M143_APP_STORE_CONNECT_DENIED"),
        ({"testflight_upload_performed": True}, "M143_TESTFLIGHT_UPLOAD_DENIED"),
        ({"alpha_release_enabled": True}, "M143_ALPHA_RELEASE_DENIED"),
        ({"raw_private_content_accessed": True}, "M143_RAW_PRIVATE_CONTENT_DENIED"),
        ({"backend_route_added": True}, "M143_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M143_DEPENDENCY_DENIED"),
        ({"production_authority_granted": True}, "M143_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m143_record_denies_unsafe_mutations(update: Any, reason: str) -> None:
    record = build_alpha_ui_app_readiness_record(_request())

    with pytest.raises(ValueError, match=reason):
        validate_alpha_ui_app_readiness_record(record.model_copy(update=update))


def test_m143_record_denies_side_effects_and_bad_status() -> None:
    record = build_alpha_ui_app_readiness_record(_request())

    with pytest.raises(ValueError, match="M143_SIDE_EFFECTS_DENIED"):
        validate_alpha_ui_app_readiness_record(
            record.model_copy(update={"side_effects_performed": ["alpha-ui-started"]})
        )


def test_m143_denies_secret_like_metadata_and_summary() -> None:
    with pytest.raises(ValueError, match="M143_SECRET_LIKE_APP_READINESS_CONTENT_DENIED"):
        validate_alpha_ui_app_readiness_policy(
            AlphaUiAppReadinessPolicy(metadata={"api_key": "x"})
        )
