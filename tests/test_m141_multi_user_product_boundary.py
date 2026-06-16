import pytest

from ultimate_ai_agent.core.productization import (
    REQUIRED_M141_ACCEPTED_CHECKPOINT_REFS,
    MultiUserProductBoundaryPolicy,
    MultiUserProductBoundaryRequest,
    MultiUserProductBoundaryStatus,
    build_multi_user_product_boundary_record,
    validate_multi_user_product_boundary_policy,
    validate_multi_user_product_boundary_record,
    validate_multi_user_product_boundary_request,
)


def _request(**overrides) -> MultiUserProductBoundaryRequest:
    data = {
        "request_ref": "multi-user-product-boundary-request:m141",
        "product_boundary_ref": "multi-user-product-boundary:m141",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M141_ACCEPTED_CHECKPOINT_REFS),
        "user_boundary_refs": [
            "user-boundary:m141:safe-user-refs-only",
            "user-boundary:m141:no-user-account-runtime",
        ],
        "workspace_boundary_refs": [
            "workspace-boundary:m141:safe-workspace-refs-only",
            "workspace-boundary:m141:no-workspace-sharing-runtime",
        ],
        "tenant_boundary_refs": [
            "tenant-boundary:m141:safe-tenant-refs-only",
            "tenant-boundary:m141:no-account-tenancy-runtime",
        ],
        "role_boundary_refs": [
            "role-boundary:m141:role-refs-not-authority",
            "role-boundary:m141:no-org-admin-runtime",
        ],
        "privacy_boundary_refs": [
            "privacy-boundary:m141:no-cross-workspace-content",
            "privacy-boundary:m141:no-identity-federation",
        ],
        "audit_ref": "audit:m141:multi-user-product-boundary",
        "replay_ref": "replay:m141:multi-user-product-boundary",
        "revocation_ref": "revocation:m141:multi-user-product-boundary",
        "kill_switch_ref": "kill-switch:m141:multi-user-product-boundary",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m141:multi-user-product-boundary:no-effect"
        ),
        "safe_summary": (
            "Define multi-user product boundary refs without account tenancy runtime."
        ),
    }
    data.update(overrides)
    return MultiUserProductBoundaryRequest(**data)


def test_m141_record_is_contract_only_and_non_authoritative() -> None:
    record = build_multi_user_product_boundary_record(_request())

    assert record.status == MultiUserProductBoundaryStatus.product_boundary_review
    assert record.contract_only is True
    assert record.review_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.product_boundary_only is True
    assert record.m101_m140_covered is True
    assert record.actor_boundary_bound is True
    assert record.workspace_boundary_bound is True
    assert record.tenant_boundary_bound is True
    assert record.role_boundary_bound is True
    assert record.privacy_boundary_bound is True
    assert record.audit_replay_bound is True
    assert record.revocation_readiness_bound is True
    assert record.no_effect_receipt_required is True
    assert record.no_multi_user_runtime is True
    assert record.no_account_tenancy is True
    assert record.no_auth_runtime is True
    assert record.no_workspace_sharing is True
    assert record.no_production_authority is True
    assert record.accepted_checkpoint_refs == list(
        REQUIRED_M141_ACCEPTED_CHECKPOINT_REFS
    )
    assert record.multi_user_runtime_started is False
    assert record.account_tenancy_enabled is False
    assert record.tenant_runtime_started is False
    assert record.workspace_sharing_enabled is False
    assert record.identity_federation_enabled is False
    assert record.auth_runtime_started is False
    assert record.login_enabled is False
    assert record.session_cookie_enabled is False
    assert record.credential_handling_performed is False
    assert record.persistent_identity_store_enabled is False
    assert record.account_connector_enabled is False
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
    assert record.alpha_privacy_review_enabled is False
    assert record.alpha_release_enabled is False
    assert record.beta_release_enabled is False
    assert record.production_authority_granted is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M141_MULTI_USER_PRODUCT_BOUNDARY_REVIEW_ONLY",
        "M141_M101_M140_COVERED",
        "M141_NO_MULTI_USER_RUNTIME",
        "M141_NO_ACCOUNT_TENANCY",
        "M141_NO_AUTH_OR_IDENTITY_FEDERATION",
        "M141_NO_WORKSPACE_SHARING",
        "M141_NO_PRODUCTION_AUTHORITY",
        "M142_REMAINS_FUTURE",
    ]


