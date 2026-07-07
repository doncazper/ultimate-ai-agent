#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_PROMPT_STABILITY_AUTHORITY_MAPPING_REF,
    RUNTIME_PROMPT_STABILITY_AUTHORITY_STATE_CLI_REF,
    RUNTIME_PROMPT_STABILITY_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_PROMPT_STABILITY_BLOCKED_AUTHORITY_REFS,
    build_runtime_prompt_stability_tiers_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"Hermes Runtime Adoption Phase 23 verification failed: {message}")


def _assert_read_model(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "runtime_prompt_stability_tiers.v1":
        _fail("unexpected prompt stability schema")
    if payload.get("status") != "read_only_prompt_contract_posture":
        _fail("prompt stability posture is not read-only")
    if payload.get("route_ref") != "GET /api/runtime/prompt-stability-tiers":
        _fail("route ref drifted")
    if payload.get("cli_ref") != "uaa runtime inspect-prompt-stability-tiers":
        _fail("CLI ref drifted")
    if (
        payload.get("authority_state_route_ref")
        != RUNTIME_PROMPT_STABILITY_AUTHORITY_STATE_ROUTE_REF
    ):
        _fail("authority state route ref drifted")
    if (
        payload.get("authority_state_cli_ref")
        != RUNTIME_PROMPT_STABILITY_AUTHORITY_STATE_CLI_REF
    ):
        _fail("authority state CLI ref drifted")
    if (
        payload.get("authority_state_mapping_ref")
        != RUNTIME_PROMPT_STABILITY_AUTHORITY_MAPPING_REF
    ):
        _fail("authority mapping ref drifted")
    if payload.get("authority_state_decision_outcome") != "allow":
        _fail("prompt stability must be allowed only as Workspace read")
    if not str(payload.get("authority_state_decision_ref") or "").startswith(
        "authority-policy-decision-ref:"
    ):
        _fail("authority decision ref missing")
    unsupported = set(payload.get("unsupported_adapter_refs") or [])
    if "adapter-ref:prompt-stability-model-call:not-implemented" not in unsupported:
        _fail("missing prompt stability unsupported adapter ref")
    for required in (
        "safe_prompt_manifest_required",
        "prompt_hashes_required",
        "redacted_receipt_required",
        "proof_link_required",
    ):
        if payload.get(required) is not True:
            _fail(f"{required} must remain true")
    for flag in (
        "raw_prompt_persistence_enabled",
        "raw_response_persistence_enabled",
        "provider_payload_persistence_enabled",
        "hidden_prompt_injection_enabled",
        "context_injection_enabled",
        "model_call_enabled",
        "provider_sdk_enabled",
        "model_output_authority_enabled",
        "cache_write_enabled",
        "production_authority_enabled",
    ):
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    blockers = set(payload.get("blocked_authority_refs") or [])
    if set(RUNTIME_PROMPT_STABILITY_BLOCKED_AUTHORITY_REFS) - blockers:
        _fail("missing prompt stability blocked authority refs")
    tiers = payload.get("tiers") or []
    if payload.get("tier_count") != len(tiers):
        _fail("tier count mismatch")
    if len(tiers) != 5:
        _fail("expected five prompt stability tiers")
    for tier in tiers:
        for flag in (
            "raw_prompt_persisted",
            "raw_response_persisted",
            "provider_payload_persisted",
            "hidden_prompt_injection_enabled",
            "context_injection_enabled",
            "model_call_performed",
            "provider_sdk_call_performed",
            "model_output_authoritative",
            "cache_write_enabled",
            "production_authority_enabled",
        ):
            if tier.get(flag) is not False:
                _fail(f"tier {flag} must remain false")


def verify_core() -> None:
    _assert_read_model(
        build_runtime_prompt_stability_tiers_read_model().model_dump(mode="json")
    )


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/api/runtime/prompt-stability-tiers")
    if response.status_code != 200:
        _fail(
            f"GET /api/runtime/prompt-stability-tiers returned {response.status_code}"
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
            "inspect-prompt-stability-tiers",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    _assert_read_model(payload.get("runtime_prompt_stability_tiers") or {})
    authority_state = payload.get("authority_state") or {}
    if (
        authority_state.get("mapping_ref")
        != RUNTIME_PROMPT_STABILITY_AUTHORITY_MAPPING_REF
    ):
        _fail("CLI authority mapping drifted")
    if authority_state.get("decision_outcome") != "allow":
        _fail("CLI authority decision drifted")
    if payload.get("hidden_prompt_injection_performed") is not False:
        _fail("CLI claimed hidden prompt injection")
    if payload.get("context_injection_performed") is not False:
        _fail("CLI claimed context injection")
    if payload.get("model_call_performed") is not False:
        _fail("CLI claimed model call")
    if payload.get("cache_write_performed") is not False:
        _fail("CLI claimed cache write")


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 23 prompt stability verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
