import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_control_center_frontend.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_control_center_frontend", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_control_center_frontend_verifier_passes_current_repo():
    verifier = load_verifier()

    assert verifier.verify(ROOT) == []


def test_control_center_frontend_verifier_tracks_m20_device_drift_strings():
    verifier = load_verifier()

    for endpoint in [
        "/device-capabilities/bluetooth",
        "/device-capabilities/nfc",
        "/device-capabilities/biometrics",
        "/device-capabilities/local-network",
        "/device-capabilities/screen-capture",
        "/mobile/permissions",
        "/mobile/background-service",
    ]:
        assert endpoint in verifier.FORBIDDEN_ENDPOINTS

    for fragment in [
        "android.permission",
        "manifest.permission",
        "avcapture",
        "cllocation",
        "locationmanager",
        "navigator.geolocation",
        "navigator.mediadevices",
        "notification.requestpermission",
        "pushmanager",
    ]:
        assert (
            fragment in verifier.BROWSER_API_FRAGMENTS
            or fragment in verifier.NATIVE_OR_PLUGIN_FRAGMENTS
        )

    for dependency in ['"@capacitor/core"', '"cordova"', '"ionic"', '"flutter"']:
        assert dependency in verifier.FORBIDDEN_FRONTEND_DEPENDENCIES


def test_control_center_frontend_verifier_blocks_tracked_build_and_log_artifacts(tmp_path, monkeypatch):
    verifier = load_verifier()

    monkeypatch.setattr(
        verifier.subprocess,
        "check_output",
        lambda *args, **kwargs: "\n".join(
            [
                "apps/control-center/build/index.html",
                "apps/control-center/logs/frontend-smoke.log",
            ]
        ),
    )

    failures = verifier._tracked_artifact_failures(tmp_path)

    assert any("apps/control-center/build/index.html" in failure for failure in failures)
    assert any("apps/control-center/logs/frontend-smoke.log" in failure for failure in failures)


def test_control_center_frontend_verifier_blocks_forbidden_frontend_strings(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n',
        encoding="utf-8",
    )
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false };\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        'export function ActionPreviewForm() { return <button>Execute</button>; }\n',
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("dangerous action control label" in failure for failure in failures)


def test_control_center_frontend_verifier_blocks_m15_mutation_routes_and_labels(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false };\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ApprovalQueuePanel.tsx").write_text(
        'export function ApprovalQueuePanel() { fetch("/control-center/approvals/execute"); '
        'return <button>Deny</button>; }\n',
        encoding="utf-8",
    )
    (app_root / "src/components/ReceiptViewerPanel.tsx").write_text(
        'export function ReceiptViewerPanel() { return "/receipts/delete"; }\n',
        encoding="utf-8",
    )
    (app_root / "src/components/EventViewerPanel.tsx").write_text(
        'export function EventViewerPanel() { return "/events/raw"; }\n',
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("/control-center/approvals/execute" in failure for failure in failures)
    assert any("/receipts/delete" in failure for failure in failures)
    assert any("/events/raw" in failure for failure in failures)
    assert any("dangerous action control label" in failure and "Deny" in failure for failure in failures)


def test_control_center_frontend_verifier_blocks_raw_m15_review_fields(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ApprovalQueuePanel.tsx").write_text(
        "export function ApprovalQueuePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ReceiptViewerPanel.tsx").write_text(
        "export function ReceiptViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventViewerPanel.tsx").write_text(
        "export function EventViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false, "
        "m15Review: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "approvalGrantAllowed: false, rawPromptBody: 'prompt text', rawFileBody: 'file text', "
        "rawMemoryContent: 'memory text', credentialRef: 'cred_live_value_123456' } };\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("raw M15 review field" in failure and "rawPromptBody" in failure for failure in failures)
    assert any("raw M15 review field" in failure and "rawFileBody" in failure for failure in failures)
    assert any("raw M15 review field" in failure and "rawMemoryContent" in failure for failure in failures)
    assert any("credential-like M15 review field" in failure and "credentialRef" in failure for failure in failures)


def test_control_center_frontend_verifier_requires_approval_authority_boundary_copy(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ApprovalQueuePanel.tsx").write_text(
        "export function ApprovalQueuePanel() { return <p>Approval review dashboard</p>; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ReceiptViewerPanel.tsx").write_text(
        "export function ReceiptViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventViewerPanel.tsx").write_text(
        "export function EventViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false, "
        "m15Review: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "approvalGrantAllowed: false } };\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("approval authority boundary copy" in failure for failure in failures)


def test_control_center_frontend_verifier_blocks_raw_m16_trace_fields(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ApprovalQueuePanel.tsx").write_text(
        "export function ApprovalQueuePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ReceiptViewerPanel.tsx").write_text(
        "export function ReceiptViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventViewerPanel.tsx").write_text(
        "export function EventViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventTimelineTracePanel.tsx").write_text(
        "export function EventTimelineTracePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false, "
        "m15Review: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "approvalGrantAllowed: false }, "
        "m16Trace: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "rawPromptBody: 'prompt text', rawFileContent: 'file text', rawMemoryContent: 'memory text', "
        "rawProviderPayload: 'provider payload', credentialRef: 'cred_live_value_123456' } };\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("raw M16 trace field" in failure and "rawPromptBody" in failure for failure in failures)
    assert any("raw M16 trace field" in failure and "rawFileContent" in failure for failure in failures)
    assert any("raw M16 trace field" in failure and "rawMemoryContent" in failure for failure in failures)
    assert any("raw M16 trace field" in failure and "rawProviderPayload" in failure for failure in failures)
    assert any("credential-like M16 trace field" in failure and "credentialRef" in failure for failure in failures)


def test_control_center_frontend_verifier_requires_m16_trace_boundary_copy(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ApprovalQueuePanel.tsx").write_text(
        "export function ApprovalQueuePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ReceiptViewerPanel.tsx").write_text(
        "export function ReceiptViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventViewerPanel.tsx").write_text(
        "export function EventViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventTimelineTracePanel.tsx").write_text(
        "export function EventTimelineTracePanel() { return <p>Event timeline</p>; }\n",
        encoding="utf-8",
    )
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false, "
        "m15Review: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "approvalGrantAllowed: false }, "
        "m16Trace: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only' } };\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("M16 trace boundary copy" in failure for failure in failures)


