#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_CONTEXT_REFERENCES_AUTHORITY_MAPPING_REF,
    RUNTIME_CONTEXT_REFERENCES_AUTHORITY_STATE_CLI_REF,
    RUNTIME_CONTEXT_REFERENCES_AUTHORITY_STATE_ROUTE_REF,
    build_runtime_context_references_read_model,
)


DENIED_FLAGS = [
    "live_url_fetch_enabled",
    "raw_path_persistence_enabled",
    "raw_file_content_persistence_enabled",
    "automatic_context_injection_enabled",
    "hidden_prompt_context_enabled",
    "secret_config_reads_enabled",
    "provider_model_call_enabled",
    "connector_writes_enabled",
    "shell_execution_enabled",
    "browser_automation_enabled",
    "production_authority_enabled",
]


def _fail(message: str) -> None:
    raise SystemExit(
        f"Hermes Runtime Adoption Phase 16 verification failed: {message}"
    )


def _assert_context(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "runtime_context_references.v1":
        _fail("unexpected context references schema")
    if payload.get("status") != "read_only_context_reference_preview":
        _fail("context references posture is not read-only preview")
    if (
        payload.get("authority_state_route_ref")
        != RUNTIME_CONTEXT_REFERENCES_AUTHORITY_STATE_ROUTE_REF
    ):
        _fail("authority state route ref drifted")
    if (
        payload.get("authority_state_cli_ref")
        != RUNTIME_CONTEXT_REFERENCES_AUTHORITY_STATE_CLI_REF
    ):
        _fail("authority state CLI ref drifted")
    if (
        payload.get("authority_state_mapping_ref")
        != RUNTIME_CONTEXT_REFERENCES_AUTHORITY_MAPPING_REF
    ):
        _fail("authority state mapping ref drifted")
    if payload.get("authority_state_decision_outcome") != "allow":
        _fail("authority state decision outcome drifted")
    if not payload.get("authority_state_reason_refs"):
        _fail("authority state reason refs missing")
    unsupported = set(payload.get("unsupported_adapter_refs") or [])
    if "adapter-ref:context-references-live-url-fetch:not-implemented" not in unsupported:
        _fail("live URL fetch unsupported adapter ref missing")
    for flag in DENIED_FLAGS:
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    references = payload.get("references") or []
    if payload.get("reference_count") != len(references):
        _fail("reference count mismatch")
    if not references:
        _fail("context references missing")
    kinds = {ref.get("ref_kind") for ref in references}
    expected_kinds = {
        "file",
        "folder",
        "diff",
        "url_evidence",
        "run",
        "proof",
        "task",
        "memory",
        "crm_object",
        "issue",
    }
    if kinds != expected_kinds:
        _fail(f"unexpected ref kinds: {sorted(kinds)}")
    for ref in references:
        if not ref.get("why_included_refs"):
            _fail("context ref missing why-included refs")
        for flag in (
            "live_url_fetch_performed",
            "raw_path_persisted",
            "raw_file_content_persisted",
            "raw_prompt_persisted",
            "raw_response_persisted",
            "raw_provider_payload_persisted",
            "secret_config_read_performed",
            "automatic_context_injection_performed",
            "provider_model_call_performed",
            "connector_write_performed",
            "shell_execution_performed",
            "browser_automation_performed",
            "production_authority_performed",
        ):
            if ref.get(flag) is not False:
                _fail(f"context ref {flag} must remain false")


def verify_core() -> None:
    read_model = build_runtime_context_references_read_model()
    _assert_context(read_model.model_dump(mode="json"))


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/api/runtime/context-references")
    if response.status_code != 200:
        _fail(f"GET /api/runtime/context-references returned {response.status_code}")
    body = response.json()
    _assert_context(body.get("data") or {})
    serialized = json.dumps(body).lower()
    for forbidden in (
        "/users/",
        "raw_prompt material",
        "raw_response material",
        "raw_provider_payload material",
    ):
        if forbidden in serialized:
            _fail(f"API payload exposed forbidden marker {forbidden}")


def verify_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-context-references",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    _assert_context(payload.get("runtime_context_references") or {})
    authority_state = payload.get("authority_state") or {}
    if (
        authority_state.get("mapping_ref")
        != RUNTIME_CONTEXT_REFERENCES_AUTHORITY_MAPPING_REF
    ):
        _fail("CLI authority mapping ref drifted")
    if authority_state.get("decision_outcome") != "allow":
        _fail("CLI authority decision outcome drifted")
    if payload.get("live_url_fetch_performed") is not False:
        _fail("CLI claimed live URL fetch")
    if payload.get("automatic_context_injection_performed") is not False:
        _fail("CLI claimed automatic context injection")


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 16 context references verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
