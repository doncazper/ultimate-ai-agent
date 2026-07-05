from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.dev import uaa_founder_loop
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.storage import (
    EVIDENCE_AUDIT_GROUP_KINDS,
    EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF,
    EVIDENCE_AUDIT_RECEIPT_SPINE_SOURCE,
    FOUNDER_LOOP_STATE_DIR_ENV,
    FounderLoopEvidenceAuditReceiptEnvelope,
    FounderLoopRepository,
)


BROAD_AUTHORITY_FLAGS = (
    "approval_ref_authority",
    "action_execution_enabled",
    "tool_execution_enabled",
    "connector_write_enabled",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "provider_sdk_call_enabled",
    "live_web_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "background_autonomy_enabled",
    "external_export_enabled",
    "production_authority_enabled",
)


def test_evidence_audit_spine_is_backend_owned_and_tamper_aware(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop")
    timeline = repo.evidence_timeline(limit=20)
    spine = timeline["evidence_audit_receipt_spine"]

    assert timeline["evidence_audit_receipt_spine_contract_ref"] == (
        EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF
    )
    assert spine["schema_version"] == "goatcitadel-catchup-evidence-audit-spine.v1"
    assert spine["contract_ref"] == EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF
    assert spine["source"] == EVIDENCE_AUDIT_RECEIPT_SPINE_SOURCE
    assert spine["backend_owned"] is True
    assert spine["control_center_presentation_only"] is True
    assert spine["safe_refs_only"] is True
    assert spine["redacted_summaries_only"] is True
    assert spine["raw_content_included"] is False
    assert spine["timeline_group_kinds"] == list(EVIDENCE_AUDIT_GROUP_KINDS)
    assert spine["group_count"] == len(EVIDENCE_AUDIT_GROUP_KINDS)
    assert spine["envelope_count"] == len(spine["receipt_envelopes"])
    assert spine["missing_receipt_count"] == len(spine["missing_receipt_refs"])
    assert spine["receipt_envelope_field_refs"]
    assert "receipt-envelope-field:artifact-hash-ref" in (
        spine["receipt_envelope_field_refs"]
    )
    assert "GET /control-center/evidence/timeline" in spine["route_refs"]
    assert "inspect-evidence-audit-spine" in spine["cli_ref"]
    assert spine["portable_evidence_posture"] == (
        "hash_refs_and_verifier_refs_available_for_local_inspection_only"
    )
    for flag in BROAD_AUTHORITY_FLAGS:
        assert spine[flag] is False

    group_kinds = {group["group_kind"] for group in spine["groups"]}
    assert group_kinds == set(EVIDENCE_AUDIT_GROUP_KINDS)
    action_group = next(
        group for group in spine["groups"] if group["group_kind"] == "action_proposals"
    )
    assert action_group["event_refs"] or action_group["timeline_item_refs"]
    assert action_group["status"] in {
        "receipt_refs_recorded",
        "missing_receipt_refs_visible",
    }

    envelope = spine["receipt_envelopes"][0]
    assert envelope["envelope_ref"].startswith("receipt-envelope:")
    assert envelope["artifact_hash_ref"].startswith(
        "artifact-hash-ref:evidence-audit-envelope:sha256-"
    )
    assert envelope["verifier_version_ref"] == (
        "verifier-ref:goatcitadel-catchup-evidence-audit:v1"
    )
    assert envelope["redaction_status"] == "redacted_summary_only"
    assert envelope["input_ref"].startswith("input-ref:redacted:")
    assert envelope["output_ref"].startswith("output-ref:redacted:")
    assert envelope["action_execution_enabled"] is False
    assert envelope["provider_model_call_enabled"] is False
    assert envelope["shell_subprocess_execution_enabled"] is False
    assert envelope["production_authority_enabled"] is False

    serialized = json.dumps(spine, sort_keys=True).lower()
    for forbidden in [
        "raw prompt",
        "raw response",
        "provider payload",
        "raw log",
        "api key",
        "/users/",
        "/home/",
        "/var/",
        "/etc/",
    ]:
        assert forbidden not in serialized


def test_evidence_audit_spine_api_exposes_existing_evidence_timeline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(FOUNDER_LOOP_STATE_DIR_ENV, str(tmp_path / "api-state"))
    response = TestClient(app).get("/control-center/evidence/timeline")

    assert response.status_code == 200
    data = response.json()["data"]
    spine = data["evidence_audit_receipt_spine"]
    assert data["evidence_audit_receipt_spine_contract_ref"] == (
        EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF
    )
    assert spine["contract_ref"] == EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF
    assert spine["source"] == EVIDENCE_AUDIT_RECEIPT_SPINE_SOURCE
    assert spine["backend_owned"] is True
    assert spine["control_center_presentation_only"] is True
    assert spine["provider_model_call_enabled"] is False
    assert spine["browser_execution_enabled"] is False
    assert spine["production_authority_enabled"] is False


def test_evidence_audit_spine_cli_inspects_same_read_model(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "cli-state"
    FounderLoopRepository(state_dir)

    exit_code = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "inspect-evidence-audit-spine",
            "--limit",
            "20",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    spine = output["evidence_audit_receipt_spine"]
    assert output["command_ref"] == (
        "repo-local-command:founder-loop-evidence-audit-spine"
    )
    assert output["safe_refs_only"] is True
    assert output["raw_content_omitted"] is True
    assert output["raw_paths_omitted"] is True
    assert output["evidence_audit_receipt_spine_contract_ref"] == (
        EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF
    )
    assert spine["contract_ref"] == EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF
    assert spine["missing_receipt_count"] == len(spine["missing_receipt_refs"])
    assert spine["approval_ref_authority"] is False
    assert spine["action_execution_enabled"] is False


def test_evidence_audit_receipt_envelope_rejects_unsafe_content() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        FounderLoopEvidenceAuditReceiptEnvelope(
            envelope_ref="receipt-envelope:unsafe-test",
            receipt_ref="missing-receipt:unsafe-test",
            receipt_recorded=False,
            run_ref="run-ref:unsafe-test",
            action_ref="action-ref:not-applicable",
            approval_ref="approval-ref:not-required-or-not-scoped",
            event_ref="evidence-event:unsafe-test",
            timeline_item_ref="evidence-timeline:unsafe/test",
            group_ref="evidence-audit-group:unsafe-test",
            authority_decision_ref="authority-decision-ref:missing-receipt-read-only",
            input_ref="input-ref:redacted:unsafe-test",
            output_ref="output-ref:redacted:unsafe-test",
            artifact_hash_ref="artifact-hash-ref:unsafe:sha256-abcdef0123456789",
            timestamp_ref="timestamp-ref:recorded",
            verifier_version_ref="verifier-ref:goatcitadel-catchup-evidence-audit:v1",
            safe_summary="Contains raw prompt material and must be rejected.",
            missing_receipt_refs=["missing-receipt:unsafe-test"],
        )