def test_control_center_frontend_verifier_blocks_raw_m17_knowledge_fields_and_paths(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ApprovalQueuePanel.tsx").write_text(
        "export function ApprovalQueuePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ReceiptViewerPanel.tsx").write_text(
        "export function ReceiptViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventViewerPanel.tsx").write_text(
        "export function EventViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventTimelineTracePanel.tsx").write_text(
        "export function EventTimelineTracePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EvidenceFileMemoryViewerPanel.tsx").write_text(
        "export function EvidenceFileMemoryViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false, "
        "m15Review: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "approvalGrantAllowed: false }, "
        "m16Trace: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only' }, "
        "m17Knowledge: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "rawEvidencePayload: 'evidence payload', rawFileContent: 'file text', rawMemoryContent: 'memory text', "
        "credentialRef: 'cred_live_value_123456', filePath: '/Users/example/project/private.md' } };\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("raw M17 knowledge field" in failure and "rawEvidencePayload" in failure for failure in failures)
    assert any("raw M17 knowledge field" in failure and "rawFileContent" in failure for failure in failures)
    assert any("raw M17 knowledge field" in failure and "rawMemoryContent" in failure for failure in failures)
    assert any("credential-like M17 knowledge field" in failure and "credentialRef" in failure for failure in failures)
    assert any("private path fragment in M17 knowledge fixture" in failure for failure in failures)


def test_control_center_frontend_verifier_requires_m17_knowledge_boundary_copy(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ApprovalQueuePanel.tsx").write_text(
        "export function ApprovalQueuePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ReceiptViewerPanel.tsx").write_text(
        "export function ReceiptViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventViewerPanel.tsx").write_text(
        "export function EventViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventTimelineTracePanel.tsx").write_text(
        "export function EventTimelineTracePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EvidenceFileMemoryViewerPanel.tsx").write_text(
        "export function EvidenceFileMemoryViewerPanel() { return <p>Knowledge refs</p>; }\n",
        encoding="utf-8",
    )
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false, "
        "m15Review: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "approvalGrantAllowed: false }, "
        "m16Trace: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only' }, "
        "m17Knowledge: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "NO_RAW_CONTENT: true, MEMORY_NOT_AUTHORITY: true } };\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("M17 knowledge boundary copy" in failure for failure in failures)


def test_control_center_frontend_verifier_requires_m17_hardening_markers(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ApprovalQueuePanel.tsx").write_text(
        "export function ApprovalQueuePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ReceiptViewerPanel.tsx").write_text(
        "export function ReceiptViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventViewerPanel.tsx").write_text(
        "export function EventViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventTimelineTracePanel.tsx").write_text(
        "export function EventTimelineTracePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EvidenceFileMemoryViewerPanel.tsx").write_text(
        "export function EvidenceFileMemoryViewerPanel() { "
        "return <p>Evidence views are read-only File ref views are read-only "
        "Memory is recall, not authority Canonical files and governed source systems outrank memory "
        "No filesystem browsing is available</p>; }\n",
        encoding="utf-8",
    )
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false, "
        "m15Review: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "approvalGrantAllowed: false }, "
        "m16Trace: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "externalExportAllowed: false, exportStatus: 'NO_EXTERNAL_EXPORT', noRawContent: true }, "
        "m17Knowledge: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "NO_RAW_CONTENT: true, MEMORY_NOT_AUTHORITY: true } };\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("M17 hardening mock marker missing" in failure for failure in failures)
    assert any("M17 hardening selected-state marker missing" in failure for failure in failures)


