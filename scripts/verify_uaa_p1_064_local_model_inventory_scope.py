#!/usr/bin/env python3
"""Validate the UAA-P1-064 read-only local model inventory scope.

This verifier is inspection-only. It checks that UAA-P1-064 is promoted as the
Ready Next milestone for read-only Python Agent Core inventory and CLI
inspection, while lifecycle, switching, downloads, route authority, Control
Center activation, and runtime adapters remain blocked.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "UAA-P1-064"
SCOPE_DOC = ROOT / "docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md"
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
    / "docs/backlog/reconciliation/2026-06-21-uaa-p1-064-ready-next-promotion.json"
)
SCOPE_REF = "docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md"

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
            failures.append(f"{rel_path} missing UAA-P1-064 fragment: {fragment}")


def _validate_scope_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, SCOPE_DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(SCOPE_DOC),
        text,
        [
            "Status: Ready Next",
            "UAA-P1-064 is the first implementation milestone",
            "Python Agent Core as the authority",
            "read-only Python Agent Core inventory",
            "Detect local model candidates from GGUF",
            "Hugging Face/MLX-style directories",
            "Ollama manifests or blobs",
            "LM Studio-style directories",
            "uaa local-model status",
            "uaa local-model list",
            "uaa local-model inspect <model-ref>",
            "runnable_now",
            "needs_adapter",
            "blocked",
            "No start, stop, activate, switch, or unload behavior",
            "No process control and no llama.cpp lifecycle management",
            "No OpenAPI or route authority",
            "No model downloads or model movement",
            "No provider SDK calls, model calls, web fetching",
            "No Control Center activation control",
            "Verification Commands",
            "scripts/verify_uaa_p1_064_local_model_inventory_scope.py",
            "Stop And Ask Conditions",
        ],
        failures,
    )
    failures.extend(_scan_text(_rel(SCOPE_DOC), text))


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "UAA-P1-064 Local Model Inventory Read-Only Backend + CLI",
            "UAA-P1-064 is Ready Next only",
            "CLI parity first: uaa local-model status",
            "No start, stop, activate, switch",
            "scripts/verify_uaa_p1_064_local_model_inventory_scope.py",
        ],
        ROADMAP: [
            "`UAA-P1-064` Ready Next: read-only local model inventory backend + CLI",
            "`UAA-P1-064` Ready Next: implement only the read-only Python Agent Core",
            SCOPE_REF,
        ],
        PRODUCT_TRUTH: [
            "UAA-P1-064 is Ready Next for read-only Python Agent Core inventory and CLI inspection only",
            "Ready Next for UAA-P1-064 read-only inventory and CLI inspection",
            SCOPE_REF,
        ],
        GAP_MAP: [
            "UAA-P1-064 may add read-only inventory and CLI inspection only",
            "UAA-P1-064 read-only inventory scope doc",
        ],
        DOCS_README: [SCOPE_REF],
        DOCS_INDEX: [SCOPE_REF],
        CANONICAL_MAP: [SCOPE_REF],
        RECOMMENDATION_LOG: [
            "UAA-P1-064 Local Model Inventory Ready Next",
            "implementation-ready for read-only inventory and CLI inspection only",
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
        "reconciliation:2026-06-21-uaa-p1-064-ready-next-promotion"
    ):
        failures.append("UAA-P1-064 reconciliation artifact id drifted")
    if artifact.get("next_prompt_ref") != "prompt-ref:uaa-p1-064-conveyor-restart":
        failures.append("UAA-P1-064 reconciliation artifact must point to restart prompt")

    safety = artifact.get("reconciliation_safety")
    if not isinstance(safety, dict) or set(safety) != REQUIRED_SAFETY_FLAGS:
        failures.append("UAA-P1-064 reconciliation safety flags are incomplete")
    elif any(safety.get(flag) is not False for flag in REQUIRED_SAFETY_FLAGS):
        failures.append("UAA-P1-064 reconciliation safety flags must all be false")

    serialized = json.dumps(artifact, sort_keys=True)
    for fragment in [
        "recommendation:uaa-p1-064-ready-next-scope",
        "recommendation:uaa-p1-064-implementation",
        "recommendation:uaa-p1-064-runtime-authority",
        "READY_NEXT_NOT_STARTED",
        "MISSING_SCOPED_AUTHORITY",
        SCOPE_REF,
    ]:
        if fragment not in serialized:
            failures.append(f"UAA-P1-064 reconciliation artifact missing: {fragment}")
    failures.extend(_scan_text(_rel(RECONCILIATION_ARTIFACT), serialized))


def validate_uaa_p1_064_local_model_inventory_scope(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    _validate_scope_doc(root, failures)
    _validate_active_docs(root, failures)
    _validate_reconciliation_artifact(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate UAA-P1-064 local model inventory scope."
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root to validate.")
    args = parser.parse_args(argv)
    failures = validate_uaa_p1_064_local_model_inventory_scope(Path(args.root).resolve())
    if failures:
        print("UAA-P1-064 local model inventory scope verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("UAA-P1-064 local model inventory scope verification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
