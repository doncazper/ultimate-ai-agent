import pytest

from ultimate_ai_agent.core.productization import (
    REQUIRED_M149_ACCEPTED_CHECKPOINT_REFS,
    AlphaReleaseCandidateFreezePolicy,
    AlphaReleaseCandidateFreezeRequest,
    AlphaReleaseCandidateFreezeStatus,
    build_alpha_release_candidate_freeze_record,
    validate_alpha_release_candidate_freeze_policy,
    validate_alpha_release_candidate_freeze_record,
    validate_alpha_release_candidate_freeze_request,
)


def _request(**overrides) -> AlphaReleaseCandidateFreezeRequest:
    data = {
        "request_ref": "alpha-release-candidate-freeze-request:m149",
        "release_candidate_ref": "alpha-release-candidate-freeze:m149",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M149_ACCEPTED_CHECKPOINT_REFS),
        "release_candidate_refs": [
            "release-candidate:m149:freeze",
            "release-candidate:m149:no-tag",
        ],
        "freeze_checklist_refs": [
            "freeze-checklist:m149:contracts",
            "freeze-checklist:m149:foundation-gate",
        ],
        "alpha_readiness_refs": [
            "alpha-readiness:m149:readiness-summary",
            "alpha-readiness:m149:no-public-release",
        ],
        "evidence_index_refs": [
            "evidence-index:m149:gate-results",
            "evidence-index:m149:docs-currentness",
        ],
        "blocker_summary_refs": [
            "blocker-summary:m149:none-recorded",
            "blocker-summary:m149:m150-future",
        ],
        "signoff_review_refs": [
            "signoff-review:m149:local-review",
            "signoff-review:m149:no-distribution",
        ],
        "m150_promotion_gate_refs": [
            "m150-promotion-gate:m149:future-only",
            "m150-promotion-gate:m149:no-alpha-publish",
        ],
        "audit_ref": "audit:m149:alpha-release-candidate-freeze",
        "replay_ref": "replay:m149:alpha-release-candidate-freeze",
        "revocation_ref": "revocation:m149:alpha-release-candidate-freeze",
        "kill_switch_ref": "kill-switch:m149:alpha-release-candidate-freeze",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m149:alpha-release-candidate-freeze:no-effect"
        ),
        "safe_summary": "Record alpha release candidate freeze refs without release authority.",
    }
    data.update(overrides)
    return AlphaReleaseCandidateFreezeRequest(**data)


def test_m149_record_is_freeze_only_and_non_authoritative() -> None:
    record = build_alpha_release_candidate_freeze_record(_request())

    assert record.status == AlphaReleaseCandidateFreezeStatus.freeze_recorded
    assert record.contract_only is True
    assert record.review_only is True
    assert record.freeze_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.alpha_release_candidate_freeze_only is True
    assert record.disabled_by_default is True
    assert record.m101_m148_covered is True
    assert record.release_candidates_bound is True
    assert record.freeze_checklists_bound is True
    assert record.alpha_readiness_bound is True
    assert record.evidence_indexes_bound is True
    assert record.blocker_summaries_bound is True
    assert record.signoff_reviews_bound is True
    assert record.m150_promotion_gates_bound is True
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
    assert record.no_m150_release is True
    assert record.no_release_automation is True
    assert record.no_backend_route is True
    assert record.no_control_center_control is True
    assert record.no_dependency is True
    assert record.no_production_authority is True
    assert record.accepted_checkpoint_refs == list(
        REQUIRED_M149_ACCEPTED_CHECKPOINT_REFS
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
    assert record.m150_release_performed is False
    assert record.release_automation_started is False
    assert record.auth_runtime_started is False
    assert record.connector_runtime_started is False
    assert record.plugin_marketplace_runtime_started is False
    assert record.execution_performed is False
    assert record.tool_execution_performed is False
    assert record.network_access_performed is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.production_authority_granted is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M149_ALPHA_RELEASE_CANDIDATE_FREEZE_REVIEW_ONLY",
        "M149_M101_M148_COVERED",
        "M149_FREEZE_ONLY",
        "M149_DISABLED_BY_DEFAULT",
        "M149_NO_RELEASE_PUBLICATION",
        "M149_NO_RELEASE_TAG",
        "M149_NO_TAG_CREATION",
        "M149_NO_ARTIFACT_BUILD",
        "M149_NO_ARTIFACT_UPLOAD",
        "M149_NO_ARTIFACT_EXPORT",
        "M149_NO_EXTERNAL_DISTRIBUTION",
        "M149_NO_APP_STORE_SUBMISSION",
        "M149_NO_TESTFLIGHT_SUBMISSION",
        "M149_NO_BETA_RELEASE",
        "M149_NO_M150_RELEASE",
        "M149_NO_RELEASE_AUTOMATION",
        "M149_NO_BACKEND_ROUTE",
        "M149_NO_PRODUCTION_AUTHORITY",
        "M150_REMAINS_FUTURE",
    ]


