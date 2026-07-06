#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_VIRTUAL_PROVIDER_MOA_BLOCKED_AUTHORITY_REFS,
    build_runtime_virtual_provider_moa_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"Hermes Runtime Adoption Phase 20 verification failed: {message}")


def _assert_read_model(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "runtime_virtual_provider_moa.v1":
        _fail("unexpected virtual provider schema")
    if payload.get("status") != "read_only_virtual_provider_preset_posture":
        _fail("virtual provider posture is not read-only")
    if payload.get("route_ref") != "GET /api/runtime/virtual-provider-moa":
        _fail("route ref drifted")
    for flag in (
        "live_model_fanout_enabled",
        "provider_sdk_enabled",
        "external_runtime_dispatch_enabled",
        "hidden_advisor_prompts_enabled",
        "raw_prompt_persistence_enabled",
        "raw_response_persistence_enabled",
        "output_authority_enabled",
        "production_authority_enabled",
    ):
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    blockers = set(payload.get("blocked_authority_refs") or [])
    if set(RUNTIME_VIRTUAL_PROVIDER_MOA_BLOCKED_AUTHORITY_REFS) - blockers:
        _fail("missing virtual provider blocked authority refs")
    presets = payload.get("presets") or []
    if payload.get("preset_count") != len(presets):
        _fail("preset count mismatch")
    if not presets:
        _fail("virtual provider presets missing")
    for preset in presets:
        for flag in (
            "live_model_fanout_enabled",
            "provider_sdk_enabled",
            "external_runtime_dispatch_enabled",
            "hidden_advisor_prompts_enabled",
            "raw_prompt_persistence_enabled",
            "raw_response_persistence_enabled",
            "output_authority_enabled",
            "production_authority_enabled",
        ):
            if preset.get(flag) is not False:
                _fail(f"preset {flag} must remain false")
        slots = preset.get("slots") or []
        if preset.get("slot_count") != len(slots):
            _fail("slot count mismatch")
        for slot in slots:
            for flag in (
                "configured_for_live_call",
                "provider_sdk_call_enabled",
                "external_runtime_dispatch_enabled",
                "hidden_advisor_prompt_enabled",
                "raw_prompt_persisted",
                "raw_response_persisted",
                "output_authoritative",
                "production_authority_enabled",
            ):
                if slot.get(flag) is not False:
                    _fail(f"slot {flag} must remain false")


def verify_core() -> None:
    _assert_read_model(
        build_runtime_virtual_provider_moa_read_model().model_dump(mode="json")
    )


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/api/runtime/virtual-provider-moa")
    if response.status_code != 200:
        _fail(f"GET /api/runtime/virtual-provider-moa returned {response.status_code}")
    body = response.json()
    if body.get("success") is not True:
        _fail("API did not return success envelope")
    _assert_read_model(body.get("data") or {})
    serialized = json.dumps(body).lower()
    for forbidden in ("/users/", "raw_prompt_payload", "raw_response_payload"):
        if forbidden in serialized:
            _fail(f"API payload exposed forbidden marker {forbidden}")


def verify_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-virtual-provider-moa",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    _assert_read_model(payload.get("runtime_virtual_provider_moa") or {})
    if payload.get("live_model_fanout_performed") is not False:
        _fail("CLI claimed live model fan-out")
    if payload.get("provider_sdk_call_performed") is not False:
        _fail("CLI claimed provider SDK call")
    if payload.get("external_runtime_dispatch_performed") is not False:
        _fail("CLI claimed external runtime dispatch")


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 20 virtual provider verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
