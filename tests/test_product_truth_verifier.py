from pathlib import Path

import pytest

import scripts.verify_product_truth as verifier


def _write_text(root: Path, rel_path: str, text: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_product_truth_verifier_clean_scopes_pass(tmp_path: Path) -> None:
    _write_text(
        tmp_path,
        "docs/kanban/current_board.md",
        "\n".join([
            "## UAA-P1-057 Product truth regression checks",
            "Goal: prevent blocked, skipped, pending, mock-only, planned, or not-scoped work",
            "from being described as complete, production-ready, or publicly released.",
            "Status: in progress",
            "Blocked for production-readiness claims.",
            "Planned for frontend render timing.",
        ]),
    )
    _write_text(
        tmp_path,
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "\n".join([
            "| Capability | Status |",
            "|---|---|",
            "| Product shell | Shipped for operator gap map; blocked for product-readiness claims. |",
            "| Local model | Shipped for smoke harness; blocked for production-readiness claims. |",
        ]),
    )

    findings = verifier.validate_product_truth(
        root=tmp_path,
        scopes=(
            "docs/kanban/current_board.md",
            "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        ),
    )

    assert findings == []


def test_product_truth_verifier_flags_blocked_work_claimed_complete(tmp_path: Path) -> None:
    _write_text(
        tmp_path,
        "docs/production/RELEASE_EVIDENCE_PACKET.md",
        "\n".join([
            "The blocked feature is complete.",
            "The mock-only surface is production-ready.",
            "Not-scoped work is shipped.",
        ]),
    )

    findings = verifier.validate_product_truth(
        root=tmp_path,
        scopes=("docs/production/RELEASE_EVIDENCE_PACKET.md",),
    )

    categories = {f.category for f in findings}
    assert "blocked_work_claimed_complete" in categories
    assert "mock_only_work_claimed_complete" in categories
    assert "not_scoped_work_claimed_complete" in categories
    for finding in findings:
        assert finding.evidence_hash.startswith("sha256:")
        # Safe message must not echo the raw offending line content.
        assert "The blocked feature is complete." not in finding.safe_message
        assert "production-ready" not in finding.safe_message


def test_product_truth_verifier_flags_pending_partial_skipped_planned_overclaims(
    tmp_path: Path,
) -> None:
    findings = verifier.scan_text(
        "docs/production/RELEASE_VERIFICATION_LANES.md",
        "\n".join([
            "The pending migration is complete.",
            "The partial implementation is production-ready.",
            "The skipped test suite is passing.",
            "planned milestone is released",
        ]),
    )

    categories = {f.category for f in findings}
    assert "pending_work_claimed_complete" in categories
    assert "partial_work_claimed_complete" in categories
    assert "skipped_work_claimed_passing" in categories
    assert "planned_work_claimed_released" in categories


def test_product_truth_verifier_flags_autonomy_overclaims() -> None:
    findings = verifier.scan_text(
        "README.md",
        "\n".join([
            "The agent is fully autonomous.",
            "The system is broadly autonomous.",
            "It operates autonomously without human oversight.",
            "Autonomous background execution is enabled.",
        ]),
    )

    categories = {f.category for f in findings}
    assert "broad_autonomy_claim" in categories
    assert "autonomous_without_oversight_claim" in categories
    assert "autonomous_execution_enabled_claim" in categories


def test_product_truth_verifier_no_false_positive_on_correct_disclaimer_language() -> None:
    # These are the correct disclaimer forms used throughout the real repo docs.
    clean_lines = [
        "blocked for production-readiness claims",
        "blocked for broader route extraction",
        "blocked for actual release-candidate promotion",
        "blocked for live restore claims",
        "blocked for runtime activation",
        "remains blocked",
        "is blocked",
        "blocked by a missing gate",
        "planned for frontend render timing",
        "planned for future milestones",
        "Planned: not shipped as product behavior",
        "pass/fail/blocked/skipped states are covered",
        "blocked/unknown provenance handling",
        "mock-only not product-ready",
        "partial backend not product ready",
        "no broad autonomy or autonomous background sessions",
        "autonomous background execution, public distribution, remain disabled",
    ]
    for line in clean_lines:
        findings = verifier.scan_text("test.md", line)
        assert findings == [], (
            f"False positive on: {line!r} → categories: "
            f"{[f.category for f in findings]}"
        )


def test_product_truth_verifier_cli_redacts_failure_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sensitive_label = "auth_service_migration"
    _write_text(
        tmp_path,
        "docs/kanban/current_board.md",
        f"The blocked {sensitive_label} work is complete.",
    )

    exit_code = verifier.main([
        "--root", str(tmp_path),
        "--scope", "docs/kanban/current_board.md",
    ])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "blocked_work_claimed_complete" in output
    assert sensitive_label not in output


def test_product_truth_verifier_json_report_structure(tmp_path: Path) -> None:
    _write_text(
        tmp_path,
        "README.md",
        "The system is broadly autonomous.",
    )

    exit_code = verifier.main([
        "--root", str(tmp_path),
        "--scope", "README.md",
        "--json",
    ])

    report = verifier.build_scan_report(
        root=tmp_path,
        scopes=("README.md",),
    )
    assert exit_code == 1
    assert report["schema_version"] == verifier.PRODUCT_TRUTH_SCHEMA_VERSION
    assert report["task_ref"] == verifier.PRODUCT_TRUTH_TASK_REF
    assert report["status"] == "failed"
    assert report["report_safety"]["offending_content_echoed"] is False
    assert report["finding_count"] >= 1
    for finding in report["findings"]:
        assert "broad_autonomy_claim" == finding["category"]
        assert "broadly autonomous" not in finding["safe_message"]
