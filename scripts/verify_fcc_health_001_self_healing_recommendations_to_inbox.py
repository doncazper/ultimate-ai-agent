#!/usr/bin/env python3
"""Validate FCC-HEALTH-001 recommendation-to-inbox truth."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "FCC-HEALTH-001"
DOC = ROOT / "docs/control_center/FCC_HEALTH_001_SELF_HEALING_RECOMMENDATIONS_TO_INBOX.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
MATURITY_MANIFEST = ROOT / "docs/control_center/operational_maturity_manifest.json"
HEALTH_MODULE = ROOT / "src/ultimate_ai_agent/core/control_center/health_recommendations.py"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
API_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FOCUSED_TEST = ROOT / "tests/test_fcc_health_001_self_healing_recommendations_to_inbox.py"

DOC_REF = "docs/control_center/FCC_HEALTH_001_SELF_HEALING_RECOMMENDATIONS_TO_INBOX.md"
VERIFIER_REF = "scripts/verify_fcc_health_001_self_healing_recommendations_to_inbox.py"
TEST_REF = "tests/test_fcc_health_001_self_healing_recommendations_to_inbox.py"
ACTION_KIND = "self_heal_recommendation"


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
            failures.append(f"{rel_path} missing FCC-HEALTH-001 fragment: {fragment}")


def _validate_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(DOC),
        text,
        [
            "Status: Implemented for first backend-owned recommendation read-model",
            "RecommendationCandidate",
            ACTION_KIND,
            "Action Inbox",
            "recommendation_review_only_no_execution_path",
            "proposal_only_no_execution_path",
            "no autonomous coding",
            "no auto-apply patches",
            "no provider/model calls",
            "no connector reads or writes",
            "no production authority",
            VERIFIER_REF,
            TEST_REF,
        ],
        failures,
    )


def _validate_backend_and_frontend(root: Path, failures: list[str]) -> None:
    requirements = {
        HEALTH_MODULE: [
            "FCC_HEALTH_RECOMMENDATION_CONTRACT_REF",
            "FCC_HEALTH_RECOMMENDATION_BINDING_CONTRACT_REF",
            "FCC_HEALTH_RECOMMENDATION_ACTION_KIND",
            "_UNSAFE_HUMAN_TEXT_PATTERNS",
            "RecommendationCandidate",
            "build_fcc_health_recommendations",
            "documentation_currentness_drift",
            "source_readiness_gap",
            "operational_maturity_gap",
            "auto_code_authorized: bool = False",
            "auto_apply_authorized: bool = False",
            "provider_model_call_authorized: bool = False",
            "connector_write_authorized: bool = False",
            "task_execution_authorized: bool = False",
            "production_authority_enabled: bool = False",
            "contains_secret_like",
            "FCC_HEALTH_RECOMMENDATION_UNSAFE_HUMAN_TEXT_REJECTED",
            "FCC_HEALTH_RECOMMENDATION_UNSAFE_EVIDENCE_REF_REJECTED",
            "max_length=360",
        ],
        STORAGE: [
            "build_fcc_health_recommendations",
            "_health_recommendation_action_items",
            ACTION_KIND,
            "not_required_recommendation_review_only",
            "recommendation_review_only_no_execution_path",
            "health_recommendation_blocked_authority_refs",
            "health_recommendation_auto_apply_authorized",
            "health_recommendation_provider_model_call_authorized",
            "health_recommendation_connector_write_authorized",
            "health_recommendation_production_authority_enabled",
        ],
        API_TYPES: [
            "health_recommendation_ref",
            "health_recommendation_kind",
            "health_recommendation_lifecycle_state",
            "health_recommendation_blocked_authority_refs",
            "health_recommendation_auto_apply_authorized",
            "health_recommendation_provider_model_call_authorized",
            "health_recommendation_connector_write_authorized",
            "health_recommendation_production_authority_enabled",
        ],
        FOCUSED_TEST: [
            "test_recommendation_candidate_denies_authority_flags",
            "test_recommendation_candidate_denies_unsafe_human_text",
            "test_recommendation_candidate_bounds_summary_and_evidence_refs",
            "test_health_recommendations_are_safe_ref_review_candidates",
            "test_health_recommendations_project_into_action_inbox_without_execution",
            ACTION_KIND,
            "proposal_only_no_execution_path",
        ],
    }
    for path, fragments in requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "FCC-HEALTH-001 Self-Healing Recommendations To Inbox",
            DOC_REF,
            "FCC-DOGFOOD-001 Fourteen-Day Private Operator Harness",
        ],
        FCC_BOARD: [
            "FCC-HEALTH-001",
            "Self-Healing Recommendations To Inbox",
            DOC_REF,
            "backend-owned recommendation read-model",
        ],
        PRODUCT_TRUTH: [
            "FCC-HEALTH-001",
            DOC_REF,
            ACTION_KIND,
            "no auto-code",
            "no auto-apply",
            "no model/provider calls",
            "no connector writes",
            "no production authority",
        ],
        DOCS_README: [DOC_REF],
        DOCS_INDEX: [DOC_REF],
        MATURITY_MANIFEST: [
            DOC_REF,
            TEST_REF,
            VERIFIER_REF,
            "self_heal_recommendation",
        ],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def validate_fcc_health_001_self_healing_recommendations_to_inbox(
    root: Path = ROOT,
) -> list[str]:
    failures: list[str] = []
    _validate_doc(root, failures)
    _validate_backend_and_frontend(root, failures)
    _validate_active_docs(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate FCC-HEALTH-001 recommendation-to-inbox truth."
    )
    parser.parse_args(argv)
    failures = validate_fcc_health_001_self_healing_recommendations_to_inbox()
    if failures:
        print(f"{TASK_REF} verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"{TASK_REF} verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
