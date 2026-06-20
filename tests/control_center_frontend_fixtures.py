from __future__ import annotations

from pathlib import Path


DEFAULT_PACKAGE_JSON = '{"dependencies":{"react":"1.0.0"}}'
DEFAULT_PACKAGE_LOCK = "{}"
DEFAULT_VITE_CONFIG = (
    'export default { server: { proxy: { "/control-center": { target: "http://127.0.0.1:8000" }, '
    '"/runtime": { target: "http://127.0.0.1:8000" } } } };\n'
)
DEFAULT_BASE_URL_TS = (
    "export function resolveApiBaseUrl() { return true; }\n"
    "const policy = ['localhost', '127.0.0.1', '::1', 'EXTERNAL_API_BASE_URL_BLOCKED', "
    "'SECRET_LIKE_API_BASE_URL_REJECTED', 'containsSecretLike'];\n"
)
DEFAULT_CLIENT_TS = (
    'import { resolveApiBaseUrl } from "./baseUrl";\n'
    'fetch(API_ENDPOINTS.actionPreview, { method: "POST" });\n'
)
DEFAULT_ENDPOINTS_TS = (
    'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n'
    "export function isAllowedReadEndpoint() { return true; }\n"
    "export function isPreviewEndpoint() { return true; }\n"
)
DEFAULT_REDACTION_TS = "export const redact = true;\n"
DEFAULT_APP_TEST_TSX = "export const testFile = true;\n"

SAFE_M15_REVIEW_SECTION = (
    "m15Review: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
    "approvalGrantAllowed: false }"
)
SAFE_M16_TRACE_SECTION = "m16Trace: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only' }"
SAFE_M17_KNOWLEDGE_SECTION = (
    "m17Knowledge: { nonAuthoritative: true, redactionStatus: 'redacted_summary_only', "
    "NO_RAW_CONTENT: true, MEMORY_NOT_AUTHORITY: true }"
)
SAFE_M18_RUNTIME_SECTION = (
    "m18Runtime: { validationOnly: true, noRuntimeExecution: true, "
    "modelOutputAuthoritative: false }"
)


def control_center_mock_data(*sections: str) -> str:
    body = (
        "export const mockControlCenterData = { mock: true, production_ready: false, "
        "real_model_runtime_ready: false, remote_execution_ready: false, mobile_sensor_ready: false, "
        "plugin_or_native_build_ready: false, execution_enabled: false, dispatch_enabled: false, "
        "sensor_access_enabled: false, plugin_enablement_allowed: false, model_output_authoritative: false"
    )
    if sections:
        body = f"{body}, {', '.join(sections)}"
    return f"{body} }};\n"


def write_control_center_app_fixture(
    tmp_path: Path,
    *,
    package_json: str = DEFAULT_PACKAGE_JSON,
    package_lock: str = DEFAULT_PACKAGE_LOCK,
    vite_config: str | None = DEFAULT_VITE_CONFIG,
    base_url_ts: str | None = DEFAULT_BASE_URL_TS,
    client_ts: str | None = DEFAULT_CLIENT_TS,
    endpoints_ts: str | None = DEFAULT_ENDPOINTS_TS,
    redaction_ts: str | None = DEFAULT_REDACTION_TS,
    app_test_tsx: str | None = DEFAULT_APP_TEST_TSX,
    mock_data_ts: str | None = None,
    components: dict[str, str] | None = None,
    env_example: str | None = None,
) -> Path:
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)

    files: dict[str, str | None] = {
        "package.json": package_json,
        "package-lock.json": package_lock,
        "vite.config.ts": vite_config,
        "src/api/baseUrl.ts": base_url_ts,
        "src/api/client.ts": client_ts,
        "src/api/endpoints.ts": endpoints_ts,
        "src/api/redaction.ts": redaction_ts,
        "src/App.test.tsx": app_test_tsx,
        "src/mocks/controlCenterData.ts": mock_data_ts or control_center_mock_data(),
        ".env.example": env_example,
    }
    for relative_path, contents in files.items():
        if contents is not None:
            (app_root / relative_path).write_text(contents, encoding="utf-8")

    for filename, contents in (components or {}).items():
        (app_root / "src/components" / filename).write_text(contents, encoding="utf-8")

    return app_root
