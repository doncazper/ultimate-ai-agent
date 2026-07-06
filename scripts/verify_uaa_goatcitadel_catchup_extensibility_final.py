#!/usr/bin/env python3
"""Verify GoatCitadel catch-up Phase 09 extensibility hardening."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
)


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOC_REFS = {
    "doc:plugin-skill-ecosystem-boundary",
    "doc:inspectable-extension-catalog",
    "doc:extension-activation-grants",
    "doc:goatcitadel-catchup-extensibility-final",
}

REQUIRED_BLOCKED = {
    "callable_extension_catalog",
    "plugin_runtime_import",
    "arbitrary_plugin_execution",
    "skill_runtime_import",
    "connector_writes",
    "shell_subprocess_execution",
    "unrestricted_network_access",
    "browser_automation",
    "public_distribution",
}

DENIED_TRUE_FLAGS = (
    "callable_catalog_enabled",
    "automatic_instruction_loading_enabled",
    "full_instruction_auto_load_enabled",
    "hidden_skill_activation_enabled",
    "skill_runtime_import_enabled",
    "external_marketplace_fetch_enabled",
    "runtime_import_enabled",
    "execution_enabled",
    "connector_writes_enabled",
    "shell_execution_enabled",
    "network_access_enabled",
    "browser_automation_enabled",
    "mobile_control_enabled",
    "public_distribution_claimed",
)


class VerificationError(RuntimeError):
    """Raised when Phase 09 verification fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def _catalog_payload() -> dict[str, object]:
    return build_default_inspectable_extension_catalog().model_dump(mode="json")


def _verify_catalog_contract(payload: dict[str, object]) -> None:
    _require(
        payload["catalog_status"] == "read_only_inspection", "catalog is not read-only"
    )
    for field in DENIED_TRUE_FLAGS:
        _require(payload[field] is False, f"catalog enables denied flag: {field}")

    _require(
        REQUIRED_DOC_REFS.issubset(set(payload["docs_refs"])),
        "catalog missing required docs refs",
    )
    _require(
        REQUIRED_BLOCKED.issubset(set(payload["blocked_capabilities"])),
        "catalog missing blocked capability refs",
    )
    _require(
        "doc:goatcitadel-catchup-extensibility-final"
        in payload["developer_guidance_refs"],
        "catalog missing Phase 09 developer guidance ref",
    )
    _require(
        "verifier:goatcitadel-catchup-extensibility-final"
        in payload["final_hardening_refs"],
        "catalog missing Phase 09 verifier ref",
    )

    entries = payload["entries"]
    _require(isinstance(entries, list) and len(entries) >= 2, "catalog entries missing")
    for entry in entries:
        for field in (
            "visibility_status",
            "trust_posture",
            "callable_posture",
            "required_grant_refs",
            "blocked_reason",
            "review_evidence_refs",
            "safe_adoption_posture",
        ):
            _require(field in entry, f"catalog entry missing {field}")
        _require(
            entry["callable_posture"] != "callable", "entry claims callable posture"
        )
        _require(entry["review_evidence_refs"], "entry missing review evidence refs")


def _verify_api_route(payload: dict[str, object]) -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/extensions/catalog")
    _require(response.status_code == 200, "extension catalog route failed")
    body = response.json()
    _require(body["success"] is True, "extension catalog route did not succeed")
    _require(
        body["operation"] == "inspect_extension_catalog", "route operation drifted"
    )
    _require(
        body["data"]["catalog_ref"] == payload["catalog_ref"], "route catalog drifted"
    )
    for field in DENIED_TRUE_FLAGS:
        _require(body["data"][field] is False, f"route enables denied flag: {field}")


def _verify_cli(payload: dict[str, object]) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-catalog",
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    cli_payload = json.loads(result.stdout)
    _require(
        cli_payload["catalog_ref"] == payload["catalog_ref"], "CLI catalog drifted"
    )
    _require(
        cli_payload["callable_catalog_enabled"] is False,
        "CLI claims callable catalog authority",
    )


def _verify_docs() -> None:
    doc = (
        ROOT
        / "docs"
        / "control_center"
        / "UAA_GOATCITADEL_CATCHUP_EXTENSIBILITY_FINAL.md"
    ).read_text(encoding="utf-8")
    scoreboard = (
        ROOT / "docs" / "control_center" / "UAA_GOATCITADEL_CATCHUP_SCOREBOARD.md"
    ).read_text(encoding="utf-8")

    for text, name in ((doc, "Phase 09 doc"), (scoreboard, "scoreboard")):
        lowered = text.lower()
        for phrase in (
            "plugin runtime import remains blocked",
            "connector writes remain blocked",
            "production authority remains blocked",
            "safe refs",
            "30-day plan",
        ):
            _require(phrase in lowered, f"{name} missing phrase: {phrase}")
        for unsafe in (
            "plugin runtime import is enabled",
            "connector writes are enabled",
            "production authority is enabled",
            "broad autonomy is enabled",
        ):
            _require(unsafe not in lowered, f"{name} contains unsafe claim: {unsafe}")


def main() -> int:
    try:
        payload = _catalog_payload()
        _verify_catalog_contract(payload)
        _verify_api_route(payload)
        _verify_cli(payload)
        _verify_docs()
    except VerificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("UAA GoatCitadel catch-up extensibility final verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
