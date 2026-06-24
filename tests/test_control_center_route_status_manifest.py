from pathlib import Path
import json
import re

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest


ROOT = Path(__file__).resolve().parents[1]
ROUTE_STATUS_MANIFEST_PATH = ROOT / "docs/control_center/route_status_manifest.json"
PRODUCT_LANGUAGE_RULES_PATH = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"


def _load_route_status_manifest() -> dict:
    return json.loads(ROUTE_STATUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def _visible_frontend_routes() -> set[str]:
    routes_text = (ROOT / "apps/control-center/src/routes.tsx").read_text(
        encoding="utf-8"
    )
    return set(re.findall(r'\{\s*path:\s*"([^"]+)",\s*label:', routes_text))


def _api_route_index() -> dict[tuple[str, str], object]:
    manifest = build_api_manifest(app)
    return {(route.method, route.path): route for route in manifest.routes}


def test_control_center_route_status_manifest_covers_visible_actions() -> None:
    manifest = _load_route_status_manifest()
    visible_actions = manifest["visible_actions"]
    action_routes = {
        action["frontend_route"]
        for action in visible_actions
        if action.get("frontend_route")
    }

    assert manifest["schema_version"] == "uaa-control-center-route-status.v1"
    assert manifest["status"] == "active UAA-P1-030 route status manifest"
    assert manifest["operator_readiness_taxonomy_ref"] == (
        "docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md"
    )
    assert manifest["openapi_path_count"] == 136
    assert _visible_frontend_routes().issubset(action_routes)

    required_fields = {
        "action_id",
        "label",
        "owner",
        "auth_posture",
        "side_effect_class",
        "risk_class",
        "release_status",
        "ui_surface",
        "frontend_route",
        "approval_requirement",
        "evidence_audit_output",
        "backend_routes",
        "missing_backend_routes",
    }
    action_ids = [action["action_id"] for action in visible_actions]
    assert len(action_ids) == len(set(action_ids))

    allowed_statuses = set(manifest["allowed_release_statuses"])
    assert manifest["release_status_taxonomy_map"] == {
        "status_available_not_completion": "status_only",
        "preview_available_not_execution": "preview_only",
        "partial_backend_not_product_ready": "partial",
        "founder_loop_v1_proofed": "shipped",
        "mock_only_not_product_ready": "mock_only",
        "local_ui_state_only_not_evidence": "local_ui_state_only",
        "blocked_missing_backend": "blocked",
    }
    for action in visible_actions:
        assert required_fields.issubset(action)
        assert action["release_status"] in allowed_statuses
        assert action["risk_class"] in {"low", "medium", "high"}
        assert action["approval_requirement"]
        assert action["evidence_audit_output"]

    for action_id in [
        "navigate-setup-assistant",
        "submit-action-preview",
        "select-local-detail-card",
        "toggle-review-only-file-decision",
    ]:
        assert action_id in action_ids

    evidence_action = next(
        action
        for action in visible_actions
        if action["action_id"] == "navigate-evidence"
    )
    assert {
        "method": "GET",
        "path": "/control-center/today/summary",
        "operation_id": "get_control_center_today_summary",
        "side_effect_class": "local_dev_workspace_only",
        "route_classification": "local_sensitive",
    } in evidence_action["backend_routes"]


def test_control_center_route_status_manifest_matches_openapi_and_api_manifest() -> (
    None
):
    route_status = _load_route_status_manifest()
    api_routes = _api_route_index()
    openapi_paths = app.openapi()["paths"]

    manifest_routes = []
    for section_name in ["surfaces", "visible_actions"]:
        route_key = (
            "current_backend_routes" if section_name == "surfaces" else "backend_routes"
        )
        for item in route_status[section_name]:
            manifest_routes.extend(item.get(route_key, []))

    assert manifest_routes
    for route in manifest_routes:
        key = (route["method"], route["path"])
        assert key in api_routes
        assert route["operation_id"] == api_routes[key].operation_id
        side_effect_class = getattr(
            api_routes[key].side_effect_class,
            "value",
            api_routes[key].side_effect_class,
        )
        assert route["side_effect_class"] == side_effect_class
        route_classification = getattr(
            api_routes[key].route_classification,
            "value",
            api_routes[key].route_classification,
        )
        assert route["route_classification"] == route_classification
        assert route["path"] in openapi_paths
        assert route["method"].lower() in openapi_paths[route["path"]]
        assert (
            route["operation_id"]
            == openapi_paths[route["path"]][route["method"].lower()]["operationId"]
        )


def test_control_center_route_status_manifest_keeps_unready_actions_unready() -> None:
    manifest = _load_route_status_manifest()
    surfaces = {surface["surface"]: surface for surface in manifest["surfaces"]}
    actions = {action["action_id"]: action for action in manifest["visible_actions"]}
    release_available = {
        "status_available_not_completion",
        "preview_available_not_execution",
    }

    for surface in [
        "Chat Local Operator",
        "Plans",
        "Models",
        "Approvals",
        "Files",
        "Runtime",
        "Evidence",
        "Settings",
    ]:
        assert surface in surfaces

    assert surfaces["Settings"]["release_status"] == "status_available_not_completion"
    assert (
        surfaces["Chat Local Operator"]["release_status"] == "founder_loop_v1_proofed"
    )
    assert surfaces["Evidence"]["release_status"] == "founder_loop_v1_proofed"
    assert surfaces["Runtime"]["release_status"] == "status_available_not_completion"

    for action in actions.values():
        if not action["backend_routes"]:
            assert action["release_status"] not in release_available
        if (
            action["missing_backend_routes"]
            and action["release_status"] in release_available
        ):
            assert action["action_id"] in {"navigate-settings", "navigate-inbox"}


def test_control_center_product_language_rules_are_current_and_enforced() -> None:
    doc_text = PRODUCT_LANGUAGE_RULES_PATH.read_text(encoding="utf-8").lower()
    doc_compact = " ".join(doc_text.split())
    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
    agents_compact = " ".join(agents_text.split())

    for fragment in [
        "status: active uaa-p1-031 product language rules",
        "cli is a first-class operator surface",
        "product behavior must not live only in react state",
        "no hidden authority",
        "no fake completion",
        "no frontend-only product behavior",
        "no raw json as primary ui for operator-critical flows",
        "no production/public distribution claims without evidence",
        "no model/provider output as authority",
        "no completed-state language for blocked/skipped/pending work",
        "today, inbox, plans, actions, memory, evidence, and settings",
    ]:
        assert fragment in doc_compact

    for fragment in [
        "cli is a first-class operator surface",
        "product behavior must not live only in react state",
        "python core/api contract",
        "command-line or repo-local script inspection path",
        "tests and redacted evidence",
    ]:
        assert fragment in agents_compact

    for rel_path in [
        "README.md",
        "docs/README.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
        "docs/control_center/OPERATOR_SHELL_GAP_MAP.md",
        "docs/control_center/ROUTE_STATUS_MANIFEST.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "docs/kanban/current_board.md",
    ]:
        assert (
            "docs/control_center/product_language_rules.md"
            in (ROOT / rel_path).read_text(encoding="utf-8").lower()
        )

    for frontend_path in [
        ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx",
        ROOT / "apps/control-center/src/components/LocalRuntimeStatusPanel.tsx",
        ROOT / "apps/control-center/src/components/ActionPreviewForm.tsx",
        ROOT / "apps/control-center/src/components/FileReviewSurfacePanel.tsx",
    ]:
        frontend_text = frontend_path.read_text(encoding="utf-8")
        for unsafe in [
            "Production ready",
            "Public release",
            "Public distribution",
            "Completed successfully",
            "Execution completed",
            "Model output is authority",
            "Provider output is authority",
            "Raw JSON",
        ]:
            assert unsafe not in frontend_text

    manifest = _load_route_status_manifest()
    actions = {action["action_id"]: action for action in manifest["visible_actions"]}
    completion_words = re.compile(r"\b(complete|completed|done|finished|succeeded)\b")
    for item in [*manifest["surfaces"], *manifest["visible_actions"]]:
        release_status = item["release_status"]
        if not any(
            marker in release_status
            for marker in ["blocked", "partial", "mock", "local_ui_state"]
        ):
            continue
        checked_text = " ".join(
            str(item.get(field, ""))
            for field in ["label", "approval_requirement", "evidence_audit_output"]
        ).lower()
        assert completion_words.search(checked_text) is None

    assert (
        actions["submit-action-preview"]["release_status"]
        == "preview_available_not_execution"
    )
    assert actions["submit-action-preview"]["backend_routes"][0]["operation_id"] == (
        "post_control_center_actions_preview"
    )
    assert actions["toggle-review-only-file-decision"]["backend_routes"] == []
    assert actions["toggle-review-only-file-decision"]["release_status"] == (
        "local_ui_state_only_not_evidence"
    )

    serialized = json.dumps(manifest).lower()
    for forbidden in [
        "production_ready",
        "public_release_ready",
        "broad_autonomy_enabled",
        "shell_authority_enabled",
        "connector_writes_enabled",
        "plugin_runtime_enabled",
    ]:
        assert forbidden not in serialized
