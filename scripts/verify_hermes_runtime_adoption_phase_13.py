#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
    validate_inspectable_extension_catalog,
)


DENIED_ROOT_FLAGS = [
    "automatic_instruction_loading_enabled",
    "full_instruction_auto_load_enabled",
    "hidden_skill_activation_enabled",
    "skill_runtime_import_enabled",
    "external_marketplace_fetch_enabled",
    "runtime_import_enabled",
    "execution_enabled",
    "connector_writes_enabled",
]


def _fail(message: str) -> None:
    raise SystemExit(f"Hermes Runtime Adoption Phase 13 verification failed: {message}")


def _assert_catalog(catalog: dict[str, object]) -> None:
    if catalog.get("progressive_disclosure_enabled") is not True:
        _fail("progressive disclosure is not enabled")
    if catalog.get("metadata_first_index_enabled") is not True:
        _fail("metadata-first index is not enabled")
    for flag in DENIED_ROOT_FLAGS:
        if catalog.get(flag) is not False:
            _fail(f"{flag} must remain false")
    if "compact-skill-index:uaa-owned-progressive-disclosure" not in (
        catalog.get("compact_skill_index_refs") or []
    ):
        _fail("compact skill index ref missing")
    skill_entries = [
        entry
        for entry in catalog.get("entries", [])
        if entry.get("package_identity", {}).get("package_kind") == "skill"
    ]
    if not skill_entries:
        _fail("skill metadata entry missing")
    skill = skill_entries[0]
    if skill.get("progressive_disclosure_status") != "metadata_indexed":
        _fail("skill entry is not metadata-indexed")
    if skill.get("full_instruction_load_posture") != (
        "operator_selected_review_required"
    ):
        _fail("skill entry does not require operator-selected instruction review")
    if skill.get("automatic_instruction_loading_enabled") is not False:
        _fail("skill entry auto instruction loading must remain false")
    if skill.get("hidden_activation_enabled") is not False:
        _fail("skill entry hidden activation must remain false")


def verify_core() -> None:
    catalog = build_default_inspectable_extension_catalog()
    validate_inspectable_extension_catalog(catalog)
    _assert_catalog(catalog.model_dump(mode="json"))


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/extensions/catalog")
    if response.status_code != 200:
        _fail(f"GET /extensions/catalog returned {response.status_code}")
    body = response.json()
    if body.get("success") is not True:
        _fail("GET /extensions/catalog did not return success")
    payload = json.dumps(body).lower()
    for forbidden in ("raw_prompt", "raw_response", "raw_provider_payload", "/users/"):
        if forbidden in payload:
            _fail(f"API payload exposed forbidden marker {forbidden}")
    _assert_catalog(body.get("data") or {})


def verify_cli() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dev/uaa_extensions.py", "inspect-catalog", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = result.stdout.lower()
    for forbidden in ("raw_prompt", "raw_response", "raw_provider_payload", "/users/"):
        if forbidden in payload:
            _fail(f"CLI payload exposed forbidden marker {forbidden}")
    _assert_catalog(json.loads(result.stdout))


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 13 progressive skill verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
