import pytest

from ultimate_ai_agent.core.productization import (
    REQUIRED_M142_ACCEPTED_CHECKPOINT_REFS,
    AlphaPrivacyReviewPolicy,
    AlphaPrivacyReviewRequest,
    AlphaPrivacyReviewStatus,
    build_alpha_privacy_review_record,
    validate_alpha_privacy_review_policy,
    validate_alpha_privacy_review_record,
    validate_alpha_privacy_review_request,
)


def _request(**overrides) -> AlphaPrivacyReviewRequest:
    data = {
        "request_ref": "alpha-privacy-review-request:m142",
        "privacy_review_ref": "alpha-privacy-review:m142",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M142_ACCEPTED_CHECKPOINT_REFS),
        "privacy_review_refs": [
            "privacy-review:m142:safe-summary-only",
            "privacy-review:m142:no-raw-private-content",
        ],
        "data_boundary_refs": [
            "data-boundary:m142:safe-refs-only",
            "data-boundary:m142:no-cross-workspace-raw-content",
        ],
        "disclosure_review_refs": [
            "disclosure-review:m142:no-raw-prompt",
            "disclosure-review:m142:no-provider-payload",
        ],
        "consent_review_refs": [
            "consent-review:m142:consent-copy-review",
            "consent-review:m142:revocation-copy-review",
        ],
        "retention_review_refs": [
            "retention-review:m142:no-production-retention",
            "retention-review:m142:no-audit-export",
        ],
        "audit_ref": "audit:m142:alpha-privacy-review",
        "replay_ref": "replay:m142:alpha-privacy-review",
        "revocation_ref": "revocation:m142:alpha-privacy-review",
        "kill_switch_ref": "kill-switch:m142:alpha-privacy-review",
        "no_effect_receipt_plan_ref": "receipt-plan:m142:alpha-privacy-review:no-effect",
        "safe_summary": "Record alpha privacy review refs without raw private content.",
    }
    data.update(overrides)
    return AlphaPrivacyReviewRequest(**data)


def test_m142_record_is_contract_only_and_non_authoritative() -> None:
    record = build_alpha_privacy_review_record(_request())

    assert record.status == AlphaPrivacyReviewStatus.privacy_review_recorded
    assert record.contract_only is True
    assert record.review_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.alpha_privacy_review_only is True
    assert record.m101_m141_covered is True
    assert record.privacy_review_bound is True
    assert record.data_boundary_bound is True
    assert record.disclosure_review_bound is True
    assert record.consent_review_bound is True
    assert record.retention_review_bound is True
    assert record.audit_replay_bound is True
    assert record.revocation_readiness_bound is True
    assert record.no_effect_receipt_required is True
    assert record.no_privacy_review_execution is True
    assert record.no_alpha_signoff is True
    assert record.no_alpha_ui_runtime is True
    assert record.no_production_authority is True
    assert record.accepted_checkpoint_refs == list(
        REQUIRED_M142_ACCEPTED_CHECKPOINT_REFS
    )
    assert record.privacy_review_execution_performed is False
    assert record.alpha_privacy_signoff_enabled is False
    assert record.alpha_ui_runtime_started is False
    assert record.alpha_release_enabled is False
    assert record.beta_release_enabled is False
    assert record.production_authority_granted is False
    assert record.multi_user_runtime_started is False
    assert record.account_tenancy_enabled is False
    assert record.workspace_sharing_enabled is False
    assert record.identity_federation_enabled is False
    assert record.auth_runtime_started is False
    assert record.login_enabled is False
    assert record.session_cookie_enabled is False
    assert record.credential_handling_performed is False
    assert record.raw_private_content_accessed is False
    assert record.raw_prompt_payload_exposed is False
    assert record.execution_performed is False
    assert record.tool_execution_performed is False
    assert record.shell_execution_performed is False
    assert record.browser_action_performed is False
    assert record.connector_action_performed is False
    assert record.network_access_performed is False
    assert record.plugin_execution_performed is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M142_ALPHA_PRIVACY_REVIEW_REVIEW_ONLY",
        "M142_M101_M141_COVERED",
        "M142_NO_PRIVACY_REVIEW_EXECUTION",
        "M142_NO_ALPHA_PRIVACY_SIGNOFF",
        "M142_NO_ALPHA_UI_RUNTIME",
        "M142_NO_RAW_PRIVATE_CONTENT",
        "M142_NO_PRODUCTION_AUTHORITY",
        "M143_REMAINS_FUTURE",
    ]


