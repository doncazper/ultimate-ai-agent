#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_CONTEXT_BUDGET_PRESSURE_BLOCKED_AUTHORITY_REFS,
    build_runtime_context_budget_pressure_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"Hermes Runtime Adoption Phase 24 verification failed: {message}")


def _assert_read_model(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "runtime_context_budget_pressure.v1":
        _fail("unexpected context budget schema")
    if payload.get("status") != "read_only_context_budget_pressure_posture":
        _fail("context budget posture is not read-only")
    if payload.get("route_ref") != "GET /api/runtime/context-budget-pressure":
        _fail("route ref drifted")
    if payload.get("cli_ref") != "uaa runtime inspect-context-budget-pressure":
        _fail("CLI ref drifted")
    for required in (
        "compression_proposal_required",
        "operator_approval_required",
        "source_coverage_required",
        "retrieval_log_required",
        "summary_receipt_required",
    ):
        if payload.get(required) is not True:
            _fail(f"{required} must remain true")
    for flag in (
        "hidden_compression_enabled",
        "automatic_context_mutation_enabled",
        "model_summarization_enabled",
        "raw_context_persistence_enabled",
        "raw_prompt_persistence_enabled",
        "raw_response_persistence_enabled",
        "provider_payload_persistence_enabled",
        "context_injection_enabled",
        "provider_sdk_enabled",
        "cache_write_enabled",
        "production_authority_enabled",
    ):
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    blockers = set(payload.get("blocked_authority_refs") or [])
    if set(RUNTIME_CONTEXT_BUDGET_PRESSURE_BLOCKED_AUTHORITY_REFS) - blockers:
        _fail("missing context budget blocked authority refs")
    segments = payload.get("segments") or []
    proposals = payload.get("proposals") or []
    if payload.get("segment_count") != len(segments):
        _fail("segment count mismatch")
    if payload.get("proposal_count") != len(proposals):
        _fail("proposal count mismatch")
    if len(segments) != 4:
        _fail("expected four context budget segments")
    if len(proposals) != 3:
        _fail("expected three context budget proposals")
    for segment in segments:
        for flag in (
            "hidden_compression_enabled",
            "automatic_context_mutation_enabled",
            "model_summarization_call_performed",
            "summary_receipt_created",
            "raw_context_persisted",
            "raw_prompt_persisted",
            "raw_response_persisted",
            "provider_payload_persisted",
            "context_injection_performed",
            "provider_sdk_call_performed",
            "cache_write_performed",
            "production_authority_enabled",
        ):
            if segment.get(flag) is not False:
                _fail(f"segment {flag} must remain false")
    for proposal in proposals:
        for flag in (
            "auto_applied",
            "hidden_compression_performed",
            "automatic_context_mutation_performed",
            "model_summarization_call_performed",
            "summary_receipt_created",
            "raw_context_persisted",
            "raw_prompt_persisted",
            "raw_response_persisted",
            "provider_payload_persisted",
            "context_injection_performed",
            "provider_sdk_call_performed",
            "cache_write_performed",
            "production_authority_enabled",
        ):
            if proposal.get(flag) is not False:
                _fail(f"proposal {flag} must remain false")


def verify_core() -> None:
    _assert_read_model(
        build_runtime_context_budget_pressure_read_model().model_dump(mode="json")
    )


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/api/runtime/context-budget-pressure")
    if response.status_code != 200:
        _fail(
            f"GET /api/runtime/context-budget-pressure returned {response.status_code}"
        )
    body = response.json()
    if body.get("success") is not True:
        _fail("API did not return success envelope")
    _assert_read_model(body.get("data") or {})
    serialized = json.dumps(body).lower()
    for forbidden in (
        "/users/",
        "raw_context_payload",
        "raw_prompt_payload",
        "provider_payload_value",
    ):
        if forbidden in serialized:
            _fail(f"API payload exposed forbidden marker {forbidden}")


def verify_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-context-budget-pressure",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    _assert_read_model(payload.get("runtime_context_budget_pressure") or {})
    if payload.get("hidden_compression_performed") is not False:
        _fail("CLI claimed hidden compression")
    if payload.get("automatic_context_mutation_performed") is not False:
        _fail("CLI claimed automatic context mutation")
    if payload.get("model_summarization_call_performed") is not False:
        _fail("CLI claimed model summarization")
    if payload.get("context_injection_performed") is not False:
        _fail("CLI claimed context injection")
    if payload.get("cache_write_performed") is not False:
        _fail("CLI claimed cache write")


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 24 context budget verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
