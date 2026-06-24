#!/usr/bin/env python3
"""Validate the UAA-P1-066 read-only Control Center local model status slice."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "UAA-P1-066"
SCOPE_DOC = (
    ROOT / "docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md"
)
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
ROADMAP = ROOT / "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
CANONICAL_ROADMAP = ROOT / "docs/canonical/09_roadmap.md"
README = ROOT / "README.md"
OPERATIONAL_MATURITY_MANIFEST = (
    ROOT / "docs/control_center/operational_maturity_manifest.json"
)
CORE_STATUS = ROOT / "src/ultimate_ai_agent/core/control_center/operational_status.py"
API_APP = ROOT / "src/ultimate_ai_agent/api/app.py"
API_MANIFEST = ROOT / "src/ultimate_ai_agent/api/manifest.py"
FRONTEND_ENDPOINTS = ROOT / "apps/control-center/src/api/endpoints.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/OperatorFlowPanels.tsx"
FRONTEND_STATES = ROOT / "apps/control-center/src/components/OperatorSurfaceStates.tsx"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
ROUTE_TEST = ROOT / "tests/test_control_center_api_routes.py"
MANIFEST_TEST = ROOT / "tests/test_api_manifest.py"

SCOPE_REF = "docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md"
ROUTE_REF = "GET /control-center/local-models/status"
ROUTE_PATH = "/control-center/local-models/status"
CORE_INVENTORY_REF = "src/ultimate_ai_agent/core/local_model_management/inventory.py"
CLI_REF = "scripts/dev/uaa_local_model.py"
FRONTEND_ENDPOINT_REF = (
    "apps/control-center/src/api/endpoints.ts::controlCenterLocalModelsStatus"
)
VERIFIER_REF = "scripts/verify_uaa_p1_066_local_model_control_center_status.py"


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_text(root: Path, path: Path, failures: list[str]) -> str:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return ""
    return target.read_text(encoding="utf-8")


def _read_json(root: Path, path: Path, failures: list[str]) -> dict[str, Any]:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return {}
    try:
        loaded = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON in {rel_path.as_posix()}: {exc.msg}")
        return {}
    if not isinstance(loaded, dict):
        failures.append(f"{rel_path.as_posix()} must contain a JSON object")
        return {}
    return loaded


def _require_fragments(
    rel_path: str,
    text: str,
    fragments: list[str],
    failures: list[str],
) -> None:
    compact = " ".join(text.lower().split())
    lowered = text.lower()
    for fragment in fragments:
        needle = fragment.lower()
        if needle not in lowered and needle not in compact:
            failures.append(f"{rel_path} missing UAA-P1-066 fragment: {fragment}")


def _validate_scope_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, SCOPE_DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(SCOPE_DOC),
        text,
        [
            "Status: Implemented",
            "strictly read-only Control Center model inventory and status surface",
            ROUTE_REF,
            "ControlCenterLocalModelsStatus",
            "build_control_center_local_models_status",
            CORE_INVENTORY_REF,
            CLI_REF,
            FRONTEND_ENDPOINT_REF,
            "proposal_review_only",
            "lifecycle_actions",
            "all lifecycle actions are false",
            "model_download",
            "model_switch",
            "provider_model_authority",
            "No start, stop, activate, switch, unload, or lifecycle controls",
            "No React-owned model truth",
            VERIFIER_REF,
            "tests/test_control_center_api_routes.py::test_control_center_local_models_status_is_read_only_and_blocks_lifecycle",
            "tests/test_api_manifest.py",
        ],
        failures,
    )


def _validate_backend_contract(root: Path, failures: list[str]) -> None:
    backend_requirements = {
        CORE_STATUS: [
            "LOCAL_MODELS_STATUS_ROUTE_REF",
            ROUTE_REF,
            "ControlCenterLocalModelsStatus",
            "build_control_center_local_models_status",
            "inspect_local_model_inventory",
            "inspect_local_model_gateway",
            "proposal_review_only: bool = True",
            "download_enabled",
            "switch_enabled",
            "start_enabled",
            "stop_enabled",
            "runtime_adapter_execution_enabled",
            "provider_model_authority_enabled",
            "CONTROL_CENTER_LOCAL_MODELS_LIFECYCLE_DENIED",
        ],
        API_APP: [
            '@app.get("/control-center/local-models/status"',
            "control_center_local_models_status",
            "build_control_center_local_models_status",
        ],
        API_MANIFEST: [
            '"/control-center/local-models/status"',
            "LOCAL_READONLY_PATHS",
        ],
        ROUTE_TEST: [
            "test_control_center_local_models_status_is_read_only_and_blocks_lifecycle",
            "all(enabled is False",
            "model_download",
            "provider_model_authority",
        ],
        MANIFEST_TEST: [
            'routes_by_path["/control-center/local-models/status"]',
            "local_readonly",
            "validation_only",
            "protected_route",
        ],
    }
    for path, fragments in backend_requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def _validate_frontend_binding(root: Path, failures: list[str]) -> None:
    frontend_requirements = {
        FRONTEND_ENDPOINTS: [
            "controlCenterLocalModelsStatus",
            '"/control-center/local-models/status"',
        ],
        FRONTEND_CLIENT: [
            "controlCenterLocalModelsStatus",
            "localModelsStatus",
        ],
        FRONTEND_TYPES: [
            "ControlCenterLocalModelsStatus",
            'route_ref: "GET /control-center/local-models/status"',
            "lifecycle_actions",
            "blocked_authorities",
        ],
        FRONTEND_PANEL: [
            "ModelsOperatorPanel",
            "Backend-owned Local Models status",
            "localModelsStatus.lifecycle_actions",
            "provider/model authority stay blocked",
        ],
        FRONTEND_STATES: [
            "Backend-owned Local Models status",
            "download, start/stop, switch",
        ],
        FRONTEND_TEST: [
            "renders Settings and Local Models backend-owned status routes",
            "Backend-owned Local Models status",
            "model_download",
            "keeps read endpoints separate from the single preview POST endpoint",
        ],
    }
    for path, fragments in frontend_requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def _validate_operational_maturity_manifest(root: Path, failures: list[str]) -> None:
    manifest = _read_json(root, OPERATIONAL_MATURITY_MANIFEST, failures)
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        failures.append("operational maturity manifest must contain modules list")
        return

    local_models = next(
        (
            item
            for item in modules
            if isinstance(item, dict) and item.get("module_id") == "local_models"
        ),
        None,
    )
    if not isinstance(local_models, dict):
        failures.append("operational maturity manifest missing local_models module")
        return

    expected_values: dict[str, object] = {
        "current_rank": 2,
        "current_rank_label": "proposal_review",
        "real_local_mutation": False,
        "durable_receipt": False,
    }
    for key, expected in expected_values.items():
        if local_models.get(key) != expected:
            failures.append(
                f"local_models maturity {key} must be {expected!r}, "
                f"got {local_models.get(key)!r}"
            )

    for field, expected in {
        "backend_routes": ROUTE_REF,
        "cli_or_script_refs": "scripts/dev/uaa_local_model.py status",
        "evidence_refs": SCOPE_REF,
        "test_refs": (
            "tests/test_control_center_api_routes.py::"
            "test_control_center_local_models_status_is_read_only_and_blocks_lifecycle"
        ),
        "verifier_refs": VERIFIER_REF,
        "blocked_authorities": "provider_model_authority",
        "missing_contracts": "approval_bound_switch",
    }.items():
        values = local_models.get(field)
        if not isinstance(values, list) or expected not in values:
            failures.append(f"local_models maturity {field} missing {expected}")

    ui_binding = local_models.get("ui_status_binding")
    if not isinstance(ui_binding, dict):
        failures.append("local_models maturity missing ui_status_binding")
        return
    if ui_binding.get("status_route_ref") != ROUTE_REF:
        failures.append("local_models ui_status_binding status_route_ref drifted")
    if ui_binding.get("frontend_endpoint_ref") != FRONTEND_ENDPOINT_REF:
        failures.append("local_models ui_status_binding endpoint ref drifted")


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        README: [
            "UAA-P1-066 is implemented as read-only Local Model Control Center inventory/status support",
            ROUTE_REF,
            "No lifecycle, switching, activation, downloads, runtime adapters, or production-readiness claim",
        ],
        CURRENT_BOARD: [
            "UAA-P1-066 Local Model Manager Read-Only Control Center Inventory/Status",
            "Gate met",
            ROUTE_REF,
            "FCC-INBOX-001 Deeper Action Inbox / Approval Envelope UX",
            "No lifecycle, switching, activate/unload/start/stop",
        ],
        FCC_BOARD: [
            "UAA-P1-066 is implemented as a strictly read-only Local Model Manager support lane",
            ROUTE_REF,
        ],
        ROADMAP: [
            "`UAA-P1-066` Done: read-only Control Center inventory/status only",
            ROUTE_REF,
            "no lifecycle control, switching, start/stop/activate/unload behavior",
        ],
        PRODUCT_TRUTH: [
            "UAA-P1-066 implements strictly read-only Control Center inventory/status support only",
            ROUTE_REF,
            "UAA-P1-066 read-only Control Center inventory/status support",
        ],
        GAP_MAP: [
            "UAA-P1-066 renders read-only backend-owned inventory/status state",
            ROUTE_REF,
        ],
        DOCS_README: [
            "UAA-P1-066 is implemented as a strictly read-only Local Model Control Center inventory/status support lane",
            ROUTE_REF,
        ],
        DOCS_INDEX: [SCOPE_REF],
        CANONICAL_ROADMAP: [
            "UAA-P1-066 is implemented as a strictly read-only Local Model Control Center inventory/status support lane",
            ROUTE_REF,
        ],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def validate_uaa_p1_066_local_model_control_center_status(
    root: Path = ROOT,
) -> list[str]:
    failures: list[str] = []
    _validate_scope_doc(root, failures)
    _validate_backend_contract(root, failures)
    _validate_frontend_binding(root, failures)
    _validate_operational_maturity_manifest(root, failures)
    _validate_active_docs(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the UAA-P1-066 read-only Control Center local model "
            "inventory/status slice."
        )
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root to inspect.")
    args = parser.parse_args(argv)

    failures = validate_uaa_p1_066_local_model_control_center_status(
        Path(args.root).resolve()
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(f"{TASK_REF} read-only Control Center local model status verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
