#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RuntimeCapabilityGroupKind,
    build_runtime_capability_discovery_read_model,
)


def main() -> int:
    read_model = build_runtime_capability_discovery_read_model()
    failures: list[str] = []

    if read_model.schema_version != "runtime_capability_discovery.v1":
        failures.append("schema version drifted")
    if read_model.runtime_reachable:
        failures.append("runtime reachability claimed without transport authority")
    if read_model.live_discovery_performed:
        failures.append("live discovery was claimed")
    if not read_model.stale_or_unreachable_degrades_to_blocked:
        failures.append("stale/unreachable states must degrade to blocked")
    if not read_model.runtime_supported_cannot_grant_uaa_permission:
        failures.append("runtime support must not grant UAA permission")
    if read_model.uaa_authorized_capability_count != 0:
        failures.append("capability discovery authorized execution")
    if read_model.control_center_talks_directly_to_runtime:
        failures.append("Control Center direct runtime access was enabled")
    if not read_model.safe_refs_only:
        failures.append("safe refs only flag is false")
    if any(
        [
            read_model.raw_prompt_persisted,
            read_model.raw_response_persisted,
            read_model.raw_provider_payload_persisted,
            read_model.raw_runtime_payload_persisted,
            read_model.raw_log_persisted,
            read_model.raw_local_path_persisted,
            read_model.credential_material_persisted,
        ]
    ):
        failures.append("raw or sensitive persistence flag was enabled")
    expected_groups = {kind.value for kind in RuntimeCapabilityGroupKind}
    actual_groups = {group.group_kind for group in read_model.capability_groups}
    if actual_groups != expected_groups:
        failures.append("capability taxonomy is incomplete")
    for group in read_model.capability_groups:
        if group.uaa_authorized_for_execution:
            failures.append(f"{group.group_ref} authorized execution")
        if not group.stale_or_unreachable_degrades_to_blocked:
            failures.append(f"{group.group_ref} does not degrade stale state")

    if failures:
        print("Hermes runtime adoption Phase 02 verifier failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        "OK: Hermes runtime adoption Phase 02 capability discovery is "
        "static, safe-ref, and non-authoritative."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
