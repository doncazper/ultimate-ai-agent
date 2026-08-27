#!/usr/bin/env python3
"""Verify the bounded FIN-002 synthetic CSV import-preview slice."""

from __future__ import annotations

import inspect
from pathlib import Path

from ultimate_ai_agent.core.finance.import_preview import (
    load_synthetic_import_fixture_manifest,
    preview_synthetic_csv_fixture,
    synthetic_import_fixture_manifest_ref,
)


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_MANIFEST_REF = (
    "fixture-manifest-ref:finance/FIN-002:sha256:"
    "cc14f2beb2fe339752fcb59de76fe50662358caefe612ed6e730524e9e6cfbf8"
)
EXPECTED_FIXTURE_REFS = {
    "fixture-ref:finance/FIN-002:synthetic-csv-adversarial:v1",
    "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1",
    "fixture-ref:finance/FIN-002:synthetic-csv-duplicate:v1",
}
REQUIRED_DOC_PHRASES = {
    "docs/product/UAA_FINANCE_FIN002_SYNTHETIC_IMPORT_PREVIEW.md": (
        "synthetic-only",
        "arbitrary operator-supplied financial data is rejected",
        "no import commit authority",
        "independent fin-000 promotion",
    ),
    "docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md": (
        "fin-002a",
        "synthetic csv import preview",
    ),
}


def verify() -> list[str]:
    failures: list[str] = []
    if synthetic_import_fixture_manifest_ref() != EXPECTED_MANIFEST_REF:
        failures.append("FIN002 fixture manifest digest drifted")
    fixtures = load_synthetic_import_fixture_manifest()
    if {item.fixture_ref for item in fixtures} != EXPECTED_FIXTURE_REFS:
        failures.append("FIN002 fixture inventory drifted")
    for fixture in fixtures:
        preview = preview_synthetic_csv_fixture(fixture.fixture_ref)
        actual_counts = (
            preview.row_count,
            preview.accepted_count,
            preview.duplicate_count,
            preview.quarantine_count,
        )
        expected_counts = (
            fixture.expected_row_count,
            fixture.expected_accepted_count,
            fixture.expected_duplicate_count,
            fixture.expected_quarantine_count,
        )
        if actual_counts != expected_counts:
            failures.append(f"FIN002 fixture outcome drifted: {fixture.fixture_ref}")
        read_model = preview.redacted_read_model()
        required_false = (
            "raw_source_content_included",
            "arbitrary_operator_input_allowed",
            "mutation_performed",
            "commit_authority_granted",
            "connector_authority_granted",
            "ocr_authority_granted",
            "real_financial_data_allowed",
        )
        if any(read_model.get(field) is not False for field in required_false):
            failures.append(f"FIN002 authority posture drifted: {fixture.fixture_ref}")
    parameters = set(inspect.signature(preview_synthetic_csv_fixture).parameters)
    if parameters != {"fixture_ref", "existing_fingerprint_refs"}:
        failures.append("FIN002 preview public input boundary drifted")
    module_source = (
        ROOT / "src/ultimate_ai_agent/core/finance/import_preview.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "from pathlib import Path",
        "open(",
        ".read_bytes(",
        ".read_text(",
    ):
        if forbidden in module_source:
            failures.append(f"FIN002 preview added a file-input primitive: {forbidden}")
    cli_source = (ROOT / "scripts/dev/uaa_finance_import.py").read_text(
        encoding="utf-8"
    )
    for forbidden in ("--file", "--path", "--input"):
        if forbidden in cli_source:
            failures.append(f"FIN002 CLI added an arbitrary input option: {forbidden}")
    for relative, phrases in REQUIRED_DOC_PHRASES.items():
        text = (ROOT / relative).read_text(encoding="utf-8").lower()
        for phrase in phrases:
            if phrase not in text:
                failures.append(
                    f"FIN002 truth phrase missing from {relative}: {phrase}"
                )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("FIN-002 synthetic import preview verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
