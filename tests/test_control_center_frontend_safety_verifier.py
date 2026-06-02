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
