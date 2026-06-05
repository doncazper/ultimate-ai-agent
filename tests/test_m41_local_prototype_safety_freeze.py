import scripts.verify_all as verify_all
import scripts.verify_documentation_integrity as docs_verifier


def test_m41_static_verifier_is_registered() -> None:
    assert (
        "M41 local prototype safety freeze scan",
        "verify_m41_local_prototype_safety_freeze",
    ) in verify_all.SCAN_SEQUENCE
    assert hasattr(verify_all, "verify_m41_local_prototype_safety_freeze")


def test_m41_documentation_integrity_docs_are_registered_and_current_repo_passes() -> None:
    required_docs = set(docs_verifier.REQUIRED_M41_LOCAL_PROTOTYPE_SAFETY_DOCS)

    assert "docs/prototype/LOCAL_PROTOTYPE_SAFETY_FREEZE.md" in required_docs
    assert "docs/prototype/LOCAL_PROTOTYPE_BROWSER_SMOKE_REVIEW.md" in required_docs
    assert "docs/prototype/LOCAL_PROTOTYPE_NO_AUTHORITY_BOUNDARY.md" in required_docs
    assert "docs/prototype/M41_TO_M42_BOUNDARY.md" in required_docs
    assert docs_verifier.verify() == []
