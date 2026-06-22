import json
from collections import Counter
from pathlib import Path

from fastapi.routing import APIRoute

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest, route_side_effect_class


ROOT = Path(__file__).resolve().parents[1]
ROUTE_GROUPING_MAP = ROOT / "docs/api/UAA_P1_021_FASTAPI_ROUTE_GROUPING_MAP.md"
ROUTE_STATUS_MANIFEST = ROOT / "docs/control_center/route_status_manifest.json"
EXPECTED_ROUTE_COUNT = 126

EVIDENCE_BEHAVIOR_BY_ROUTE_GROUP = {
    "adapter-boundary": "validation decision refs",
    "api-boundary": "manifest metadata refs",
    "approval-authority": "approval validation refs",
    "consent": "consent validation refs",
    "context-budget": "context budget validation refs",
    "contracts": "contract validation refs",
    "control-center": "route-status and bounded summary refs",
    "cost-governor": "cost estimate and budget validation refs",
    "extension-catalog": "read-only catalog metadata refs",
    "files": "safe file refs and approval/rollback refs",
    "foundation-gate": "Foundation Gate report refs",
    "kernel": "local run refs and blocked mutation refs",
    "ledger": "receipt, event, and run-state validation refs",
    "mattermost": "bridge status, role, receipt, and audit refs",
    "memory": "memory provenance and review refs",
    "model-router": "route preview decision refs",
    "model-runtime": "runtime validation refs",
    "observability": "redacted session and client-error refs",
    "openwebui-local-test": "local loopback safe response refs",
    "provider-registry": "provider validation refs",
    "remote-workers": "dry-run remote worker planning refs",
    "runtime-boundary": "runtime boundary validation refs",
    "runtime-readiness": "runtime readiness and capability refs",
    "secret-broker": "secret reference validation refs",
    "system": "health and version status refs",
    "task-decomposition": "plan, approval, run, audit, and receipt refs",
    "tool-broker": "tool validation and risk decision refs",
    "truth": "truth validation and evidence refs",
    "web-evidence": "governed web evidence receipt refs",
    "world-state": "world-state validation refs",
}


def test_route_module_ownership_map_covers_current_api_manifest() -> None:
    manifest = build_api_manifest(app)
    group_summary = _parse_route_group_summary()
    documented_routes = _parse_documented_routes()

    assert manifest.route_count == EXPECTED_ROUTE_COUNT
    assert len(app.openapi()["paths"]) == EXPECTED_ROUTE_COUNT
    assert len(documented_routes) == EXPECTED_ROUTE_COUNT

    route_keys = {(route.method, route.path) for route in manifest.routes}
    assert route_keys == set(documented_routes)
    assert set(manifest.route_groups) == set(group_summary)
    assert set(EVIDENCE_BEHAVIOR_BY_ROUTE_GROUP) == set(group_summary)

    operation_ids = [route.operation_id for route in manifest.routes]
    assert len(operation_ids) == len(set(operation_ids)) == EXPECTED_ROUTE_COUNT

    actual_counts_by_group = Counter()
    actual_side_effects_by_group: dict[str, Counter[str]] = {}
    for route in manifest.routes:
        assert route.tags, f"{route.method} {route.path} is missing a route group tag"
        route_group = route.tags[0]
        summary = group_summary[route_group]
        documented = documented_routes[(route.method, route.path)]

        assert summary["owner"]
        assert summary["target_service_module"].endswith("_service")
        assert summary["risk_class"] in {"low", "medium", "high"}
        assert summary["release_status"] in {
            "partial_backend_not_product_ready",
            "preview_available_not_execution",
            "status_available_not_completion",
        }
        assert summary["auth_posture"]
        assert summary["operation_id_posture"] == "stable/generated from path; unique"
        assert EVIDENCE_BEHAVIOR_BY_ROUTE_GROUP[route_group]

        assert route.operation_id == documented["operation_id"]
        assert route.side_effect_class == documented["side_effect_class"]
        assert route.side_effect_class == route_side_effect_class(route.path).value
        assert documented["auth_posture"] == "future"
        assert documented["blocked_from_production"] == "yes"
        assert route.requires_auth_future is True
        assert route.blocked_from_production is True

        actual_counts_by_group[route_group] += 1
        actual_side_effects_by_group.setdefault(route_group, Counter())[route.side_effect_class] += 1

    for route_group, summary in group_summary.items():
        assert actual_counts_by_group[route_group] == summary["count"]
        assert actual_side_effects_by_group[route_group] == summary["side_effect_class_mix"]


