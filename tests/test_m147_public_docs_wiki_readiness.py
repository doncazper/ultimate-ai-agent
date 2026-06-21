from typing import Any
import pytest

from ultimate_ai_agent.core.productization import (
    REQUIRED_M147_ACCEPTED_CHECKPOINT_REFS,
    PublicDocsWikiReadinessPolicy,
    PublicDocsWikiReadinessRequest,
    PublicDocsWikiReadinessStatus,
    build_public_docs_wiki_readiness_record,
    validate_public_docs_wiki_readiness_policy,
    validate_public_docs_wiki_readiness_record,
    validate_public_docs_wiki_readiness_request,
)


def _request(**overrides: Any) -> PublicDocsWikiReadinessRequest:
    data = {
        "request_ref": "public-docs-wiki-readiness-request:m147",
        "public_doc_ref": "public-docs-wiki-readiness:m147",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M147_ACCEPTED_CHECKPOINT_REFS),
        "public_doc_refs": [
            "public-doc:m147:readme",
            "public-doc:m147:safety-overview",
        ],
        "wiki_readiness_refs": [
            "wiki-readiness:m147:landing-index",
            "wiki-readiness:m147:no-upload",
        ],
        "docs_index_refs": [
            "docs-index:m147:canonical-map-entry",
            "docs-index:m147:no-generated-site",
        ],
        "canonical_map_refs": [
            "canonical-map:m147:public-docs",
            "canonical-map:m147:wiki-readiness",
        ],
        "release_note_refs": [
            "release-note:m147:checkpoint",
            "release-note:m147:no-release-publish",
        ],
        "disclosure_review_refs": [
            "disclosure-review:m147:authority-boundary",
            "disclosure-review:m147:no-sensitive-content",
        ],
        "publishing_checklist_refs": [
            "publishing-checklist:m147:manual-review",
            "publishing-checklist:m147:no-automation",
        ],
        "audit_ref": "audit:m147:public-docs-wiki-readiness",
        "replay_ref": "replay:m147:public-docs-wiki-readiness",
        "revocation_ref": "revocation:m147:public-docs-wiki-readiness",
        "kill_switch_ref": "kill-switch:m147:public-docs-wiki-readiness",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m147:public-docs-wiki-readiness:no-effect"
        ),
        "safe_summary": "Record public docs and wiki readiness refs without publishing authority.",
    }
    data.update(overrides)
    return PublicDocsWikiReadinessRequest(**data)


def test_m147_record_is_contract_only_and_non_authoritative() -> None:
    record = build_public_docs_wiki_readiness_record(_request())

    assert record.status == PublicDocsWikiReadinessStatus.readiness_recorded
    assert record.contract_only is True
    assert record.review_only is True
    assert record.deterministic is True
    assert record.local_only is True
    assert record.safe_refs_only is True
    assert record.docs_readiness_only is True
    assert record.disabled_by_default is True
    assert record.m101_m146_covered is True
    assert record.public_docs_bound is True
    assert record.wiki_readiness_bound is True
    assert record.docs_indexes_bound is True
    assert record.canonical_maps_bound is True
    assert record.release_notes_bound is True
    assert record.disclosure_reviews_bound is True
    assert record.publishing_checklists_bound is True
    assert record.audit_replay_bound is True
    assert record.revocation_bound is True
    assert record.no_effect_receipt_required is True
    assert record.no_public_publish is True
    assert record.no_wiki_publish is True
    assert record.no_wiki_automation is True
    assert record.no_github_wiki_runtime is True
    assert record.no_docs_site_deploy is True
    assert record.no_external_distribution is True
    assert record.no_artifact_upload is True
    assert record.no_release_publish is True
    assert record.no_docs_runtime is True
    assert record.no_auth_runtime is True
    assert record.no_backend_route is True
    assert record.no_control_center_control is True
    assert record.no_dependency is True
    assert record.no_production_authority is True
    assert record.accepted_checkpoint_refs == list(
        REQUIRED_M147_ACCEPTED_CHECKPOINT_REFS
    )
    assert record.public_publish_started is False
    assert record.wiki_publish_started is False
    assert record.wiki_automation_started is False
    assert record.github_wiki_runtime_performed is False
    assert record.docs_site_deploy_started is False
    assert record.external_distribution_performed is False
    assert record.artifact_upload_started is False
    assert record.release_publish_started is False
    assert record.docs_runtime_performed is False
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
        "M147_PUBLIC_DOCS_WIKI_READINESS_REVIEW_ONLY",
        "M147_M101_M146_COVERED",
        "M147_DISABLED_BY_DEFAULT",
        "M147_NO_PUBLIC_PUBLISH",
        "M147_NO_WIKI_PUBLISH",
        "M147_NO_WIKI_AUTOMATION",
        "M147_NO_GITHUB_WIKI_RUNTIME",
        "M147_NO_DOCS_SITE_DEPLOY",
        "M147_NO_EXTERNAL_DISTRIBUTION",
        "M147_NO_ARTIFACT_UPLOAD",
        "M147_NO_RELEASE_PUBLISH",
        "M147_NO_DOCS_RUNTIME",
        "M147_NO_AUTH_RUNTIME",
        "M147_NO_BACKEND_ROUTE",
        "M147_NO_PRODUCTION_AUTHORITY",
        "M148_REMAINS_FUTURE",
    ]


