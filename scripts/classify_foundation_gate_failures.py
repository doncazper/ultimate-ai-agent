#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT_PATH = ROOT / "reports" / "foundation_gate" / "latest_foundation_gate_report.json"
DEFAULT_OUTPUT_PATH = ROOT / "tests" / "fixtures" / "foundation_gate_failure_classification.json"
CLASSIFICATIONS = {
    "real_unsafe_route_drift",
    "expected_safe_route_family_needs_normalization",
    "stale_historical_expectation",
    "unknown_needs_review",
}
EXTRACTED_ROUTE_BOUNDARY_EVALUATOR_DATA_FILE = (
    "src/ultimate_ai_agent/core/gate/evaluator_modules/route_boundaries.py"
)


def classify_failures(report: dict[str, Any]) -> dict[str, Any]:
    failed_results = [
        result for result in report.get("results", []) if result.get("status") == "failed"
    ]
    items = [_classified_item(result) for result in failed_results]
    classification_counts = Counter(item["classification"] for item in items)
    family_counts = Counter(item["family"] for item in items)
    return {
        "schema_version": "uaa-foundation-gate-failure-classification.v1",
        "source": {
            "report_ref": "foundation-gate-report:latest",
            "overall_status": report.get("overall_status"),
            "failed_count": len(failed_results),
        },
        "classification_counts": dict(sorted(classification_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "items": items,
        "redactions_applied": [
            "criterion_ids_only",
            "raw_logs_omitted",
            "raw_paths_omitted",
            "safe_refs_only",
        ],
    }


def _classified_item(result: dict[str, Any]) -> dict[str, str]:
    criterion_id = str(result.get("criterion_id", "unknown"))
    family = _family_for(criterion_id)
    classification = _classification_for(result, family)
    return {
        "criterion_id": criterion_id,
        "family": family,
        "classification": classification,
        "reason_code": _reason_code_for(classification, criterion_id, result),
    }


def _family_for(criterion_id: str) -> str:
    if "route_boundary" in criterion_id or criterion_id.endswith("_api_contract_unchanged"):
        return "route_boundary"
    if criterion_id.startswith("m13_frontend") or criterion_id.startswith("m13_web_shell"):
        return "frontend_product_language"
    if "redaction" in criterion_id or "secret" in criterion_id:
        return "security_redaction"
    if "storage" in criterion_id or "backup" in criterion_id:
        return "storage_backup"
    return criterion_id.split("_", 1)[0]


def _classification_for(result: dict[str, Any], family: str) -> str:
    criterion_id = str(result.get("criterion_id", "unknown"))
    if _is_extracted_evaluator_data_static_scan_false_positive(result):
        return "stale_historical_expectation"
    if family == "route_boundary" or criterion_id == "m12_control_center_api_read_only":
        return "expected_safe_route_family_needs_normalization"
    if criterion_id == "m13_frontend_ci_covers_local_checks":
        return "stale_historical_expectation"
    return "unknown_needs_review"


def _reason_code_for(
    classification: str,
    criterion_id: str,
    result: dict[str, Any],
) -> str:
    if _is_extracted_evaluator_data_static_scan_false_positive(result):
        return "EXTRACTED_EVALUATOR_DATA_STATIC_SCAN_FALSE_POSITIVE"
    if classification == "expected_safe_route_family_needs_normalization":
        return "POST_MILESTONE_SAFE_ROUTE_FAMILY_PENDING"
    if classification == "stale_historical_expectation":
        return "GATE_EXPECTATION_NEEDS_REFRESH"
    if classification == "real_unsafe_route_drift":
        return "UNSAFE_ROUTE_DRIFT_REVIEW_REQUIRED"
    return f"REVIEW_REQUIRED:{criterion_id}"


def _is_extracted_evaluator_data_static_scan_false_positive(result: dict[str, Any]) -> bool:
    criterion_id = str(result.get("criterion_id", ""))
    failures = [str(failure) for failure in result.get("failures", [])]
    return (
        criterion_id.endswith("_static_safety")
        and bool(failures)
        and all(EXTRACTED_ROUTE_BOUNDARY_EVALUATOR_DATA_FILE in failure for failure in failures)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args(argv)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    summary = classify_failures(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "written",
                "classification_ref": "foundation-gate-failure-classification:latest",
                "failed_count": summary["source"]["failed_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
