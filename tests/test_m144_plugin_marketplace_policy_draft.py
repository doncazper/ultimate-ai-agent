from typing import Any
import pytest

from ultimate_ai_agent.core.productization import (
    REQUIRED_M144_ACCEPTED_CHECKPOINT_REFS,
    PluginMarketplacePolicyDraftPolicy,
    PluginMarketplacePolicyDraftRequest,
    PluginMarketplacePolicyDraftStatus,
    build_plugin_marketplace_policy_draft_record,
    validate_plugin_marketplace_policy_draft_policy,
    validate_plugin_marketplace_policy_draft_record,
    validate_plugin_marketplace_policy_draft_request,
)


def _request(**overrides: Any) -> PluginMarketplacePolicyDraftRequest:
    data = {
        "request_ref": "plugin-marketplace-policy-draft-request:m144",
        "policy_draft_ref": "plugin-marketplace-policy-draft:m144",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M144_ACCEPTED_CHECKPOINT_REFS),
        "marketplace_policy_refs": [
            "marketplace-policy:m144:disabled-by-default",
            "marketplace-policy:m144:no-runtime",
        ],
        "publisher_policy_refs": [
            "publisher-policy:m144:identity-review-only",
            "publisher-policy:m144:no-publish-authority",
        ],
        "listing_review_refs": [
            "listing-review:m144:safe-summary-only",
            "listing-review:m144:no-listing-mutation",
        ],
        "provenance_review_refs": [
            "provenance-review:m144:source-ref-only",
            "provenance-review:m144:no-package-import",
        ],
        "signature_review_refs": [
            "signature-review:m144:policy-only",
            "signature-review:m144:no-runtime-verification",
        ],
        "sandbox_review_refs": [
            "sandbox-review:m144:future-test-plan",
            "sandbox-review:m144:no-plugin-execution",
        ],
        "permission_mapping_refs": [
            "permission-mapping:m144:tool-broker-plan",
            "permission-mapping:m144:no-permission-grant",
        ],
        "approval_policy_refs": [
            "approval-policy:m144:high-risk-human-review",
            "approval-policy:m144:no-approval-capture",
        ],
        "audit_ref": "audit:m144:plugin-marketplace-policy-draft",
        "replay_ref": "replay:m144:plugin-marketplace-policy-draft",
        "revocation_ref": "revocation:m144:plugin-marketplace-policy-draft",
        "kill_switch_ref": "kill-switch:m144:plugin-marketplace-policy-draft",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m144:plugin-marketplace-policy-draft:no-effect"
        ),
        "safe_summary": "Record plugin marketplace policy refs without runtime authority.",
    }
    data.update(overrides)
    return PluginMarketplacePolicyDraftRequest(**data)