def test_m141_record_uses_safe_refs_only() -> None:
    record = build_multi_user_product_boundary_record(_request())

    assert record.record_ref == "multi-user-product-boundary-record:m141"
    assert record.product_boundary_ref == "multi-user-product-boundary:m141"
    assert all(ref.startswith("user-boundary:") for ref in record.user_boundary_refs)
    assert all(
        ref.startswith("workspace-boundary:") for ref in record.workspace_boundary_refs
    )
    assert all(ref.startswith("tenant-boundary:") for ref in record.tenant_boundary_refs)
    assert all(ref.startswith("role-boundary:") for ref in record.role_boundary_refs)
    assert all(ref.startswith("privacy-boundary:") for ref in record.privacy_boundary_refs)
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
        ("multi_user_runtime_enabled", "M141_MULTI_USER_RUNTIME_DENIED"),
        ("account_tenancy_enabled", "M141_ACCOUNT_TENANCY_DENIED"),
        ("tenant_runtime_enabled", "M141_TENANT_RUNTIME_DENIED"),
        ("workspace_sharing_enabled", "M141_WORKSPACE_SHARING_DENIED"),
        ("identity_federation_enabled", "M141_IDENTITY_FEDERATION_DENIED"),
        ("org_admin_runtime_enabled", "M141_ORG_ADMIN_RUNTIME_DENIED"),
        ("cross_workspace_access_enabled", "M141_CROSS_WORKSPACE_ACCESS_DENIED"),
        ("auth_runtime_enabled", "M141_AUTH_RUNTIME_DENIED"),
        ("login_enabled", "M141_LOGIN_DENIED"),
        ("session_cookie_enabled", "M141_SESSION_COOKIE_DENIED"),
        ("credential_handling_enabled", "M141_CREDENTIAL_HANDLING_DENIED"),
        (
            "persistent_identity_store_enabled",
            "M141_PERSISTENT_IDENTITY_STORE_DENIED",
        ),
        ("account_connector_enabled", "M141_ACCOUNT_CONNECTOR_DENIED"),
        ("production_runtime_enabled", "M141_PRODUCTION_RUNTIME_DENIED"),
        ("execution_enabled", "M141_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M141_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M141_SHELL_EXECUTION_DENIED"),
        ("browser_action_enabled", "M141_BROWSER_ACTION_DENIED"),
        ("connector_action_enabled", "M141_CONNECTOR_ACTION_DENIED"),
        ("network_access_enabled", "M141_NETWORK_ACCESS_DENIED"),
        ("plugin_execution_enabled", "M141_PLUGIN_EXECUTION_DENIED"),
        ("model_call_enabled", "M141_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M141_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M141_CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "M141_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M141_DEPENDENCY_DENIED"),
        ("alpha_privacy_review_enabled", "M141_ALPHA_PRIVACY_REVIEW_DENIED"),
        ("alpha_release_enabled", "M141_ALPHA_RELEASE_DENIED"),
        ("beta_release_enabled", "M141_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M141_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m141_policy_denies_authority_expansion(field, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_multi_user_product_boundary_policy(
            MultiUserProductBoundaryPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("multi_user_runtime_requested", "M141_MULTI_USER_RUNTIME_DENIED"),
        ("account_tenancy_requested", "M141_ACCOUNT_TENANCY_DENIED"),
        ("tenant_runtime_requested", "M141_TENANT_RUNTIME_DENIED"),
        ("workspace_sharing_requested", "M141_WORKSPACE_SHARING_DENIED"),
        ("identity_federation_requested", "M141_IDENTITY_FEDERATION_DENIED"),
        ("auth_runtime_requested", "M141_AUTH_RUNTIME_DENIED"),
        ("login_requested", "M141_LOGIN_DENIED"),
        ("session_cookie_requested", "M141_SESSION_COOKIE_DENIED"),
        ("credential_handling_requested", "M141_CREDENTIAL_HANDLING_DENIED"),
        ("account_connector_requested", "M141_ACCOUNT_CONNECTOR_DENIED"),
        ("production_runtime_requested", "M141_PRODUCTION_RUNTIME_DENIED"),
        ("execution_requested", "M141_EXECUTION_DENIED"),
        ("tool_execution_requested", "M141_TOOL_EXECUTION_DENIED"),
        ("shell_execution_requested", "M141_SHELL_EXECUTION_DENIED"),
        ("browser_action_requested", "M141_BROWSER_ACTION_DENIED"),
        ("connector_action_requested", "M141_CONNECTOR_ACTION_DENIED"),
        ("network_access_requested", "M141_NETWORK_ACCESS_DENIED"),
        ("plugin_execution_requested", "M141_PLUGIN_EXECUTION_DENIED"),
        ("dependency_requested", "M141_DEPENDENCY_DENIED"),
        ("alpha_privacy_review_requested", "M141_ALPHA_PRIVACY_REVIEW_DENIED"),
        ("beta_release_requested", "M141_BETA_RELEASE_DENIED"),
        ("production_authority_requested", "M141_PRODUCTION_AUTHORITY_DENIED"),
        ("contains_raw_prompt", "M141_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M141_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M141_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M141_SECRET_DENIED"),
    ],
)
def test_m141_request_denies_unsafe_inputs(field, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_multi_user_product_boundary_request(
            _request().model_copy(update={field: True})
        )


def test_m141_requires_exact_checkpoint_and_boundary_refs() -> None:
    with pytest.raises(ValueError, match="M141_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_multi_user_product_boundary_request(
            _request(accepted_checkpoint_refs=[])
        )

    with pytest.raises(ValueError, match="M141_CHECKPOINT_REF_REQUIRED"):
        validate_multi_user_product_boundary_request(
            _request(accepted_checkpoint_refs=["checkpoint:m101"])
        )

    with pytest.raises(ValueError, match="M141_CHECKPOINT_REF_UNEXPECTED"):
        validate_multi_user_product_boundary_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M141_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m141",
                ]
            )
        )

    with pytest.raises(ValueError, match="M141_CHECKPOINT_REF_DUPLICATE"):
        validate_multi_user_product_boundary_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M141_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m140",
                ]
            )
        )

    with pytest.raises(ValueError, match="M141_USER_BOUNDARY_REF_REQUIRED"):
        validate_multi_user_product_boundary_request(_request(user_boundary_refs=[]))

    with pytest.raises(ValueError, match="M141_REF_DUPLICATE"):
        validate_multi_user_product_boundary_request(
            _request(
                tenant_boundary_refs=[
                    "tenant-boundary:m141:no-tenancy-runtime",
                    "tenant-boundary:m141:no-tenancy-runtime",
                ]
            )
        )


