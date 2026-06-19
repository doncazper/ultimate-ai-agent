from fastapi.testclient import TestClient
from pathlib import Path
import json
import re

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]
ROUTE_STATUS_MANIFEST_PATH = ROOT / "docs/control_center/route_status_manifest.json"
PRODUCT_LANGUAGE_RULES_PATH = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"


def _load_route_status_manifest() -> dict:
    return json.loads(ROUTE_STATUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def _visible_frontend_routes() -> set[str]:
    routes_text = (ROOT / "apps/control-center/src/routes.tsx").read_text(encoding="utf-8")
    return set(re.findall(r'\{\s*path:\s*"([^"]+)",\s*label:', routes_text))


def _api_route_index():
    manifest = build_api_manifest(app)
    return {(route.method, route.path): route for route in manifest.routes}


def test_control_center_api_routes_are_read_only_preview_only():
    for path in [
        "/control-center/manifest",
        "/control-center/dashboard",
        "/control-center/status",
        "/control-center/routes",
        "/control-center/approvals/summary",
        "/control-center/runtime-readiness/summary",
        "/control-center/foundation-gate/summary",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["success"] is True

    manifest = client.get("/control-center/manifest").json()["data"]
    assert manifest["metadata"]["frontend_implemented"] is False
    assert "runtime_execution" in manifest["blocked_capabilities"]


def test_control_center_action_preview_api_denies_execute_and_does_not_echo_secret():
    secret = "api_key='abcdefghijklmnop'"
    response = client.post(
        "/control-center/actions/preview",
        json={
            "request_id": "cc_api_preview_secret",
            "actor_context": {"actor_type": "user", "actor_id": "local_operator"},
            "action_kind": "preview_action",
            "target_ref": "runtime/execute/model",
            "purpose": "try to execute",
            "risk_level": "medium",
            "data_classification": "system_internal",
            "consent_refs": [],
            "metadata": {"claim": secret},
        },
    )

    body = response.text
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "RUNTIME_EXECUTION_BLOCKED" in response.json()["data"]["reason_codes"]
    assert "SECRET_LIKE_VALUE_REJECTED" in response.json()["data"]["reason_codes"]
    assert secret not in body


def test_control_center_openapi_routes_and_operation_ids_are_safe():
    schema = app.openapi()
    paths = schema["paths"]
    required = {
        "/control-center/manifest",
        "/control-center/dashboard",
        "/control-center/status",
        "/control-center/routes",
        "/control-center/approvals/summary",
        "/control-center/runtime-readiness/summary",
        "/control-center/foundation-gate/summary",
        "/control-center/actions/preview",
    }
    assert required.issubset(paths)
    for forbidden in [
        "/control-center/actions/execute",
        "/control-center/plugins/enable",
        "/control-center/runtime/execute",
        "/control-center/remote-workers/dispatch",
        "/control-center/mobile/sensors",
        "/control-center/frontend",
    ]:
        assert forbidden not in paths

    operation_ids = [
        spec["operationId"]
        for methods in paths.values()
        for spec in methods.values()
        if isinstance(spec, dict) and "operationId" in spec
    ]
    assert "/files/review/approvals/capture" in paths
    assert "/v1/models" in paths
    assert "/v1/chat/completions" in paths
    assert "/task-decomposition/run" in paths
    assert "/files/tree/preview" in paths
    assert "/extensions/catalog" in paths
    assert len(paths) == 95
    assert len(operation_ids) == len(set(operation_ids)) == 95


def test_control_center_operator_shell_gap_map_is_current_and_safe():
    doc_path = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
    text = doc_path.read_text(encoding="utf-8")
    compact = " ".join(text.lower().split())

    assert "status: active uaa-p0-007 operator-shell gap map" in compact
    assert "api boundary: current fastapi manifest has 95 openapi paths" in compact
    assert (
        "| surface | current frontend component/page | current backend route(s) | "
        "missing backend route(s) | authority boundary | side-effect class | "
        "approval requirement | evidence/audit output | readiness status | "
        "production-readiness blocker |"
    ) in compact

    for surface in [
        "chat shell",
        "plans",
        "models",
        "approvals",
        "files",
        "runtime",
        "evidence",
        "settings",
    ]:
        assert f"| {surface} |" in compact

    for route in [
        "`get /v1/models`",
        "`post /v1/chat/completions`",
        "`post /task-decomposition/classify`",
        "`post /task-decomposition/decompose`",
        "`post /files/tree/preview`",
        "`post /files/read/preview`",
        "`get /control-center/routes`",
    ]:
        assert route in compact

    for rule in [
        "no hidden authority",
        "no fake completion",
        "no raw json as primary ui for operator-critical flows",
    ]:
        assert rule in compact

    for forbidden in [
        "production ready for external users",
        "public distribution is available",
        "control center executes actions",
        "plugin runtime import is enabled",
    ]:
        assert forbidden not in compact


def test_control_center_route_status_manifest_covers_visible_actions():
    manifest = _load_route_status_manifest()
    visible_actions = manifest["visible_actions"]
    action_routes = {
        action["frontend_route"] for action in visible_actions if action.get("frontend_route")
    }

    assert manifest["schema_version"] == "uaa-control-center-route-status.v1"
    assert manifest["status"] == "active UAA-P1-030 route status manifest"
    assert manifest["openapi_path_count"] == 93
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
    for action in visible_actions:
        assert required_fields.issubset(action)
        assert action["release_status"] in allowed_statuses
        assert action["risk_class"] in {"low", "medium", "high"}
        assert action["approval_requirement"]
        assert action["evidence_audit_output"]

    for action_id in [
        "submit-action-preview",
        "select-local-detail-card",
        "toggle-review-only-file-decision",
    ]:
        assert action_id in action_ids


def test_control_center_route_status_manifest_matches_openapi_and_api_manifest():
    route_status = _load_route_status_manifest()
    api_routes = _api_route_index()
    openapi_paths = app.openapi()["paths"]

    manifest_routes = []
    for section_name in ["surfaces", "visible_actions"]:
        route_key = "current_backend_routes" if section_name == "surfaces" else "backend_routes"
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
        assert route["path"] in openapi_paths
        assert route["method"].lower() in openapi_paths[route["path"]]
        assert route["operation_id"] == openapi_paths[route["path"]][route["method"].lower()]["operationId"]


def test_control_center_route_status_manifest_keeps_unready_actions_unready():
    manifest = _load_route_status_manifest()
    surfaces = {surface["surface"]: surface for surface in manifest["surfaces"]}
    actions = {action["action_id"]: action for action in manifest["visible_actions"]}
    release_available = {"status_available_not_completion", "preview_available_not_execution"}

    for surface in [
        "Chat Shell",
        "Plans",
        "Models",
        "Approvals",
        "Files",
        "Runtime",
        "Evidence",
        "Settings",
    ]:
        assert surface in surfaces

    assert surfaces["Settings"]["release_status"] == "blocked_missing_backend"
    assert surfaces["Chat Shell"]["release_status"] == "blocked_missing_backend"
    assert surfaces["Runtime"]["release_status"] == "status_available_not_completion"

    for action in actions.values():
        if not action["backend_routes"] or action["missing_backend_routes"]:
            assert action["release_status"] not in release_available


def test_control_center_product_language_rules_are_current_and_enforced():
    doc_text = PRODUCT_LANGUAGE_RULES_PATH.read_text(encoding="utf-8").lower()
    doc_compact = " ".join(doc_text.split())

    for fragment in [
        "status: active uaa-p1-031 product language rules",
        "no hidden authority",
        "no fake completion",
        "no raw json as primary ui for operator-critical flows",
        "no production/public distribution claims without evidence",
        "no model/provider output as authority",
        "no completed-state language for blocked/skipped/pending work",
    ]:
        assert fragment in doc_compact

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
        assert "docs/control_center/product_language_rules.md" in (
            ROOT / rel_path
        ).read_text(encoding="utf-8").lower()

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
        if not any(marker in release_status for marker in ["blocked", "partial", "mock", "local_ui_state"]):
            continue
        checked_text = " ".join(
            str(item.get(field, ""))
            for field in ["label", "approval_requirement", "evidence_audit_output"]
        ).lower()
        assert completion_words.search(checked_text) is None

    assert actions["submit-action-preview"]["release_status"] == "preview_available_not_execution"
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
