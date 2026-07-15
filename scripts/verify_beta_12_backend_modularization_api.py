#!/usr/bin/env python3
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.api.rate_limits import route_rate_limit_group  # noqa: E402
from scripts.verification.api_routes import (  # noqa: E402
    EXPECTED_OPENAPI_PATH_COUNT,
    EXPECTED_ROUTE_COUNT,
)
from scripts.verify_control_center_release_surface import (  # noqa: E402
    verify as verify_release_surface,
)


LANE_DOC = ROOT / "docs/api/BETA_12_BACKEND_MODULARIZATION_API.md"
API_README = ROOT / "docs/api/README.md"
EXTRACTION_PLAN = ROOT / "docs/api/UAA_P1_052_SERVICE_MODULE_EXTRACTION_PLAN.md"
ROUTE_GROUPING_MAP = ROOT / "docs/api/UAA_P1_021_FASTAPI_ROUTE_GROUPING_MAP.md"
RELEASE_SURFACE = ROOT / "docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
APP_MODULE = ROOT / "src/ultimate_ai_agent/api/app.py"
CONTROL_CENTER_MODULE = ROOT / "src/ultimate_ai_agent/api/control_center.py"

EXTRACTED_CONTROL_CENTER_ROUTES = {
    ("GET", "/control-center/manifest"),
    ("GET", "/control-center/dashboard"),
    ("GET", "/control-center/status"),
    ("GET", "/control-center/routes"),
    ("GET", "/control-center/approvals/summary"),
    ("GET", "/control-center/approvals/queue"),
    ("GET", "/control-center/runs/observability"),
    ("GET", "/control-center/runtime-readiness/summary"),
    ("GET", "/control-center/settings/status"),
    ("GET", "/control-center/local-models/status"),
    ("GET", "/control-center/foundation-gate/summary"),
    ("GET", "/control-center/setup-assistant/summary"),
    ("GET", "/control-center/coding/session"),
    ("GET", "/control-center/coding/context"),
    ("GET", "/control-center/coding/patch-apply-readiness"),
    ("GET", "/control-center/coding/patch-proposal"),
    ("GET", "/control-center/coding/test-command-readiness"),
    ("GET", "/control-center/coding/git-review"),
    ("GET", "/control-center/coding/live-preview"),
    ("GET", "/control-center/coding/multi-agent-review"),
    ("GET", "/control-center/work-board"),
    ("POST", "/control-center/actions/preview"),
}

EXPECTED_SIDE_EFFECT_MIX = {
    "none": 12,
    "validation_only": 80,
    "local_dev_workspace_only": 183,
    "governed_network_read_only": 6,
    "authenticated_connector_mutation": 4,
    "destructive_local_sensitive": 1,
    "local_sensitive": 1,
    "destructive_external": 1,
    "system_browser_exact_launch": 1,
}


def _app_route_index() -> dict[tuple[str, str], APIRoute]:
    return {
        (method, route.path): route
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in sorted(route.methods - {"HEAD", "OPTIONS"})
    }


def _append_route_failures(failures: list[str]) -> None:
    manifest = build_api_manifest(app)
    if manifest.route_count != EXPECTED_ROUTE_COUNT:
        failures.append(
            f"route count drifted: {manifest.route_count}, expected {EXPECTED_ROUTE_COUNT}"
        )
    side_effect_mix = Counter(route.side_effect_class for route in manifest.routes)
    if dict(side_effect_mix) != EXPECTED_SIDE_EFFECT_MIX:
        failures.append(f"side-effect mix drifted: {dict(side_effect_mix)}")
    manifest_routes = {(route.method, route.path): route for route in manifest.routes}
    app_routes = _app_route_index()
    for route_key in sorted(EXTRACTED_CONTROL_CENTER_ROUTES):
        manifest_route = manifest_routes.get(route_key)
        app_route = app_routes.get(route_key)
        if manifest_route is None:
            failures.append(f"missing manifest route: {route_key[0]} {route_key[1]}")
            continue
        if app_route is None:
            failures.append(f"missing app route: {route_key[0]} {route_key[1]}")
            continue
        if manifest_route.tags != ["control-center"]:
            failures.append(f"{route_key[0]} {route_key[1]} tag drifted")
        if app_route.endpoint.__module__ != "ultimate_ai_agent.api.control_center":
            failures.append(
                f"{route_key[0]} {route_key[1]} still owned by {app_route.endpoint.__module__}"
            )


def _append_rate_limit_failures(failures: list[str]) -> None:
    checks = {
        (
            "POST",
            "/control-center/memory/context-packs/context-pack-ref:proposal:safe/action-proposal",
        ): "memory_context_pack_action_proposal",
        (
            "GET",
            "/task-decomposition/runs/task-decomposition-run:demo/lifecycle",
        ): "task_decomposition",
    }
    for (method, path), expected_group in checks.items():
        actual = route_rate_limit_group(method, path)
        if actual != expected_group:
            failures.append(
                f"{method} {path} rate-limit group drifted: {actual}, expected {expected_group}"
            )


