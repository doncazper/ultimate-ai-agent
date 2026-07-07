#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_MAPPING_REF,
    RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_CLI_REF,
    RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_USAGE_COST_ANALYTICS_BLOCKED_AUTHORITY_REFS,
    build_runtime_usage_cost_analytics_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"Hermes Runtime Adoption Phase 22 verification failed: {message}")


def _assert_read_model(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "runtime_usage_cost_analytics.v1":
        _fail("unexpected usage cost analytics schema")
    if payload.get("status") != "read_only_redacted_accounting_posture":
        _fail("usage cost analytics posture is not read-only")
    if payload.get("route_ref") != "GET /api/runtime/usage-cost-analytics":
        _fail("route ref drifted")
    if payload.get("cli_ref") != "uaa runtime inspect-usage-cost-analytics":
        _fail("CLI ref drifted")
    if (
        payload.get("authority_state_route_ref")
        != RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_ROUTE_REF
    ):
        _fail("authority state route ref drifted")
    if (
        payload.get("authority_state_cli_ref")
        != RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_CLI_REF
    ):
        _fail("authority state CLI ref drifted")
    if (
        payload.get("authority_state_mapping_ref")
        != RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_MAPPING_REF
    ):
        _fail("authority mapping ref drifted")
    if payload.get("authority_state_decision_outcome") != "allow":
        _fail("usage cost analytics must be allowed only as Workspace read")
    if not str(payload.get("authority_state_decision_ref") or "").startswith(
        "authority-policy-decision-ref:"
    ):
        _fail("authority decision ref missing")
    unsupported = set(payload.get("unsupported_adapter_refs") or [])
    if "adapter-ref:usage-cost-provider-call:not-implemented" not in unsupported:
        _fail("missing usage cost unsupported adapter ref")
    for flag in (
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
    ):
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    blockers = set(payload.get("blocked_authority_refs") or [])
    if set(RUNTIME_USAGE_COST_ANALYTICS_BLOCKED_AUTHORITY_REFS) - blockers:
        _fail("missing usage cost analytics blocked authority refs")
    records = payload.get("records") or []
    if payload.get("record_count") != len(records):
        _fail("record count mismatch")
    if not records:
        _fail("usage cost analytics records missing")
    total_in = sum(int(record.get("estimated_input_tokens") or 0) for record in records)
    total_out = sum(
        int(record.get("estimated_output_tokens") or 0) for record in records
    )
    total_units = sum(
        int(record.get("estimated_total_tokens") or 0) for record in records
    )
    total_cost = sum(
        int(record.get("estimated_cost_minor_units") or 0) for record in records
    )
    if payload.get("total_estimated_input_tokens") != total_in:
        _fail("input accounting total mismatch")
    if payload.get("total_estimated_output_tokens") != total_out:
        _fail("output accounting total mismatch")
    if payload.get("total_estimated_tokens") != total_units:
        _fail("total accounting mismatch")
    if payload.get("total_estimated_cost_minor_units") != total_cost:
        _fail("cost accounting mismatch")
    for record in records:
        if int(record.get("estimated_total_tokens") or 0) != int(
            record.get("estimated_input_tokens") or 0
        ) + int(record.get("estimated_output_tokens") or 0):
            _fail("record accounting total mismatch")
        for flag in (
            "provider_call_performed",
            "provider_sdk_call_performed",
            "billing_action_performed",
            "live_price_fetch_performed",
            "raw_prompt_persisted",
            "raw_response_persisted",
            "provider_payload_persisted",
            "output_authoritative",
            "production_authority_enabled",
        ):
            if record.get(flag) is not False:
                _fail(f"record {flag} must remain false")


def verify_core() -> None:
    _assert_read_model(
        build_runtime_usage_cost_analytics_read_model().model_dump(mode="json")
    )


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/api/runtime/usage-cost-analytics")
    if response.status_code != 200:
        _fail(
            f"GET /api/runtime/usage-cost-analytics returned {response.status_code}"
        )
    body = response.json()
    if body.get("success") is not True:
        _fail("API did not return success envelope")
    _assert_read_model(body.get("data") or {})
    serialized = json.dumps(body).lower()
    for forbidden in (
        "/users/",
        "raw_prompt_payload",
        "raw_response_payload",
        "provider_payload_value",
    ):
        if forbidden in serialized:
            _fail(f"API payload exposed forbidden marker {forbidden}")


def verify_cli() -> None:
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
    _assert_read_model(payload.get("runtime_usage_cost_analytics") or {})
    authority_state = payload.get("authority_state") or {}
    if (
        authority_state.get("mapping_ref")
        != RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_MAPPING_REF
    ):
        _fail("CLI authority mapping drifted")
    if authority_state.get("decision_outcome") != "allow":
        _fail("CLI authority decision drifted")
    if payload.get("provider_call_performed") is not False:
        _fail("CLI claimed provider call")
    if payload.get("provider_sdk_call_performed") is not False:
        _fail("CLI claimed provider SDK call")
    if payload.get("billing_action_performed") is not False:
        _fail("CLI claimed billing action")
    if payload.get("operator_export_performed") is not False:
        _fail("CLI claimed operator export")


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 22 usage cost analytics verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
