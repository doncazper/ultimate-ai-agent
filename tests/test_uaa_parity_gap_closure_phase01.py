from pathlib import Path

from scripts import verify_uaa_parity_gap_closure_phase01 as phase01


REPORT = Path(phase01.REPORT_REF)


def _report() -> str:
    return REPORT.read_text(encoding="utf-8")


def test_phase01_ledger_passes_current_repository() -> None:
    assert phase01.verify() == []


def test_phase01_ledger_has_every_coverage_id_exactly_once() -> None:
    rows = list(phase01.ROW.finditer(_report()))

    assert tuple(row.group("id") for row in rows) == phase01.EXPECTED_IDS
    assert len(rows) == 54
    assert {row.group("status") for row in rows} <= phase01.ALLOWED_STATUSES


def test_phase01_ledger_rejects_duplicate_or_missing_id() -> None:
    report = _report()
    duplicated = report.replace("| H02 |", "| H01 |", 1)

    failures = phase01.verify(report_text=duplicated, check_refs=False)

    assert any("all 54 IDs exactly once" in failure for failure in failures)


def test_phase01_ledger_rejects_unknown_status() -> None:
    report = _report().replace("`planned_only`", "`looks_done`", 1)

    failures = phase01.verify(report_text=report, check_refs=False)

    assert any("invalid status" in failure for failure in failures)


def test_phase01_ledger_requires_proof_for_merged_proven_rows() -> None:
    report = _report().replace(
        "`.github/workflows/ci.yml`; `scripts/verification/verify_ci_evidence_dag.py`; `tests/test_ci_workflow.py`; `tests/test_ci_command_manifest.py`",
        "`docs/developer/CI_EVIDENCE_DAG_ARCHITECTURE.md`",
        1,
    )

    failures = phase01.verify(report_text=report, check_refs=False)

    assert any(
        "merged_proven status lacks focused test proof" in failure
        for failure in failures
    )
    assert any(
        "merged_proven status lacks implementation or operator proof" in failure
        for failure in failures
    )
    assert any("P10 merged_proven proof drifted" in failure for failure in failures)


def test_phase01_ledger_rejects_status_promotion_without_item_proof() -> None:
    report = _report().replace(
        "| H01 | `outcome:persistent-goal-lifecycle` | 04 | `planned_only` |",
        "| H01 | `outcome:persistent-goal-lifecycle` | 04 | `merged_proven` |",
        1,
    ).replace(
        "| durable goal store, lifecycle, API/CLI/UI, receipts |",
        "| none; unrelated proof is not sufficient |",
        1,
    )

    failures = phase01.verify(report_text=report, check_refs=False)

    assert any("H01 status drifted" in failure for failure in failures)


def test_phase01_ledger_rejects_cross_item_merged_proof() -> None:
    report = _report().replace(
        "`.github/workflows/ci.yml`; `scripts/verification/verify_ci_evidence_dag.py`; `tests/test_ci_workflow.py`; `tests/test_ci_command_manifest.py`",
        "`.github/workflows/supply-chain.yml`; `uv.lock`; `apps/control-center/package-lock.json`; `tests/test_supply_chain_workflow.py`",
        1,
    )

    failures = phase01.verify(report_text=report, check_refs=False)

    assert any("P10 merged_proven proof drifted" in failure for failure in failures)


def test_phase01_ledger_validates_root_level_proof_refs() -> None:
    report = _report().replace("`uv.lock`", "`missing-root-proof.lock`", 1)

    failures = phase01.verify(report_text=report, check_refs=True)

    assert "ledger proof ref is missing: missing-root-proof.lock" in failures


def test_phase01_ledger_validates_root_level_ledger_refs() -> None:
    report = _report().replace("`Makefile`", "`MISSING.md`", 1)

    failures = phase01.verify(report_text=report, check_refs=True)

    assert "ledger proof ref is missing: MISSING.md" in failures


