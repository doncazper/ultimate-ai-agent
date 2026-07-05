#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    GOVERNED_PRODUCT_PILOT_PROFILE_REF,
    GOVERNED_PRODUCT_PILOT_REQUIRED_BLOCKED_AUTHORITY_REFS,
    build_governed_product_pilot_authority_profile,
    verify_portable_evidence_envelope,
)


PROFILE_ROUTE = "/api/runtime/governed-product-pilot-profile"


def _append(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)


def _cli_profile() -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dev" / "uaa_runtime.py"),
            "authority-profile",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)["authority_profile"]


def _cli_verify_profile_envelope() -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dev" / "uaa_runtime.py"),
            "verify-evidence-envelope",
            "--profile",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)["verification"]


def main() -> int:
    failures: list[str] = []
    profile = build_governed_product_pilot_authority_profile().model_dump(mode="json")

    _append(
        profile["profile_ref"] == GOVERNED_PRODUCT_PILOT_PROFILE_REF,
        failures,
        "profile ref mismatch",
    )
    _append(
        profile["default_runtime_profile"] == "sealed",
        failures,
        "sealed default profile changed",
    )
    _append(
        profile["sealed_default_hard_rules_preserved"] is True,
        failures,
        "sealed hard rules are not marked preserved",
    )
    for field in [
        "control_center_mints_authority",
        "broad_autonomy_enabled",
        "unrestricted_shell_subprocess_enabled",
        "browser_automation_enabled",
        "connector_writes_enabled",
        "remote_execution_enabled",
        "plugin_runtime_import_enabled",
        "production_authority_enabled",
        "public_beta_or_release_claim_enabled",
        "raw_prompt_response_provider_payload_log_path_persistence_enabled",
    ]:
        _append(profile[field] is False, failures, f"{field} must remain false")
    required = set(GOVERNED_PRODUCT_PILOT_REQUIRED_BLOCKED_AUTHORITY_REFS)
    _append(
        required.issubset(set(profile["blocked_authority_refs"])),
        failures,
        "required blocked authority refs missing",
    )
    _append(len(profile["lanes"]) >= 4, failures, "core pilot lanes missing")
    for lane in profile["lanes"]:
        if lane["execution_capable"] and not lane["read_only_no_op"]:
            _append(
                lane["approval_binding_required"] is True,
                failures,
                f"execution lane {lane['lane_ref']} lacks approval binding",
            )
        _append(lane["raw_persistence_allowed"] is False, failures, "raw persistence allowed")
        _append(
            lane["control_center_presentation_only"] is True,
            failures,
            "Control Center presentation-only posture missing",
        )

    envelope = profile["portable_evidence_envelope"]
    for field in [
        "receipt_ref",
        "evidence_ref",
        "action_id",
        "side_effect_class",
        "policy_decision_ref",
        "approval_ref",
        "issued_at",
        "envelope_hash_ref",
        "signed_envelope_ref",
        "verifier_version_ref",
    ]:
        _append(bool(envelope.get(field)), failures, f"evidence envelope missing {field}")
    _append(
        envelope["signed_envelope_ref"].startswith("signed-envelope-ref:sha256:"),
        failures,
        "evidence envelope signed ref is not local hash signed",
    )
    _append(
        envelope["public_notarization_enabled"] is False,
        failures,
        "portable evidence must not claim public notarization",
    )
    _append(
        envelope["raw_payload_persisted"] is False,
        failures,
        "portable evidence must not persist raw payloads",
    )
    verification = verify_portable_evidence_envelope(envelope).model_dump(mode="json")
    _append(
        verification["verification_status"] == "passed",
        failures,
        "portable evidence offline verification failed",
    )
    _append(
        verification["tamper_detected"] is False,
        failures,
        "fresh portable evidence envelope should not be tampered",
    )
    tampered = envelope | {"action_id": "governed-product-pilot-tampered"}
    tampered_verification = verify_portable_evidence_envelope(tampered).model_dump(
        mode="json"
    )
    _append(
        tampered_verification["verification_status"] == "failed",
        failures,
        "portable evidence verifier did not reject tampered envelope",
    )
    _append(
        tampered_verification["tamper_detected"] is True,
        failures,
        "portable evidence verifier did not mark tamper detection",
    )

    client = TestClient(app)
    response = client.get(PROFILE_ROUTE)
    _append(response.status_code == 200, failures, "profile API route failed")
    if response.status_code == 200:
        body = response.json()
        _append(body["success"] is True, failures, "profile API route returned failure")
        _append(
            body["data"]["profile_ref"] == profile["profile_ref"],
            failures,
            "profile API route returned different profile ref",
        )

    cli_profile = _cli_profile()
    _append(
        cli_profile["profile_ref"] == profile["profile_ref"],
        failures,
        "CLI profile ref mismatch",
    )
    cli_verification = _cli_verify_profile_envelope()
    _append(
        cli_verification["verification_status"] == "passed",
        failures,
        "CLI evidence envelope verification failed",
    )
    _append(
        cli_verification["input_path_echoed"] is False,
        failures,
        "CLI evidence verifier must not echo local input paths",
    )

    manifest = build_api_manifest(app).model_dump(mode="json")
    manifest_paths = {route["path"] for route in manifest["routes"]}
    _append(PROFILE_ROUTE in manifest_paths, failures, "profile route missing from manifest")
    _append(
        "governed_product_pilot_authority_profile"
        in manifest["capabilities_declared"],
        failures,
        "profile capability missing from manifest",
    )
    _append(
        "governed_product_pilot_production_authority"
        in manifest["capabilities_blocked"],
        failures,
        "production authority block missing from manifest",
    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Governed Product Pilot authority profile verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
