#!/usr/bin/env python3
"""Validate the UAA-P1-061 morning reconciliation artifact contract.

This verifier is inspection-only. It validates docs, schema, and template
structure for safe recommendation reconciliation artifacts. It does not execute
prompts, call models, inspect private conversation content, or create runtime
state.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "uaa_morning_reconciliation_artifact.v1"
TASK_REF = "UAA-P1-061"
ARTIFACT_DOC = ROOT / "docs/backlog/MORNING_RECONCILIATION_ARTIFACT.md"
TEMPLATE_PATH = ROOT / "docs/backlog/MORNING_RECONCILIATION_TEMPLATE.json"
SCHEMA_PATH = ROOT / "docs/schemas/morning_reconciliation_artifact.schema.json"
RECOMMENDATION_LOG = ROOT / "docs/backlog/codex_recommendation_log.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
ROADMAP = ROOT / "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md"
TAXONOMY_REF = "docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md"
RECOMMENDATION_LOG_REF = "docs/backlog/codex_recommendation_log.md"

REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "task_ref",
    "reconciliation_id",
    "created_at_utc",
    "source_loop_ref",
    "operator_readiness_taxonomy_ref",
    "recommendation_log_ref",
    "safe_summary",
    "completed_recommendations",
    "deferred_recommendations",
    "rejected_recommendations",
    "blocked_recommendations",
    "next_prompt_ref",
    "reconciliation_safety",
}

BUCKETS = {
    "completed_recommendations": "completed",
    "deferred_recommendations": "deferred",
    "rejected_recommendations": "rejected",
    "blocked_recommendations": "blocked",
}

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
    target = root / path.relative_to(ROOT)
    if not target.exists():
        failures.append(f"missing required file: {path.relative_to(ROOT).as_posix()}")
        return ""
    return target.read_text(encoding="utf-8")


def _read_json(root: Path, path: Path, failures: list[str]) -> dict[str, Any]:
    target = root / path.relative_to(ROOT)
    if not target.exists():
        failures.append(f"missing required file: {path.relative_to(ROOT).as_posix()}")
        return {}
    try:
        loaded = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON in {path.relative_to(ROOT).as_posix()}: {exc.msg}")
        return {}
    if not isinstance(loaded, dict):
        failures.append(f"{path.relative_to(ROOT).as_posix()} must contain a JSON object")
        return {}
    return loaded


def _scan_text(rel_path: str, text: str) -> list[str]:
    lowered = text.lower()
    failures: list[str] = []
    for fragment in sorted(FORBIDDEN_PRIVATE_FRAGMENTS):
        if fragment in lowered:
            failures.append(f"{rel_path} contains forbidden raw/private fragment: {fragment}")
    return failures


def _require_fragments(rel_path: str, text: str, fragments: list[str], failures: list[str]) -> None:
    compact = " ".join(text.lower().split())
    lowered = text.lower()
    for fragment in fragments:
        needle = fragment.lower()
        if needle not in lowered and needle not in compact:
            failures.append(f"{rel_path} missing reconciliation fragment: {fragment}")


def _validate_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, ARTIFACT_DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(ARTIFACT_DOC),
        text,
        [
            "Status: active UAA-P1-061 morning reconciliation artifact check",
            "completed_recommendations",
            "deferred_recommendations",
            "rejected_recommendations",
            "blocked_recommendations",
            "docs/backlog/codex_recommendation_log.md",
            "docs/schemas/morning_reconciliation_artifact.schema.json",
            "scripts/verify_morning_reconciliation_artifact.py",
            "does not add routes",
            "Do not store raw prompt content",
        ],
        failures,
    )
    failures.extend(_scan_text(_rel(ARTIFACT_DOC), text))


def _validate_schema(root: Path, failures: list[str]) -> None:
    schema = _read_json(root, SCHEMA_PATH, failures)
    if not schema:
        return
    if schema.get("title") != "uaa_morning_reconciliation_artifact":
        failures.append("morning reconciliation schema title mismatch")
    required = schema.get("required")
    if not isinstance(required, list) or set(required) != REQUIRED_TOP_LEVEL_KEYS:
        failures.append("morning reconciliation schema required keys drifted")
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        failures.append("morning reconciliation schema properties must be an object")
    else:
        schema_version = properties.get("schema_version", {})
        task_ref = properties.get("task_ref", {})
        taxonomy_ref = properties.get("operator_readiness_taxonomy_ref", {})
        log_ref = properties.get("recommendation_log_ref", {})
        if not isinstance(schema_version, dict) or schema_version.get("const") != SCHEMA_VERSION:
            failures.append("morning reconciliation schema must pin schema_version")
        if not isinstance(task_ref, dict) or task_ref.get("const") != TASK_REF:
            failures.append("morning reconciliation schema must pin task_ref")
        if not isinstance(taxonomy_ref, dict) or taxonomy_ref.get("const") != TAXONOMY_REF:
            failures.append("morning reconciliation schema must pin taxonomy ref")
        if not isinstance(log_ref, dict) or log_ref.get("const") != RECOMMENDATION_LOG_REF:
            failures.append("morning reconciliation schema must pin recommendation log ref")
    schema_text = json.dumps(schema, sort_keys=True)
    for bucket, status in BUCKETS.items():
        if bucket not in schema_text or status not in schema_text:
            failures.append(f"morning reconciliation schema missing bucket/status: {bucket}")
    for safety_flag in REQUIRED_SAFETY_FLAGS:
        if safety_flag not in schema_text:
            failures.append(f"morning reconciliation schema missing safety flag: {safety_flag}")
    failures.extend(_scan_text(_rel(SCHEMA_PATH), schema_text))


def _validate_entry(bucket: str, expected_status: str, entry: Any, failures: list[str]) -> None:
    if not isinstance(entry, dict):
        failures.append(f"{bucket} entry must be an object")
        return
    if entry.get("status") != expected_status:
        failures.append(f"{bucket} entry status must be {expected_status}")
    for field_name in (
        "recommendation_ref",
        "source_milestone_ref",
        "safe_summary",
        "reason_code",
        "next_action_ref",
    ):
        if not isinstance(entry.get(field_name), str) or not entry[field_name]:
            failures.append(f"{bucket} entry missing {field_name}")
    evidence_refs = entry.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        failures.append(f"{bucket} entry must include evidence refs")
    if isinstance(entry.get("safe_summary"), str):
        failures.extend(_scan_text(f"template:{bucket}", entry["safe_summary"]))


def _validate_template(root: Path, failures: list[str]) -> None:
    template = _read_json(root, TEMPLATE_PATH, failures)
    if not template:
        return
    if set(template) != REQUIRED_TOP_LEVEL_KEYS:
        failures.append("morning reconciliation template top-level keys drifted")
    if template.get("schema_version") != SCHEMA_VERSION:
        failures.append("morning reconciliation template schema_version mismatch")
    if template.get("task_ref") != TASK_REF:
        failures.append("morning reconciliation template task_ref mismatch")
    if template.get("operator_readiness_taxonomy_ref") != TAXONOMY_REF:
        failures.append("morning reconciliation template taxonomy ref mismatch")
    if template.get("recommendation_log_ref") != RECOMMENDATION_LOG_REF:
        failures.append("morning reconciliation template recommendation log ref mismatch")
    for bucket, expected_status in BUCKETS.items():
        entries = template.get(bucket)
        if not isinstance(entries, list) or not entries:
            failures.append(f"morning reconciliation template missing bucket: {bucket}")
            continue
        for entry in entries:
            _validate_entry(bucket, expected_status, entry, failures)
    safety = template.get("reconciliation_safety")
    if not isinstance(safety, dict) or set(safety) != REQUIRED_SAFETY_FLAGS:
        failures.append("morning reconciliation template safety flags are incomplete")
    elif any(safety.get(flag) is not False for flag in REQUIRED_SAFETY_FLAGS):
        failures.append("morning reconciliation template safety flags must all be false")
    failures.extend(_scan_text(_rel(TEMPLATE_PATH), json.dumps(template, sort_keys=True)))


def _validate_active_links(root: Path, failures: list[str]) -> None:
    docs = {
        _rel(RECOMMENDATION_LOG): _read_text(root, RECOMMENDATION_LOG, failures),
        _rel(CURRENT_BOARD): _read_text(root, CURRENT_BOARD, failures),
        _rel(ROADMAP): _read_text(root, ROADMAP, failures),
    }
    required_fragments = {
        _rel(RECOMMENDATION_LOG): [TASK_REF, "MORNING_RECONCILIATION_ARTIFACT.md"],
        _rel(CURRENT_BOARD): [TASK_REF, "Morning reconciliation artifact check"],
        _rel(ROADMAP): [TASK_REF, "morning reconciliation"],
    }
    for rel_path, text in docs.items():
        _require_fragments(rel_path, text, required_fragments[rel_path], failures)


def validate_morning_reconciliation_artifact(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    _validate_doc(root, failures)
    _validate_schema(root, failures)
    _validate_template(root, failures)
    _validate_active_links(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate UAA-P1-061 morning reconciliation artifacts.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root to validate.")
    args = parser.parse_args(argv)
    failures = validate_morning_reconciliation_artifact(Path(args.root).resolve())
    if failures:
        print("Morning reconciliation artifact verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Morning reconciliation artifact verification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