def test_m149_record_uses_safe_refs_only() -> None:
    record = build_alpha_release_candidate_freeze_record(_request())

    assert record.record_ref == "alpha-release-candidate-freeze-record:m149"
    assert record.release_candidate_ref == "alpha-release-candidate-freeze:m149"
    assert all(ref.startswith("release-candidate:") for ref in record.release_candidate_refs)
    assert all(ref.startswith("freeze-checklist:") for ref in record.freeze_checklist_refs)
    assert all(ref.startswith("alpha-readiness:") for ref in record.alpha_readiness_refs)
    assert all(ref.startswith("evidence-index:") for ref in record.evidence_index_refs)
    assert all(ref.startswith("blocker-summary:") for ref in record.blocker_summary_refs)
    assert all(ref.startswith("signoff-review:") for ref in record.signoff_review_refs)
    assert all(
        ref.startswith("m150-promotion-gate:")
        for ref in record.m150_promotion_gate_refs
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
        ("release_publication_enabled", "M149_RELEASE_PUBLICATION_DENIED"),
        ("release_tag_enabled", "M149_RELEASE_TAG_DENIED"),
        ("tag_creation_enabled", "M149_TAG_CREATION_DENIED"),
        ("artifact_build_enabled", "M149_ARTIFACT_BUILD_DENIED"),
        ("artifact_upload_enabled", "M149_ARTIFACT_UPLOAD_DENIED"),
        ("artifact_export_enabled", "M149_ARTIFACT_EXPORT_DENIED"),
        ("external_distribution_enabled", "M149_EXTERNAL_DISTRIBUTION_DENIED"),
        ("app_store_submission_enabled", "M149_APP_STORE_SUBMISSION_DENIED"),
        ("testflight_submission_enabled", "M149_TESTFLIGHT_SUBMISSION_DENIED"),
        ("beta_release_enabled", "M149_BETA_RELEASE_DENIED"),
        ("m150_release_enabled", "M149_M150_RELEASE_DENIED"),
        ("release_automation_enabled", "M149_RELEASE_AUTOMATION_DENIED"),
        ("auth_runtime_enabled", "M149_AUTH_RUNTIME_DENIED"),
        ("connector_runtime_enabled", "M149_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_enabled",
            "M149_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("tool_execution_enabled", "M149_TOOL_EXECUTION_DENIED"),
        ("network_access_enabled", "M149_NETWORK_ACCESS_DENIED"),
        ("backend_route_enabled", "M149_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M149_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M149_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m149_policy_denies_authority_expansion(field, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_alpha_release_candidate_freeze_policy(
            AlphaReleaseCandidateFreezePolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("release_publication_requested", "M149_RELEASE_PUBLICATION_DENIED"),
        ("release_tag_requested", "M149_RELEASE_TAG_DENIED"),
        ("tag_creation_requested", "M149_TAG_CREATION_DENIED"),
        ("artifact_build_requested", "M149_ARTIFACT_BUILD_DENIED"),
        ("artifact_upload_requested", "M149_ARTIFACT_UPLOAD_DENIED"),
        ("artifact_export_requested", "M149_ARTIFACT_EXPORT_DENIED"),
        ("external_distribution_requested", "M149_EXTERNAL_DISTRIBUTION_DENIED"),
        ("app_store_submission_requested", "M149_APP_STORE_SUBMISSION_DENIED"),
        ("testflight_submission_requested", "M149_TESTFLIGHT_SUBMISSION_DENIED"),
        ("m150_release_requested", "M149_M150_RELEASE_DENIED"),
        ("release_automation_requested", "M149_RELEASE_AUTOMATION_DENIED"),
        ("auth_runtime_requested", "M149_AUTH_RUNTIME_DENIED"),
        ("connector_runtime_requested", "M149_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_requested",
            "M149_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("contains_raw_private_content", "M149_RAW_PRIVATE_CONTENT_DENIED"),
        ("contains_raw_prompt", "M149_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M149_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M149_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M149_SECRET_DENIED"),
        ("backend_route_requested", "M149_BACKEND_ROUTE_DENIED"),
        ("dependency_requested", "M149_DEPENDENCY_DENIED"),
        ("production_authority_requested", "M149_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m149_request_denies_unsafe_inputs(field, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_alpha_release_candidate_freeze_request(
            _request().model_copy(update={field: True})
        )


def test_m149_requires_exact_checkpoint_and_safety_refs() -> None:
    with pytest.raises(ValueError, match="M149_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_alpha_release_candidate_freeze_request(
            _request(accepted_checkpoint_refs=[])
        )

    with pytest.raises(ValueError, match="M149_CHECKPOINT_REF_REQUIRED"):
        validate_alpha_release_candidate_freeze_request(
            _request(accepted_checkpoint_refs=["checkpoint:m101"])
        )

    with pytest.raises(ValueError, match="M149_CHECKPOINT_REF_UNEXPECTED"):
        validate_alpha_release_candidate_freeze_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M149_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m149",
                ]
            )
        )

    for field, reason in [
        ("release_candidate_refs", "M149_RELEASE_CANDIDATE_REF_REQUIRED"),
        ("freeze_checklist_refs", "M149_FREEZE_CHECKLIST_REF_REQUIRED"),
        ("alpha_readiness_refs", "M149_ALPHA_READINESS_REF_REQUIRED"),
        ("evidence_index_refs", "M149_EVIDENCE_INDEX_REF_REQUIRED"),
        ("blocker_summary_refs", "M149_BLOCKER_SUMMARY_REF_REQUIRED"),
        ("signoff_review_refs", "M149_SIGNOFF_REVIEW_REF_REQUIRED"),
        ("m150_promotion_gate_refs", "M149_M150_PROMOTION_GATE_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_alpha_release_candidate_freeze_request(_request(**{field: []}))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"release_publication_started": True}, "M149_RELEASE_PUBLICATION_DENIED"),
        ({"release_tag_created": True}, "M149_RELEASE_TAG_DENIED"),
        ({"tag_creation_performed": True}, "M149_TAG_CREATION_DENIED"),
        ({"artifact_build_performed": True}, "M149_ARTIFACT_BUILD_DENIED"),
        ({"artifact_upload_started": True}, "M149_ARTIFACT_UPLOAD_DENIED"),
        ({"artifact_export_started": True}, "M149_ARTIFACT_EXPORT_DENIED"),
        ({"external_distribution_started": True}, "M149_EXTERNAL_DISTRIBUTION_DENIED"),
        ({"app_store_submission_started": True}, "M149_APP_STORE_SUBMISSION_DENIED"),
        ({"testflight_submission_started": True}, "M149_TESTFLIGHT_SUBMISSION_DENIED"),
        ({"beta_release_enabled": True}, "M149_BETA_RELEASE_DENIED"),
        ({"m150_release_performed": True}, "M149_M150_RELEASE_DENIED"),
        ({"release_automation_started": True}, "M149_RELEASE_AUTOMATION_DENIED"),
        ({"auth_runtime_started": True}, "M149_AUTH_RUNTIME_DENIED"),
        ({"backend_route_added": True}, "M149_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M149_DEPENDENCY_DENIED"),
        ({"production_authority_granted": True}, "M149_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m149_record_denies_unsafe_mutations(update, reason) -> None:
    record = build_alpha_release_candidate_freeze_record(_request())

    with pytest.raises(ValueError, match=reason):
        validate_alpha_release_candidate_freeze_record(record.model_copy(update=update))


def test_m149_denies_side_effect_receipts_and_secret_like_metadata() -> None:
    with pytest.raises(ValueError, match="M149_SIDE_EFFECTS_DENIED"):
        validate_alpha_release_candidate_freeze_request(
            _request(side_effects_performed=["published alpha release"])
        )

    record = build_alpha_release_candidate_freeze_record(_request())
    with pytest.raises(ValueError, match="M149_SIDE_EFFECTS_DENIED"):
        validate_alpha_release_candidate_freeze_record(
            record.model_copy(update={"side_effects_performed": ["created git tag"]})
        )

    with pytest.raises(ValueError, match="M149_SECRET_LIKE_RELEASE_FREEZE_CONTENT_DENIED"):
        validate_alpha_release_candidate_freeze_policy(
            AlphaReleaseCandidateFreezePolicy(metadata={"api_key": "x"})
        )
