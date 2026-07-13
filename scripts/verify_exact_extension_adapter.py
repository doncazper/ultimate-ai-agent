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
    score = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    _require(score["score"] == 9.0, "exact extension evidence score drifted")
    _require(score["confidence"] == "high", "evidence confidence drifted")
    _require(
        sum(item["points"] for item in score["score_basis"]) == score["score"],
        "evidence score basis does not reconcile",
    )
    _require(
        all(item["status"] == "passed" for item in score["score_basis"]),
        "an extensibility score gate is not passed",
    )
    for forbidden_flag in (
        "authority_granted_by_score",
        "raw_content_persisted",
        "local_paths_persisted",
        "credentials_persisted",
    ):
        _require(score[forbidden_flag] is False, f"unsafe score flag: {forbidden_flag}")

    read_model = build_exact_extension_adapter_read_model()
    _require(
        read_model.ready_for_request_scoped_evaluation,
        "exact extension reference adapter is not ready for policy evaluation",
    )
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
