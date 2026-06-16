import pytest

from ultimate_ai_agent.core.productization import (
    REQUIRED_M148_ACCEPTED_CHECKPOINT_REFS,
    ExternalSecurityReviewPolicy,
    ExternalSecurityReviewRequest,
    ExternalSecurityReviewStatus,
    build_external_security_review_record,
    validate_external_security_review_policy,
    validate_external_security_review_record,
    validate_external_security_review_request,
)


def _request(**overrides) -> ExternalSecurityReviewRequest:
    data = {
        "request_ref": "external-security-review-request:m148",
        "security_review_ref": "external-security-review:m148",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M148_ACCEPTED_CHECKPOINT_REFS),
        "security_review_refs": [
            "security-review:m148:readme",
            "security-review:m148:safety-overview",
        ],
        "threat_model_refs": [
            "threat-model:m148:landing-index",
            "threat-model:m148:no-upload",
        ],
        "review_scope_refs": [
            "review-scope:m148:evidence-index-entry",
            "review-scope:m148:no-generated-site",
        ],
        "evidence_index_refs": [
            "evidence-index:m148:security-reviews",
            "evidence-index:m148:threat-model",
        ],
        "finding_summary_refs": [
            "finding-summary:m148:checkpoint",
            "finding-summary:m148:no-release-publish",
        ],
        "disclosure_review_refs": [
            "disclosure-review:m148:authority-boundary",
            "disclosure-review:m148:no-sensitive-content",
        ],
        "remediation_plan_refs": [
            "remediation-plan:m148:manual-review",
            "remediation-plan:m148:no-automation",
        ],
        "audit_ref": "audit:m148:external-security-review",
        "replay_ref": "replay:m148:external-security-review",
        "revocation_ref": "revocation:m148:external-security-review",
        "kill_switch_ref": "kill-switch:m148:external-security-review",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m148:external-security-review:no-effect"
        ),
        "safe_summary": "Record security reviews and threat model refs without external security authority.",
    }
    data.update(overrides)
    return ExternalSecurityReviewRequest(**data)


def test_m148_record_is_contract_only_and_non_authoritative() -> None:
    record = build_external_security_review_record(_request())

    assert record.status == ExternalSecurityReviewStatus.readiness_recorded
    assert record.contract_only is True
    assert record.review_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.external_security_review_only is True
    assert record.disabled_by_default is True
    assert record.m101_m147_covered is True
    assert record.security_reviews_bound is True
    assert record.threat_model_bound is True
    assert record.review_scopes_bound is True
    assert record.evidence_indexes_bound is True
    assert record.finding_summaries_bound is True
    assert record.disclosure_reviews_bound is True
    assert record.remediation_plans_bound is True
    assert record.audit_replay_bound is True
    assert record.revocation_bound is True
    assert record.no_effect_receipt_required is True
    assert record.no_external_vendor_handoff is True
    assert record.no_security_vendor_handoff is True
    assert record.no_external_review_automation is True
    assert record.no_scanner_runtime is True
    assert record.no_vulnerability_scan is True
    assert record.no_repository_export is True
    assert record.no_artifact_export is True
    assert record.no_issue_export is True
    assert record.no_security_review_runtime is True
    assert record.no_auth_runtime is True
    assert record.no_backend_route is True
    assert record.no_control_center_control is True
    assert record.no_dependency is True
    assert record.no_production_authority is True
    assert record.accepted_checkpoint_refs == list(
        REQUIRED_M148_ACCEPTED_CHECKPOINT_REFS
    )
    assert record.external_vendor_handoff_started is False
    assert record.security_vendor_handoff_started is False
    assert record.external_review_automation_started is False
    assert record.scanner_runtime_performed is False
    assert record.vulnerability_scan_started is False
    assert record.repository_export_performed is False
    assert record.artifact_export_started is False
    assert record.issue_export_started is False
    assert record.security_review_runtime_performed is False
    assert record.auth_runtime_started is False
    assert record.login_enabled is False
    assert record.connector_runtime_started is False
    assert record.plugin_marketplace_runtime_started is False
    assert record.execution_performed is False
    assert record.tool_execution_performed is False
    assert record.network_access_performed is False
    assert record.backend_route_added is False
    assert record.control_center_control_added is False
    assert record.dependency_added is False
    assert record.beta_release_enabled is False
    assert record.production_authority_granted is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M148_EXTERNAL_SECURITY_REVIEW_REVIEW_ONLY",
        "M148_M101_M147_COVERED",
        "M148_DISABLED_BY_DEFAULT",
        "M148_NO_EXTERNAL_VENDOR_HANDOFF",
        "M148_NO_SECURITY_VENDOR_HANDOFF",
        "M148_NO_EXTERNAL_REVIEW_AUTOMATION",
        "M148_NO_SCANNER_RUNTIME",
        "M148_NO_VULNERABILITY_SCAN",
        "M148_NO_REPOSITORY_EXPORT",
        "M148_NO_ARTIFACT_EXPORT",
        "M148_NO_ISSUE_EXPORT",
        "M148_NO_SECURITY_REVIEW_RUNTIME",
        "M148_NO_AUTH_RUNTIME",
        "M148_NO_BACKEND_ROUTE",
        "M148_NO_PRODUCTION_AUTHORITY",
        "M149_REMAINS_FUTURE",
    ]


