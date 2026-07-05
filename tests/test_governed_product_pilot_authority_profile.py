import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.runtime_gateway import (
    GOVERNED_PRODUCT_PILOT_PROFILE_REF,
    GOVERNED_PRODUCT_PILOT_REQUIRED_BLOCKED_AUTHORITY_REFS,
    GovernedProductPilotAuthorityProfileReadModel,
    GovernedProductPilotPortableEvidenceEnvelope,
    build_governed_product_pilot_authority_profile,
    verify_portable_evidence_envelope,
)


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_governed_product_pilot_profile_preserves_sealed_baseline() -> None:
    profile = build_governed_product_pilot_authority_profile()
    payload = profile.model_dump(mode="json")

    assert payload["profile_ref"] == GOVERNED_PRODUCT_PILOT_PROFILE_REF
    assert payload["default_runtime_profile"] == "sealed"
    assert payload["sealed_default_hard_rules_preserved"] is True
    assert payload["sealed_profile_deny_by_default"] is True
    assert payload["pilot_profile_exact_lane_only"] is True
    assert payload["runtime_gateway_required"] is True
    assert payload["control_center_mints_authority"] is False
    assert payload["control_center_presentation_only"] is True
    assert payload["production_authority_enabled"] is False
    assert payload["public_beta_or_release_claim_enabled"] is False
    assert payload["raw_prompt_response_provider_payload_log_path_persistence_enabled"] is False
    assert set(GOVERNED_PRODUCT_PILOT_REQUIRED_BLOCKED_AUTHORITY_REFS).issubset(
        set(payload["blocked_authority_refs"])
    )


def test_governed_product_pilot_lanes_are_exact_and_receipt_backed() -> None:
    profile = build_governed_product_pilot_authority_profile()
    lanes = {lane.lane_ref: lane.model_dump(mode="json") for lane in profile.lanes}

    assert set(lanes) >= {
        "lane-ref:governed-product-pilot-live-local-agent-runtime",
        "lane-ref:governed-product-pilot-mature-action-execution",
        "lane-ref:governed-product-pilot-portable-evidence",
        "lane-ref:governed-product-pilot-durable-orchestration",
    }
    for lane in lanes.values():
        assert lane["enabled_in_sealed_profile"] is False
        assert lane["exact_micro_lane_only"] is True
        assert lane["idempotency_required"] is True
        assert lane["audit_receipt_required"] is True
        assert lane["rollback_or_safe_disable_required"] is True
        assert lane["redaction_required"] is True
        assert lane["python_core_owned"] is True
        assert lane["cli_parity"] is True
        assert lane["api_parity"] is True
        assert lane["raw_persistence_allowed"] is False
        assert lane["generic_tool_execution_enabled"] is False
        assert lane["broad_authority_enabled"] is False
        assert lane["receipt_refs"]
        assert lane["evidence_refs"]
        if lane["execution_capable"] and not lane["read_only_no_op"]:
            assert lane["approval_binding_required"] is True


def test_portable_evidence_envelope_contains_required_signed_fields() -> None:
    envelope = build_governed_product_pilot_authority_profile().portable_evidence_envelope
    payload = envelope.model_dump(mode="json")

    assert payload["receipt_ref"].startswith("receipt-ref:")
    assert payload["evidence_ref"].startswith("evidence-ref:")
    assert payload["action_id"] == "governed-product-pilot-authority-profile"
    assert payload["side_effect_class"] == "local_dev_workspace_only"
    assert payload["policy_decision_ref"].startswith("policy-decision-ref:")
    assert payload["approval_ref"].startswith("approval-ref:")
    assert payload["verifier_version_ref"].startswith("verifier-version-ref:")
    assert payload["envelope_hash_ref"].startswith("hash-ref:sha256:")
    assert payload["signed_envelope_ref"].startswith("signed-envelope-ref:sha256:")
    assert payload["public_notarization_enabled"] is False
    assert payload["signing_key_material_persisted"] is False
    assert payload["safe_refs_only"] is True
    assert payload["raw_payload_persisted"] is False

    with pytest.raises(ValidationError):
        GovernedProductPilotPortableEvidenceEnvelope(
            **(
                payload
                | {
                    "raw_payload_persisted": True,
                }
            )
        )


