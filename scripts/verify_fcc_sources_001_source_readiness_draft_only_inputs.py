#!/usr/bin/env python3
"""Validate FCC-SOURCES-001 source readiness and draft-only input truth."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "FCC-SOURCES-001"
DOC = ROOT / "docs/control_center/FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
MATURITY_MANIFEST = ROOT / "docs/control_center/operational_maturity_manifest.json"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
API_ROUTE = ROOT / "src/ultimate_ai_agent/api/founder_loop.py"
API_MANIFEST = ROOT / "src/ultimate_ai_agent/api/manifest.py"
API_TYPES = ROOT / "apps/control-center/src/api/types.ts"
ENDPOINTS = ROOT / "apps/control-center/src/api/endpoints.ts"
FOUNDER_LOOP_PANELS = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
CONTROL_CENTER_ROUTE_TEST = ROOT / "tests/test_control_center_api_routes.py"
STORAGE_BRIEFING_TEST = ROOT / "tests/test_founder_loop_storage_briefing.py"

DOC_REF = "docs/control_center/FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md"
VERIFIER_REF = "scripts/verify_fcc_sources_001_source_readiness_draft_only_inputs.py"
ROUTE = "GET /control-center/sources/readiness"


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
            failures.append(f"{rel_path} missing FCC-SOURCES-001 fragment: {fragment}")


def _validate_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(DOC),
        text,
        [
            "Status: Implemented",
            "Primary surfaces: `/inbox`, `/today`, `/briefing`, and `/actions`",
            ROUTE,
            "FounderLoopSourceReadiness",
            "SourceReadinessCards",
            "source_readiness_items",
            "source_readiness_posture",
            "source_readiness_proposal_candidates",
            "proposal_only_no_execution_path",
            "ready",
            "blocked",
            "missing",
            "metadata_only",
            "unavailable",
            "not_configured",
            "does not add account auth",
            "React must not invent source readiness",
            VERIFIER_REF,
        ],
        failures,
    )


def _validate_backend_and_frontend(root: Path, failures: list[str]) -> None:
    requirements = {
        STORAGE: [
            "def source_readiness(",
            "founder_loop_source_readiness.v1",
            "python_core_source_readiness_read_model",
            "source_readiness_items",
            "source_readiness_posture",
            "source_readiness_proposal_candidates",
            "Define email read-only metadata contract",
            "Define calendar read-only metadata contract",
            "Resolve missing account-auth boundary",
            "proposal_only_no_execution_path",
            "connector_runtime_enabled",
            "account_auth_enabled",
            "raw_source_ingestion_enabled",
            "write_authority_enabled",
            "blocked-state:no-connector-write",
        ],
        API_ROUTE: [
            '@router.get("/sources/readiness"',
            "control_center_sources_readiness",
            "connector_runtime_omitted",
        ],
        API_MANIFEST: [
            "control_center_source_readiness_status",
            '"/control-center/sources/readiness"',
        ],
        API_TYPES: [
            "FounderLoopSourceReadinessStatus",
            '"metadata_only"',
            "FounderLoopSourceReadinessProposalCandidate",
            "proposal_only_no_execution_path",
            "connector_runtime_enabled",
            "account_auth_enabled",
            "raw_source_ingestion_enabled",
            "write_authority_enabled",
        ],
        ENDPOINTS: [
            "founderSourceReadiness",
            '"/control-center/sources/readiness"',
        ],
        FOUNDER_LOOP_PANELS: [
            "SourceReadinessCards",
            "SourceReadinessProposalCards",
            "Backend-owned source readiness posture",
            "read-only metadata",
            "connector runtime",
            "Raw source ingestion",
            "Write authority",
        ],
        APP_TEST: [
            "metadata_only",
            "/control-center/sources/readiness",
            "live email, calendar, account, polling",
            "Connector draft proposals",
            "draft_proposals_ready_no_send_write",
            "contract-ref:connector-draft-only-proposals:v1",
            "raw source",
        ],
        CONTROL_CENTER_ROUTE_TEST: [
            "test_control_center_source_readiness_route_is_backend_owned_read_only",
            "/control-center/sources/readiness",
            "control_center_sources_readiness",
            "connector_runtime_omitted",
            "source_readiness_proposal_candidates",
            "proposal_only_no_execution_path",
        ],
        STORAGE_BRIEFING_TEST: [
            "source_readiness_items",
            "source_readiness_posture",
            "metadata_only",
            "not_configured",
        ],
    }
    for path, fragments in requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "FCC-SOURCES-001 Source Readiness And Draft-only Inputs",
            DOC_REF,
            "FCC-MEMORY-CRM-001 Professional Memory And CRM-lite Binding",
        ],
        FCC_BOARD: [
            "FCC-SOURCES-001",
            "Source Readiness And Draft-only Inputs",
            DOC_REF,
        ],
        PRODUCT_TRUTH: [
            "FCC-SOURCES-001",
            DOC_REF,
            "Source Readiness is implemented as a backend-owned read-only route",
        ],
        GAP_MAP: [
            "dedicated backend-owned Source Readiness read model",
            "draft-only proposal candidates",
        ],
        DOCS_README: [DOC_REF],
        DOCS_INDEX: [DOC_REF],
        MATURITY_MANIFEST: [
            DOC_REF,
            VERIFIER_REF,
            "backend_owned_source_readiness_proposal_candidates_connector_runtime_blocked",
        ],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def validate_fcc_sources_001_source_readiness_draft_only_inputs(
    root: Path = ROOT,
) -> list[str]:
    failures: list[str] = []
    _validate_doc(root, failures)
    _validate_backend_and_frontend(root, failures)
    _validate_active_docs(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate FCC-SOURCES-001 source readiness and draft-only input truth."
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root to inspect.")
    args = parser.parse_args(argv)

    failures = validate_fcc_sources_001_source_readiness_draft_only_inputs(
        Path(args.root).resolve()
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(f"{TASK_REF} Source Readiness verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