def _append_static_failures(failures: list[str]) -> None:
    required_fragments = {
        LANE_DOC: [
            "Full-strength version",
            "Repo-safe beta-12 version",
            "Blocked / Needs Authority",
            "Exact Promotion Path",
            "ultimate_ai_agent.api.control_center",
            "169-route",
            "adds no provider/model calls",
        ],
        API_README: [
            "BETA_12_BACKEND_MODULARIZATION_API.md",
            "Beta 12 extracts",
            "adds no routes and no runtime authority",
        ],
        EXTRACTION_PLAN: [
            f"Current OpenAPI path count: {EXPECTED_OPENAPI_PATH_COUNT}",
            "configure_openapi_contract(app)",
            "Beta 12 starts this extraction",
            "`/control-center/settings/status`",
        ],
        ROUTE_GROUPING_MAP: [
            "`local_dev_workspace_only`:81",
            "| GET | `/control-center/proof/index` | `get_control_center_proof_index` | `local_dev_workspace_only`",
            "| GET | `/control-center/start-here/summary` | `get_control_center_start_here_summary` | `local_dev_workspace_only`",
            "| GET | `/control-center/trust-authority/matrix` | `get_control_center_trust_authority_matrix` | `local_dev_workspace_only`",
            "| GET | `/control-center/coding/context` | `get_control_center_coding_context` | `local_dev_workspace_only`",
            "| GET | `/control-center/coding/patch-apply-readiness` | `get_control_center_coding_patch_apply_readiness` | `local_dev_workspace_only`",
            "| GET | `/control-center/coding/patch-proposal` | `get_control_center_coding_patch_proposal` | `local_dev_workspace_only`",
            "| GET | `/control-center/coding/session` | `get_control_center_coding_session` | `local_dev_workspace_only`",
            "| GET | `/control-center/coding/test-command-readiness` | `get_control_center_coding_test_command_readiness` | `local_dev_workspace_only`",
            "| GET | `/control-center/coding/git-review` | `get_control_center_coding_git_review` | `local_dev_workspace_only`",
            "| GET | `/control-center/coding/live-preview` | `get_control_center_coding_live_preview` | `local_dev_workspace_only`",
            "| GET | `/control-center/coding/multi-agent-review` | `get_control_center_coding_multi_agent_review` | `local_dev_workspace_only`",
            "| GET | `/control-center/work-board` | `get_control_center_work_board` | `local_dev_workspace_only`",
        ],
        RELEASE_SURFACE: [
            "Beta 12 Backend Modularization/API Contract",
            "ultimate_ai_agent.api.control_center",
            "scripts/verify_beta_12_backend_modularization_api.py",
        ],
        TRUTH_PACKET: [
            "Beta 12 Backend Modularization/API Contract",
            "src/ultimate_ai_agent/api/control_center.py",
            "scripts/verify_beta_12_backend_modularization_api.py",
        ],
        CURRENT_BOARD: [
            "Beta 12 Backend Modularization/API Contract hardening",
            "ultimate_ai_agent.api.control_center",
            "scripts/verify_beta_12_backend_modularization_api.py",
        ],
        CONTROL_CENTER_MODULE: [
            "register_control_center_routes",
            "task_decomposition_service_getter",
            "get_control_center_dashboard",
        ],
        APP_MODULE: [
            "register_control_center_routes",
            "task_decomposition_service_getter=lambda: _task_decomposition_service",
        ],
    }
    for path, fragments in required_fragments.items():
        if not path.exists():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        compact = " ".join(text.split())
        for fragment in fragments:
            if fragment not in text and fragment not in compact:
                failures.append(
                    f"{path.relative_to(ROOT)} missing beta-12 fragment: {fragment}"
                )
    app_text = APP_MODULE.read_text(encoding="utf-8")
    for route_path in (
        "/control-center/manifest",
        "/control-center/dashboard",
        "/control-center/actions/preview",
    ):
        if (
            f'@app.get("{route_path}"' in app_text
            or f'@app.post("{route_path}"' in app_text
        ):
            failures.append(f"{route_path} still declared directly in api.app")


def validate_beta_12_backend_modularization_api() -> list[str]:
    failures: list[str] = []
    _append_route_failures(failures)
    _append_rate_limit_failures(failures)
    _append_static_failures(failures)
    for failure in verify_release_surface():
        failures.append(f"release surface verifier: {failure}")
    return failures


def main() -> int:
    failures = validate_beta_12_backend_modularization_api()
    if failures:
        for failure in failures:
            print(f"[beta-12] {failure}", file=sys.stderr)
        return 1
    print("Beta 12 backend modularization/API verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
