#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.core.providers.control_plane import (  # noqa: E402
    build_model_provider_control_plane_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def _assert_no_authority(payload: dict[str, object]) -> None:
    serialized = json.dumps(payload, sort_keys=True)
    forbidden = [
        '"uaa_may_invoke_any_listed_model": true',
        '"uaa_invocation_allowed": true',
        '"provider_sdk_call_enabled": true',
        '"remote_model_call_enabled": true',
        '"live_provider_discovery_enabled": true',
        '"live_provider_network_call_performed": true',
        '"credential_collection_enabled": true',
        '"credential_material_visible": true',
        '"billing_authority_granted": true',
        '"model_output_authority_enabled": true',
        '"raw_provider_payload_persisted": true',
    ]
    for fragment in forbidden:
        if fragment in serialized:
            _fail(f"forbidden delegated model catalog authority: {fragment}")


def _assert_catalog(payload: dict[str, object]) -> None:
    catalog = payload.get("delegated_runtime_model_catalog")
    if not isinstance(catalog, dict):
        _fail("delegated runtime model catalog missing")
    if catalog.get("schema_version") != "delegated_runtime_model_catalog.v1":
        _fail("delegated model catalog schema drifted")
    if catalog.get("status") != "read_only_runtime_model_availability":
        _fail("delegated model catalog must stay read-only")
    if catalog.get("runtime_profiles_route_ref") != "GET /api/runtime/profiles":
        _fail("runtime profile route binding missing")
    if catalog.get("runtime_says_available_is_not_authority") is not True:
        _fail("runtime availability must not become authority")
    if catalog.get("uaa_may_invoke_any_listed_model") is not False:
        _fail("catalog must not authorize model invocation")
    if catalog.get("uaa_authorized_model_count") != 0:
        _fail("catalog authorized model count must remain zero")
    for flag in [
        "live_provider_discovery_enabled",
        "provider_sdk_call_enabled",
        "remote_model_call_enabled",
        "credential_collection_enabled",
        "billing_authority_granted",
        "model_output_authority_enabled",
    ]:
        if catalog.get(flag) is not False:
            _fail(f"{flag} must remain false")
    records = catalog.get("records")
    if not isinstance(records, list) or not records:
        _fail("delegated model catalog records missing")
    if catalog.get("model_count") != len(records):
        _fail("delegated model catalog count drifted")
    available_count = 0
    for record in records:
        if not isinstance(record, dict):
            _fail("delegated model catalog record is invalid")
        if record.get("runtime_reported_available") is True:
            available_count += 1
        if record.get("runtime_profile_ref") == record.get(
            "delegated_runtime_profile_ref"
        ):
            _fail("runtime profile ref must differ from delegated runtime ref")
        if record.get("uaa_invocation_allowed") is not False:
            _fail("delegated model record must not authorize invocation")
        if record.get("provider_sdk_call_enabled") is not False:
            _fail("delegated model record must not enable provider SDK calls")
        if record.get("live_provider_network_call_performed") is not False:
            _fail("delegated model record must not perform network calls")
        if record.get("raw_provider_payload_persisted") is not False:
            _fail("delegated model record must not persist raw provider payloads")
        if not record.get("blocked_authority_refs"):
            _fail("delegated model record blockers missing")
    if catalog.get("runtime_reported_available_count") != available_count:
        _fail("delegated model catalog available count drifted")
    if "proof-ref:hermes-runtime-adoption:phase-07:model-provider-catalog" not in (
        catalog.get("proof_refs") or []
    ):
        _fail("phase 07 proof ref missing")


def main() -> None:
    read_model = build_model_provider_control_plane_read_model()
    core_payload = read_model.model_dump(mode="json")
    _assert_catalog(core_payload)
    _assert_no_authority(core_payload)

    client = TestClient(app)
    response = client.get("/control-center/providers/runtime-control-plane")
    if response.status_code != 200:
        _fail(f"runtime control plane route returned {response.status_code}")
    body = response.json()
    api_payload = body.get("data")
    if not isinstance(api_payload, dict):
        _fail("runtime control plane route did not return data")
    _assert_catalog(api_payload)
    _assert_no_authority(api_payload)

    result = subprocess.run(
        [sys.executable, "scripts/inspect_model_provider_control_plane.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(result.stdout)
    _assert_catalog(cli_payload)
    _assert_no_authority(cli_payload)
    print(
        "Hermes Runtime Adoption Phase 07 model provider catalog verification passed."
    )


if __name__ == "__main__":
    main()