def test_m144_record_is_policy_draft_only_and_non_authoritative() -> None:
    record = build_plugin_marketplace_policy_draft_record(_request())

    assert record.status == PluginMarketplacePolicyDraftStatus.policy_draft_recorded
    assert record.contract_only is True
    assert record.review_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.policy_draft_only is True
    assert record.disabled_by_default is True
    assert record.m101_m143_covered is True
    assert record.marketplace_policy_bound is True
    assert record.publisher_policy_bound is True
    assert record.listing_review_bound is True
    assert record.provenance_review_bound is True
    assert record.signature_review_bound is True
    assert record.sandbox_review_bound is True
    assert record.permission_mapping_bound is True
    assert record.approval_policy_bound is True
    assert record.audit_replay_bound is True
    assert record.revocation_bound is True
    assert record.no_effect_receipt_required is True
    assert record.no_plugin_install is True
    assert record.no_plugin_enablement is True
    assert record.no_plugin_execution is True
    assert record.no_marketplace_runtime is True
    assert record.no_marketplace_publish is True
    assert record.no_external_plugin_authority is True
    assert record.no_package_import is True
    assert record.no_network_plugin_fetch is True
    assert record.no_dependency is True
    assert record.no_production_authority is True
    assert record.accepted_checkpoint_refs == list(
        REQUIRED_M144_ACCEPTED_CHECKPOINT_REFS
    )
    assert record.plugin_marketplace_runtime_started is False
    assert record.marketplace_publish_performed is False
    assert record.plugin_install_performed is False
    assert record.plugin_enablement_performed is False
    assert record.plugin_execution_performed is False
    assert record.external_plugin_authority_granted is False
    assert record.external_plugin_loaded is False
    assert record.marketplace_listing_mutation_performed is False
    assert record.package_import_performed is False
    assert record.runtime_import_performed is False
    assert record.network_plugin_fetch_performed is False
    assert record.package_download_performed is False
    assert record.artifact_upload_performed is False
    assert record.signature_verification_runtime_performed is False
    assert record.credential_handling_performed is False
    assert record.execution_performed is False
    assert record.tool_execution_performed is False
    assert record.shell_execution_performed is False
    assert record.browser_action_performed is False
    assert record.connector_action_performed is False
    assert record.network_access_performed is False
    assert record.model_call_performed is False
    assert record.memory_write_performed is False
    assert record.context_injection_performed is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.production_authority_granted is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M144_PLUGIN_MARKETPLACE_POLICY_DRAFT_REVIEW_ONLY",
        "M144_M101_M143_COVERED",
        "M144_DISABLED_BY_DEFAULT",
        "M144_NO_PLUGIN_INSTALL",
        "M144_NO_PLUGIN_ENABLEMENT",
        "M144_NO_PLUGIN_EXECUTION",
        "M144_NO_MARKETPLACE_RUNTIME",
        "M144_NO_MARKETPLACE_PUBLISH",
        "M144_NO_EXTERNAL_PLUGIN_AUTHORITY",
        "M144_NO_PACKAGE_IMPORT",
        "M144_NO_NETWORK_PLUGIN_FETCH",
        "M144_NO_PRODUCTION_AUTHORITY",
        "M145_REMAINS_FUTURE",
    ]


