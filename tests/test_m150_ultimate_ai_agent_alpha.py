from typing import Any
import pytest

from ultimate_ai_agent.core.productization import (
    REQUIRED_M150_ACCEPTED_CHECKPOINT_REFS,
    UltimateAiAgentAlphaPolicy,
    UltimateAiAgentAlphaRequest,
    UltimateAiAgentAlphaStatus,
    build_ultimate_ai_agent_alpha_record,
    validate_ultimate_ai_agent_alpha_policy,
    validate_ultimate_ai_agent_alpha_record,
    validate_ultimate_ai_agent_alpha_request,
)


def _request(**overrides: Any) -> UltimateAiAgentAlphaRequest:
    data = {
        "request_ref": "ultimate-ai-agent-alpha-request:m150",
        "alpha_target_ref": "ultimate-ai-agent-alpha:m150",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M150_ACCEPTED_CHECKPOINT_REFS),
        "alpha_target_refs": [
            "alpha-target:m150:v1.2.0-alpha",
            "alpha-target:m150:no-public-release",
        ],
        "release_candidate_freeze_refs": [
            "release-candidate-freeze:m149:accepted",
            "release-candidate-freeze:m150:no-tag",
        ],
        "alpha_readiness_refs": [
            "alpha-readiness:m150:target-summary",
            "alpha-readiness:m150:local-only",
        ],
        "evidence_index_refs": [
            "evidence-index:m150:gate-results",
            "evidence-index:m150:docs-currentness",
        ],
        "blocker_summary_refs": [
            "blocker-summary:m150:none-recorded",
            "blocker-summary:m150:beta-future",
        ],
        "signoff_review_refs": [
            "signoff-review:m150:local-review",
            "signoff-review:m150:no-distribution",
        ],
        "beta_promotion_gate_refs": [
            "beta-promotion-gate:m150:future-only",
            "beta-promotion-gate:m150:no-beta-publish",
        ],
        "audit_ref": "audit:m150:ultimate-ai-agent-alpha",
        "replay_ref": "replay:m150:ultimate-ai-agent-alpha",
        "revocation_ref": "revocation:m150:ultimate-ai-agent-alpha",
        "kill_switch_ref": "kill-switch:m150:ultimate-ai-agent-alpha",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m150:ultimate-ai-agent-alpha:no-effect"
        ),
        "safe_summary": "Record v1.2.0-alpha target refs without release authority.",
    }
    data.update(overrides)
    return UltimateAiAgentAlphaRequest(**data)


def test_m150_record_is_alpha_target_only_and_non_authoritative() -> None:
    record = build_ultimate_ai_agent_alpha_record(_request())

    assert record.status == UltimateAiAgentAlphaStatus.alpha_target_recorded
    assert record.product_target_ref == "product-target:v1.2.0-alpha"
    assert record.contract_only is True
    assert record.review_only is True
    assert record.alpha_target_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.disabled_by_default is True
    assert record.m101_m149_covered is True
    assert record.alpha_targets_bound is True
    assert record.release_candidate_freezes_bound is True
    assert record.alpha_readiness_bound is True
    assert record.evidence_indexes_bound is True
    assert record.blocker_summaries_bound is True
    assert record.signoff_reviews_bound is True
    assert record.beta_promotion_gates_bound is True
    assert record.audit_replay_bound is True
    assert record.revocation_bound is True
    assert record.no_effect_receipt_required is True
    assert record.no_release_publication is True
    assert record.no_release_tag is True
    assert record.no_tag_creation is True
    assert record.no_artifact_build is True
    assert record.no_artifact_upload is True
    assert record.no_artifact_export is True
    assert record.no_external_distribution is True
    assert record.no_app_store_submission is True
    assert record.no_testflight_submission is True
    assert record.no_beta_release is True
    assert record.no_release_automation is True
    assert record.no_backend_route is True
    assert record.no_control_center_control is True
    assert record.no_dependency is True
    assert record.no_production_authority is True
    assert record.accepted_checkpoint_refs == list(
        REQUIRED_M150_ACCEPTED_CHECKPOINT_REFS
    )
    assert record.release_publication_started is False
    assert record.release_tag_created is False
    assert record.tag_creation_performed is False
    assert record.artifact_build_performed is False
    assert record.artifact_upload_started is False
    assert record.artifact_export_started is False
    assert record.external_distribution_started is False
    assert record.app_store_submission_started is False
    assert record.testflight_submission_started is False
    assert record.beta_release_enabled is False
    assert record.release_automation_started is False
    assert record.auth_runtime_started is False
    assert record.connector_runtime_started is False
    assert record.execution_performed is False
    assert record.tool_execution_performed is False
    assert record.network_access_performed is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.production_authority_granted is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M150_ULTIMATE_AI_AGENT_ALPHA_REVIEW_ONLY",
        "M150_M101_M149_COVERED",
        "M150_ALPHA_TARGET_ONLY",
        "M150_DISABLED_BY_DEFAULT",
        "M150_NO_RELEASE_PUBLICATION",
        "M150_NO_RELEASE_TAG",
        "M150_NO_TAG_CREATION",
        "M150_NO_ARTIFACT_BUILD",
        "M150_NO_ARTIFACT_UPLOAD",
        "M150_NO_ARTIFACT_EXPORT",
        "M150_NO_EXTERNAL_DISTRIBUTION",
        "M150_NO_APP_STORE_SUBMISSION",
        "M150_NO_TESTFLIGHT_SUBMISSION",
        "M150_NO_BETA_RELEASE",
        "M150_NO_RELEASE_AUTOMATION",
        "M150_NO_BACKEND_ROUTE",
        "M150_NO_PRODUCTION_AUTHORITY",
        "BETA_REMAINS_FUTURE",
    ]