def test_m141_revalidates_model_copy_mutations() -> None:
    record = build_multi_user_product_boundary_record(_request())

    for update, reason in [
        ({"review_only": False}, "M141_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_only": False}, "M141_SAFE_REFS_ONLY_REQUIRED"),
        ({"product_boundary_only": False}, "M141_PRODUCT_BOUNDARY_ONLY_REQUIRED"),
        ({"m101_m140_covered": False}, "M141_M101_M140_COVERAGE_REQUIRED"),
        ({"actor_boundary_bound": False}, "M141_ACTOR_BOUNDARY_REQUIRED"),
        ({"workspace_boundary_bound": False}, "M141_WORKSPACE_BOUNDARY_REQUIRED"),
        ({"tenant_boundary_bound": False}, "M141_TENANT_BOUNDARY_REQUIRED"),
        ({"role_boundary_bound": False}, "M141_ROLE_BOUNDARY_REQUIRED"),
        ({"privacy_boundary_bound": False}, "M141_PRIVACY_BOUNDARY_REQUIRED"),
        ({"multi_user_runtime_started": True}, "M141_MULTI_USER_RUNTIME_DENIED"),
        ({"account_tenancy_enabled": True}, "M141_ACCOUNT_TENANCY_DENIED"),
        ({"tenant_runtime_started": True}, "M141_TENANT_RUNTIME_DENIED"),
        ({"workspace_sharing_enabled": True}, "M141_WORKSPACE_SHARING_DENIED"),
        ({"identity_federation_enabled": True}, "M141_IDENTITY_FEDERATION_DENIED"),
        ({"auth_runtime_started": True}, "M141_AUTH_RUNTIME_DENIED"),
        ({"login_enabled": True}, "M141_LOGIN_DENIED"),
        ({"session_cookie_enabled": True}, "M141_SESSION_COOKIE_DENIED"),
        ({"credential_handling_performed": True}, "M141_CREDENTIAL_HANDLING_DENIED"),
        ({"tool_execution_performed": True}, "M141_TOOL_EXECUTION_DENIED"),
        ({"browser_action_performed": True}, "M141_BROWSER_ACTION_DENIED"),
        ({"connector_action_performed": True}, "M141_CONNECTOR_ACTION_DENIED"),
        ({"backend_route_added": True}, "M141_BACKEND_ROUTE_DENIED"),
        ({"alpha_privacy_review_enabled": True}, "M141_ALPHA_PRIVACY_REVIEW_DENIED"),
        ({"beta_release_enabled": True}, "M141_BETA_RELEASE_DENIED"),
        (
            {"production_authority_granted": True},
            "M141_PRODUCTION_AUTHORITY_DENIED",
        ),
        ({"side_effects_performed": ["created tenant"]}, "M141_SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_multi_user_product_boundary_record(
                record.model_copy(update=update)
            )


def test_m141_denies_secret_like_metadata_and_requires_reason_code() -> None:
    with pytest.raises(
        ValueError,
        match="M141_SECRET_LIKE_PRODUCT_BOUNDARY_CONTENT_DENIED",
    ):
        build_multi_user_product_boundary_record(
            _request(metadata={"tenant_token": "abcde12345678901234567890"})
        )

    record = build_multi_user_product_boundary_record(_request())
    with pytest.raises(ValueError, match="M141_REASON_CODE_REQUIRED"):
        validate_multi_user_product_boundary_record(
            record.model_copy(update={"reason_codes": ["M142_REMAINS_FUTURE"]})
        )