def test_portable_evidence_offline_verifier_detects_tamper_and_missing_fields() -> None:
    envelope = build_governed_product_pilot_authority_profile().portable_evidence_envelope
    payload = envelope.model_dump(mode="json")

    verified = verify_portable_evidence_envelope(payload)
    assert verified.verification_status == "passed"
    assert verified.offline_verification_performed is True
    assert verified.required_fields_present is True
    assert verified.envelope_hash_valid is True
    assert verified.signed_envelope_ref_valid is True
    assert verified.redaction_status_valid is True
    assert verified.tamper_detected is False
    assert verified.input_path_echoed is False

    tampered = payload | {"action_id": "governed-product-pilot-tampered"}
    tampered_result = verify_portable_evidence_envelope(tampered)
    assert tampered_result.verification_status == "failed"
    assert tampered_result.envelope_hash_valid is False
    assert tampered_result.tamper_detected is True
    assert (
        "failure-reason-ref:portable-evidence-envelope-hash-invalid"
        in tampered_result.failure_reason_refs
    )

    missing = dict(payload)
    missing.pop("approval_ref")
    missing_result = verify_portable_evidence_envelope(missing)
    assert missing_result.verification_status == "failed"
    assert missing_result.required_fields_present is False
    assert (
        "missing-field-ref:governed-product-pilot-evidence:approval-ref"
        in missing_result.missing_field_refs
    )

    raw_persistence = payload | {"raw_payload_persisted": True}
    raw_result = verify_portable_evidence_envelope(raw_persistence)
    assert raw_result.verification_status == "failed"
    assert raw_result.redaction_status_valid is False
    assert (
        "failure-reason-ref:portable-evidence-redaction-status-invalid"
        in raw_result.failure_reason_refs
    )


def test_durable_orchestration_profile_marks_progress_as_non_truth() -> None:
    profile = build_governed_product_pilot_authority_profile()
    durable = profile.durable_orchestration_contract

    assert durable["local_run_records"] is True
    assert durable["checkpoints_supported"] is True
    assert durable["approval_wait_states_supported"] is True
    assert durable["retry_recovery_posture_supported"] is True
    assert durable["dead_letter_state_supported"] is True
    assert durable["durable_event_log_is_source_of_truth"] is True
    assert durable["progress_refs_are_source_of_truth"] is False
    assert durable["resume_requires_exact_lane"] is True
    assert durable["cancel_requires_exact_lane"] is True
    assert durable["retry_requires_exact_lane"] is True
    assert set(durable["read_model_status_refs"]) >= {
        "run-status-ref:active",
        "run-status-ref:completed",
        "run-status-ref:blocked",
        "run-status-ref:failed",
        "run-status-ref:recovered",
    }


def test_profile_contract_rejects_broad_authority() -> None:
    payload = build_governed_product_pilot_authority_profile().model_dump(mode="json")

    with pytest.raises(ValidationError):
        GovernedProductPilotAuthorityProfileReadModel(
            **(payload | {"production_authority_enabled": True})
        )
    with pytest.raises(ValidationError):
        GovernedProductPilotAuthorityProfileReadModel(
            **(payload | {"browser_automation_enabled": True})
        )


def test_governed_product_pilot_profile_api_and_manifest_parity() -> None:
    response = client.get("/api/runtime/governed-product-pilot-profile")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_governed_product_pilot_profile"
    assert body["data"]["profile_ref"] == GOVERNED_PRODUCT_PILOT_PROFILE_REF
    assert body["data"]["control_center_mints_authority"] is False

    manifest = build_api_manifest(app)
    route_index = {(route.method, route.path): route for route in manifest.routes}
    route = route_index[("GET", "/api/runtime/governed-product-pilot-profile")]
    assert route.route_classification == "local_sensitive"
    assert route.approval_posture == "not_required_for_route_classification"
    assert route.idempotency_required is False
    assert "governed_product_pilot_authority_profile" in manifest.capabilities_declared
    assert "governed_product_pilot_production_authority" in manifest.capabilities_blocked


def test_governed_product_pilot_profile_cli_parity() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dev" / "uaa_runtime.py"),
            "authority-profile",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)

    assert payload["schema_version"] == "governed-runtime-cli:v1"
    assert payload["command_ref"] == "repo-local-command:uaa-runtime-authority-profile"
    assert payload["authority_profile"]["profile_ref"] == GOVERNED_PRODUCT_PILOT_PROFILE_REF
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True


def test_portable_evidence_cli_export_and_offline_verify(tmp_path: Path) -> None:
    export_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dev" / "uaa_runtime.py"),
            "export-evidence-envelope",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    export_payload = json.loads(export_result.stdout)
    envelope_path = tmp_path / "portable-evidence-envelope.json"
    envelope_path.write_text(
        json.dumps(export_payload["portable_evidence_envelope"], sort_keys=True),
        encoding="utf-8",
    )

    verify_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dev" / "uaa_runtime.py"),
            "verify-evidence-envelope",
            "--input",
            str(envelope_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    verify_payload = json.loads(verify_result.stdout)

    assert verify_payload["command_ref"] == (
        "repo-local-command:uaa-runtime-verify-evidence-envelope"
    )
    assert verify_payload["safe_refs_only"] is True
    assert verify_payload["raw_paths_omitted"] is True
    assert str(envelope_path) not in verify_result.stdout
    verification = verify_payload["verification"]
    assert verification["verification_status"] == "passed"
    assert verification["input_path_echoed"] is False

    profile_verify = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dev" / "uaa_runtime.py"),
            "verify-evidence-envelope",
            "--profile",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert json.loads(profile_verify.stdout)["verification"]["verification_status"] == "passed"
