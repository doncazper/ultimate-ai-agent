from pathlib import Path

import pytest

import scripts.verify_documentation_integrity as docs_verifier
import scripts.verify_all as static_verifier
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator


def test_post_m100_documentation_integrity_guard_accepts_current_repo() -> None:
    failures = docs_verifier._verify_post_m100_roadmap_reconciliation_docs(
        docs_verifier.ROOT,
        "1.7.2",
    )

    assert failures == []


def test_post_m100_documentation_integrity_guard_rejects_sensor_runtime_claim(
    tmp_path: Path,
) -> None:
    _copy_minimal_post_m100_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8")
        + (
            "\nThis sentence intentionally claims unsafe runtime. "
            "Mobile sensor runtime is implemented.\n"
        ),
        encoding="utf-8",
    )

    failures = docs_verifier._verify_post_m100_roadmap_reconciliation_docs(
        tmp_path,
        "1.6.0",
    )

    assert any("mobile sensor runtime is implemented" in failure.lower() for failure in failures)


def test_post_m100_documentation_integrity_guard_rejects_missing_row_status(
    tmp_path: Path,
) -> None:
    _copy_minimal_post_m100_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            "| Checkpoint M127 | pre-alpha checkpoint | M127 | Connector Write Dry-Run Planner | Planned/provisional |",
            "| Checkpoint M127 | pre-alpha checkpoint | M127 | Connector Write Dry-Run Planner | Deferred |",
        ),
        encoding="utf-8",
    )

    failures = docs_verifier._verify_post_m100_roadmap_reconciliation_docs(
        tmp_path,
        "1.6.0",
    )

    assert any("m127" in failure.lower() for failure in failures)
    assert any("planned/provisional" in failure.lower() for failure in failures)


def test_post_m100_documentation_integrity_guard_allows_negated_future_claim(
    tmp_path: Path,
) -> None:
    _copy_minimal_post_m100_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8")
        + (
                "\nNo M104 is implemented. Without any evidence, M104 backend route "
                "appears only as a negated safety example. The docs do not say "
                "M105 has started.\n"
        ),
        encoding="utf-8",
    )

    failures = docs_verifier._verify_post_m100_roadmap_reconciliation_docs(
        tmp_path,
        "1.7.2",
    )

    assert failures == []


def test_post_m100_static_verifier_accepts_current_repo() -> None:
    static_verifier.verify_post_m100_roadmap_reconciliation()


def test_post_m100_static_verifier_rejects_missing_row_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_minimal_post_m100_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            "| Checkpoint M136 | pre-alpha checkpoint | M136 | Cross-Tool Dependency Execution | Planned/provisional |",
            "| Checkpoint M136 | pre-alpha checkpoint | M136 | Cross-Tool Dependency Execution | Deferred |",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(static_verifier, "ROOT", tmp_path)

    with pytest.raises(SystemExit):
        static_verifier.verify_post_m100_roadmap_reconciliation()


def test_post_m100_static_verifier_allows_negated_future_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_minimal_post_m100_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8")
        + "\nThere is never evidence that M136 has started in v1.4.1.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(static_verifier, "ROOT", tmp_path)

    static_verifier.verify_post_m100_roadmap_reconciliation()


def test_post_m100_foundation_gate_criterion_registered_and_passes() -> None:
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    assert "post_m100_roadmap_reconciliation" in criteria
    result = FoundationGateEvaluator().evaluate(
        [criteria["post_m100_roadmap_reconciliation"]]
    ).results[0]

    assert result.status == "passed", result.failures


def test_post_m100_foundation_gate_rejects_missing_row_status(tmp_path: Path) -> None:
    _copy_minimal_post_m100_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            "| Checkpoint M129 | pre-alpha checkpoint | M129 | Connector Audit + Revocation Hardening | Planned/provisional |",
            "| Checkpoint M129 | pre-alpha checkpoint | M129 | Connector Audit + Revocation Hardening | Deferred |",
        ),
        encoding="utf-8",
    )
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    result = FoundationGateEvaluator(root=tmp_path).evaluate(
        [criteria["post_m100_roadmap_reconciliation"]]
    ).results[0]

    assert result.status == "failed"
    assert any("m129" in failure.lower() for failure in result.failures)


def test_post_m100_foundation_gate_allows_negated_future_claim(tmp_path: Path) -> None:
    _copy_minimal_post_m100_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8")
        + (
            "\nNo M103 is implemented. There is never evidence that M104 is "
            "implemented. This does not say M105 has started.\n"
        ),
        encoding="utf-8",
    )
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    result = FoundationGateEvaluator(root=tmp_path).evaluate(
        [criteria["post_m100_roadmap_reconciliation"]]
    ).results[0]

    assert result.status == "passed", result.failures


def test_post_m100_documentation_integrity_guard_rejects_stale_beta_mapping(
    tmp_path: Path,
) -> None:
    _copy_minimal_post_m100_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8")
        + "\n| v1.54.0 | M150 | Ultimate AI Agent Beta 1 | Planned/provisional |\n",
        encoding="utf-8",
    )

    failures = docs_verifier._verify_post_m100_roadmap_reconciliation_docs(
        tmp_path,
        "1.7.2",
    )

    assert any("stale m150 beta" in failure.lower() for failure in failures)


def test_post_m100_documentation_integrity_guard_rejects_future_semver_rows(
    tmp_path: Path,
) -> None:
    _copy_minimal_post_m100_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8")
        + "\n| v1.7.2 | pre-alpha | M104 | Notification Planning, No Push Execution | Planned/provisional |\n",
        encoding="utf-8",
    )

    failures = docs_verifier._verify_post_m100_roadmap_reconciliation_docs(
        tmp_path,
        "1.7.2",
    )

    assert any("future milestone semver row" in failure.lower() for failure in failures)


def test_post_m100_static_verifier_rejects_future_semver_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_minimal_post_m100_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8")
        + "\n| v1.7.48 | v1.0.0-alpha | M150 | Ultimate AI Agent v1.0.0-alpha | Planned/provisional |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(static_verifier, "ROOT", tmp_path)

    with pytest.raises(SystemExit):
        static_verifier.verify_post_m100_roadmap_reconciliation()


def _copy_minimal_post_m100_docs(root: Path) -> None:
    for rel_path in [
        "README.md",
        "VERSION.md",
        "docs/canonical/09_roadmap.md",
        "docs/roadmap/README.md",
        "docs/roadmap/MILESTONE_CHARTERS.md",
        "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
        "tests/test_post_m100_roadmap_reconciliation.py",
        *docs_verifier.REQUIRED_POST_M100_RECONCILIATION_DOCS,
    ]:
        src = docs_verifier.ROOT / rel_path
        dst = root / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            dst.write_text("v1.4.1 post-M100 placeholder\n", encoding="utf-8")