def test_phase01_ledger_rejects_unresolved_merged_proven_delta() -> None:
    report = _report().replace(
        "none; preserve eight shards",
        "frontend proof remains; preserve eight shards",
        1,
    )

    failures = phase01.verify(report_text=report, check_refs=False)

    assert any("retains an unresolved delta" in failure for failure in failures)


def test_phase01_ledger_rejects_absolute_local_paths() -> None:
    report = _report() + "\nEvidence captured at /tmp/operator-checkout.\n"

    failures = phase01.verify(report_text=report, check_refs=False)

    assert "ledger contains an absolute local path" in failures


def test_phase01_ledger_rejects_arbitrary_posix_local_paths() -> None:
    for path in ("/nix/store/local-proof", "/project/checkout/private-proof"):
        failures = phase01.verify(
            report_text=_report() + f"\nEvidence captured at {path}.\n",
            check_refs=False,
        )

        assert "ledger contains an absolute local path" in failures


def test_phase01_ledger_rejects_traversal_proof_refs() -> None:
    report = _report().replace(
        "`docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`",
        "`docs/../../../../etc/passwd`",
        1,
    )

    failures = phase01.verify(report_text=report, check_refs=True)

    assert "ledger proof ref is unsafe: docs/../../../../etc/passwd" in failures


def test_phase01_proof_path_rejects_symlink_and_backslash_escape(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repository = tmp_path / "repository"
    outside = tmp_path / "outside"
    repository.mkdir()
    outside.mkdir()
    (outside / "proof.md").write_text("outside", encoding="utf-8")
    (repository / "docs").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(phase01, "ROOT", repository)

    assert phase01._repo_path("docs/proof.md") is None
    assert phase01._repo_path(r"docs\..\proof.md") is None


def test_phase01_ledger_rejects_alias_drift() -> None:
    report = _report().replace(
        "`outcome:persistent-goal-lifecycle`: H01, O01, L06",
        "`outcome:persistent-goal-lifecycle`: H01, O01",
        1,
    )

    failures = phase01.verify(report_text=report, check_refs=False)

    assert "canonical alias graph drifted" in failures


def test_phase01_ledger_rejects_dependency_graph_drift() -> None:
    report = _report().replace(
        "- Phase 04 precedes Phases 05, 06, 08, 09, and 10.\n",
        "",
        1,
    )

    failures = phase01.verify(report_text=report, check_refs=False)

    assert "phase dependency graph drifted" in failures


def test_phase01_ledger_rejects_per_id_phase_drift() -> None:
    report = _report().replace(
        "| H01 | `outcome:persistent-goal-lifecycle` | 04 |",
        "| H01 | `outcome:persistent-goal-lifecycle` | 09 |",
        1,
    )

    failures = phase01.verify(report_text=report, check_refs=False)

    assert any("H01 phase drifted" in failure for failure in failures)


def test_phase01_ledger_rejects_execution_prerequisite_drift() -> None:
    report = _report().replace(
        "| 08 | ready after 04/06/07 | performance; preserve proven P10/L14 |",
        "| 08 | ready | performance; preserve proven P10/L14 |",
        1,
    )

    failures = phase01.verify(report_text=report, check_refs=False)

    assert "phase execution ledger drifted" in failures


def test_phase01_ledger_rejects_unresolved_inventory_placeholders() -> None:
    report = _report().replace("commit:", "commit:INVENTORY_SHA-", 1)

    failures = phase01.verify(report_text=report, check_refs=False)

    assert any("INVENTORY_SHA" in failure for failure in failures)


def test_phase01_ledger_requires_exact_inventory_and_baseline_anchors() -> None:
    report = _report().replace(
        phase01.EXPECTED_INVENTORY_BASE,
        "0000000000000000000000000000000000000000",
        1,
    ).replace(phase01.EXPECTED_ACTIVE_BASELINE, "v0.0.0", 1)

    failures = phase01.verify(report_text=report, check_refs=False)

    assert any("Inventory base" in failure for failure in failures)
    assert any("Active baseline" in failure for failure in failures)
