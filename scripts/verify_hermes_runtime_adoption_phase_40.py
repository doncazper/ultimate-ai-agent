#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_TRAJECTORY_EVAL_CAPTURE.md"
MANIFEST = ROOT / "docs/runtime/hermes_runtime_trajectory_eval_manifest.json"
SCHEMA = ROOT / "docs/schemas/hermes_runtime_trajectory_eval.schema.json"
TEMPLATE = ROOT / "reports/hermes_runtime_adoption/trajectory_eval_report_template.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
DOC_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"{path} did not contain a JSON object")
    return payload


def main() -> int:
    failures: list[str] = []

    for path in [DOC, MANIFEST, SCHEMA, TEMPLATE, PRODUCT_TRUTH, DOC_INDEX]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    manifest = _load_json(MANIFEST)
    schema = _load_json(SCHEMA)
    doc_text = DOC.read_text(encoding="utf-8")
    template_text = TEMPLATE.read_text(encoding="utf-8")
    product_truth_text = PRODUCT_TRUTH.read_text(encoding="utf-8")
    index_text = DOC_INDEX.read_text(encoding="utf-8")

    if manifest.get("schema_version") != "hermes_runtime_trajectory_eval_manifest.v1":
        failures.append("manifest schema_version drifted")
    if manifest.get("status") != "repo_safe_manifest_only":
        failures.append("manifest status is not repo-safe")

    expected_runtime_refs = {
        "runtime-ref:uaa-native-supervisor",
        "runtime-ref:hermes-agent",
        "runtime-ref:codex",
        "runtime-ref:claude",
        "runtime-ref:local-model",
    }
    actual_runtime_refs = {
        str(item.get("runtime_ref"))
        for item in manifest.get("runtime_refs", [])
        if isinstance(item, dict)
    }
    missing_runtime_refs = expected_runtime_refs - actual_runtime_refs
    if missing_runtime_refs:
        failures.append(f"manifest missing runtime refs: {sorted(missing_runtime_refs)}")

    expected_dimensions = {
        "eval-dimension:task_completion",
        "eval-dimension:cost",
        "eval-dimension:safety",
        "eval-dimension:proof",
        "eval-dimension:usefulness",
    }
    actual_dimensions = {
        str(item.get("dimension_ref"))
        for item in manifest.get("benchmark_dimensions", [])
        if isinstance(item, dict)
    }
    missing_dimensions = expected_dimensions - actual_dimensions
    if missing_dimensions:
        failures.append(f"manifest missing eval dimensions: {sorted(missing_dimensions)}")

    policy = manifest.get("trajectory_record_policy", {})
    if not isinstance(policy, dict):
        failures.append("manifest trajectory_record_policy is not an object")
        policy = {}
    for required_true in [
        "safe_refs_only",
        "redacted_summaries_only",
        "bounded_previews_only",
    ]:
        if policy.get(required_true) is not True:
            failures.append(f"manifest policy {required_true} must be true")
    for required_false in [
        "raw_transcript_export_enabled",
        "raw_prompt_persistence_enabled",
        "raw_response_persistence_enabled",
        "raw_provider_payload_persistence_enabled",
        "raw_log_persistence_enabled",
        "raw_local_path_persistence_enabled",
        "model_calls_enabled",
        "provider_sdk_calls_enabled",
        "external_upload_enabled",
        "automated_background_evals_enabled",
        "remote_benchmark_execution_enabled",
        "control_center_mints_authority",
    ]:
        if policy.get(required_false) is not False:
            failures.append(f"manifest policy {required_false} must be false")

    blocked_refs = set(manifest.get("blocked_authority_refs", []))
    for expected in [
        "blocked-authority-ref:trajectory-raw-transcript-export",
        "blocked-authority-ref:trajectory-model-call",
        "blocked-authority-ref:trajectory-provider-sdk-call",
        "blocked-authority-ref:trajectory-external-upload",
        "blocked-authority-ref:trajectory-background-eval",
        "blocked-authority-ref:trajectory-remote-benchmark",
        "blocked-authority-ref:trajectory-score-action-authority",
    ]:
        if expected not in blocked_refs:
            failures.append(f"missing blocked authority ref {expected}")

    if schema.get("additionalProperties") is not False:
        failures.append("trajectory schema must forbid additional properties")
    if schema.get("properties", {}).get("schema_version", {}).get("const") != (
        "hermes_runtime_trajectory_eval_record.v1"
    ):
        failures.append("trajectory record schema_version const drifted")
    schema_properties = set(schema.get("properties", {}))
    forbidden_schema_properties = {
        "raw_transcript",
        "raw_prompt",
        "raw_response",
        "provider_payload",
        "raw_log",
        "local_path",
        "username",
        "hostname",
        "credential",
        "secret",
    }
    present_forbidden = schema_properties & forbidden_schema_properties
    if present_forbidden:
        failures.append(f"schema exposes forbidden fields: {sorted(present_forbidden)}")

    redaction = schema.get("properties", {}).get("redaction", {}).get("properties", {})
    if redaction.get("safe_refs_only", {}).get("const") is not True:
        failures.append("schema redaction.safe_refs_only must be true")
    if redaction.get("redacted_summaries_only", {}).get("const") is not True:
        failures.append("schema redaction.redacted_summaries_only must be true")
    if redaction.get("raw_material_persisted", {}).get("const") is not False:
        failures.append("schema redaction.raw_material_persisted must be false")

    for expected in [
        "Full-Strength",
        "Repo-Safe",
        "Blocked / Needs Authority",
        "Exact Promotion Path",
        "raw transcript export",
        "model or provider calls",
        "external result upload",
        "automated background eval runs",
        "Planning text and manifest presence do not grant runtime invocation",
    ]:
        if expected not in doc_text:
            failures.append(f"doc missing {expected}")

    for expected in [
        "Benchmark Dimensions",
        "Trajectory Records",
        "Safety And Authority",
        "Known Gaps",
        "Decision",
        "must not contain raw prompt",
    ]:
        if expected not in template_text:
            failures.append(f"report template missing {expected}")

    for expected in [
        "Hermes Runtime Adoption Phase 40",
        "UAA_HERMES_RUNTIME_TRAJECTORY_EVAL_CAPTURE.md",
        "hermes_runtime_trajectory_eval_manifest.json",
        "hermes_runtime_trajectory_eval.schema.json",
        "trajectory_eval_report_template.md",
    ]:
        if expected not in product_truth_text:
            failures.append(f"product truth missing {expected}")

    if "Hermes runtime trajectory eval capture" not in index_text:
        failures.append("documentation index missing trajectory eval entry")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 40 trajectory eval capture verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
