#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ultimate_ai_agent.core.providers.control_plane import (
    MODEL_PROVIDER_RESEARCH_POSTURE_CONTRACT_REF,
    build_model_provider_control_plane_read_model,
)


ROOT = Path(__file__).resolve().parents[1]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _assert_no_authority(payload: dict[str, object]) -> None:
    serialized = json.dumps(payload, sort_keys=True)
    forbidden = [
        '"provider_sdk_call_enabled": true',
        '"remote_model_call_enabled": true',
        '"live_web_fetch_enabled": true',
        '"browser_automation_enabled": true',
        '"credential_entry_enabled": true',
        '"memory_write_authorized": true',
        '"action_execution_authorized": true',
        '"context_injection_authorized": true',
        '"production_authority_enabled": true',
        '"broad_autonomy_enabled": true',
        '"generated_text_is_verified_fact": true',
        '"browser_action_enabled_by_control_plane": true',
        '"fetched_content_instruction_authority_enabled": true',
    ]
    for fragment in forbidden:
        _assert(fragment not in serialized, f"forbidden authority: {fragment}")


def _assert_posture(payload: dict[str, object]) -> None:
    posture = payload["model_provider_research_posture"]
    _assert(isinstance(posture, dict), "posture missing")
    _assert(
        posture["contract_ref"] == MODEL_PROVIDER_RESEARCH_POSTURE_CONTRACT_REF,
        "contract ref drifted",
    )
    _assert(posture["provider_count"] >= 1, "provider posture rows missing")
    _assert(
        posture["provider_count"] == len(posture["provider_postures"]),
        "provider count drifted",
    )
    truth = posture["model_output_truth"]
    _assert(isinstance(truth, dict), "model output truth missing")
    _assert(
        truth["status"] == "proposal_and_evidence_not_authority",
        "model output truth posture drifted",
    )
    _assert(
        truth["verified_fact_refs_required"] is True, "verified fact refs not required"
    )
    external = posture["external_information"]
    _assert(isinstance(external, dict), "external information posture missing")
    _assert(
        external["status"] == "web_access_gateway_deny_by_default",
        "external information posture drifted",
    )
    _assert(external["web_access_gateway_required"] is True, "gateway not required")
    _assert(
        external["fetched_content_untrusted"] is True, "fetched content not untrusted"
    )
    _assert_no_authority(posture)


def main() -> int:
    read_model = build_model_provider_control_plane_read_model()
    payload = read_model.model_dump(mode="json")
    _assert_posture(payload)

    cli = subprocess.run(
        [sys.executable, "scripts/inspect_model_provider_control_plane.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(cli.stdout)
    _assert_posture(cli_payload)

    print("goatcitadel_catchup_model_provider_research: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
