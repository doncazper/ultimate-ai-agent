#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from ultimate_ai_agent.core.control_center.operational_status import (
    build_control_center_settings_status,
)


def inspect_settings_authority_posture() -> dict[str, Any]:
    status = build_control_center_settings_status()
    payload = status.model_dump(mode="json")
    return {
        "ok": True,
        "schema_version": payload["schema_version"],
        "contract_ref": payload["settings_authority_contract_ref"],
        "route_ref": payload["route_ref"],
        "status": payload["status"],
        "authority_postures": payload["authority_postures"],
        "kill_switch_postures": payload["kill_switch_postures"],
        "feature_flag_postures": payload["feature_flag_postures"],
        "blocked_authorities": payload["blocked_authorities"],
        "redactions_applied": payload["redactions_applied"],
        "authority_denied": {
            "callable_runtime_authority_enabled": payload[
                "callable_runtime_authority_enabled"
            ],
            "provider_configuration_enabled": payload[
                "provider_configuration_enabled"
            ],
            "installer_behavior_enabled": payload["installer_behavior_enabled"],
            "settings_toggle_grants_authority": payload[
                "settings_toggle_grants_authority"
            ],
            "catalog_visibility_grants_authority": payload[
                "catalog_visibility_grants_authority"
            ],
            "production_authority_enabled": payload["production_authority_enabled"],
        },
        "inspection_refs": [
            payload["api_manifest_route_ref"],
            payload["runtime_readiness_route_ref"],
            payload["runtime_capability_matrix_ref"],
            payload["platform_capability_snapshot_ref"],
            payload["platform_capability_inspection_ref"],
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect backend-owned Settings authority posture without granting authority."
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args()
    payload = inspect_settings_authority_posture()
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
