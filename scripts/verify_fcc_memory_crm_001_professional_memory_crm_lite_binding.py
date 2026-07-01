#!/usr/bin/env python3
"""Validate FCC-MEMORY-CRM-001 professional memory and CRM-lite truth."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "FCC-MEMORY-CRM-001"
DOC = ROOT / "docs/control_center/FCC_MEMORY_CRM_001_PROFESSIONAL_MEMORY_CRM_LITE_BINDING.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
MATURITY_MANIFEST = ROOT / "docs/control_center/operational_maturity_manifest.json"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
API_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FOUNDER_LOOP_PANELS = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
CONTROL_CENTER_ROUTE_TEST = ROOT / "tests/test_control_center_api_routes.py"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
STORAGE_SAFETY_TEST = ROOT / "tests/test_founder_loop_storage_safety.py"
BUSINESS_MEMORY = ROOT / "src/ultimate_ai_agent/core/memory/business_memory.py"
CLI_INSPECT = ROOT / "scripts/inspect_relationship_crm_lite_memory.py"

DOC_REF = "docs/control_center/FCC_MEMORY_CRM_001_PROFESSIONAL_MEMORY_CRM_LITE_BINDING.md"
VERIFIER_REF = "scripts/verify_fcc_memory_crm_001_professional_memory_crm_lite_binding.py"


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
            failures.append(f"{rel_path} missing FCC-MEMORY-CRM-001 fragment: {fragment}")


def _validate_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(DOC),
        text,
        [
            "Status: Implemented",
            "Primary surfaces: `/today`, `/briefing`, `/actions`, and `/memory`",
            "crm_lite_followups",
            "memory_why_shown_items",
            "CrmLiteRelationshipFollowUp",
            "contract-ref:relationship-crm-lite-memory:v1",
            "FounderLoopCrmLiteFollowUp",
            "FounderLoopMemoryWhyShownItem",
            "scripts/inspect_relationship_crm_lite_memory.py",
            "state_not_found_no_write",
            "existing_state_unreadable_redacted",
            "reviewed professional memory",
            "recall, not truth or authority",
            "stale state",
            "conflict state",
            "missing evidence refs",
            "does not add automatic memory truth",
            "local/read-only/proposal-only",
            VERIFIER_REF,
        ],
        failures,
    )


def _validate_backend_and_frontend(root: Path, failures: list[str]) -> None:
    requirements = {
        BUSINESS_MEMORY: [
            "CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF",
            "CrmLiteRelationshipFollowUp",
            "crm_lite_relationship_authority_posture",
            "review_only_stale_check_required",
            "blocked-state:crm-lite-no-connector-read",
            "blocked-state:crm-lite-no-hidden-context-injection",
            "hidden_memory_write_authorized",
        ],
        STORAGE: [
            "def _crm_lite_followups(",
            "def _memory_why_shown_items(",
            "build_crm_lite_relationship_followup",
            "crm_lite_relationship_authority_posture",
            "crm_lite_followups",
            "memory_why_shown_items",
            "relationship_ref",
            "person_ref",
            "org_ref",
            "project_ref",
            "opportunity_ref",
            "promise_ref",
            "crm_lite_relationship_memory_contract_ref",
            "draft_available",
            "blocked-state:crm-lite-no-connector-read",
            "blocked-state:crm-lite-no-hidden-memory-write",
            "blocked-state:no-external-crm-write",
            "blocked-state:no-account-sync",
            "blocked-state:no-connector-write",
            "reviewed_recall_only",
            "context_injection_authorized",
            "memory_truth_authority",
            "conflict_unknown_review_required",
        ],
        API_TYPES: [
            "FounderLoopCrmLiteFollowUp",
            "FounderLoopMemoryWhyShownItem",
            "contract_ref",
            "relationship_ref",
            "person_ref",
            "org_ref",
            "project_ref",
            "opportunity_ref",
            "promise_ref",
            "relationship_memory_posture",
            "draft_available",
            "crm_sync_enabled",
            "crm_write_enabled",
            "external_write_enabled",
            "connector_read_authorized",
            "hidden_memory_write_authorized",
            "model_provider_call_authorized",
            "reviewed_recall_only",
            "context_injection_authorized",
            "memory_truth_authority",
        ],
        FOUNDER_LOOP_PANELS: [
            "CrmLiteFollowUpCards",
            "MemoryWhyShownCards",
            "CRM-lite follow-ups",
            "Memory why shown",
            "Relationship memory",
            "CRM sync",
            "CRM writes",
            "External writes",
            "Connector reads",
            "Hidden memory writes",
            "Reviewed recall only",
            "Context injection",
            "Memory truth",
        ],
        APP_TEST: [
            "CRM-lite follow-ups",
            "Memory why shown",
            "context_injection_authorized: false",
            "memory_truth_authority: false",
        ],
        CONTROL_CENTER_ROUTE_TEST: [
            "crm_lite_followups",
            "memory_why_shown_items",
            'actions["crm_lite_followups"][0]["crm_write_enabled"] is False',
        ],
        STORAGE_TEST: [
            "follow_up_commitment_refs",
            "memory_to_loop_binding_contract_ref",
            "context_injection_authorized",
            "memory_truth_authority",
        ],
        STORAGE_SAFETY_TEST: [
            "memory_truth_authority",
            "context_injection_authorized",
        ],
        CLI_INSPECT: [
            "repo-local-command:inspect-relationship-crm-lite-memory",
            "CrmLiteRelationshipFollowUp",
            "read_only=True",
            "state_not_found_no_write",
            "existing_state_unreadable_redacted",
            "read-failed-redacted",
            "crm_lite_relationship_authority_posture",
            "raw_content_omitted",
            "connector_runtime_enabled",
            "production_authority_enabled",
        ],
    }
    for path, fragments in requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "FCC-MEMORY-CRM-001 Professional Memory And CRM-lite Binding",
            DOC_REF,
            "FCC-REVIEW-001 Evidence Narrative And Weekly CEO Review",
        ],
        FCC_BOARD: [
            "FCC-MEMORY-CRM-001",
            "Professional Memory And CRM-lite Binding",
            DOC_REF,
        ],
        PRODUCT_TRUTH: [
            "FCC-MEMORY-CRM-001",
            DOC_REF,
            "Professional memory and CRM-lite binding is implemented",
        ],
        GAP_MAP: [
            "CRM-lite follow-up refs",
            "Memory Review",
            "reviewed recall-only",
        ],
        DOCS_README: [DOC_REF],
        DOCS_INDEX: [DOC_REF],
        MATURITY_MANIFEST: [
            DOC_REF,
            VERIFIER_REF,
            "automatic_memory_truth",
            "context_injection",
        ],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def validate_fcc_memory_crm_001_professional_memory_crm_lite_binding(
    root: Path = ROOT,
) -> list[str]:
    failures: list[str] = []
    _validate_doc(root, failures)
    _validate_backend_and_frontend(root, failures)
    _validate_active_docs(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate FCC-MEMORY-CRM-001 professional memory and CRM-lite truth."
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root to inspect.")
    args = parser.parse_args(argv)

    failures = validate_fcc_memory_crm_001_professional_memory_crm_lite_binding(
        Path(args.root).resolve()
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(f"{TASK_REF} Professional Memory and CRM-lite verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
