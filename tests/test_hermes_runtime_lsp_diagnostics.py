import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_LSP_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS,
    RUNTIME_LSP_DIAGNOSTICS_CONTRACT_REF,
    RuntimeLspDiagnosticEvidenceContract,
    RuntimeLspDiagnosticsReadModel,
    build_runtime_lsp_diagnostics_read_model,
)


client = TestClient(app)


def test_lsp_diagnostics_is_read_only_evidence_posture() -> None:
    read_model = build_runtime_lsp_diagnostics_read_model()

    assert read_model.schema_version == "runtime_lsp_diagnostics.v1"
    assert read_model.contract_ref == RUNTIME_LSP_DIAGNOSTICS_CONTRACT_REF
    assert read_model.status == "diagnostic_evidence_placeholder_posture"
    assert read_model.route_ref == "GET /api/runtime/lsp-diagnostics"
    assert read_model.cli_ref == "uaa runtime inspect-lsp-diagnostics"
    assert read_model.diagnostic_count == 3
    assert read_model.evidence_placeholder_count == 1
    assert read_model.proof_ready_count == 1
    assert read_model.execution_blocked_count == 1
    assert read_model.diagnostic_evidence_contract_visible is True
    assert read_model.receipt_plan_visible is True
    assert read_model.proof_link_visible is True
    assert read_model.redaction_policy_visible is True
    assert read_model.allowlisted_server_required_for_promotion is True
    assert read_model.cwd_jail_required_for_promotion is True
    assert read_model.timeout_required_for_promotion is True
    assert read_model.language_server_started is False
    assert read_model.dependency_install_enabled is False
    assert read_model.shell_execution_enabled is False
    assert read_model.file_read_enabled is False
    assert read_model.file_write_enabled is False
    assert read_model.provider_call_enabled is False
    assert read_model.control_center_mints_authority is False
    assert read_model.raw_path_persisted is False
    assert read_model.raw_diagnostic_payload_persisted is False
    assert set(RUNTIME_LSP_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_lsp_diagnostic_contracts_are_safe_refs_only() -> None:
    read_model = build_runtime_lsp_diagnostics_read_model()
    statuses_by_label = {
        diagnostic.display_label: diagnostic.status
        for diagnostic in read_model.diagnostics
    }

    assert statuses_by_label == {
        "Python semantic proof": "proof_ready",
        "TypeScript diagnostic placeholder": "evidence_placeholder",
        "Docs diagnostic blocked lane": "execution_blocked",
    }
    for diagnostic in read_model.diagnostics:
        assert diagnostic.diagnostic_ref.startswith("lsp-diagnostic-ref:")
        assert diagnostic.source_scope_ref.startswith("source-scope-ref:")
        assert diagnostic.evidence_ref.startswith("evidence-ref:")
        assert diagnostic.receipt_plan_ref.startswith("receipt-plan-ref:")
        assert diagnostic.proof_ref.startswith("proof-ref:")
        assert diagnostic.language_server_started is False
        assert diagnostic.dependency_install_enabled is False
        assert diagnostic.shell_execution_enabled is False
        assert diagnostic.file_read_enabled is False
        assert diagnostic.file_write_enabled is False
        assert diagnostic.provider_call_enabled is False
        assert diagnostic.raw_path_persisted is False
        assert diagnostic.raw_diagnostic_payload_persisted is False
        assert set(RUNTIME_LSP_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS).issubset(
            set(diagnostic.blocked_authority_refs)
        )


@pytest.mark.parametrize(
    "field",
    [
        "language_server_started",
        "dependency_install_enabled",
        "shell_execution_enabled",
        "file_read_enabled",
        "file_write_enabled",
        "provider_call_enabled",
        "control_center_mints_authority",
        "raw_path_persisted",
        "raw_diagnostic_payload_persisted",
    ],
)
def test_lsp_diagnostics_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_lsp_diagnostics_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_DENIED"):
        RuntimeLspDiagnosticsReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "language_server_started",
        "dependency_install_enabled",
        "shell_execution_enabled",
        "file_read_enabled",
        "file_write_enabled",
        "provider_call_enabled",
        "raw_path_persisted",
        "raw_diagnostic_payload_persisted",
    ],
)
def test_lsp_diagnostic_contract_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_lsp_diagnostics_read_model()
        .diagnostics[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_LSP_DIAGNOSTIC_CONTRACT_AUTHORITY_DENIED",
    ):
        RuntimeLspDiagnosticEvidenceContract(**payload)


def test_lsp_diagnostics_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/lsp-diagnostics")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_lsp_diagnostics"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/lsp-diagnostics"
    assert data["diagnostic_count"] == 3
    assert data["language_server_started"] is False
    assert data["dependency_install_enabled"] is False
    assert data["shell_execution_enabled"] is False
    assert data["file_read_enabled"] is False
    assert data["file_write_enabled"] is False
    assert data["provider_call_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_path_value" not in serialized
    assert "raw_diagnostic_payload_value" not in serialized


def test_lsp_diagnostics_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-lsp-diagnostics",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_lsp_diagnostics"]
    assert payload["safe_refs_only"] is True
    assert payload["evidence_only"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["raw_file_content_omitted"] is True
    assert payload["raw_diagnostic_payloads_omitted"] is True
    assert payload["language_server_started"] is False
    assert payload["dependency_install_performed"] is False
    assert payload["shell_execution_performed"] is False
    assert payload["file_read_performed"] is False
    assert payload["file_write_performed"] is False
    assert payload["provider_call_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/lsp-diagnostics"
    assert read_model["cli_ref"] == "uaa runtime inspect-lsp-diagnostics"
    assert read_model["diagnostic_count"] == 3
