import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/runtime/hermes_runtime_trajectory_eval_manifest.json"
SCHEMA = ROOT / "docs/schemas/hermes_runtime_trajectory_eval.schema.json"


def test_trajectory_eval_manifest_keeps_runtime_execution_blocked() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    policy = manifest["trajectory_record_policy"]

    assert manifest["schema_version"] == "hermes_runtime_trajectory_eval_manifest.v1"
    assert manifest["status"] == "repo_safe_manifest_only"
    assert policy["safe_refs_only"] is True
    assert policy["redacted_summaries_only"] is True
    assert policy["raw_transcript_export_enabled"] is False
    assert policy["model_calls_enabled"] is False
    assert policy["provider_sdk_calls_enabled"] is False
    assert policy["external_upload_enabled"] is False
    assert policy["automated_background_evals_enabled"] is False
    assert policy["control_center_mints_authority"] is False
    assert {
        "runtime-ref:uaa-native-supervisor",
        "runtime-ref:hermes-agent",
        "runtime-ref:codex",
        "runtime-ref:claude",
        "runtime-ref:local-model",
    }.issubset({runtime["runtime_ref"] for runtime in manifest["runtime_refs"]})


def test_trajectory_eval_schema_contains_only_safe_refs_and_redacted_summaries() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    properties = schema["properties"]

    assert schema["additionalProperties"] is False
    assert properties["schema_version"]["const"] == (
        "hermes_runtime_trajectory_eval_record.v1"
    )
    assert "raw_transcript" not in properties
    assert "raw_prompt" not in properties
    assert "raw_response" not in properties
    assert "provider_payload" not in properties
    assert properties["redaction"]["properties"]["safe_refs_only"]["const"] is True
    assert properties["redaction"]["properties"]["redacted_summaries_only"]["const"] is True
    assert properties["redaction"]["properties"]["raw_material_persisted"]["const"] is False


def test_phase_40_verifier_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/verify_hermes_runtime_adoption_phase_40.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "trajectory eval capture verifier passed" in result.stdout
