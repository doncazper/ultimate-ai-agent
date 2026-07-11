#!/usr/bin/env python3
"""Validate FCC-DOGFOOD-001 private 14-day harness truth."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "FCC-DOGFOOD-001"
DOC = ROOT / "docs/macos/FCC_DOGFOOD_001_FOURTEEN_DAY_PRIVATE_HARNESS.md"
HARNESS_JSON = ROOT / "docs/macos/private_operator_14_day_dogfood_harness_v1.json"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
READINESS_MODULE = ROOT / "src/ultimate_ai_agent/core/readiness/private_operator_trial.py"
READINESS_INIT = ROOT / "src/ultimate_ai_agent/core/readiness/__init__.py"
FOCUSED_TEST = ROOT / "tests/test_fcc_dogfood_001_fourteen_day_private_harness.py"

DOC_REF = "docs/macos/FCC_DOGFOOD_001_FOURTEEN_DAY_PRIVATE_HARNESS.md"
HARNESS_JSON_REF = "docs/macos/private_operator_14_day_dogfood_harness_v1.json"
VERIFIER_REF = "scripts/verify_fcc_dogfood_001_fourteen_day_private_harness.py"
TEST_REF = "tests/test_fcc_dogfood_001_fourteen_day_private_harness.py"


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_text(root: Path, path: Path, failures: list[str]) -> str:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return ""
    return target.read_text(encoding="utf-8")


def _require_fragments(
    rel_path: str,
    text: str,
    fragments: list[str],
    failures: list[str],
) -> None:
    compact = " ".join(text.lower().split())
    lowered = text.lower()
    for fragment in fragments:
        needle = fragment.lower()
        if needle not in lowered and needle not in compact:
            failures.append(f"{rel_path} missing FCC-DOGFOOD-001 fragment: {fragment}")


def _validate_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(DOC),
        text,
        [
            "Status: Implemented as a local/private safe-ref-only harness",
            HARNESS_JSON_REF,
            "build_private_dogfood_harness()",
            "not_run",
            "pending_operator_review",
            "Accepted and revised finding refs are intentionally empty",
            "no telemetry upload",
            "no background monitoring",
            "no raw prompts",
            "no provider/model calls",
            "no connector writes",
            "no public beta",
            "no production authority",
            VERIFIER_REF,
            TEST_REF,
        ],
        failures,
    )


def _validate_code_and_artifact(root: Path, failures: list[str]) -> None:
    requirements = {
        READINESS_MODULE: [
            "PRIVATE_OPERATOR_DOGFOOD_HARNESS_CONTRACT_REF",
            "PrivateDogfoodDailyEntry",
            "PrivateDogfoodHarness",
            "build_private_dogfood_harness",
            "duration_days: Literal[14]",
            "telemetry_upload_enabled: bool = False",
            "background_monitoring_enabled: bool = False",
            "raw_private_content_allowed: bool = False",
            "private dogfood harness must define days 1 through 14",
        ],
        READINESS_INIT: [
            "PRIVATE_OPERATOR_DOGFOOD_HARNESS_CONTRACT_REF",
            "PrivateDogfoodDailyEntry",
            "PrivateDogfoodHarness",
            "build_private_dogfood_harness",
        ],
        FOCUSED_TEST: [
            "test_private_dogfood_harness_defines_fourteen_pending_days",
            "test_private_dogfood_harness_json_artifact_validates",
            "test_private_dogfood_harness_rejects_authority_and_raw_content",
            "telemetry_upload_enabled",
            "raw_private_content_allowed",
        ],
        HARNESS_JSON: [
            "implemented_private_14_day_dogfood_harness_safe_refs_only",
            '"duration_days": 14',
            '"day_index": 1',
            '"day_index": 14',
            '"capture_state": "not_run"',
            '"manual_review_status": "pending_operator_review"',
            '"telemetry_upload_enabled": false',
            '"background_monitoring_enabled": false',
            '"raw_private_content_allowed": false',
            '"public_beta_claim_enabled": false',
            '"production_authority_enabled": false',
        ],
    }
    for path, fragments in requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)

    try:
        from ultimate_ai_agent.core.readiness import PrivateDogfoodHarness
    except Exception as exc:  # pragma: no cover - verifier diagnostics
        failures.append(f"could not import PrivateDogfoodHarness: {exc}")
        return

    raw = _read_text(root, HARNESS_JSON, failures)
    if not raw:
        return
    try:
        harness = PrivateDogfoodHarness.model_validate_json(raw)
    except Exception as exc:  # pragma: no cover - verifier diagnostics
        failures.append(f"private dogfood harness artifact failed validation: {exc}")
        return
    if harness.duration_days != 14 or len(harness.daily_entries) != 14:
        failures.append("private dogfood harness must define exactly 14 days")
    if [entry.day_index for entry in harness.daily_entries] != list(range(1, 15)):
        failures.append("private dogfood harness day indexes must be 1 through 14")
    if harness.accepted_finding_refs or harness.revised_finding_refs:
        failures.append("private dogfood harness must not claim accepted/revised findings")
    denied_flags = [
        "telemetry_upload_enabled",
        "background_monitoring_enabled",
        "raw_private_content_allowed",
        "public_beta_claim_enabled",
        "production_authority_enabled",
        "connector_write_enabled",
        "provider_model_authority_allowed",
        "action_execution_enabled",
        "backend_route_added",
    ]
    for flag in denied_flags:
        if getattr(harness, flag) is not False:
            failures.append(f"private dogfood harness enables denied flag {flag}")


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "FCC-DOGFOOD-001 Fourteen-Day Private Operator Harness",
            DOC_REF,
            "FCC-ACTION-001 Approval-Bound Local Authority Capability",
        ],
        FCC_BOARD: [
            "FCC-DOGFOOD-001",
            "Fourteen-Day Private Operator Harness",
            DOC_REF,
            HARNESS_JSON_REF,
        ],
        PRODUCT_TRUTH: [
            "FCC-DOGFOOD-001",
            DOC_REF,
            HARNESS_JSON_REF,
            "no telemetry upload",
            "no public beta",
            "no production authority",
        ],
        DOCS_README: [DOC_REF, HARNESS_JSON_REF],
        DOCS_INDEX: [DOC_REF, HARNESS_JSON_REF],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def validate_fcc_dogfood_001_fourteen_day_private_harness(
    root: Path = ROOT,
) -> list[str]:
    failures: list[str] = []
    _validate_doc(root, failures)
    _validate_code_and_artifact(root, failures)
    _validate_active_docs(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate FCC-DOGFOOD-001 private 14-day harness truth."
    )
    parser.parse_args(argv)
    failures = validate_fcc_dogfood_001_fourteen_day_private_harness()
    if failures:
        print(f"{TASK_REF} verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"{TASK_REF} verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