def test_m144_record_uses_safe_refs_only() -> None:
    record = build_plugin_marketplace_policy_draft_record(_request())

    assert record.record_ref == "plugin-marketplace-policy-draft-record:m144"
    assert record.policy_draft_ref == "plugin-marketplace-policy-draft:m144"
    assert all(
        ref.startswith("marketplace-policy:")
        for ref in record.marketplace_policy_refs
    )
    assert all(ref.startswith("publisher-policy:") for ref in record.publisher_policy_refs)
    assert all(ref.startswith("listing-review:") for ref in record.listing_review_refs)
    assert all(
        ref.startswith("provenance-review:")
        for ref in record.provenance_review_refs
    )
    assert all(
        ref.startswith("signature-review:")
        for ref in record.signature_review_refs
    )
    assert all(ref.startswith("sandbox-review:") for ref in record.sandbox_review_refs)
    assert all(
        ref.startswith("permission-mapping:")
        for ref in record.permission_mapping_refs
    )
    assert all(ref.startswith("approval-policy:") for ref in record.approval_policy_refs)
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
        ("plugin_marketplace_runtime_enabled", "M144_MARKETPLACE_RUNTIME_DENIED"),
        ("marketplace_publish_enabled", "M144_MARKETPLACE_PUBLISH_DENIED"),
        ("plugin_install_enabled", "M144_PLUGIN_INSTALL_DENIED"),
        ("plugin_enablement_enabled", "M144_PLUGIN_ENABLEMENT_DENIED"),
        ("plugin_execution_enabled", "M144_PLUGIN_EXECUTION_DENIED"),
        (
            "external_plugin_authority_enabled",
            "M144_EXTERNAL_PLUGIN_AUTHORITY_DENIED",
        ),
        ("external_plugin_loading_enabled", "M144_EXTERNAL_PLUGIN_LOADING_DENIED"),
        ("marketplace_listing_mutation_enabled", "M144_MARKETPLACE_MUTATION_DENIED"),
        ("package_import_enabled", "M144_PACKAGE_IMPORT_DENIED"),
        ("runtime_import_enabled", "M144_RUNTIME_IMPORT_DENIED"),
        ("network_plugin_fetch_enabled", "M144_NETWORK_PLUGIN_FETCH_DENIED"),
        ("package_download_enabled", "M144_PACKAGE_DOWNLOAD_DENIED"),
        ("artifact_upload_enabled", "M144_ARTIFACT_UPLOAD_DENIED"),
        (
            "signature_verification_runtime_enabled",
            "M144_SIGNATURE_RUNTIME_DENIED",
        ),
        ("credential_handling_enabled", "M144_CREDENTIAL_HANDLING_DENIED"),
        ("execution_enabled", "M144_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M144_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M144_SHELL_EXECUTION_DENIED"),
        ("browser_action_enabled", "M144_BROWSER_ACTION_DENIED"),
        ("connector_action_enabled", "M144_CONNECTOR_ACTION_DENIED"),
        ("network_access_enabled", "M144_NETWORK_ACCESS_DENIED"),
        ("backend_route_enabled", "M144_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M144_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M144_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m144_policy_denies_authority_expansion(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_plugin_marketplace_policy_draft_policy(
            PluginMarketplacePolicyDraftPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("plugin_marketplace_runtime_requested", "M144_MARKETPLACE_RUNTIME_DENIED"),
        ("marketplace_publish_requested", "M144_MARKETPLACE_PUBLISH_DENIED"),
        ("plugin_install_requested", "M144_PLUGIN_INSTALL_DENIED"),
        ("plugin_enablement_requested", "M144_PLUGIN_ENABLEMENT_DENIED"),
        ("plugin_execution_requested", "M144_PLUGIN_EXECUTION_DENIED"),
        (
            "external_plugin_authority_requested",
            "M144_EXTERNAL_PLUGIN_AUTHORITY_DENIED",
        ),
        ("external_plugin_loading_requested", "M144_EXTERNAL_PLUGIN_LOADING_DENIED"),
        ("marketplace_listing_mutation_requested", "M144_MARKETPLACE_MUTATION_DENIED"),
        ("package_import_requested", "M144_PACKAGE_IMPORT_DENIED"),
        ("runtime_import_requested", "M144_RUNTIME_IMPORT_DENIED"),
        ("network_plugin_fetch_requested", "M144_NETWORK_PLUGIN_FETCH_DENIED"),
        ("package_download_requested", "M144_PACKAGE_DOWNLOAD_DENIED"),
        ("artifact_upload_requested", "M144_ARTIFACT_UPLOAD_DENIED"),
        (
            "signature_verification_runtime_requested",
            "M144_SIGNATURE_RUNTIME_DENIED",
        ),
        ("contains_raw_manifest_content", "M144_RAW_MANIFEST_CONTENT_DENIED"),
        ("contains_raw_package_content", "M144_RAW_PACKAGE_CONTENT_DENIED"),
        ("contains_raw_prompt", "M144_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M144_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M144_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M144_SECRET_DENIED"),
        ("backend_route_requested", "M144_BACKEND_ROUTE_DENIED"),
        ("dependency_requested", "M144_DEPENDENCY_DENIED"),
        ("production_authority_requested", "M144_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m144_request_denies_unsafe_inputs(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_plugin_marketplace_policy_draft_request(
            _request().model_copy(update={field: True})
        )


def test_m144_requires_exact_checkpoint_and_policy_refs() -> None:
    with pytest.raises(ValueError, match="M144_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_plugin_marketplace_policy_draft_request(
            _request(accepted_checkpoint_refs=[])
        )

    with pytest.raises(ValueError, match="M144_CHECKPOINT_REF_REQUIRED"):
        validate_plugin_marketplace_policy_draft_request(
            _request(accepted_checkpoint_refs=["checkpoint:m101"])
        )

    with pytest.raises(ValueError, match="M144_CHECKPOINT_REF_UNEXPECTED"):
        validate_plugin_marketplace_policy_draft_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M144_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m145",
                ]
            )
        )

    for field, reason in [
        ("marketplace_policy_refs", "M144_MARKETPLACE_POLICY_REF_REQUIRED"),
        ("publisher_policy_refs", "M144_PUBLISHER_POLICY_REF_REQUIRED"),
        ("listing_review_refs", "M144_LISTING_REVIEW_REF_REQUIRED"),
        ("provenance_review_refs", "M144_PROVENANCE_REVIEW_REF_REQUIRED"),
        ("signature_review_refs", "M144_SIGNATURE_REVIEW_REF_REQUIRED"),
        ("sandbox_review_refs", "M144_SANDBOX_REVIEW_REF_REQUIRED"),
        ("permission_mapping_refs", "M144_PERMISSION_MAPPING_REF_REQUIRED"),
        ("approval_policy_refs", "M144_APPROVAL_POLICY_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_plugin_marketplace_policy_draft_request(_request(**{field: []}))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        (
            {"plugin_marketplace_runtime_started": True},
            "M144_MARKETPLACE_RUNTIME_DENIED",
        ),
        ({"marketplace_publish_performed": True}, "M144_MARKETPLACE_PUBLISH_DENIED"),
        ({"plugin_install_performed": True}, "M144_PLUGIN_INSTALL_DENIED"),
        ({"plugin_enablement_performed": True}, "M144_PLUGIN_ENABLEMENT_DENIED"),
        ({"plugin_execution_performed": True}, "M144_PLUGIN_EXECUTION_DENIED"),
        (
            {"external_plugin_authority_granted": True},
            "M144_EXTERNAL_PLUGIN_AUTHORITY_DENIED",
        ),
        ({"external_plugin_loaded": True}, "M144_EXTERNAL_PLUGIN_LOADING_DENIED"),
        ({"package_import_performed": True}, "M144_PACKAGE_IMPORT_DENIED"),
        ({"network_plugin_fetch_performed": True}, "M144_NETWORK_PLUGIN_FETCH_DENIED"),
        ({"package_download_performed": True}, "M144_PACKAGE_DOWNLOAD_DENIED"),
        ({"artifact_upload_performed": True}, "M144_ARTIFACT_UPLOAD_DENIED"),
        ({"backend_route_added": True}, "M144_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M144_DEPENDENCY_DENIED"),
        ({"production_authority_granted": True}, "M144_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m144_record_denies_unsafe_mutations(update: Any, reason: str) -> None:
    record = build_plugin_marketplace_policy_draft_record(_request())

    with pytest.raises(ValueError, match=reason):
        validate_plugin_marketplace_policy_draft_record(record.model_copy(update=update))


def test_m144_denies_side_effect_receipts_and_secret_like_metadata() -> None:
    with pytest.raises(ValueError, match="M144_SIDE_EFFECTS_DENIED"):
        validate_plugin_marketplace_policy_draft_request(
            _request(side_effects_performed=["published marketplace listing"])
        )

    record = build_plugin_marketplace_policy_draft_record(_request())
    with pytest.raises(ValueError, match="M144_SIDE_EFFECTS_DENIED"):
        validate_plugin_marketplace_policy_draft_record(
            record.model_copy(update={"side_effects_performed": ["installed plugin"]})
        )

    with pytest.raises(
        ValueError, match="M144_SECRET_LIKE_MARKETPLACE_POLICY_CONTENT_DENIED"
    ):
        validate_plugin_marketplace_policy_draft_policy(
            PluginMarketplacePolicyDraftPolicy(metadata={"api_key": "x"})
        )
