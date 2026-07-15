#!/usr/bin/env python3
"""Verify the exact repo-owned extension adapter contract and operator truth."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from ultimate_ai_agent.core.extension_catalog import (
    EXACT_EXTENSION_ADAPTER_REF,
    EXACT_EXTENSION_CAPABILITY_REF,
    ExactExtensionAdapterManifest,
    build_exact_extension_adapter_read_model,
    load_exact_extension_adapter_manifest,
)
from ultimate_ai_agent.core.capability_availability import (
    build_capability_availability_read_model,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs/tooling/exact_extension_adapter_manifest.json"
SCHEMA_PATH = ROOT / "docs/schemas/exact_extension_adapter.schema.json"
SOURCE_PATH = ROOT / "src/ultimate_ai_agent/core/extension_catalog/exact_adapter.py"
SCORE_PATH = ROOT / "docs/benchmarks/extensibility/exact_extension_adapter_score.json"
EXPECTED_EVIDENCE_GATES = {
    "evidence-gate:extension:declaration-and-schema",
    "evidence-gate:extension:runtime-truth-dimensions",
    "evidence-gate:extension:exact-core-owned-adapter",
    "evidence-gate:extension:request-scoped-authority",
    "evidence-gate:extension:replay-receipts-redaction",
    "evidence-gate:extension:api-cli-visibility",
    "evidence-gate:extension:adversarial-failure-proof",
}


class VerificationError(RuntimeError):
    """Raised when exact extension evidence drifts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def verify() -> None:
    manifest = load_exact_extension_adapter_manifest(MANIFEST_PATH)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(manifest.model_dump(mode="json")),
        key=lambda error: list(error.path),
    )
    _require(not errors, "exact extension manifest does not match schema")
    _require(
        ExactExtensionAdapterManifest.model_json_schema() == schema,
        "exact extension schema drifted from Python contract",
    )
    evidence = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    _require(
        evidence["schema_version"] == "uaa_exact_extension_lane_evidence.v1",
        "exact extension lane evidence schema drifted",
    )
    _require(evidence["not_component_score"] is True, "lane evidence claims a score")
    _require("score" not in evidence, "lane evidence retains a numeric score")
    _require("score_basis" not in evidence, "lane evidence retains score weights")
    _require(
        evidence["aggregate_component_score"] is None,
        "lane evidence invents an aggregate component score",
    )
    _require(evidence["confidence"] == "high", "evidence confidence drifted")
    _require(evidence["scope"] == "one_core_owned_metadata_adapter_lane", "lane scope drifted")
    _require(
        len(evidence["gate_results"])
        == evidence["passed_gate_count"]
        == evidence["total_gate_count"],
        "lane evidence gate counts do not reconcile",
    )
    _require(
        all(item["status"] == "passed" for item in evidence["gate_results"]),
        "an exact extension lane evidence gate is not passed",
    )
    gate_refs = [item["gate_ref"] for item in evidence["gate_results"]]
    _require(len(gate_refs) == len(set(gate_refs)), "lane evidence gates are duplicated")
    _require(set(gate_refs) == EXPECTED_EVIDENCE_GATES, "lane evidence gates drifted")
    for forbidden_flag in (
        "authority_granted_by_score",
        "raw_content_persisted",
        "local_paths_persisted",
        "credentials_persisted",
    ):
        _require(
            evidence[forbidden_flag] is False,
            f"unsafe lane evidence flag: {forbidden_flag}",
        )

    read_model = build_exact_extension_adapter_read_model()
    _require(
        not read_model.ready_for_request_scoped_evaluation,
        "missing observations incorrectly claim runtime readiness",
    )
    _require(bool(read_model.blocker_codes), "fail-closed read model lacks blockers")
    _require(not read_model.invocation_authorized, "readiness claims authority")
    _require(not read_model.execution_performed, "read model claims execution")
    _require(
        not read_model.global_extension_runtime_enabled,
        "global extension runtime was enabled",
    )
    _require(
        not read_model.arbitrary_runtime_import_enabled,
        "arbitrary runtime import was enabled",
    )

    availability = build_capability_availability_read_model()
    snapshot = next(
        (
            item
            for item in availability.snapshots
            if item.adapter_ref == EXACT_EXTENSION_ADAPTER_REF
        ),
        None,
    )
    _require(snapshot is not None, "exact extension availability snapshot missing")
    _require(
        snapshot.capability_ref == EXACT_EXTENSION_CAPABILITY_REF,
        "exact extension availability capability drifted",
    )
    _require(
        snapshot.runtime_readiness_status == "unknown",
        "static availability invented current runtime readiness",
    )
    _require(
        snapshot.authority_posture == "lease_required",
        "availability does not retain request-scoped lease posture",
    )

    source = SOURCE_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "importlib.import_module",
        "SourceFileLoader",
        "spec_from_file_location",
        "exec(",
        "eval(",
        "subprocess.",
        "requests.",
        "httpx.",
    ):
        _require(forbidden not in source, f"forbidden runtime mechanism: {forbidden}")

    env = {"PYTHONPATH": "src", "PATH": os.environ.get("PATH", "")}
    cli = subprocess.run(
        [sys.executable, "scripts/dev/uaa_extensions.py", "inspect-exact-adapter"],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    _require(
        "General extension runtime: disabled" in cli.stdout,
        "human CLI omits the general-runtime boundary",
    )
    _require(
        "Callability still requires fresh" in cli.stdout,
        "human CLI omits request-scoped authority",
    )
    _require(
        "Ready for request-scoped evaluation: no" in cli.stdout,
        "human CLI invents current runtime readiness",
    )


def main() -> int:
    try:
        verify()
    except (VerificationError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"exact extension adapter verification failed: {exc}", file=sys.stderr)
        return 1
    print("exact extension adapter verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
