from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts import verify_product_loop_012_private_trial_script as pl012
from ultimate_ai_agent.core.readiness import (
    PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_BLOCKED_REFS,
    PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES,
    PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF,
    PrivateProductLoopTrialScript,
    PrivateProductLoopTrialStep,
    build_private_product_loop_trial_script,
)


ROOT = Path(__file__).resolve().parents[1]
DENIED_FLAGS = [
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_readiness_claim_enabled",
    "production_authority_enabled",
    "connector_runtime_enabled",
    "connector_write_enabled",
    "provider_model_authority_allowed",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "provider_sdk_call_enabled",
    "live_web_enabled",
    "unrestricted_shell_enabled",
    "shell_subprocess_execution_enabled",
    "shell_browser_execution_enabled",
    "telemetry_export_enabled",
    "remote_execution_enabled",
    "account_sync_enabled",
    "crm_write_enabled",
    "memory_write_authorized",
    "action_execution_enabled",
    "code_apply_execution_enabled",
    "runtime_authority_added",
    "backend_route_added",
]


def test_product_loop_trial_script_defines_private_manual_loop() -> None:
    script = build_private_product_loop_trial_script()
    payload = script.model_dump(mode="json")

    assert payload["contract_ref"] == PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF
    assert payload["milestone_ref"] == "milestone:product-loop-012"
    assert [step["surface"] for step in payload["manual_steps"]] == (
        PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES
    )
    assert [item["surface"] for item in payload["acceptance_ledger"]] == (
        PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES
    )
    assert all(
        item["review_state"] == "pending_operator_review"
        for item in payload["acceptance_ledger"]
    )
    assert set(PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )
    assert payload["local_private_only"] is True
    assert payload["safe_refs_only"] is True
    assert payload["manual_operator_review_required"] is True
    for flag in DENIED_FLAGS:
        assert payload[flag] is False


def test_product_loop_trial_json_artifact_matches_builder() -> None:
    artifact = ROOT / "docs/control_center/private_product_loop_trial_script_v1.json"
    parsed = PrivateProductLoopTrialScript.model_validate_json(
        artifact.read_text(encoding="utf-8")
    )

    assert parsed == build_private_product_loop_trial_script()


def test_product_loop_trial_rejects_authority_and_private_content() -> None:
    payload = build_private_product_loop_trial_script().model_dump(mode="json")

    unsafe = json.loads(json.dumps(payload))
    unsafe["provider_model_call_enabled"] = True
    with pytest.raises(ValidationError):
        PrivateProductLoopTrialScript(**unsafe)

    unsafe_step = json.loads(json.dumps(payload["manual_steps"][0]))
    unsafe_step["telemetry_export_enabled"] = True
    with pytest.raises(ValidationError):
        PrivateProductLoopTrialStep(**unsafe_step)

    raw_step = json.loads(json.dumps(payload["manual_steps"][0]))
    raw_step["safe_checklist_summary"] = "raw prompt material"
    with pytest.raises(ValidationError):
        PrivateProductLoopTrialStep(**raw_step)

    raw_ref_step = json.loads(json.dumps(payload["manual_steps"][0]))
    raw_ref_step["evidence_refs"] = ["evidence-ref:raw_prompt"]
    with pytest.raises(ValidationError):
        PrivateProductLoopTrialStep(**raw_ref_step)


def test_product_loop_trial_rejects_duplicate_or_extra_surfaces() -> None:
    payload = build_private_product_loop_trial_script().model_dump(mode="json")
    duplicate = json.loads(json.dumps(payload))
    duplicate["manual_steps"].append(json.loads(json.dumps(duplicate["manual_steps"][0])))

    with pytest.raises(ValidationError):
        PrivateProductLoopTrialScript(**duplicate)

    reordered = json.loads(json.dumps(payload))
    reordered["acceptance_ledger"] = list(reversed(reordered["acceptance_ledger"]))

    with pytest.raises(ValidationError):
        PrivateProductLoopTrialScript(**reordered)


def test_product_loop_trial_cli_matches_safe_schema() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_product_loop_trial_script.py"),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    payload = json.loads(completed.stdout)

    assert payload["ok"] is True
    assert payload["contract_ref"] == PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF
    assert payload["surfaces"] == PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES
    assert len(payload["acceptance_ledger"]) == len(
        PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES
    )
    assert set(payload["denied_flags"]) == set(DENIED_FLAGS)
    assert not any(payload["denied_flags"].values())
    assert payload["local_private_only"] is True
    assert payload["safe_refs_only"] is True


def test_product_loop_trial_cli_defaults_to_human_checklist() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/inspect_product_loop_trial_script.py")],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert "Manual checklist:" in completed.stdout
    assert "Acceptance ledger:" in completed.stdout
    assert "Denied authority:" in completed.stdout
    assert '"manual_steps"' not in completed.stdout


def test_product_loop_012_verifier_passes_current_repo() -> None:
    assert pl012.main() == 0
