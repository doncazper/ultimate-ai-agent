#!/usr/bin/env python3
"""Validate the release evidence packet schema and template.

This verifier is inspection-only. It validates release packet structure and safe
evidence rules, but it does not execute release checks or create artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKET_SCHEMA_VERSION = "uaa_release_evidence_packet.v1"
PACKET_TASK_REF = "UAA-P1-044"
SCHEMA_PATH = ROOT / "docs" / "schemas" / "release_evidence_packet.schema.json"
TEMPLATE_PATH = ROOT / "docs" / "production" / "RELEASE_EVIDENCE_PACKET_TEMPLATE.json"
DOC_PATH = ROOT / "docs" / "production" / "RELEASE_EVIDENCE_PACKET.md"
REQUIRED_STATUS_VALUES = {
    "pass",
    "fail",
    "skipped",
    "blocked",
    "accepted_failure",
}
REQUIRED_LANE_IDS = {
    "docs",
    "openapi",
    "api-safety",
    "security-redaction",
    "local-model-e2e",
    "durability",
    "frontend",
    "performance",
}
REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "task_ref",
    "packet_id",
    "release_candidate_ref",
    "commit_ref",
    "baseline_ref",
    "created_at_utc",
    "status_semantics",
    "verification_lanes",
    "report_refs",
    "accepted_failures",
    "artifact_hashes",
    "release_blockers",
    "not_scoped",
    "rollback_notes",
    "non_goals",
    "packet_safety",
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
FORBIDDEN_OVERCLAIMS = {
    "public distribution is available",
    "public release is available",
    "signed installer is ready",
    "hosted production support is available",
    "grants production authority",
    "shell execution is enabled",
    "subprocess execution is enabled",
    "connector writes are enabled",
    "plugin runtime import is enabled",
    "mobile control is enabled",
    "broad autonomy is enabled",
}
HASH_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")


def _load_json(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.exists():
        failures.append(f"missing required file: {path.relative_to(ROOT).as_posix()}")
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON in {path.relative_to(ROOT).as_posix()}: {exc.msg}")
        return {}
    if not isinstance(loaded, dict):
        failures.append(f"{path.relative_to(ROOT).as_posix()} must contain a JSON object")
        return {}
    return loaded


def _scan_text_for_forbidden_fragments(rel_path: str, text: str) -> list[str]:
    lowered = text.lower()
    failures: list[str] = []
    for fragment in sorted(FORBIDDEN_PRIVATE_FRAGMENTS):
        if fragment in lowered:
            failures.append(f"{rel_path} contains forbidden private/raw fragment: {fragment}")
    for fragment in sorted(FORBIDDEN_OVERCLAIMS):
        if fragment in lowered:
            failures.append(f"{rel_path} contains unsupported release claim: {fragment}")
    return failures


def _template_lane_ids(template: dict[str, Any]) -> set[str]:
    lanes = template.get("verification_lanes")
    if not isinstance(lanes, list):
        return set()
    return {
        lane.get("lane_id")
        for lane in lanes
        if isinstance(lane, dict) and isinstance(lane.get("lane_id"), str)
    }


def validate_release_evidence_packet(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    schema = _load_json(root / SCHEMA_PATH.relative_to(ROOT), failures)
    template = _load_json(root / TEMPLATE_PATH.relative_to(ROOT), failures)

    doc = root / DOC_PATH.relative_to(ROOT)
    if not doc.exists():
        failures.append("missing release evidence packet doc")
    else:
        doc_text = doc.read_text(encoding="utf-8")
        for fragment in [
            "Status: active UAA-P1-044 release evidence packet format",
            "commit_ref",
            "verification_lanes",
            "report_refs",
            "accepted_failures",
            "artifact_hashes",
            "release_blockers",
            "not_scoped",
            "rollback_notes",
            "non_goals",
            "packet_safety",
            "pass",
            "fail",
            "skipped",
            "blocked",
            "accepted_failure",
            "No production authority",
        ]:
            if fragment not in doc_text:
                failures.append(f"release evidence packet doc missing fragment: {fragment}")
        failures.extend(
            _scan_text_for_forbidden_fragments(
                DOC_PATH.relative_to(ROOT).as_posix(),
                doc_text,
            )
        )

    if schema:
        if schema.get("title") != "uaa_release_evidence_packet":
            failures.append("release evidence schema title mismatch")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            failures.append("release evidence schema properties must be an object")
        else:
            schema_version = properties.get("schema_version", {})
            task_ref = properties.get("task_ref", {})
            if not isinstance(schema_version, dict) or schema_version.get("const") != PACKET_SCHEMA_VERSION:
                failures.append("release evidence schema must pin schema_version")
            if not isinstance(task_ref, dict) or task_ref.get("const") != PACKET_TASK_REF:
                failures.append("release evidence schema must pin task_ref")
        required = schema.get("required")
        if not isinstance(required, list) or set(required) != REQUIRED_TOP_LEVEL_KEYS:
            failures.append("release evidence schema required keys drifted")
        schema_text = json.dumps(schema, sort_keys=True)
        for status in REQUIRED_STATUS_VALUES:
            if status not in schema_text:
                failures.append(f"release evidence schema missing status: {status}")
        for safety_flag in REQUIRED_SAFETY_FLAGS:
            if safety_flag not in schema_text:
                failures.append(f"release evidence schema missing safety flag: {safety_flag}")
        failures.extend(
            _scan_text_for_forbidden_fragments(
                SCHEMA_PATH.relative_to(ROOT).as_posix(),
                schema_text,
            )
        )

    if template:
        if set(template) != REQUIRED_TOP_LEVEL_KEYS:
            failures.append("release evidence template top-level keys drifted")
        if template.get("schema_version") != PACKET_SCHEMA_VERSION:
            failures.append("release evidence template schema_version mismatch")
        if template.get("task_ref") != PACKET_TASK_REF:
            failures.append("release evidence template task_ref mismatch")
        semantics = template.get("status_semantics")
        if not isinstance(semantics, dict) or set(semantics) != REQUIRED_STATUS_VALUES:
            failures.append("release evidence template status semantics are incomplete")
        lane_ids = _template_lane_ids(template)
        if lane_ids != REQUIRED_LANE_IDS:
            failures.append("release evidence template lane coverage is incomplete")
        safety = template.get("packet_safety")
        if not isinstance(safety, dict) or set(safety) != REQUIRED_SAFETY_FLAGS:
            failures.append("release evidence template safety flags are incomplete")
        elif any(safety.get(flag) is not False for flag in REQUIRED_SAFETY_FLAGS):
            failures.append("release evidence template safety flags must all be false")
        blockers = template.get("release_blockers")
        if not isinstance(blockers, list) or not blockers:
            failures.append("release evidence template must keep a placeholder blocker")
        elif not any(
            isinstance(blocker, dict) and blocker.get("status") == "open"
            for blocker in blockers
        ):
            failures.append("release evidence template must mark placeholders as open blockers")
        artifact_hashes = template.get("artifact_hashes")
        if not isinstance(artifact_hashes, list) or not artifact_hashes:
            failures.append("release evidence template must include artifact hash structure")
        else:
            for artifact in artifact_hashes:
                if not isinstance(artifact, dict):
                    failures.append("release evidence artifact hash entry must be an object")
                    continue
                if artifact.get("hash_algorithm") != "sha256":
                    failures.append("release evidence artifact hash must use sha256")
                value = artifact.get("hash_value")
                if not isinstance(value, str) or HASH_PATTERN.match(value) is None:
                    failures.append("release evidence artifact hash must use sha256:<64 hex>")
        template_text = json.dumps(template, sort_keys=True)
        failures.extend(
            _scan_text_for_forbidden_fragments(
                TEMPLATE_PATH.relative_to(ROOT).as_posix(),
                template_text,
            )
        )

    return failures


def build_release_evidence_packet_summary(root: Path = ROOT) -> dict[str, Any]:
    failures = validate_release_evidence_packet(root)
    return {
        "schema_version": PACKET_SCHEMA_VERSION,
        "task_ref": PACKET_TASK_REF,
        "overall_status": "pass" if not failures else "fail",
        "schema_ref": "schema:release-evidence-packet",
        "template_ref": "template:release-evidence-packet",
        "required_status_values": sorted(REQUIRED_STATUS_VALUES),
        "required_lane_ids": sorted(REQUIRED_LANE_IDS),
        "validation_failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable summary")
    args = parser.parse_args(argv)

    summary = build_release_evidence_packet_summary()
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif summary["validation_failures"]:
        for failure in summary["validation_failures"]:
            print(f"FAIL: {failure}")
    else:
        print("OK: Release evidence packet schema and template are safe and complete")
    return 0 if summary["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
