#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.providers import build_provider_setup_guide_catalog  # noqa: E402


ROUTE_REF = "GET /control-center/providers/setup-guide"
BLOCKED_FLAGS = (
    "credential_input_enabled",
    "raw_key_storage_enabled",
    "credential_validation_enabled",
    "provider_sdk_call_enabled",
    "model_invocation_enabled",
    "automatic_pricing_refresh_enabled",
    "provider_output_authority_enabled",
)
FORBIDDEN_TEXT = (
    "paste key",
    "paste your key",
    "save key",
    "connect provider",
    "test provider",
    "invoke provider",
    "raw prompt",
    "raw response",
    "raw provider payload",
)


def main() -> int:
    failures: list[str] = []
    catalog = build_provider_setup_guide_catalog()
    payload = catalog.model_dump(mode="json")
    text = str(payload).lower()

    if catalog.route_ref != ROUTE_REF:
        failures.append("provider setup guide route_ref is missing")
    if len(catalog.provider_cards) < 30:
        failures.append("provider setup guide must include default catalog breadth")
    if not catalog.no_credential_input or not catalog.no_provider_sdk_calls:
        failures.append("catalog denial flags are not fail-closed")
    if catalog.catalog_visibility_grants_authority:
        failures.append("catalog visibility grants authority")
    for phrase in FORBIDDEN_TEXT:
        if phrase in text:
            failures.append(f"unsafe provider setup copy found: {phrase}")

    for card in catalog.provider_cards:
        if card.authority_state != "guidance_only":
            failures.append(f"{card.provider_ref} is not guidance_only")
        for flag in BLOCKED_FLAGS:
            if getattr(card, flag):
                failures.append(f"{card.provider_ref} enables {flag}")
        if not card.pricing_may_change or not card.not_billing_authority:
            failures.append(f"{card.provider_ref} missing pricing advisory flags")
        if not {source.source_kind for source in card.source_refs} >= {
            "setup",
            "api_docs",
            "pricing",
        }:
            failures.append(f"{card.provider_ref} missing required source refs")
        if not card.authority_posture.blocker_codes:
            failures.append(f"{card.provider_ref} missing blocker codes")

    manifest = build_api_manifest(app)
    route = next(
        (
            item
            for item in manifest.routes
            if item.path == "/control-center/providers/setup-guide"
            and item.method == "GET"
        ),
        None,
    )
    if route is None:
        failures.append("provider setup guide route is not in /api/manifest")
    else:
        if route.route_classification != "local_readonly":
            failures.append("provider setup guide route is not local_readonly")
        if route.side_effect_class != "validation_only":
            failures.append("provider setup guide route side-effect class changed")

    inspect_result = subprocess.run(
        [sys.executable, "scripts/inspect_provider_setup_guide.py"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        timeout=30,  # Prevent hanging if inspection script deadlocks
    )
    if inspect_result.returncode != 0:
        failures.append("inspect_provider_setup_guide.py failed")
    if "credential_values_omitted" not in inspect_result.stdout:
        failures.append("CLI inspection does not include redaction posture")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("provider catalog cost literacy verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

