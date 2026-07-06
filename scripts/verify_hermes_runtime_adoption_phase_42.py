#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RUNTIME_MESSAGING_GATEWAY_BLOCKED_AUTHORITY_REFS,
    build_runtime_messaging_gateway_posture_read_model,
)

DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_MESSAGING_GATEWAY_POSTURE.md"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/messaging_gateway_posture.py"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
TEST = ROOT / "tests/test_hermes_runtime_messaging_gateway_posture.py"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
DOC_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_messaging_gateway_posture_read_model()

    if read_model.status != "metadata_readiness_map_only":
        failures.append("messaging gateway status is not metadata-only")
    if read_model.cli_ref != "uaa runtime inspect-messaging-gateway-posture":
        failures.append("messaging gateway CLI ref drifted")
    if read_model.platform_count != 6:
        failures.append("messaging gateway platform count drifted")
    if read_model.blocked_platform_count != read_model.platform_count:
        failures.append("not every messaging platform is blocked")

    denied_flags = {
        "connector runtime": read_model.connector_runtime_enabled,
        "connector read": read_model.connector_read_enabled,
        "send": read_model.send_enabled,
        "oauth": read_model.oauth_enabled,
        "webhook exposure": read_model.webhook_exposure_enabled,
        "account sync": read_model.account_sync_enabled,
        "external write": read_model.external_write_enabled,
        "raw message": read_model.raw_message_persisted,
        "control center authority": read_model.control_center_mints_authority,
    }
    for label, enabled in denied_flags.items():
        if enabled:
            failures.append(f"{label} unexpectedly enabled")

    missing_blocked = set(RUNTIME_MESSAGING_GATEWAY_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing blocked authority refs: {sorted(missing_blocked)}")

    for platform in read_model.platforms:
        if platform.status != "blocked_until_authority":
            failures.append(f"platform not blocked: {platform.platform_ref}")
        platform_denied = [
            platform.connector_runtime_enabled,
            platform.connector_read_enabled,
            platform.send_enabled,
            platform.oauth_enabled,
            platform.webhook_exposure_enabled,
            platform.account_sync_enabled,
            platform.external_write_enabled,
            platform.raw_message_persisted,
            platform.control_center_mints_authority,
        ]
        if any(platform_denied):
            failures.append(f"platform grants authority: {platform.platform_ref}")

    for path in [DOC, CORE, CLI, TEST, PRODUCT_TRUTH, DOC_INDEX]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    doc_text = DOC.read_text(encoding="utf-8")
    for expected in [
        "Full-Strength",
        "Repo-Safe",
        "Blocked / Needs Authority",
        "Exact Promotion Path",
        "connector runtime",
        "connector reads",
        "sends",
        "OAuth",
        "webhook exposure",
        "Planning text and readiness labels do not grant",
    ]:
        if expected not in doc_text:
            failures.append(f"doc missing {expected}")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-messaging-gateway-posture",
        "runtime_messaging_gateway_posture",
        "send_performed",
        "oauth_performed",
        "webhook_exposure_performed",
        "external_write_performed",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    product_truth = PRODUCT_TRUTH.read_text(encoding="utf-8")
    for expected in [
        "Hermes Runtime Adoption Phase 42",
        "UAA_HERMES_RUNTIME_MESSAGING_GATEWAY_POSTURE.md",
        "messaging_gateway_posture.py",
        "inspect-messaging-gateway-posture",
    ]:
        if expected not in product_truth:
            failures.append(f"product truth missing {expected}")

    if "Hermes runtime messaging gateway posture" not in DOC_INDEX.read_text(
        encoding="utf-8"
    ):
        failures.append("documentation index missing messaging gateway entry")

    cli_result = subprocess.run(
        [sys.executable, str(CLI), "inspect-messaging-gateway-posture", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("messaging gateway CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        for field in [
            "connector_runtime_performed",
            "connector_read_performed",
            "send_performed",
            "oauth_performed",
            "webhook_exposure_performed",
            "account_sync_performed",
            "external_write_performed",
        ]:
            if payload[field] is not False:
                failures.append(f"CLI claims {field}")
        if payload["runtime_messaging_gateway_posture"]["platform_count"] != 6:
            failures.append("CLI returned stale platform count")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 42 messaging gateway verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
