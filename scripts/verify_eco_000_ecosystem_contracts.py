#!/usr/bin/env python3
"""Verify ECO-000 contracts, acceptance artifacts, and non-authority scope."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ADRS = tuple(
    ROOT / "docs/decisions" / f"ADR-{number:04d}-{suffix}.md"
    for number, suffix in (
        (54, "canonical-application-object-ownership"),
        (55, "entity-links-and-projections"),
        (56, "shared-local-application-data-platform-direction"),
        (57, "existing-store-migration-and-compatibility"),
        (58, "private-data-and-governance-planes"),
        (59, "cross-app-changesets"),
        (60, "local-atomicity-and-external-compensation"),
        (61, "ecosystem-shell-navigation-and-launch"),
    )
)
REQUIRED_APPS = {"calendar", "tasks", "boards", "crm", "inbox", "organizer", "today"}
REQUIRED_STATES = {
    "empty", "loading", "locked", "offline", "stale", "conflict",
    "blocked", "partial", "error", "success", "undo",
}
REQUIRED_DIMENSIONS = {
    "primary_workflows", "canonical_records", "required_views",
    "quick_capture", "search", "filtering_saved_views", "import_export",
    "local_crud", "conflict_handling", "undo_history", "backup_recovery",
    "state_coverage", "keyboard_screen_reader", "display_modes",
    "api_cli_parity", "evidence_privacy", "standalone_worthiness",
    "optional_integrations",
}
REQUIRED_SURFACES = {
    "ECO-TODAY-DESKTOP-DEFAULT",
    "ECO-CALENDAR-DESKTOP-WEEK",
    "ECO-TASKS-DESKTOP-TODAY",
    "ECO-BOARDS-DESKTOP-GENERAL",
    "ECO-CRM-SALES-DESKTOP-HOME",
    "ECO-INBOX-DESKTOP-MULTIAPP-PROPOSAL",
    "ECO-CHANGESET-DESKTOP-REVIEW",
    "ECO-CHANGESET-DESKTOP-PARTIAL",
    "ECO-SEARCH-DESKTOP-PALETTE",
    "ECO-SETTINGS-DESKTOP-PRIVACY",
    "ECO-TODAY-NARROW-AGENDA",
    "ECO-ORGANIZER-WALLBOARD-SCHEDULE",
}


def _load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def verify() -> list[str]:
    failures: list[str] = []

    for path in REQUIRED_ADRS:
        if not path.is_file():
            failures.append(f"missing ADR: {path.name}")

    acceptance = _load("docs/product/eco_000_app_acceptance.json")
    if acceptance.get("implementation_authorized") is not False:
        failures.append("ECO-000 acceptance must not authorize implementation")
    if acceptance.get("runtime_routes_added") is not False:
        failures.append("ECO-000 acceptance must not add runtime routes")
    if set(acceptance.get("required_states", [])) != REQUIRED_STATES:
        failures.append("standalone acceptance state coverage is incomplete")
    if set(acceptance.get("required_dimensions", [])) != REQUIRED_DIMENSIONS:
        failures.append("standalone acceptance dimensions are incomplete")
    apps = acceptance.get("apps", [])
    app_ids = {item.get("app_id") for item in apps if isinstance(item, dict)}
    if app_ids != REQUIRED_APPS:
        failures.append("standalone app acceptance set is incomplete")
    for item in apps:
        if not isinstance(item, dict):
            failures.append("invalid app acceptance record")
            continue
        if item.get("status") != "planned":
            failures.append(f"app must remain planned: {item.get('app_id')}")
        if item.get("local_manual_useful") is not True:
            failures.append(f"local/manual usefulness missing: {item.get('app_id')}")
        if item.get("connector_required") is not False:
            failures.append(f"connector-free usefulness missing: {item.get('app_id')}")
        if not item.get("workflow_refs") or not item.get("view_refs"):
            failures.append(f"workflow/view acceptance missing: {item.get('app_id')}")
    crm = next((item for item in apps if item.get("app_id") == "crm"), {})
    if set(crm.get("required_presets", [])) != {
        "sales", "real_estate", "professional_network", "personal_network",
        "private_relationships",
    }:
        failures.append("CRM preset acceptance is incomplete")
    if crm.get("shared_boards_required") is not True:
        failures.append("CRM must require shared Boards")

    manifest = _load("docs/design/ecosystem_north_star/render_manifest.json")
    if manifest.get("implementation_evidence") is not False:
        failures.append("render manifest must not claim implementation evidence")
    if manifest.get("runtime_routes_added") is not False:
        failures.append("render manifest must not claim runtime routes")
    surfaces = manifest.get("surfaces", [])
    surface_ids = {
        item.get("surface_state_ref") for item in surfaces if isinstance(item, dict)
    }
    if surface_ids != REQUIRED_SURFACES:
        failures.append("required render surface/state coverage is incomplete")
    for item in surfaces:
        if not isinstance(item, dict):
            failures.append("invalid render manifest record")
            continue
        asset = ROOT / "docs/design/ecosystem_north_star" / str(item.get("asset"))
        if not asset.is_file() or asset.stat().st_size < 1_000:
            failures.append(f"render asset missing or empty: {asset.name}")
        if item.get("status") != "reviewed" or item.get("shipped") is not False:
            failures.append(f"render truth invalid: {item.get('surface_state_ref')}")

    required_docs = (
        "docs/architecture/ECO_000_EXISTING_STATE_AND_MIGRATION_INVENTORY.md",
        "docs/architecture/ECO_000_ROUTE_AND_INFORMATION_ARCHITECTURE.md",
        "docs/security/ECO_000_APP_ECOSYSTEM_THREAT_MODEL.md",
        "docs/product/ECO_000_APP_ACCEPTANCE_MATRIX.md",
        "docs/quality/ECO_000_QUALITY_BUDGETS.md",
        "docs/design/ecosystem_north_star/RENDER_BRIEFS.md",
        "docs/design/ecosystem_north_star/RENDER_VARIATION_MATRIX.md",
    )
    for relative in required_docs:
        if not (ROOT / relative).is_file():
            failures.append(f"missing ECO-000 artifact: {relative}")

    api_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src/ultimate_ai_agent/api").glob("*.py")
    )
    if "/ecosystem" in api_text or "/calendar" in api_text and "eco-000" in api_text.lower():
        failures.append("ECO-000 runtime API route detected")

    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(
        "ECO-000 verified: ownership/acceptance/render artifacts are complete; "
        "apps remain planned and runtime authority is unchanged."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
