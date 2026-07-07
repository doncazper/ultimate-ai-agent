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
    RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_MAPPING_REF,
    RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_STATE_CLI_REF,
    RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_MANAGED_SCOPE_POLICY_BLOCKED_AUTHORITY_REFS,
    build_runtime_managed_scope_policy_read_model,
)


ROUTE = "/api/runtime/managed-scope-policy"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_MANAGED_SCOPE_POLICY.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/managed_scope_policy.py"
TEST = ROOT / "tests/test_hermes_runtime_managed_scope_policy.py"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_managed_scope_policy_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("managed scope route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-managed-scope-policy":
        failures.append("managed scope CLI ref is stale")
    if read_model.status != "read_only_local_policy_profile_posture":
        failures.append("managed scope posture is not read-only")
    if (
        read_model.authority_state_route_ref
        != RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_STATE_ROUTE_REF
    ):
        failures.append("managed scope AuthorityState route ref drifted")
    if (
        read_model.authority_state_cli_ref
        != RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_STATE_CLI_REF
    ):
        failures.append("managed scope AuthorityState CLI ref drifted")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_MAPPING_REF
    ):
        failures.append("managed scope AuthorityState mapping ref drifted")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("managed scope inspection must be allowed under read-only")
    if (
        "adapter-ref:managed-scope-system-config-write:not-implemented"
        not in read_model.unsupported_adapter_refs
    ):
        failures.append("managed scope unsupported system config adapter missing")
    if read_model.pinned_source_count < 3:
        failures.append("managed scope has too few pinned sources")
    if read_model.drift_warning_count < 1:
        failures.append("managed scope lacks drift warnings")
    if not read_model.local_config_source_visible:
        failures.append("local config source visibility is disabled")
    if not read_model.precedence_visible or not read_model.verification_visible:
        failures.append("precedence or verification visibility is disabled")
    unsafe_flags = {
        "system config write": read_model.system_config_write_enabled,
        "privileged write": read_model.privileged_write_enabled,
        "mdm delivery": read_model.mdm_delivery_enabled,
        "managed protected material": read_model.managed_secrets_enabled,
        "unsigned runtime config override": (
            read_model.unsigned_runtime_config_override_enabled
        ),
        "production enforcement": read_model.production_enforcement_claimed,
        "control center authority mint": read_model.control_center_mints_authority,
        "runtime config mutation": read_model.runtime_config_mutation_performed,
        "raw config persistence": read_model.raw_config_persisted,
        "raw path persistence": read_model.raw_local_path_persisted,
        "account material persistence": read_model.account_material_persisted,
        "credential material persistence": read_model.credential_material_persisted,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_MANAGED_SCOPE_POLICY_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing managed scope blocked refs: {sorted(missing_blocked)}")

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
        failures.append("API manifest missing managed scope route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("managed scope route side-effect classification drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("managed scope route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-managed-scope-policy",
        "runtime_managed_scope_policy",
        "raw_config_omitted",
        "protected_material_omitted",
        "system_config_write_performed",
        "authority_state",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    for path in [DOC, CORE, TEST]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    if DOC.exists():
        doc_text = DOC.read_text(encoding="utf-8")
        for expected in [
            "Full-Strength",
            "Repo-Safe",
            "Blocked / Needs Authority",
            "Exact Promotion Path",
            ROUTE,
            "inspect-managed-scope-policy",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-managed-scope-policy",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("managed scope CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_managed_scope_policy"]
        authority_state = payload.get("authority_state", {})
        if (
            authority_state.get("mapping_ref")
            != RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_MAPPING_REF
        ):
            failures.append("managed scope CLI AuthorityState mapping drifted")
        if authority_state.get("decision_outcome") != "allow":
            failures.append("managed scope CLI AuthorityState outcome drifted")
        if payload["system_config_write_performed"] is not False:
            failures.append("managed scope CLI claims system config write")
        if payload["mdm_delivery_performed"] is not False:
            failures.append("managed scope CLI claims MDM delivery")
        if payload["production_enforcement_claimed"] is not False:
            failures.append("managed scope CLI claims production enforcement")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("managed scope CLI returned stale route ref")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 27 managed scope verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
