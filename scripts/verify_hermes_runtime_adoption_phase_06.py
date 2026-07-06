#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    build_runtime_profile_isolation_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def _assert_profiles_payload(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "runtime_profile_isolation.v1":
        _fail("unexpected runtime profile isolation schema")
    if payload.get("status") != "profile_metadata_read_model_only":
        _fail("profiles must stay metadata read-model only")
    if payload.get("route_ref") != "GET /api/runtime/profiles":
        _fail("runtime profiles route ref drifted")
    if payload.get("cli_ref") != "uaa runtime inspect-profiles":
        _fail("runtime profiles CLI ref drifted")
    if payload.get("uaa_profile_refs_separate_from_delegated_runtime_refs") is not True:
        _fail("UAA profile refs must stay separate from delegated runtime refs")
    if payload.get("safe_refs_only") is not True:
        _fail("runtime profiles must use safe refs only")
    for flag in [
        "profile_creation_enabled",
        "profile_deletion_enabled",
        "runtime_config_write_enabled",
        "sensitive_material_copy_enabled",
        "runtime_default_change_enabled",
        "cross_profile_authority_bleed_allowed",
        "control_center_mints_profiles",
        "raw_profile_names_persisted",
        "raw_workspace_paths_persisted",
        "raw_sensitive_material_persisted",
    ]:
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    profiles = payload.get("profiles")
    if not isinstance(profiles, list) or len(profiles) != 5:
        _fail("expected five runtime profile records")
    if payload.get("profile_count") != len(profiles):
        _fail("profile count drifted")
    uaa_refs = set()
    delegated_refs = set()
    roles = set()
    configured = 0
    blocked = 0
    for profile in profiles:
        if not isinstance(profile, dict):
            _fail("profile record is invalid")
        uaa_refs.add(str(profile.get("profile_ref")))
        delegated_refs.add(str(profile.get("delegated_runtime_profile_ref")))
        roles.add(profile.get("role"))
        if profile.get("configured_status") == "metadata_configured":
            configured += 1
        else:
            blocked += 1
        for flag in [
            "configured_for_live_runtime",
            "can_create_runtime_profile",
            "can_delete_runtime_profile",
            "can_write_runtime_config",
            "can_copy_sensitive_material",
            "can_change_runtime_defaults",
            "can_execute_tools",
            "can_call_models",
            "can_write_memory",
            "can_access_workspace_paths",
            "cross_profile_authority_bleed_allowed",
        ]:
            if profile.get(flag) is not False:
                _fail(f"profile {flag} must remain false")
        if not str(profile.get("workspace_scope_ref", "")).startswith(
            "workspace-scope-ref:"
        ):
            _fail("profile workspace scope ref is invalid")
        if not str(profile.get("memory_scope_ref", "")).startswith(
            "memory-scope-ref:"
        ):
            _fail("profile memory scope ref is invalid")
    if uaa_refs & delegated_refs:
        _fail("UAA and delegated runtime profile refs overlap")
    if roles != {"coding", "research", "operations", "crm", "review"}:
        _fail(f"unexpected profile roles: {sorted(roles)}")
    if payload.get("configured_profile_count") != configured:
        _fail("configured profile count drifted")
    if payload.get("blocked_profile_count") != blocked:
        _fail("blocked profile count drifted")
    blocked_refs = payload.get("blocked_authority_refs")
    if not isinstance(blocked_refs, list) or (
        "blocked-authority:runtime-profile-config-write" not in blocked_refs
    ):
        _fail("missing runtime profile config-write blocker")


def main() -> None:
    read_model = build_runtime_profile_isolation_read_model()
    _assert_profiles_payload(read_model.model_dump(mode="json"))

    client = TestClient(app)
    response = client.get("/api/runtime/profiles")
    if response.status_code != 200:
        _fail(f"runtime profiles route returned {response.status_code}")
    body = response.json()
    _assert_profiles_payload(body.get("data", {}))
    if body.get("redactions_applied") is None:
        _fail("runtime profiles route must report redactions")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-profiles",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(result.stdout)
    for flag in [
        "execution_performed",
        "profile_creation_performed",
        "profile_deletion_performed",
        "runtime_config_write_performed",
        "sensitive_material_copy_performed",
        "runtime_default_change_performed",
    ]:
        if cli_payload.get(flag) is not False:
            _fail(f"CLI {flag} must remain false")
    _assert_profiles_payload(cli_payload.get("runtime_profile_isolation", {}))
    print(
        "Hermes Runtime Adoption Phase 06 runtime profile isolation verification passed."
    )


if __name__ == "__main__":
    main()
