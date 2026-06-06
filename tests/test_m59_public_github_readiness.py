import pytest

from ultimate_ai_agent.core.public_readiness import (
    PublicGitHubReadinessPolicy,
    PublicGitHubReadinessRequest,
    PublicGitHubReadinessStatus,
    build_public_github_readiness_report,
    validate_public_github_readiness_policy,
    validate_public_github_readiness_request,
)


def _request(**overrides):
    data = {
        "request_ref": "public-readiness-request:m59",
        "readiness_ref": "public-readiness:m59",
        "repository_ref": "repo:ultimate-ai-agent",
        "baseline_ref": "baseline:v0.63.0",
        "actor_ref": "actor:local-reviewer",
        "checklist_refs": [
            "readiness:docs-current",
            "readiness:secret-hygiene",
            "readiness:artifact-hygiene",
            "readiness:route-boundary",
            "readiness:dependency-boundary",
        ],
        "artifact_refs": ["artifact:release-notes-v0.63.0"],
        "safe_summary": "Review public GitHub readiness without publishing anything.",
    }
    data.update(overrides)
    return PublicGitHubReadinessRequest(**data)


def test_public_github_readiness_report_is_review_only_and_no_effect() -> None:
    report = build_public_github_readiness_report(_request())

    assert report.status == PublicGitHubReadinessStatus.reviewed
    assert report.review_only is True
    assert report.publication_performed is False
    assert report.github_push_performed is False
    assert report.github_release_performed is False
    assert report.wiki_automation_performed is False
    assert report.external_service_performed is False
    assert report.production_authority_granted is False
    assert report.side_effects_performed == []
    assert report.reason_codes == ["M59_PUBLIC_GITHUB_READINESS_REVIEW_ONLY"]
    assert report.receipt_plan is not None
    assert report.receipt_plan.side_effects_performed == []
    assert "private key" not in str(report.model_dump()).lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("publication_requested", "PUBLICATION_DENIED"),
        ("github_push_requested", "GITHUB_PUSH_DENIED"),
        ("github_release_requested", "GITHUB_RELEASE_DENIED"),
        ("wiki_automation_requested", "WIKI_AUTOMATION_DENIED"),
        ("artifact_upload_requested", "ARTIFACT_UPLOAD_DENIED"),
        ("external_service_requested", "EXTERNAL_SERVICE_DENIED"),
        ("credential_handling_requested", "CREDENTIAL_HANDLING_DENIED"),
        ("network_access_requested", "NETWORK_ACCESS_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
        ("m60_beta_freeze_requested", "M60_BETA_FREEZE_DENIED"),
    ],
)
def test_public_github_readiness_request_denies_publication_authority_flags(
    field: str, reason: str
) -> None:
    request = _request(**{field: True})

    with pytest.raises(ValueError, match=reason):
        validate_public_github_readiness_request(request)


def test_public_github_readiness_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "publication_requested": True,
            "contains_secret": True,
        }
    )

    with pytest.raises(ValueError, match="PUBLICATION_DENIED"):
        build_public_github_readiness_report(request)


def test_public_github_readiness_requires_stable_checklist_refs() -> None:
    with pytest.raises(ValueError, match="PUBLIC_READINESS_CHECKLIST_REFS_REQUIRED"):
        validate_public_github_readiness_request(_request(checklist_refs=[]))

    with pytest.raises(ValueError, match="PUBLIC_READINESS_CHECKLIST_REF_DUPLICATE"):
        validate_public_github_readiness_request(
            _request(checklist_refs=["readiness:docs-current", "readiness:docs-current"])
        )


def test_public_github_readiness_denies_secret_like_metadata() -> None:
    request = _request(metadata={"token": "abcde12345678901234"})

    with pytest.raises(ValueError, match="SECRET_LIKE_PUBLIC_READINESS_CONTENT_DENIED"):
        build_public_github_readiness_report(request)


def test_public_github_readiness_policy_denies_publication_authority() -> None:
    policy = PublicGitHubReadinessPolicy(
        github_push_enabled=True,
        wiki_automation_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="GITHUB_PUSH_DENIED"):
        validate_public_github_readiness_policy(policy)