def test_control_center_frontend_verifier_blocks_m18_runtime_execution_and_raw_smoke_fields(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n'
        'fetch("/runtime/smoke-reports/execute", { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview", '
        'runtimeSmokeReportValidate: "/runtime/smoke-reports/validate" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n"
        "export function isRuntimeValidationEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ApprovalQueuePanel.tsx").write_text(
        "export function ApprovalQueuePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ReceiptViewerPanel.tsx").write_text(
        "export function ReceiptViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventViewerPanel.tsx").write_text(
        "export function EventViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EventTimelineTracePanel.tsx").write_text(
        "export function EventTimelineTracePanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/EvidenceFileMemoryViewerPanel.tsx").write_text(
        "export function EvidenceFileMemoryViewerPanel() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src/components/LocalRuntimeStatusPanel.tsx").write_text(
        'export function LocalRuntimeStatusPanel() { return <button>Run smoke</button>; }\n',
        encoding="utf-8",
    )
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false, "
        "m15Review: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "approvalGrantAllowed: false }, "
        "m16Trace: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only' }, "
        "m17Knowledge: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "NO_RAW_CONTENT: true, MEMORY_NOT_AUTHORITY: true }, "
        "m18Runtime: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "rawPromptBody: 'prompt text', rawResponseBody: 'response text', apiKey: 'live_secret_value_123456' } };\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("/runtime/smoke-reports/execute" in failure for failure in failures)
    assert any("dangerous action control label" in failure and "Run smoke" in failure for failure in failures)
    assert any("raw M18 runtime field" in failure and "rawPromptBody" in failure for failure in failures)
    assert any("raw M18 runtime field" in failure and "rawResponseBody" in failure for failure in failures)
    assert any("credential-like M18 runtime field" in failure and "apiKey" in failure for failure in failures)


def test_control_center_frontend_verifier_blocks_sensitive_browser_and_sdk_markers(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text(
        '{"dependencies":{"react":"1.0.0","analytics":"1.0.0"}}',
        encoding="utf-8",
    )
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n',
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false, "
        "api_key: 'live-secret-value' };\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { window.localStorage.setItem('x', 'y'); return null; }\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("forbidden frontend dependency marker" in failure and "analytics" in failure for failure in failures)
    assert any("forbidden browser API" in failure and "localstorage" in failure for failure in failures)
    assert any("secret-like fixture value" in failure for failure in failures)


def test_control_center_frontend_verifier_requires_local_backend_policy(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'fetch("https://api.example.com/control-center/manifest");\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false };\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("missing frontend file: apps/control-center/src/api/baseUrl.ts" in failure for failure in failures)
    assert any("forbidden absolute external API URL" in failure for failure in failures)
    assert any("local backend API base policy is missing" in failure for failure in failures)


def test_control_center_frontend_verifier_blocks_external_proxy_targets_and_url_credentials(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "https://api.example.com" }, '
        '"/runtime": { target: "http://user:password@127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false };\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("Vite dev proxy must target only http://127.0.0.1:8000" in failure for failure in failures)
    assert any("forbidden URL credentials" in failure for failure in failures)


def test_control_center_frontend_verifier_blocks_broad_runtime_proxy(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview", '
        'runtimeSmokeReportValidate: "/runtime/smoke-reports/validate" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n"
        "export function isRuntimeValidationEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false, "
        "m15Review: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
        "approvalGrantAllowed: false, externalExportAllowed: false }, "
        "m16Trace: { noExternalExport: true, noRawContent: true }, "
        "m17Knowledge: { memoryNotAuthority: true, noRawContent: true }, "
        "m18Runtime: { validationOnly: true, noRuntimeExecution: true, "
        "modelOutputAuthoritative: false } };\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("Vite dev proxy must not proxy broad /runtime frontend route space" in failure for failure in failures)


def test_control_center_frontend_verifier_blocks_secret_like_env_examples(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / ".env.example").write_text(
        "VITE_UAA_API_BASE_URL=http://127.0.0.1:8000?api_key=supersecretvalue123\n",
        encoding="utf-8",
    )
    (app_root / "vite.config.ts").write_text(
        'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
        '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n',
        encoding="utf-8",
    )
    (app_root / "src/api/baseUrl.ts").write_text(
        "export function resolveApiBaseUrl() { return true; }\n"
        "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
        "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n",
        encoding="utf-8",
    )
    (app_root / "src/api/client.ts").write_text(
        'import { resolveApiBaseUrl } from "./baseUrl";\n'
        'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n',
        encoding="utf-8",
    )
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
        "export function isAllowedReadEndpoint() { return true; }\n"
        "export function isPreviewEndpoint() { return true; }\n",
        encoding="utf-8",
    )
    (app_root / "src/api/redaction.ts").write_text("export const redact = true;\n", encoding="utf-8")
    (app_root / "src/App.test.tsx").write_text("export const testFile = true;\n", encoding="utf-8")
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false };\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        "export function ActionPreviewForm() { return null; }\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("secret-like API base env example" in failure for failure in failures)