def test_m147_record_uses_safe_refs_only() -> None:
    record = build_public_docs_wiki_readiness_record(_request())

    assert record.record_ref == "public-docs-wiki-readiness-record:m147"
    assert record.public_doc_ref == "public-docs-wiki-readiness:m147"
    assert all(
        ref.startswith("public-doc:")
        for ref in record.public_doc_refs
    )
    assert all(ref.startswith("wiki-readiness:") for ref in record.wiki_readiness_refs)
    assert all(
        ref.startswith("docs-index:")
        for ref in record.docs_index_refs
    )
    assert all(ref.startswith("canonical-map:") for ref in record.canonical_map_refs)
    assert all(
        ref.startswith("release-note:")
        for ref in record.release_note_refs
    )
    assert all(
        ref.startswith("disclosure-review:")
        for ref in record.disclosure_review_refs
    )
    assert all(
        ref.startswith("publishing-checklist:")
        for ref in record.publishing_checklist_refs
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
        ("public_publish_enabled", "M147_PUBLIC_PUBLISH_DENIED"),
        ("wiki_publish_enabled", "M147_WIKI_PUBLISH_DENIED"),
        ("wiki_automation_enabled", "M147_WIKI_AUTOMATION_DENIED"),
        ("github_wiki_runtime_enabled", "M147_GITHUB_WIKI_RUNTIME_DENIED"),
        ("docs_site_deploy_enabled", "M147_DOCS_SITE_DEPLOY_DENIED"),
        ("external_distribution_enabled", "M147_EXTERNAL_DISTRIBUTION_DENIED"),
        ("artifact_upload_enabled", "M147_ARTIFACT_UPLOAD_DENIED"),
        ("release_publish_enabled", "M147_RELEASE_PUBLISH_DENIED"),
        ("docs_runtime_enabled", "M147_DOCS_RUNTIME_DENIED"),
        ("auth_runtime_enabled", "M147_AUTH_RUNTIME_DENIED"),
        ("login_enabled", "M147_LOGIN_DENIED"),
        ("connector_runtime_enabled", "M147_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_enabled",
            "M147_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("tool_execution_enabled", "M147_TOOL_EXECUTION_DENIED"),
        ("network_access_enabled", "M147_NETWORK_ACCESS_DENIED"),
        ("backend_route_enabled", "M147_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M147_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M147_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M147_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m147_policy_denies_authority_expansion(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_public_docs_wiki_readiness_policy(
            PublicDocsWikiReadinessPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("public_publish_requested", "M147_PUBLIC_PUBLISH_DENIED"),
        ("wiki_publish_requested", "M147_WIKI_PUBLISH_DENIED"),
        ("wiki_automation_requested", "M147_WIKI_AUTOMATION_DENIED"),
        ("github_wiki_runtime_requested", "M147_GITHUB_WIKI_RUNTIME_DENIED"),
        ("docs_site_deploy_requested", "M147_DOCS_SITE_DEPLOY_DENIED"),
        ("external_distribution_requested", "M147_EXTERNAL_DISTRIBUTION_DENIED"),
        ("artifact_upload_requested", "M147_ARTIFACT_UPLOAD_DENIED"),
        ("release_publish_requested", "M147_RELEASE_PUBLISH_DENIED"),
        ("auth_runtime_requested", "M147_AUTH_RUNTIME_DENIED"),
        ("connector_runtime_requested", "M147_CONNECTOR_RUNTIME_DENIED"),
        (
            "plugin_marketplace_runtime_requested",
            "M147_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
        ),
        ("contains_raw_private_content", "M147_RAW_PRIVATE_CONTENT_DENIED"),
        ("contains_raw_prompt", "M147_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_raw_provider_payload", "M147_RAW_PROMPT_PAYLOAD_DENIED"),
        ("contains_cookie_or_credential", "M147_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("contains_secret", "M147_SECRET_DENIED"),
        ("backend_route_requested", "M147_BACKEND_ROUTE_DENIED"),
        ("dependency_requested", "M147_DEPENDENCY_DENIED"),
        ("production_authority_requested", "M147_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m147_request_denies_unsafe_inputs(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_public_docs_wiki_readiness_request(
            _request().model_copy(update={field: True})
        )


def test_m147_requires_exact_checkpoint_and_safety_refs() -> None:
    with pytest.raises(ValueError, match="M147_ACCEPTED_CHECKPOINTS_REQUIRED"):
        validate_public_docs_wiki_readiness_request(
            _request(accepted_checkpoint_refs=[])
        )

    with pytest.raises(ValueError, match="M147_CHECKPOINT_REF_REQUIRED"):
        validate_public_docs_wiki_readiness_request(
            _request(accepted_checkpoint_refs=["checkpoint:m101"])
        )

    with pytest.raises(ValueError, match="M147_CHECKPOINT_REF_UNEXPECTED"):
        validate_public_docs_wiki_readiness_request(
            _request(
                accepted_checkpoint_refs=[
                    *REQUIRED_M147_ACCEPTED_CHECKPOINT_REFS,
                    "checkpoint:m147",
                ]
            )
        )

    for field, reason in [
        ("public_doc_refs", "M147_PUBLIC_DOC_REF_REQUIRED"),
        ("wiki_readiness_refs", "M147_WIKI_READINESS_REF_REQUIRED"),
        ("docs_index_refs", "M147_DOCS_INDEX_REF_REQUIRED"),
        ("canonical_map_refs", "M147_CANONICAL_MAP_REF_REQUIRED"),
        ("release_note_refs", "M147_RELEASE_NOTE_REF_REQUIRED"),
        ("disclosure_review_refs", "M147_DISCLOSURE_REVIEW_REF_REQUIRED"),
        ("publishing_checklist_refs", "M147_PUBLISHING_CHECKLIST_REF_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_public_docs_wiki_readiness_request(_request(**{field: []}))


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"public_publish_started": True}, "M147_PUBLIC_PUBLISH_DENIED"),
        ({"wiki_publish_started": True}, "M147_WIKI_PUBLISH_DENIED"),
        ({"wiki_automation_started": True}, "M147_WIKI_AUTOMATION_DENIED"),
        ({"github_wiki_runtime_performed": True}, "M147_GITHUB_WIKI_RUNTIME_DENIED"),
        ({"docs_site_deploy_started": True}, "M147_DOCS_SITE_DEPLOY_DENIED"),
        (
            {"external_distribution_performed": True},
            "M147_EXTERNAL_DISTRIBUTION_DENIED",
        ),
        (
            {"artifact_upload_started": True},
            "M147_ARTIFACT_UPLOAD_DENIED",
        ),
        ({"release_publish_started": True}, "M147_RELEASE_PUBLISH_DENIED"),
        ({"docs_runtime_performed": True}, "M147_DOCS_RUNTIME_DENIED"),
        ({"auth_runtime_started": True}, "M147_AUTH_RUNTIME_DENIED"),
        ({"backend_route_added": True}, "M147_BACKEND_ROUTE_DENIED"),
        ({"dependency_added": True}, "M147_DEPENDENCY_DENIED"),
        ({"beta_release_enabled": True}, "M147_BETA_RELEASE_DENIED"),
        ({"production_authority_granted": True}, "M147_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m147_record_denies_unsafe_mutations(update: Any, reason: str) -> None:
    record = build_public_docs_wiki_readiness_record(_request())

    with pytest.raises(ValueError, match=reason):
        validate_public_docs_wiki_readiness_record(record.model_copy(update=update))


def test_m147_denies_side_effect_receipts_and_secret_like_metadata() -> None:
    with pytest.raises(ValueError, match="M147_SIDE_EFFECTS_DENIED"):
        validate_public_docs_wiki_readiness_request(
            _request(side_effects_performed=["published wiki page"])
        )

    record = build_public_docs_wiki_readiness_record(_request())
    with pytest.raises(ValueError, match="M147_SIDE_EFFECTS_DENIED"):
        validate_public_docs_wiki_readiness_record(
            record.model_copy(update={"side_effects_performed": ["deployed docs site"]})
        )

    with pytest.raises(ValueError, match="M147_SECRET_LIKE_PUBLIC_DOCS_CONTENT_DENIED"):
        validate_public_docs_wiki_readiness_policy(
            PublicDocsWikiReadinessPolicy(metadata={"api_key": "x"})
        )
