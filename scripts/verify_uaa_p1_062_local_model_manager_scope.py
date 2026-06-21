#!/usr/bin/env python3
"""Validate the UAA-P1-062 Local Model Manager docs-only scope.

This verifier is inspection-only. It checks that the UAA-P1-062 lane shape
remains documented as docs-only and that runtime model-manager authority stays
blocked until later exact scoped milestones grant them.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "UAA-P1-062"
SCOPE_DOC = ROOT / "docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
ROADMAP = ROOT / "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
CANONICAL_MAP = ROOT / "docs/canonical/CANONICAL_DOC_MAP.md"
RECOMMENDATION_LOG = ROOT / "docs/backlog/codex_recommendation_log.md"
RECONCILIATION_ARTIFACT = (
    ROOT
    / "docs/backlog/reconciliation/2026-06-21-uaa-p1-062-local-model-manager-shape.json"
)
SCOPE_REF = "docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md"

REQUIRED_SAFETY_FLAGS = {
    "raw_prompt_included",
    "raw_response_included",
    "raw_provider_payload_included",
    "raw_path_included",
    "raw_log_included",
    "username_included",
    "hostname_included",
    "serial_included",
    "environment_dump_included",
    "credential_material_included",
    "private_content_included",
}

FORBIDDEN_PRIVATE_FRAGMENTS = {
    "/users/",
    "c:\\users\\",
    "raw prompt:",
    "raw response:",
    "raw provider payload:",
    "raw path:",
    "raw log:",
    "username:",
    "hostname:",
    "serial number:",
    "environment dump:",
    "credential:",
    "api_key",
    "secret_key",
    "password=",
    "token=",
}


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_text(root: Path, path: Path, failures: list[str]) -> str:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return ""
    return target.read_text(encoding="utf-8")


def _read_json(root: Path, path: Path, failures: list[str]) -> dict[str, Any]:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return {}
    try:
        loaded = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON in {rel_path.as_posix()}: {exc.msg}")
        return {}
    if not isinstance(loaded, dict):
        failures.append(f"{rel_path.as_posix()} must contain a JSON object")
        return {}
    return loaded


def _scan_text(rel_path: str, text: str) -> list[str]:
    lowered = text.lower()
    return [
        f"{rel_path} contains forbidden raw/private fragment: {fragment}"
        for fragment in sorted(FORBIDDEN_PRIVATE_FRAGMENTS)
        if fragment in lowered
    ]


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
            failures.append(f"{rel_path} missing UAA-P1-062 fragment: {fragment}")


def _validate_scope_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, SCOPE_DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(SCOPE_DOC),
        text,
        [
            "Status: docs-only lane shape",
            "does not implement routes",
            "Python Agent Core owns local model truth",
            "No routes or OpenAPI changes",
            "No CLI commands",
            "No OpenWebUI config or runtime changes",
            "no process control",
            "no provider/model calls",
            "Candidate Implementation Roadmap",
            "Read-only inventory",
            "uaa local-model status",
            "llama-server --models-dir <approved-gguf-cache-ref> --models-max 1",
            "uaa local-model switch --to <model-ref> --dry-run",
            "Implementation Prompt For Later Scoped Milestone",
            "Implement UAA-P1-064 Local Model Inventory Read-Only Backend + CLI",
            "Future implementation stages need later documented scope",
        ],
        failures,
    )
    failures.extend(_scan_text(_rel(SCOPE_DOC), text))


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "UAA-P1-064 Local Model Inventory Read-Only Backend + CLI",
            "UAA-P1-064 adds the first read-only implementation slice",
            "backend routes, CLI commands, lifecycle authority",
            "Later Local Model Manager lifecycle",
            "This milestone adds no backend routes",
        ],
        ROADMAP: [
            "`UAA-P1-062` Done: Local Model Manager / Memory-Aware Runtime Control lane shape",
            "Runtime stages remain blocked until later exact scoped milestones",
            "read-only inventory over consolidated `$HOME/Models` roots",
            "uaa local-model status/list/inspect",
            SCOPE_REF,
        ],
        PRODUCT_TRUTH: [
            "UAA-P1-062 documents the Local Model Manager / Memory-Aware Runtime Control lane shape",
            "planned/blocked for lifecycle",
            SCOPE_REF,
        ],
        GAP_MAP: [
            "UAA-P1-062 scope doc",
            "Blocked.",
            "later backend contracts",
        ],
        DOCS_README: [SCOPE_REF],
        DOCS_INDEX: [SCOPE_REF],
        CANONICAL_MAP: [SCOPE_REF],
        RECOMMENDATION_LOG: [
            "UAA-P1-062 Local Model Manager Lane Shape",
            "No backend route, CLI command, process control",
            SCOPE_REF,
        ],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if not text:
            continue
        _require_fragments(_rel(path), text, fragments, failures)
        failures.extend(_scan_text(_rel(path), text))


def _validate_reconciliation_artifact(root: Path, failures: list[str]) -> None:
    artifact = _read_json(root, RECONCILIATION_ARTIFACT, failures)
    if not artifact:
        return
    if artifact.get("reconciliation_id") != (
        "reconciliation:2026-06-21-uaa-p1-062-local-model-manager-shape"
    ):
        failures.append("UAA-P1-062 reconciliation artifact id drifted")
    if artifact.get("next_prompt_ref") != "prompt-ref:no-documented-ready-next":
        failures.append("UAA-P1-062 reconciliation artifact must stop the conveyor")

    safety = artifact.get("reconciliation_safety")
    if not isinstance(safety, dict) or set(safety) != REQUIRED_SAFETY_FLAGS:
        failures.append("UAA-P1-062 reconciliation safety flags are incomplete")
    elif any(safety.get(flag) is not False for flag in REQUIRED_SAFETY_FLAGS):
        failures.append("UAA-P1-062 reconciliation safety flags must all be false")

    serialized = json.dumps(artifact, sort_keys=True)
    for fragment in [
        "recommendation:uaa-p1-062-docs-only-shape",
        "recommendation:uaa-p1-062-runtime-authority",
        "MISSING_SCOPED_AUTHORITY",
        SCOPE_REF,
    ]:
        if fragment not in serialized:
            failures.append(f"UAA-P1-062 reconciliation artifact missing: {fragment}")
    failures.extend(_scan_text(_rel(RECONCILIATION_ARTIFACT), serialized))


def validate_uaa_p1_062_local_model_manager_scope(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    _validate_scope_doc(root, failures)
    _validate_active_docs(root, failures)
    _validate_reconciliation_artifact(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate UAA-P1-062 local model manager docs-only scope."
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root to validate.")
    args = parser.parse_args(argv)
    failures = validate_uaa_p1_062_local_model_manager_scope(Path(args.root).resolve())
    if failures:
        print("UAA-P1-062 local model manager scope verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("UAA-P1-062 local model manager scope verification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
