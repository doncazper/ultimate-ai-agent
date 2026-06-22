#!/usr/bin/env python3
"""Verify the UAA-P1-060 operator-readiness status taxonomy bindings.

This verifier is inspection-only. It reads fixed repo-local docs and JSON
contracts to ensure readiness/status semantics stay aligned across the active
board, route status manifest, product-language rules, release evidence packet,
release lane manifest, and Foundation Gate release-lane summary path.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TAXONOMY_REF = "docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md"
TAXONOMY_PATH = ROOT / TAXONOMY_REF
ROUTE_STATUS_MANIFEST_PATH = ROOT / "docs/control_center/route_status_manifest.json"
ROUTE_STATUS_DOC_PATH = ROOT / "docs/control_center/ROUTE_STATUS_MANIFEST.md"
PRODUCT_LANGUAGE_RULES_PATH = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
RELEASE_LANES_DOC_PATH = ROOT / "docs/production/RELEASE_VERIFICATION_LANES.md"
RELEASE_PACKET_DOC_PATH = ROOT / "docs/production/RELEASE_EVIDENCE_PACKET.md"
RELEASE_PACKET_SCHEMA_PATH = ROOT / "docs/schemas/release_evidence_packet.schema.json"
RELEASE_PACKET_TEMPLATE_PATH = ROOT / "docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json"
RUN_FOUNDATION_GATE_PATH = ROOT / "scripts/run_foundation_gate.py"
GATE_REPORTS_PATH = ROOT / "src/ultimate_ai_agent/core/gate/reports.py"

CANONICAL_STATUSES = {
    "shipped",
    "planned",
    "blocked",
    "skipped",
    "mock_only",
    "not_scoped",
    "partial",
    "status_only",
    "preview_only",
    "validation_only",
    "review_only",
    "local_ui_state_only",
    "unknown",
    "needs_review",
    "accepted_failure",
}

ROUTE_STATUS_TAXONOMY_MAP = {
    "status_available_not_completion": "status_only",
    "preview_available_not_execution": "preview_only",
    "partial_backend_not_product_ready": "partial",
    "founder_loop_v1_proofed": "shipped",
    "mock_only_not_product_ready": "mock_only",
    "local_ui_state_only_not_evidence": "local_ui_state_only",
    "blocked_missing_backend": "blocked",
}

RELEASE_EVIDENCE_STATUSES = {
    "pass",
    "fail",
    "skipped",
    "blocked",
    "accepted_failure",
}

FOUNDATION_GATE_STATUS_FRAGMENTS = {
    "FoundationGateStatus.passed",
    "FoundationGateStatus.failed",
    "FoundationGateStatus.warning",
    "FoundationGateStatus.blocked",
}


def _read_text(path: Path, failures: list[str]) -> str:
    if not path.exists():
        failures.append(f"missing required file: {path.relative_to(ROOT).as_posix()}")
        return ""
    return path.read_text(encoding="utf-8")


def _read_json(path: Path, failures: list[str]) -> dict[str, Any]:
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


def _require_fragments(
    *,
    rel_path: str,
    text: str,
    fragments: set[str] | list[str] | tuple[str, ...],
    failures: list[str],
) -> None:
    lowered = text.lower()
    compact = " ".join(lowered.split())
    for fragment in fragments:
        lowered_fragment = fragment.lower()
        if lowered_fragment not in lowered and lowered_fragment not in compact:
            failures.append(f"{rel_path} missing taxonomy fragment: {fragment}")


def _validate_taxonomy_doc(root: Path, failures: list[str]) -> None:
    doc_path = root / TAXONOMY_REF
    text = _read_text(doc_path, failures)
    if not text:
        return
    _require_fragments(
        rel_path=TAXONOMY_REF,
        text=text,
        fragments=[
            "Status: active UAA-P1-060 operator-readiness status taxonomy",
            "docs/control_center/route_status_manifest.json",
            "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
            "docs/production/RELEASE_EVIDENCE_PACKET.md",
            "scripts/run_foundation_gate.py",
            "does not add",
            "accepted_failure",
        ],
        failures=failures,
    )
    for status in CANONICAL_STATUSES:
        if f"`{status}`" not in text:
            failures.append(f"{TAXONOMY_REF} missing canonical status: {status}")
    for route_status, canonical_status in ROUTE_STATUS_TAXONOMY_MAP.items():
        if f"`{route_status}`" not in text or f"`{canonical_status}`" not in text:
            failures.append(
                f"{TAXONOMY_REF} missing route mapping: "
                f"{route_status} -> {canonical_status}"
            )
    for status in RELEASE_EVIDENCE_STATUSES:
        if f"`{status}`" not in text:
            failures.append(f"{TAXONOMY_REF} missing release evidence status: {status}")


def _validate_route_status_manifest(root: Path, failures: list[str]) -> None:
    manifest = _read_json(root / ROUTE_STATUS_MANIFEST_PATH.relative_to(ROOT), failures)
    if not manifest:
        return
    if manifest.get("operator_readiness_taxonomy_ref") != TAXONOMY_REF:
        failures.append("route status manifest taxonomy ref mismatch")
    allowed = manifest.get("allowed_release_statuses")
    if not isinstance(allowed, list):
        failures.append("route status manifest allowed_release_statuses must be a list")
        allowed = []
    allowed_set = {str(status) for status in allowed}
    if allowed_set != set(ROUTE_STATUS_TAXONOMY_MAP):
        failures.append("route status manifest allowed release statuses drifted from taxonomy map")
    mapping = manifest.get("release_status_taxonomy_map")
    if mapping != ROUTE_STATUS_TAXONOMY_MAP:
        failures.append("route status manifest release_status_taxonomy_map drifted")
    for section_name, status_key in (("surfaces", "release_status"), ("visible_actions", "release_status")):
        entries = manifest.get(section_name)
        if not isinstance(entries, list):
            failures.append(f"route status manifest {section_name} must be a list")
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                failures.append(f"route status manifest {section_name} entry {index} must be an object")
                continue
            status = entry.get(status_key)
            if status not in ROUTE_STATUS_TAXONOMY_MAP:
                failures.append(f"route status manifest {section_name} entry {index} has unmapped status")

    doc_text = _read_text(root / ROUTE_STATUS_DOC_PATH.relative_to(ROOT), failures)
    _require_fragments(
        rel_path=ROUTE_STATUS_DOC_PATH.relative_to(ROOT).as_posix(),
        text=doc_text,
        fragments=[TAXONOMY_REF, "status_only", "preview_only", "mock_only"],
        failures=failures,
    )


def _validate_product_language_rules(root: Path, failures: list[str]) -> None:
    text = _read_text(root / PRODUCT_LANGUAGE_RULES_PATH.relative_to(ROOT), failures)
    _require_fragments(
        rel_path=PRODUCT_LANGUAGE_RULES_PATH.relative_to(ROOT).as_posix(),
        text=text,
        fragments=[
            TAXONOMY_REF,
            "shipped",
            "planned",
            "blocked",
            "skipped prerequisite",
            "mock only",
            "not scoped",
            "unknown",
            "needs review",
            "accepted failure",
        ],
        failures=failures,
    )


def _validate_release_evidence(root: Path, failures: list[str]) -> None:
    doc_text = _read_text(root / RELEASE_PACKET_DOC_PATH.relative_to(ROOT), failures)
    _require_fragments(
        rel_path=RELEASE_PACKET_DOC_PATH.relative_to(ROOT).as_posix(),
        text=doc_text,
        fragments=[TAXONOMY_REF, "operator_readiness_taxonomy_ref", "verification statuses"],
        failures=failures,
    )
    schema = _read_json(root / RELEASE_PACKET_SCHEMA_PATH.relative_to(ROOT), failures)
    template = _read_json(root / RELEASE_PACKET_TEMPLATE_PATH.relative_to(ROOT), failures)
    if schema:
        required = schema.get("required")
        if not isinstance(required, list) or "operator_readiness_taxonomy_ref" not in required:
            failures.append("release evidence schema must require operator_readiness_taxonomy_ref")
        properties = schema.get("properties")
        taxonomy_prop = properties.get("operator_readiness_taxonomy_ref") if isinstance(properties, dict) else None
        if not isinstance(taxonomy_prop, dict) or taxonomy_prop.get("const") != TAXONOMY_REF:
            failures.append("release evidence schema taxonomy ref const mismatch")
    if template:
        if template.get("operator_readiness_taxonomy_ref") != TAXONOMY_REF:
            failures.append("release evidence template taxonomy ref mismatch")
        semantics = template.get("status_semantics")
        if not isinstance(semantics, dict) or set(semantics) != RELEASE_EVIDENCE_STATUSES:
            failures.append("release evidence template status semantics drifted")


def _validate_release_lanes_and_foundation_gate(root: Path, failures: list[str]) -> None:
    lanes_doc = _read_text(root / RELEASE_LANES_DOC_PATH.relative_to(ROOT), failures)
    _require_fragments(
        rel_path=RELEASE_LANES_DOC_PATH.relative_to(ROOT).as_posix(),
        text=lanes_doc,
        fragments=[TAXONOMY_REF, "pass", "fail", "skipped", "blocked", "accepted_failure"],
        failures=failures,
    )
    try:
        from scripts.verify_release_lanes import build_release_lane_manifest
    except Exception as exc:  # pragma: no cover - defensive import guard.
        failures.append(f"could not import release lane manifest builder: {exc}")
        return

    manifest = build_release_lane_manifest()
    semantics = manifest.get("status_semantics")
    if not isinstance(semantics, dict) or set(semantics) != RELEASE_EVIDENCE_STATUSES:
        failures.append("release lane manifest status semantics drifted from taxonomy")

    run_gate_text = _read_text(root / RUN_FOUNDATION_GATE_PATH.relative_to(ROOT), failures)
    _require_fragments(
        rel_path=RUN_FOUNDATION_GATE_PATH.relative_to(ROOT).as_posix(),
        text=run_gate_text,
        fragments=["status_semantics", "Lane Status Semantics", "release_verification_lanes"],
        failures=failures,
    )
    reports_text = _read_text(root / GATE_REPORTS_PATH.relative_to(ROOT), failures)
    for fragment in FOUNDATION_GATE_STATUS_FRAGMENTS:
        if fragment not in reports_text:
            failures.append(f"Foundation Gate report status fragment missing: {fragment}")
    _require_fragments(
        rel_path=GATE_REPORTS_PATH.relative_to(ROOT).as_posix(),
        text=reports_text,
        fragments=["FoundationGateReleaseLaneSummary", "status_semantics"],
        failures=failures,
    )


def validate_operator_readiness_taxonomy(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    _validate_taxonomy_doc(root, failures)
    _validate_route_status_manifest(root, failures)
    _validate_product_language_rules(root, failures)
    _validate_release_evidence(root, failures)
    _validate_release_lanes_and_foundation_gate(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate UAA-P1-060 readiness taxonomy bindings.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root to validate.")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    failures = validate_operator_readiness_taxonomy(root)
    if failures:
        print("Operator readiness taxonomy verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Operator readiness taxonomy verification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