def test_m150_record_uses_safe_refs_only() -> None:
    record = build_ultimate_ai_agent_alpha_record(_request())

    assert record.record_ref == "ultimate-ai-agent-alpha-record:m150"
    assert record.alpha_target_ref == "ultimate-ai-agent-alpha:m150"
    assert all(ref.startswith("alpha-target:") for ref in record.alpha_target_refs)
    assert all(
        ref.startswith("release-candidate-freeze:")
        for ref in record.release_candidate_freeze_refs
    )
    assert all(ref.startswith("alpha-readiness:") for ref in record.alpha_readiness_refs)
    assert all(ref.startswith("evidence-index:") for ref in record.evidence_index_refs)
    assert all(ref.startswith("blocker-summary:") for ref in record.blocker_summary_refs)
    assert all(ref.startswith("signoff-review:") for ref in record.signoff_review_refs)
    assert all(
        ref.startswith("beta-promotion-gate:")
        for ref in record.beta_promotion_gate_refs
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
        ("release_publication_enabled", "M150_RELEASE_PUBLICATION_DENIED"),
        ("release_tag_enabled", "M150_RELEASE_TAG_DENIED"),
        ("tag_creation_enabled", "M150_TAG_CREATION_DENIED"),
        ("artifact_build_enabled", "M150_ARTIFACT_BUILD_DENIED"),
        ("artifact_upload_enabled", "M150_ARTIFACT_UPLOAD_DENIED"),
        ("artifact_export_enabled", "M150_ARTIFACT_EXPORT_DENIED"),
        ("external_distribution_enabled", "M150_EXTERNAL_DISTRIBUTION_DENIED"),
        ("app_store_submission_enabled", "M150_APP_STORE_SUBMISSION_DENIED"),
        ("testflight_submission_enabled", "M150_TESTFLIGHT_SUBMISSION_DENIED"),
        ("beta_release_enabled", "M150_BETA_RELEASE_DENIED"),
        ("release_automation_enabled", "M150_RELEASE_AUTOMATION_DENIED"),
        ("auth_runtime_enabled", "M150_AUTH_RUNTIME_DENIED"),
        ("connector_runtime_enabled", "M150_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_enabled",
            "M150_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("tool_execution_enabled", "M150_TOOL_EXECUTION_DENIED"),
        ("network_access_enabled", "M150_NETWORK_ACCESS_DENIED"),
        ("backend_route_enabled", "M150_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M150_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M150_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m150_policy_denies_authority_expansion(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_ultimate_ai_agent_alpha_policy(
            UltimateAiAgentAlphaPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("release_publication_requested", "M150_RELEASE_PUBLICATION_DENIED"),
        ("release_tag_requested", "M150_RELEASE_TAG_DENIED"),
        ("tag_creation_requested", "M150_TAG_CREATION_DENIED"),
        ("artifact_build_requested", "M150_ARTIFACT_BUILD_DENIED"),
        ("artifact_upload_requested", "M150_ARTIFACT_UPLOAD_DENIED"),
        ("artifact_export_requested", "M150_ARTIFACT_EXPORT_DENIED"),
        ("external_distribution_requested", "M150_EXTERNAL_DISTRIBUTION_DENIED"),
        ("app_store_submission_requested", "M150_APP_STORE_SUBMISSION_DENIED"),
        ("testflight_submission_requested", "M150_TESTFLIGHT_SUBMISSION_DENIED"),
        ("release_automation_requested", "M150_RELEASE_AUTOMATION_DENIED"),
        ("auth_runtime_requested", "M150_AUTH_RUNTIME_DENIED"),
        ("connector_runtime_requested", "M150_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_requested",
            "M150_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("contains_raw_private_content", "M150_RAW_PRIVATE_CONTENT_DENIED"),
        ("contains_raw_prompt", "M150_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M150_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M150_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M150_SECRET_DENIED"),
        ("backend_route_requested", "M150_BACKEND_ROUTE_DENIED"),
        ("dependency_requested", "M150_DEPENDENCY_DENIED"),
        ("production_authority_requested", "M150_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m150_request_denies_unsafe_inputs(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_ultimate_ai_agent_alpha_request(
            _request().model_copy(update={field: True})
        )


def test_m150_requires_exact_checkpoint_and_safety_refs() -> None:
    with pytest.raises(ValueError, match="M150_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_ultimate_ai_agent_alpha_request(_request(accepted_checkpoint_refs=[]))

    with pytest.raises(ValueError, match="M150_CHECKPOINT_REF_REQUIRED"):
        validate_ultimate_ai_agent_alpha_request(
            _request(accepted_checkpoint_refs=["checkpoint:m101"])
        )

    with pytest.raises(ValueError, match="M150_CHECKPOINT_REF_UNEXPECTED"):
        validate_ultimate_ai_agent_alpha_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M150_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m151",
                ]
            )
        )

    with pytest.raises(ValueError, match="M150_PRODUCT_TARGET_REF_REQUIRED"):
        validate_ultimate_ai_agent_alpha_request(
            _request(product_target_ref="product-target:v1.0.0-beta")
        )

    for field, reason in [
        ("alpha_target_refs", "M150_ALPHA_TARGET_REF_REQUIRED"),
        (
            "release_candidate_freeze_refs",
            "M150_RELEASE_CANDIDATE_FREEZE_REF_REQUIRED",
        ),
        ("alpha_readiness_refs", "M150_ALPHA_READINESS_REF_REQUIRED"),
        ("evidence_index_refs", "M150_EVIDENCE_INDEX_REF_REQUIRED"),
        ("blocker_summary_refs", "M150_BLOCKER_SUMMARY_REF_REQUIRED"),
        ("signoff_review_refs", "M150_SIGNOFF_REVIEW_REF_REQUIRED"),
        ("beta_promotion_gate_refs", "M150_BETA_PROMOTION_GATE_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_ultimate_ai_agent_alpha_request(
                _request().model_copy(update={field: []})
            )


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"release_publication_started": True}, "M150_RELEASE_PUBLICATION_DENIED"),
        ({"release_tag_created": True}, "M150_RELEASE_TAG_DENIED"),
        ({"tag_creation_performed": True}, "M150_TAG_CREATION_DENIED"),
        ({"artifact_build_performed": True}, "M150_ARTIFACT_BUILD_DENIED"),
        ({"artifact_upload_started": True}, "M150_ARTIFACT_UPLOAD_DENIED"),
        ({"artifact_export_started": True}, "M150_ARTIFACT_EXPORT_DENIED"),
        ({"external_distribution_started": True}, "M150_EXTERNAL_DISTRIBUTION_DENIED"),
        ({"app_store_submission_started": True}, "M150_APP_STORE_SUBMISSION_DENIED"),
        ({"testflight_submission_started": True}, "M150_TESTFLIGHT_SUBMISSION_DENIED"),
        ({"beta_release_enabled": True}, "M150_BETA_RELEASE_DENIED"),
        ({"release_automation_started": True}, "M150_RELEASE_AUTOMATION_DENIED"),
        ({"auth_runtime_started": True}, "M150_AUTH_RUNTIME_DENIED"),
        ({"backend_route_added": True}, "M150_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M150_DEPENDENCY_DENIED"),
        ({"production_authority_granted": True}, "M150_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m150_record_denies_unsafe_mutations(update: Any, reason: str) -> None:
    record = build_ultimate_ai_agent_alpha_record(_request())

    with pytest.raises(ValueError, match=reason):
        validate_ultimate_ai_agent_alpha_record(record.model_copy(update=update))


def test_m150_rejects_side_effects_and_secret_like_content() -> None:
    with pytest.raises(ValueError, match="M150_SIDE_EFFECTS_DENIED"):
        validate_ultimate_ai_agent_alpha_request(
            _request(side_effects_performed=["created-release"])
        )

    record = build_ultimate_ai_agent_alpha_record(_request())
    with pytest.raises(ValueError, match="M150_SIDE_EFFECTS_DENIED"):
        validate_ultimate_ai_agent_alpha_record(
            record.model_copy(update={"side_effects_performed": ["pushed-tag"]})
        )

    with pytest.raises(ValueError, match="M150_SECRET_LIKE_ALPHA_CONTENT_DENIED"):
        validate_ultimate_ai_agent_alpha_policy(
            UltimateAiAgentAlphaPolicy(metadata={"api_key": "redacted"})
        )
