import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_RESULT_CLASSIFICATION_BLOCKED_AUTHORITY_REFS,
    RUNTIME_RESULT_CLASSIFICATION_CONTRACT_REF,
    RuntimeResultClassificationReadModel,
    RuntimeResultClassificationRecord,
    build_runtime_result_classification_read_model,
)


client = TestClient(app)


def test_result_classification_taxonomy_is_read_only() -> None:
    read_model = build_runtime_result_classification_read_model()

    assert read_model.schema_version == "runtime_result_classification.v1"
    assert read_model.contract_ref == RUNTIME_RESULT_CLASSIFICATION_CONTRACT_REF
    assert read_model.status == "taxonomy_read_model_only"
    assert read_model.route_ref == "GET /api/runtime/result-classification"
    assert read_model.cli_ref == "uaa runtime inspect-result-classification"
    assert read_model.classification_count == 7
    assert read_model.evidence_count == 1
    assert read_model.mutation_count == 1
    assert read_model.warning_count == 1
    assert read_model.blocked_count == 1
    assert read_model.proposal_count == 1
    assert read_model.diagnostic_count == 1
    assert read_model.untrusted_data_count == 1
    assert read_model.labels_visible is True
    assert read_model.provenance_visible is True
    assert read_model.redaction_visible is True
    assert read_model.verification_status_visible is True
    assert read_model.proof_binding_visible is True
    assert read_model.receipt_requirement_visible is True
    assert read_model.tool_output_as_truth_enabled is False
    assert read_model.action_authority_enabled is False
    assert read_model.mutation_without_receipt_enabled is False
    assert read_model.unverified_evidence_promotion_enabled is False
    assert read_model.raw_output_persisted is False
    assert read_model.provider_payload_persisted is False
    assert read_model.control_center_mints_authority is False
    assert set(RUNTIME_RESULT_CLASSIFICATION_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_result_classification_records_require_labels_and_proof() -> None:
    read_model = build_runtime_result_classification_read_model()
    kinds = {record.result_kind for record in read_model.classifications}

    assert kinds == {
        "evidence",
        "mutation",
        "warning",
        "blocked",
        "proposal",
        "diagnostic",
        "untrusted_data",
    }
    for record in read_model.classifications:
        assert record.classification_ref.startswith("result-classification-ref:")
        assert record.provenance_policy_ref.startswith("provenance-policy-ref:")
        assert record.redaction_policy_ref.startswith("redaction-policy-ref:")
        assert record.receipt_requirement_ref.startswith("receipt-requirement-ref:")
        assert record.proof_binding_ref.startswith("proof-binding-ref:")
        assert record.visible_in_control_center is True
        assert record.result_label_required is True
        assert record.provenance_required is True
        assert record.redaction_required is True
        assert record.proof_binding_required is True
        assert record.tool_output_as_truth_enabled is False
        assert record.action_authority_enabled is False
        assert record.mutation_without_receipt_enabled is False
        assert record.unverified_evidence_promotion_enabled is False
        assert record.raw_output_persisted is False
        assert record.provider_payload_persisted is False
        assert record.control_center_mints_authority is False


@pytest.mark.parametrize(
    "field",
    [
        "tool_output_as_truth_enabled",
        "action_authority_enabled",
        "mutation_without_receipt_enabled",
        "unverified_evidence_promotion_enabled",
        "raw_output_persisted",
        "provider_payload_persisted",
        "control_center_mints_authority",
    ],
)
def test_result_classification_read_model_denies_authority_flags(
    field: str,
) -> None:
    payload = build_runtime_result_classification_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_RESULT_CLASSIFICATION_READ_MODEL_AUTHORITY_DENIED",
    ):
        RuntimeResultClassificationReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "tool_output_as_truth_enabled",
        "action_authority_enabled",
        "mutation_without_receipt_enabled",
        "unverified_evidence_promotion_enabled",
        "raw_output_persisted",
        "provider_payload_persisted",
        "control_center_mints_authority",
    ],
)
def test_result_classification_record_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_result_classification_read_model()
        .classifications[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_RESULT_CLASSIFICATION_RECORD_AUTHORITY_DENIED",
    ):
        RuntimeResultClassificationRecord(**payload)


def test_result_classification_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/result-classification")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_result_classification"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/result-classification"
    assert data["classification_count"] == 7
    assert data["tool_output_as_truth_enabled"] is False
    assert data["action_authority_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "raw_output_value" not in serialized
    assert "provider_payload_value" not in serialized


def test_result_classification_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-result-classification",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_result_classification"]
    assert payload["metadata_only"] is True
    assert payload["classification_only"] is True
    assert payload["tool_output_as_truth"] is False
    assert payload["action_authority_granted"] is False
    assert payload["mutation_without_receipt_allowed"] is False
    assert payload["raw_outputs_omitted"] is True
    assert payload["provider_payloads_omitted"] is True
    assert read_model["route_ref"] == "GET /api/runtime/result-classification"
    assert read_model["classification_count"] == 7