def test_uaa_p1_058_system_service_extraction_ownership_is_frozen() -> None:
    manifest_routes = {(route.method, route.path): route for route in build_api_manifest(app).routes}
    app_routes = {
        (method, route.path): route
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in sorted(route.methods - {"HEAD", "OPTIONS"})
    }

    health = manifest_routes[("GET", "/health")]
    version = manifest_routes[("GET", "/version")]

    assert health.operation_id == "get_health"
    assert version.operation_id == "get_version"
    assert health.tags == ["system"]
    assert version.tags == ["system"]
    assert health.side_effect_class == "none"
    assert version.side_effect_class == "none"
    assert health.requires_auth_future is True
    assert version.requires_auth_future is True
    assert health.blocked_from_production is True
    assert version.blocked_from_production is True

    assert app_routes[("GET", "/health")].endpoint.__module__ == (
        "ultimate_ai_agent.api.routes.system_service"
    )
    assert app_routes[("GET", "/version")].endpoint.__module__ == (
        "ultimate_ai_agent.api.routes.system_service"
    )
    assert app_routes[("GET", "/api/manifest")].endpoint.__module__ == (
        "ultimate_ai_agent.api.app"
    )


def test_route_status_manifest_remains_visible_action_subset_with_evidence() -> None:
    api_routes = {(route.method, route.path): route for route in build_api_manifest(app).routes}
    route_status = json.loads(ROUTE_STATUS_MANIFEST.read_text(encoding="utf-8"))

    assert route_status["openapi_path_count"] == EXPECTED_ROUTE_COUNT

    status_routes: set[tuple[str, str]] = set()
    for section_name, route_field in (
        ("surfaces", "current_backend_routes"),
        ("visible_actions", "backend_routes"),
    ):
        for item in route_status[section_name]:
            assert item["evidence_audit_output"]
            for route in item[route_field]:
                key = (route["method"], route["path"])
                assert key in api_routes
                assert route["operation_id"] == api_routes[key].operation_id
                assert route["side_effect_class"] == api_routes[key].side_effect_class
                status_routes.add(key)

    assert status_routes
    assert status_routes < set(api_routes)


def _parse_route_group_summary() -> dict[str, dict[str, object]]:
    rows = _rows_between("## Route Group Summary", "## All Current Routes")
    summary: dict[str, dict[str, object]] = {}
    for row in rows:
        if len(row) != 9 or row[0] == "Route group" or set(row[0]) == {"-"}:
            continue
        route_group = _clean_cell(row[0])
        summary[route_group] = {
            "count": int(_clean_cell(row[1])),
            "owner": _clean_cell(row[2]),
            "target_service_module": _clean_cell(row[3]),
            "auth_posture": _clean_cell(row[4]),
            "side_effect_class_mix": _parse_side_effect_mix(_clean_cell(row[5])),
            "risk_class": _clean_cell(row[6]),
            "operation_id_posture": _clean_cell(row[7]),
            "release_status": _clean_cell(row[8]),
        }
    return summary


def _parse_documented_routes() -> dict[tuple[str, str], dict[str, str]]:
    rows = _rows_between("## All Current Routes", "")
    routes: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        if len(row) != 7:
            continue
        method = _clean_cell(row[0])
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            continue
        path = _clean_cell(row[1])
        routes[(method, path)] = {
            "operation_id": _clean_cell(row[2]),
            "side_effect_class": _clean_cell(row[3]),
            "validation_only": _clean_cell(row[4]),
            "auth_posture": _clean_cell(row[5]),
            "blocked_from_production": _clean_cell(row[6]),
        }
    return routes


def _rows_between(start_heading: str, end_heading: str) -> list[list[str]]:
    content = ROUTE_GROUPING_MAP.read_text(encoding="utf-8")
    start = content.index(start_heading)
    section = content[start + len(start_heading) :]
    if end_heading:
        end = section.find(end_heading)
        if end != -1:
            section = section[:end]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def _clean_cell(value: str) -> str:
    return value.strip().strip("`")


def _parse_side_effect_mix(value: str) -> Counter[str]:
    mix: Counter[str] = Counter()
    for part in value.split(","):
        side_effect, count = part.strip().split(":")
        mix[_clean_cell(side_effect)] = int(_clean_cell(count))
    return mix
