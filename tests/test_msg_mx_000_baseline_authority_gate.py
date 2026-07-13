from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts import verify_msg_mx_000_baseline_authority_gate as gate


ROOT = Path(__file__).resolve().parents[1]


def _tamper(
    source: Path,
    destination: Path,
    transform: Callable[[str], str],
) -> Path:
    destination.write_text(transform(source.read_text(encoding="utf-8")), encoding="utf-8")
    return destination


def _patch_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    path_attr: str,
    transform: Callable[[str], str],
) -> None:
    source = getattr(gate, path_attr)
    path = _tamper(source, tmp_path / f"{path_attr.lower()}.md", transform)
    monkeypatch.setattr(gate, path_attr, path)


def test_msg_mx_000_baseline_authority_gate_passes() -> None:
    assert gate.verify() == []


def test_verifier_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / gate.VERIFIER_REF)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "verification passed" in result.stdout


def test_ledgers_and_sections_are_exact_and_ordered() -> None:
    text = gate.MAP_PATH.read_text(encoding="utf-8")
    failures: list[str] = []
    rows = gate._extract_ledger(text, failures)
    lane_rows = gate._extract_lane_ledger(text, failures)
    sections = gate._extract_sections(text, failures)
    assert failures == []
    assert tuple(tuple(row) for row in rows) == gate.EXPECTED_MILESTONE_ROWS
    assert [milestone for milestone, _ in sections] == list(gate.EXPECTED_MILESTONES)
    assert len(lane_rows) == sum(len(refs) for refs in gate.EXPECTED_LANE_REFS.values())


def test_runtime_sections_use_exact_canonical_fail_closed_values() -> None:
    text = gate.MAP_PATH.read_text(encoding="utf-8")
    failures: list[str] = []
    for milestone, body in gate._extract_sections(text, failures):
        if 4 <= int(milestone.rsplit("-", 1)[1]) <= 10:
            values = gate._status_values(milestone, body, failures)
            for field, expected in gate.RUNTIME_STATUS.items():
                assert values[field] == expected
    assert failures == []


def test_missing_required_field_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "- Safe-disable status: `unknown`.",
            "- Safe-disable posture omitted.",
            1,
        ),
    )
    assert any("Safe-disable status field" in failure for failure in gate.verify())


def test_status_field_trailing_claim_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "- Derived readiness: `unknown`.",
            "- Derived readiness: `unknown`; ready and may execute.",
            1,
        ),
    )
    assert any("value-only Derived readiness" in failure for failure in gate.verify())


def test_duplicate_milestone_section_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            gate.SECTION_MARKERS[1],
            "### MSG-MX-012\n\n" + gate.SECTION_MARKERS[1],
            1,
        ),
    )
    assert any("rendered, ordered, and unique" in failure for failure in gate.verify())


@pytest.mark.parametrize("wrapper", ("```text\n", "<!-- hidden\n"))
def test_non_rendered_milestone_sections_fail_closed(
    wrapper: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "### MSG-MX-004",
            f"{wrapper}### MSG-MX-004",
            1,
        ),
    )
    assert any("rendered" in failure for failure in gate.verify())


def test_heading_after_section_boundary_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text + "\n### MSG-MX-012\n",
    )
    assert any("rendered, ordered, and unique" in failure for failure in gate.verify())


def test_milestone_declaration_promotion_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "| MSG-MX-004 | planned |",
            "| MSG-MX-004 | implemented |",
            1,
        ),
    )
    assert "milestone ledger differs from the immutable baseline" in gate.verify()


def test_runtime_readiness_promotion_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "- Derived readiness: `unknown`.",
            "- Derived readiness: `ready`.",
            1,
        ),
    )
    assert any("Derived readiness" in failure for failure in gate.verify())


def test_planned_lane_membership_change_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace("planned-lane-ref:matrix:harness-smoke", "removed-lane", 1),
    )
    assert any("membership, ownership, or order" in failure for failure in gate.verify())


def test_planned_lane_positive_status_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "| unsupported | unknown | not_configured | unknown | blocked | "
            "unknown | unknown | unknown | unknown | unknown | self-bound-profile |",
            "| supported | supported | configured | healthy | blocked | "
            "available | not_metered | ready | inactive | current | self-bound-profile |",
            1,
        ),
    )
    assert any("planned lane does not fail closed" in failure for failure in gate.verify())


def test_planned_lane_binding_substitution_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "taxonomy_gap / read | disabled harness / exact service ref | "
            "gap: local service inspection",
            "shell / admin | live global adapter / wildcard target | none",
            1,
        ),
    )
    assert any("full bindings differ" in failure for failure in gate.verify())