def test_m142_record_uses_safe_refs_only() -> None:
    record = build_alpha_privacy_review_record(_request())

    assert record.record_ref == "alpha-privacy-review-record:m142"
    assert record.privacy_review_ref == "alpha-privacy-review:m142"
    assert all(ref.startswith("privacy-review:") for ref in record.privacy_review_refs)
    assert all(ref.startswith("data-boundary:") for ref in record.data_boundary_refs)
    assert all(
        ref.startswith("disclosure-review:") for ref in record.disclosure_review_refs
    )
    assert all(ref.startswith("consent-review:") for ref in record.consent_review_refs)
    assert all(
        ref.startswith("retention-review:") for ref in record.retention_review_refs
    )
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
        ("privacy_review_execution_enabled", "M142_PRIVACY_REVIEW_EXECUTION_DENIED"),
        ("alpha_privacy_signoff_enabled", "M142_ALPHA_PRIVACY_SIGNOFF_DENIED"),
        ("alpha_ui_runtime_enabled", "M142_ALPHA_UI_RUNTIME_DENIED"),
        ("alpha_release_enabled", "M142_ALPHA_RELEASE_DENIED"),
        ("beta_release_enabled", "M142_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M142_PRODUCTION_AUTHORITY_DENIED"),
        ("multi_user_runtime_enabled", "M142_MULTI_USER_RUNTIME_DENIED"),
        ("account_tenancy_enabled", "M142_ACCOUNT_TENANCY_DENIED"),
        ("workspace_sharing_enabled", "M142_WORKSPACE_SHARING_DENIED"),
        ("identity_federation_enabled", "M142_IDENTITY_FEDERATION_DENIED"),
        ("auth_runtime_enabled", "M142_AUTH_RUNTIME_DENIED"),
        ("login_enabled", "M142_LOGIN_DENIED"),
        ("session_cookie_enabled", "M142_SESSION_COOKIE_DENIED"),
        ("credential_handling_enabled", "M142_CREDENTIAL_HANDLING_DENIED"),
        ("raw_private_content_access_enabled", "M142_RAW_PRIVATE_CONTENT_DENIED"),
        ("raw_prompt_payload_exposure_enabled", "M142_RAW_PROMPT_PAYLOAD_DENIED"),
        ("execution_enabled", "M142_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M142_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M142_SHELL_EXECUTION_DENIED"),
        ("browser_action_enabled", "M142_BROWSER_ACTION_DENIED"),
        ("connector_action_enabled", "M142_CONNECTOR_ACTION_DENIED"),
        ("network_access_enabled", "M142_NETWORK_ACCESS_DENIED"),
        ("plugin_execution_enabled", "M142_PLUGIN_EXECUTION_DENIED"),
        ("backend_route_enabled", "M142_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M142_DEPENDENCY_DENIED"),
    ],
)
def test_m142_policy_denies_authority_expansion(field, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_alpha_privacy_review_policy(AlphaPrivacyReviewPolicy(**{field: True}))


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        (
            "privacy_review_execution_requested",
            "M142_PRIVACY_REVIEW_EXECUTION_DENIED",
        ),
        ("alpha_privacy_signoff_requested", "M142_ALPHA_PRIVACY_SIGNOFF_DENIED"),
        ("alpha_ui_runtime_requested", "M142_ALPHA_UI_RUNTIME_DENIED"),
        ("alpha_release_requested", "M142_ALPHA_RELEASE_DENIED"),
        ("beta_release_requested", "M142_BETA_RELEASE_DENIED"),
        ("production_authority_requested", "M142_PRODUCTION_AUTHORITY_DENIED"),
        ("multi_user_runtime_requested", "M142_MULTI_USER_RUNTIME_DENIED"),
        ("auth_runtime_requested", "M142_AUTH_RUNTIME_DENIED"),
        ("raw_private_content_access_requested", "M142_RAW_PRIVATE_CONTENT_DENIED"),
        ("contains_raw_private_content", "M142_RAW_PRIVATE_CONTENT_DENIED"),
        ("contains_raw_prompt", "M142_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M142_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M142_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M142_SECRET_DENIED"),
        ("backend_route_requested", "M142_BACKEND_ROUTE_DENIED"),
        ("dependency_requested", "M142_DEPENDENCY_DENIED"),
    ],
)
def test_m142_request_denies_unsafe_inputs(field, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_alpha_privacy_review_request(_request().model_copy(update={field: True}))


def test_m142_requires_exact_checkpoint_and_review_refs() -> None:
    with pytest.raises(ValueError, match="M142_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_alpha_privacy_review_request(_request(accepted_checkpoint_refs=[]))

    with pytest.raises(ValueError, match="M142_CHECKPOINT_REF_REQUIRED"):
        validate_alpha_privacy_review_request(
            _request(accepted_checkpoint_refs=["checkpoint:m101"])
        )

    with pytest.raises(ValueError, match="M142_CHECKPOINT_REF_UNEXPECTED"):
        validate_alpha_privacy_review_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M142_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m143",
                ]
            )
        )

    for field, reason in [
        ("privacy_review_refs", "M142_PRIVACY_REVIEW_REF_REQUIRED"),
        ("data_boundary_refs", "M142_DATA_BOUNDARY_REF_REQUIRED"),
        ("disclosure_review_refs", "M142_DISCLOSURE_REVIEW_REF_REQUIRED"),
        ("consent_review_refs", "M142_CONSENT_REVIEW_REF_REQUIRED"),
        ("retention_review_refs", "M142_RETENTION_REVIEW_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_alpha_privacy_review_request(_request(**{field: []}))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        (
            {"privacy_review_execution_performed": True},
            "M142_PRIVACY_REVIEW_EXECUTION_DENIED",
        ),
        ({"alpha_privacy_signoff_enabled": True}, "M142_ALPHA_PRIVACY_SIGNOFF_DENIED"),
        ({"alpha_ui_runtime_started": True}, "M142_ALPHA_UI_RUNTIME_DENIED"),
        ({"raw_private_content_accessed": True}, "M142_RAW_PRIVATE_CONTENT_DENIED"),
        ({"backend_route_added": True}, "M142_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M142_DEPENDENCY_DENIED"),
        ({"production_authority_granted": True}, "M142_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m142_record_denies_unsafe_mutations(update, reason) -> None:
    record = build_alpha_privacy_review_record(_request())

    with pytest.raises(ValueError, match=reason):
        validate_alpha_privacy_review_record(record.model_copy(update=update))


def test_m142_record_denies_side_effects_and_bad_status() -> None:
    record = build_alpha_privacy_review_record(_request())

    with pytest.raises(ValueError, match="M142_SIDE_EFFECTS_DENIED"):
        validate_alpha_privacy_review_record(
            record.model_copy(update={"side_effects_performed": ["alpha-ui-started"]})
        )
