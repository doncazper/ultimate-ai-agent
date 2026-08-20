from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts import verify_queue_v2_q10_parity_rebaseline as q10


LEDGER = Path(q10.LEDGER_REF)
REPORT = Path(q10.REPORT_REF)


def _payload() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _report() -> str:
    return REPORT.read_text(encoding="utf-8")


def test_q10_parity_rebaseline_passes_current_repository() -> None:
    assert q10.verify() == []


def test_q10_parity_rebaseline_has_finite_complete_gap_set() -> None:
    payload = _payload()

    assert tuple(row["gap_id"] for row in payload["gap_rows"]) == q10.EXPECTED_GAPS
    assert len(payload["gap_rows"]) == 18
    assert {row["disposition"] for row in payload["gap_rows"]} == (
        q10.ALLOWED_DISPOSITIONS
    )


def test_q10_rejects_source_revision_drift() -> None:
    payload = copy.deepcopy(_payload())
    payload["comparison_sources"][0]["revision"] = "0" * 40

    failures = q10.verify(payload=payload, check_refs=False)

    assert "hermes source revision drifted" in failures


def test_q10_rejects_unpinned_source_ref() -> None:
    payload = copy.deepcopy(_payload())
    payload["gap_rows"][0]["source_refs"][0] = "hermes:future-feature.md"

    failures = q10.verify(payload=payload, check_refs=False)

    assert any("unpinned source ref" in failure for failure in failures)


def test_q10_rejects_disposition_or_owner_inflation() -> None:
    payload = copy.deepcopy(_payload())
    payload["gap_rows"][0]["disposition"] = "close"
    payload["gap_rows"][0]["owner_refs"] = ["queue-item-ref:Q11"]

    failures = q10.verify(payload=payload, check_refs=False)

    assert "Q10-G01 disposition drifted" in failures
    assert "Q10-G01 owner routing drifted" in failures


def test_q10_rejects_backward_queue_routing() -> None:
    payload = copy.deepcopy(_payload())
    payload["gap_rows"][1]["owner_refs"] = ["queue-item-ref:Q09"]

    failures = q10.verify(payload=payload, check_refs=True)

    assert "Q10-G02 routes backward to Q09" in failures


def test_q10_rejects_missing_uaa_evidence() -> None:
    payload = copy.deepcopy(_payload())
    payload["gap_rows"][0]["uaa_evidence_refs"][0] = "docs/missing-q10-proof.md"

    failures = q10.verify(payload=payload, check_refs=True)

    assert any(
        "UAA evidence ref is missing or unsafe" in failure for failure in failures
    )


def test_q10_rejects_source_path_traversal() -> None:
    payload = copy.deepcopy(_payload())
    payload["comparison_sources"][0]["evidence_paths"][0] = "../private.md"

    failures = q10.verify(payload=payload, check_refs=False)

    assert any("evidence path is unsafe" in failure for failure in failures)


def test_q10_rejects_report_claim_without_source_ref() -> None:
    report = _report().replace("`openclaw:docs/cli/backup.md`; ", "", 1)

    failures = q10.verify(report_text=report, check_refs=False)

    assert any("source ref missing from report" in failure for failure in failures)


def test_q10_rejects_raw_local_path() -> None:
    report = _report() + "\nEvidence captured under /Users/example/private-checkout.\n"

    failures = q10.verify(report_text=report, check_refs=False)

    assert "parity rebaseline contains a raw local path" in failures


def test_q10_requires_finite_rebaseline_trigger() -> None:
    payload = copy.deepcopy(_payload())
    payload["rebaseline_trigger"] = "Repeat forever whenever upstream changes."

    failures = q10.verify(payload=payload, check_refs=False)

    assert "finite rebaseline trigger drifted" in failures
