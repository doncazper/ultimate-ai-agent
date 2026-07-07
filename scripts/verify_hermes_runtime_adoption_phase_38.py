#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RUNTIME_LOGGING_PROFILE_AUTHORITY_MAPPING_REF,
    RUNTIME_LOGGING_PROFILE_BLOCKED_AUTHORITY_REFS,
    build_runtime_logging_profile_read_model,
)


ROUTE = "/api/runtime/logging-profile"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_LOGGING_PROFILE.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/logging_profile.py"
TEST = ROOT / "tests/test_hermes_runtime_logging_profile.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_logging_profile_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("logging profile route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-logging-profile":
        failures.append("logging profile CLI ref is stale")
    if read_model.status != "quiet_default_redacted_troubleshooting_available":
        failures.append("logging profile posture is not quiet default")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_LOGGING_PROFILE_AUTHORITY_MAPPING_REF
    ):
        failures.append("logging profile AuthorityState mapping is stale")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("logging profile AuthorityState decision must allow read")
    if read_model.authority_state_status != "implemented_authority_bound_read_model":
        failures.append("logging profile AuthorityState status drifted")
    if (
        "reason-ref:authority:active-lease-grants-domain-capability"
        not in read_model.authority_state_reason_refs
    ):
        failures.append("logging profile AuthorityState reason is missing")
    if read_model.unsupported_adapter_refs:
        failures.append("logging profile should not expose unsupported adapters")
    if read_model.profile_count != 3:
        failures.append("logging profile lacks expected profiles")
    if read_model.quiet_default_count != 1:
        failures.append("logging profile quiet count drifted")
    if read_model.disabled_until_flagged_count != 1:
        failures.append("logging profile flagged count drifted")
    if read_model.blocked_raw_detail_count != 1:
        failures.append("logging profile blocked raw detail count drifted")

    unsafe_flags = {
        "verbose logging": read_model.verbose_logging_enabled,
        "raw logs": read_model.raw_logs_persisted,
        "raw prompts": read_model.raw_prompt_persisted,
        "raw responses": read_model.raw_response_persisted,
        "provider payloads": read_model.provider_payload_persisted,
        "local paths": read_model.local_path_persisted,
        "credentials": read_model.credential_material_persisted,
        "remote telemetry export": read_model.remote_telemetry_export_enabled,
        "background log stream": read_model.background_log_stream_enabled,
        "control center authority mint": read_model.control_center_mints_authority,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")

    missing_blocked = set(RUNTIME_LOGGING_PROFILE_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing logging profile blockers: {sorted(missing_blocked)}")

    for profile in read_model.profiles:
        if profile.raw_logs_persisted or profile.raw_prompt_persisted:
            failures.append(f"profile persists raw logs/prompts: {profile.profile_ref}")
        if profile.raw_response_persisted or profile.provider_payload_persisted:
            failures.append(
                f"profile persists response/provider payload: {profile.profile_ref}"
            )
        if profile.local_path_persisted or profile.credential_material_persisted:
            failures.append(f"profile persists path/credential: {profile.profile_ref}")
        if profile.remote_telemetry_export_enabled:
            failures.append(f"profile exports telemetry: {profile.profile_ref}")
        if profile.background_log_stream_enabled:
            failures.append(f"profile starts background log stream: {profile.profile_ref}")

    manifest = build_api_manifest(app)
    route = next(
        (
            item
            for item in manifest.routes
            if item.path == ROUTE and item.method == "GET"
        ),
        None,
    )
    if route is None:
        failures.append("API manifest missing logging profile route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("logging profile route side-effect drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("logging profile route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-logging-profile",
        "runtime_logging_profile",
        "verbose_logging_toggled",
        "raw_logs_omitted",
        "remote_telemetry_export_performed",
        "background_log_stream_started",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    for path in [DOC, CORE, TEST, UI]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    if DOC.exists():
        doc_text = DOC.read_text(encoding="utf-8")
        for expected in [
            "Full-Strength",
            "Repo-Safe",
            "Blocked / Needs Authority",
            "AuthorityState",
            "Exact Authority Path",
            RUNTIME_LOGGING_PROFILE_AUTHORITY_MAPPING_REF,
            ROUTE,
            "inspect-logging-profile",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [sys.executable, str(CLI), "inspect-logging-profile", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("logging profile CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_logging_profile"]
        for flag in [
            "verbose_logging_toggled",
            "remote_telemetry_export_performed",
            "background_log_stream_started",
        ]:
            if payload[flag] is not False:
                failures.append(f"logging profile CLI claims {flag}")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("logging profile CLI returned stale route ref")
        if (
            read_model_payload["authority_state_mapping_ref"]
            != RUNTIME_LOGGING_PROFILE_AUTHORITY_MAPPING_REF
        ):
            failures.append("logging profile CLI returned stale AuthorityState mapping")
        if read_model_payload["authority_state_decision_outcome"] != "allow":
            failures.append("logging profile CLI returned unsafe AuthorityState decision")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 38 logging profile verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