def test_m148_record_uses_safe_refs_only() -> None:
    record = build_external_security_review_record(_request())

    assert record.record_ref == "external-security-review-record:m148"
    assert record.security_review_ref == "external-security-review:m148"
    assert all(
        ref.startswith("security-review:")
        for ref in record.security_review_refs
    )
    assert all(ref.startswith("threat-model:") for ref in record.threat_model_refs)
    assert all(
        ref.startswith("review-scope:")
        for ref in record.review_scope_refs
    )
    assert all(ref.startswith("evidence-index:") for ref in record.evidence_index_refs)
    assert all(
        ref.startswith("finding-summary:")
        for ref in record.finding_summary_refs
    )
    assert all(
        ref.startswith("disclosure-review:")
        for ref in record.disclosure_review_refs
    )
    assert all(
        ref.startswith("remediation-plan:")
        for ref in record.remediation_plan_refs
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
        ("external_vendor_handoff_enabled", "M148_EXTERNAL_VENDOR_HANDOFF_DENIED"),
        ("security_vendor_handoff_enabled", "M148_SECURITY_VENDOR_HANDOFF_DENIED"),
        ("external_review_automation_enabled", "M148_EXTERNAL_REVIEW_AUTOMATION_DENIED"),
        ("scanner_runtime_enabled", "M148_SCANNER_RUNTIME_DENIED"),
        ("vulnerability_scan_enabled", "M148_VULNERABILITY_SCAN_DENIED"),
        ("repository_export_enabled", "M148_REPOSITORY_EXPORT_DENIED"),
        ("artifact_export_enabled", "M148_ARTIFACT_EXPORT_DENIED"),
        ("issue_export_enabled", "M148_ISSUE_EXPORT_DENIED"),
        ("security_review_runtime_enabled", "M148_SECURITY_REVIEW_RUNTIME_DENIED"),
        ("auth_runtime_enabled", "M148_AUTH_RUNTIME_DENIED"),
        ("login_enabled", "M148_LOGIN_DENIED"),
        ("connector_runtime_enabled", "M148_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_enabled",
            "M148_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("tool_execution_enabled", "M148_TOOL_EXECUTION_DENIED"),
        ("network_access_enabled", "M148_NETWORK_ACCESS_DENIED"),
        ("backend_route_enabled", "M148_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M148_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M148_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M148_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m148_policy_denies_authority_expansion(field, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_external_security_review_policy(
            ExternalSecurityReviewPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("external_vendor_handoff_requested", "M148_EXTERNAL_VENDOR_HANDOFF_DENIED"),
        ("security_vendor_handoff_requested", "M148_SECURITY_VENDOR_HANDOFF_DENIED"),
        ("external_review_automation_requested", "M148_EXTERNAL_REVIEW_AUTOMATION_DENIED"),
        ("scanner_runtime_requested", "M148_SCANNER_RUNTIME_DENIED"),
        ("vulnerability_scan_requested", "M148_VULNERABILITY_SCAN_DENIED"),
        ("repository_export_requested", "M148_REPOSITORY_EXPORT_DENIED"),
        ("artifact_export_requested", "M148_ARTIFACT_EXPORT_DENIED"),
        ("issue_export_requested", "M148_ISSUE_EXPORT_DENIED"),
        ("auth_runtime_requested", "M148_AUTH_RUNTIME_DENIED"),
        ("connector_runtime_requested", "M148_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_requested",
            "M148_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("contains_raw_private_content", "M148_RAW_PRIVATE_CONTENT_DENIED"),
        ("contains_raw_prompt", "M148_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M148_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M148_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M148_SECRET_DENIED"),
        ("backend_route_requested", "M148_BACKEND_ROUTE_DENIED"),
        ("dependency_requested", "M148_DEPENDENCY_DENIED"),
        ("production_authority_requested", "M148_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m148_request_denies_unsafe_inputs(field, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_external_security_review_request(
            _request().model_copy(update={field: True})
        )


def test_m148_requires_exact_checkpoint_and_safety_refs() -> None:
    with pytest.raises(ValueError, match="M148_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_external_security_review_request(
            _request(accepted_checkpoint_refs=[])
        )

    with pytest.raises(ValueError, match="M148_CHECKPOINT_REF_REQUIRED"):
        validate_external_security_review_request(
            _request(accepted_checkpoint_refs=["checkpoint:m101"])
        )

    with pytest.raises(ValueError, match="M148_CHECKPOINT_REF_UNEXPECTED"):
        validate_external_security_review_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M148_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m148",
                ]
            )
        )

    for field, reason in [
        ("security_review_refs", "M148_SECURITY_REVIEW_REF_REQUIRED"),
        ("threat_model_refs", "M148_THREAT_MODEL_REF_REQUIRED"),
        ("review_scope_refs", "M148_REVIEW_SCOPE_REF_REQUIRED"),
        ("evidence_index_refs", "M148_EVIDENCE_INDEX_REF_REQUIRED"),
        ("finding_summary_refs", "M148_FINDING_SUMMARY_REF_REQUIRED"),
        ("disclosure_review_refs", "M148_DISCLOSURE_REVIEW_REF_REQUIRED"),
        ("remediation_plan_refs", "M148_REMEDIATION_PLAN_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_external_security_review_request(_request(**{field: []}))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"external_vendor_handoff_started": True}, "M148_EXTERNAL_VENDOR_HANDOFF_DENIED"),
        ({"security_vendor_handoff_started": True}, "M148_SECURITY_VENDOR_HANDOFF_DENIED"),
        ({"external_review_automation_started": True}, "M148_EXTERNAL_REVIEW_AUTOMATION_DENIED"),
        ({"scanner_runtime_performed": True}, "M148_SCANNER_RUNTIME_DENIED"),
        ({"vulnerability_scan_started": True}, "M148_VULNERABILITY_SCAN_DENIED"),
        (
            {"repository_export_performed": True},
            "M148_REPOSITORY_EXPORT_DENIED",
        ),
        (
            {"artifact_export_started": True},
            "M148_ARTIFACT_EXPORT_DENIED",
        ),
        ({"issue_export_started": True}, "M148_ISSUE_EXPORT_DENIED"),
        ({"security_review_runtime_performed": True}, "M148_SECURITY_REVIEW_RUNTIME_DENIED"),
        ({"auth_runtime_started": True}, "M148_AUTH_RUNTIME_DENIED"),
        ({"backend_route_added": True}, "M148_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M148_DEPENDENCY_DENIED"),
        ({"beta_release_enabled": True}, "M148_BETA_RELEASE_DENIED"),
        ({"production_authority_granted": True}, "M148_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m148_record_denies_unsafe_mutations(update, reason) -> None:
    record = build_external_security_review_record(_request())

    with pytest.raises(ValueError, match=reason):
        validate_external_security_review_record(record.model_copy(update=update))


def test_m148_denies_side_effect_receipts_and_secret_like_metadata() -> None:
    with pytest.raises(ValueError, match="M148_SIDE_EFFECTS_DENIED"):
        validate_external_security_review_request(
            _request(side_effects_performed=["exported security packet"])
        )

    record = build_external_security_review_record(_request())
    with pytest.raises(ValueError, match="M148_SIDE_EFFECTS_DENIED"):
        validate_external_security_review_record(
            record.model_copy(update={"side_effects_performed": ["deployed docs site"]})
        )

    with pytest.raises(ValueError, match="M148_SECRET_LIKE_SECURITY_REVIEW_CONTENT_DENIED"):
        validate_external_security_review_policy(
            ExternalSecurityReviewPolicy(metadata={"api_key": "x"})
        )
