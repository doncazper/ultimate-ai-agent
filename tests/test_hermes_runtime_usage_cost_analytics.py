from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_MAPPING_REF,
    RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_CLI_REF,
    RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_USAGE_COST_ANALYTICS_BLOCKED_AUTHORITY_REFS,
    RUNTIME_USAGE_COST_ANALYTICS_CONTRACT_REF,
    RuntimeUsageCostAnalyticsReadModel,
    RuntimeUsageCostRecord,
    build_runtime_usage_cost_analytics_read_model,
)


client = TestClient(app)


def test_usage_cost_analytics_is_read_only_accounting_posture() -> None:
    read_model = build_runtime_usage_cost_analytics_read_model()

    assert read_model.schema_version == "runtime_usage_cost_analytics.v1"
    assert read_model.contract_ref == RUNTIME_USAGE_COST_ANALYTICS_CONTRACT_REF
    assert read_model.status == "read_only_redacted_accounting_posture"
    assert read_model.route_ref == "GET /api/runtime/usage-cost-analytics"
    assert read_model.cli_ref == "uaa runtime inspect-usage-cost-analytics"
    assert (
        read_model.authority_state_route_ref
        == RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_ROUTE_REF
    )
    assert (
        read_model.authority_state_cli_ref
        == RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_CLI_REF
    )
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_decision_outcome == "allow"
    assert read_model.authority_state_decision_ref.startswith(
        "authority-policy-decision-ref:"
    )
    assert read_model.authority_state_reason_refs
    assert (
        "adapter-ref:usage-cost-provider-call:not-implemented"
        in read_model.unsupported_adapter_refs
    )
    assert read_model.record_count == 4
    assert read_model.manual_diagnostic_receipt_count == 1
    assert read_model.runtime_receipt_record_count == 1
    assert read_model.provider_catalog_reference_count == 1
    assert read_model.blocked_record_count == 1
    assert read_model.total_estimated_tokens == (
        read_model.total_estimated_input_tokens
        + read_model.total_estimated_output_tokens
    )
    assert read_model.total_estimated_cost_minor_units == 14
    assert read_model.operator_export_available is False
    assert read_model.billing_action_enabled is False
    assert read_model.provider_call_enabled is False
    assert read_model.provider_sdk_enabled is False
    assert read_model.live_price_fetch_enabled is False
    assert read_model.raw_prompt_persistence_enabled is False
    assert read_model.raw_response_persistence_enabled is False
    assert read_model.provider_payload_persistence_enabled is False
    assert read_model.output_authority_enabled is False
    assert read_model.production_authority_enabled is False
    assert set(RUNTIME_USAGE_COST_ANALYTICS_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )
    assert read_model.snapshot_hash_ref.startswith(
        "snapshot-hash-ref:runtime-usage-cost-analytics:"
    )


def test_usage_cost_records_never_perform_runtime_or_billing_actions() -> None:
    read_model = build_runtime_usage_cost_analytics_read_model()

    assert {record.source_kind for record in read_model.records} == {
        "manual_diagnostic_receipt",
        "runtime_receipt_metadata",
        "provider_catalog_reference",
        "delegated_runtime_future",
    }
    for record in read_model.records:
        assert record.estimated_total_tokens == (
            record.estimated_input_tokens + record.estimated_output_tokens
        )
        assert record.provider_call_performed is False
        assert record.provider_sdk_call_performed is False
        assert record.billing_action_performed is False
        assert record.live_price_fetch_performed is False
        assert record.raw_prompt_persisted is False
        assert record.raw_response_persisted is False
        assert record.provider_payload_persisted is False
        assert record.output_authoritative is False
        assert record.production_authority_enabled is False
        assert set(RUNTIME_USAGE_COST_ANALYTICS_BLOCKED_AUTHORITY_REFS).issubset(
            set(record.blocked_authority_refs)
        )


@pytest.mark.parametrize(
    "field",
    [
        "operator_export_available",
        "billing_action_enabled",
        "provider_call_enabled",
        "provider_sdk_enabled",
        "live_price_fetch_enabled",
        "raw_prompt_persistence_enabled",
        "raw_response_persistence_enabled",
        "provider_payload_persistence_enabled",
        "output_authority_enabled",
        "production_authority_enabled",
    ],
)
def test_usage_cost_analytics_denies_authority_flags(field: str) -> None:
    payload = build_runtime_usage_cost_analytics_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_DENIED",
    ):
        RuntimeUsageCostAnalyticsReadModel(**payload)


def test_usage_cost_analytics_rejects_authority_mapping_drift() -> None:
    payload = build_runtime_usage_cost_analytics_read_model().model_dump(mode="json")
    payload["authority_state_mapping_ref"] = "lane-ref:wrong-usage-cost"

    with pytest.raises(
        ValueError,
        match="RUNTIME_USAGE_COST_AUTHORITY_MAPPING_MISMATCH",
    ):
        RuntimeUsageCostAnalyticsReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "provider_call_performed",
        "provider_sdk_call_performed",
        "billing_action_performed",
        "live_price_fetch_performed",
        "raw_prompt_persisted",
        "raw_response_persisted",
        "provider_payload_persisted",
        "output_authoritative",
        "production_authority_enabled",
    ],
)
def test_usage_cost_record_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_usage_cost_analytics_read_model()
        .records[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_USAGE_COST_RECORD_AUTHORITY_DENIED",
    ):
        RuntimeUsageCostRecord(**payload)


def test_usage_cost_analytics_api_returns_read_only_posture() -> None:
    response = client.get("/api/runtime/usage-cost-analytics")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_usage_cost_analytics"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/usage-cost-analytics"
    assert data["authority_state_mapping_ref"] == (
        RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_MAPPING_REF
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert data["provider_call_enabled"] is False
    assert data["billing_action_enabled"] is False
    assert data["operator_export_available"] is False
    assert data["record_count"] == 4
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_prompt_payload" not in serialized
    assert "raw_response_payload" not in serialized
    assert "provider_payload_value" not in serialized


def test_usage_cost_analytics_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-usage-cost-analytics",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_usage_cost_analytics"]
    authority_state = payload["authority_state"]
    assert payload["safe_refs_only"] is True
    assert (
        authority_state["mapping_ref"]
        == RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_MAPPING_REF
    )
    assert authority_state["decision_outcome"] == "allow"
    assert payload["provider_call_performed"] is False
    assert payload["provider_sdk_call_performed"] is False
    assert payload["billing_action_performed"] is False
    assert payload["live_price_fetch_performed"] is False
    assert payload["operator_export_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/usage-cost-analytics"
    assert read_model["cli_ref"] == "uaa runtime inspect-usage-cost-analytics"
    assert (
        read_model["authority_state_cli_ref"]
        == RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_CLI_REF
    )
    assert read_model["record_count"] == 4
