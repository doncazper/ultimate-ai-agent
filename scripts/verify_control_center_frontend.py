#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "package.json",
    "package-lock.json",
    "vite.config.ts",
    "src/api/baseUrl.ts",
    "src/api/client.ts",
    "src/api/endpoints.ts",
    "src/api/redaction.ts",
    "src/components/ActionPreviewForm.tsx",
    "src/mocks/controlCenterData.ts",
    "src/App.test.tsx",
]

FORBIDDEN_ENDPOINTS = [
    "/control-center/actions/execute",
    "/control-center/plugins/enable",
    "/runtime/execute",
    "/control-center/runtime/execute",
    "/remote-workers/dispatch",
    "/control-center/remote-workers/dispatch",
    "/mobile/sensors",
    "/control-center/mobile/sensors",
]

DANGEROUS_BUTTON_LABELS = ["Execute", "Run", "Send", "Deploy", "Enable", "Approve"]

BROWSER_API_FRAGMENTS = [
    "localstorage",
    "sessionstorage",
    "document.cookie",
    "indexeddb",
    "cachestorage",
    "serviceworker",
    "navigator.credentials",
    "clipboard.write",
    "navigator.geolocation",
    "navigator.mediadevices",
    "notification.requestpermission",
    "pushmanager",
]

NATIVE_OR_PLUGIN_FRAGMENTS = [
    "chrome.",
    "computer use",
    "xcode",
    "app store connect",
    "provisioning profile",
    "signing identity",
    "keychain",
]

FORBIDDEN_FRONTEND_DEPENDENCIES = [
    '"next"',
    '"tailwindcss"',
    '"stripe"',
    '"@stripe/stripe-js"',
    '"@supabase/supabase-js"',
    '"firebase"',
    '"auth0-js"',
    '"analytics"',
    '"@segment/analytics-next"',
    '"@vercel/analytics"',
    '"posthog-js"',
    '"sentry"',
    '"@sentry/react"',
    '"openai"',
    '"anthropic"',
    '"expo"',
    '"react-native"',
    '"electron"',
    '"playwright"',
    '"puppeteer"',
]

SECRET_ASSIGNMENT = re.compile(
    r"(?i)(api[_-]?key|auth[_-]?token|authorization|cookie|password|secret|token)\s*[:=]\s*['\"]?([a-z0-9_./:-]{8,})"
)

ABSOLUTE_API_URL = re.compile(r"https?://(?!localhost(?::|/|$)|127\.0\.0\.1(?::|/|$)|\[::1\](?::|/|$))[^'\"\s)]+")


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    app_root = root / "apps/control-center"
    if not app_root.exists():
        return ["apps/control-center is missing"]

    for rel_path in REQUIRED_FILES:
        if not (app_root / rel_path).exists():
            failures.append(f"missing frontend file: apps/control-center/{rel_path}")

    failures.extend(_tracked_artifact_failures(root))
    failures.extend(_package_failures(app_root))

    implementation_files = _implementation_files(app_root)
    for path in implementation_files:
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for endpoint in FORBIDDEN_ENDPOINTS:
            if endpoint in text:
                failures.append(f"forbidden frontend endpoint in {rel}: {endpoint}")
        for fragment in BROWSER_API_FRAGMENTS:
            if fragment in lowered:
                failures.append(f"forbidden browser API in {rel}: {fragment}")
        for fragment in NATIVE_OR_PLUGIN_FRAGMENTS:
            if fragment in lowered:
                failures.append(f"forbidden native/plugin reference in {rel}: {fragment}")
        for match in ABSOLUTE_API_URL.finditer(text):
            failures.append(f"forbidden absolute external API URL in {rel}: {match.group(0)}")
        failures.extend(_button_label_failures(rel, text))

    mock_path = app_root / "src/mocks/controlCenterData.ts"
    if mock_path.exists():
        mock_text = mock_path.read_text(encoding="utf-8")
        mock_lowered = mock_text.lower()
        for match in SECRET_ASSIGNMENT.finditer(mock_text):
            value = match.group(2).lower()
            if value not in {"false", "mock", "placeholder"}:
                failures.append(f"secret-like fixture value in {mock_path.relative_to(root)}: {match.group(1)}")
        required_mock_safety = [
            "mock: true",
            "production_ready: false",
            "real_model_runtime_ready: false",
            "remote_execution_ready: false",
            "mobile_sensor_ready: false",
            "plugin_or_native_build_ready: false",
            "execution_enabled: false",
            "dispatch_enabled: false",
            "sensor_access_enabled: false",
            "plugin_enablement_allowed: false",
            "model_output_authoritative: false",
        ]
        for fragment in required_mock_safety:
            if fragment not in mock_lowered:
                failures.append(f"mock fixture missing safety marker: {fragment}")

    endpoints = app_root / "src/api/endpoints.ts"
    base_url = app_root / "src/api/baseUrl.ts"
    client = app_root / "src/api/client.ts"
    vite_config = app_root / "vite.config.ts"
    if endpoints.exists():
        text = endpoints.read_text(encoding="utf-8")
        if 'actionPreview: "/control-center/actions/preview"' not in text:
            failures.append("action preview endpoint declaration is missing")
        if text.count("/control-center/actions/preview") != 1:
            failures.append("action preview endpoint must appear exactly once in endpoint declarations")
        if "isAllowedReadEndpoint" not in text or "isPreviewEndpoint" not in text:
            failures.append("endpoint allowlist helpers are missing")
    if client.exists():
        text = client.read_text(encoding="utf-8")
        if text.count('method: "POST"') != 1:
            failures.append("frontend client must declare exactly one POST")
        if "API_ENDPOINTS.actionPreview" not in text:
            failures.append("frontend client must post only through API_ENDPOINTS.actionPreview")
        if "resolveApiBaseUrl" not in text:
            failures.append("frontend client must resolve API base through local backend policy")
    if base_url.exists():
        text = base_url.read_text(encoding="utf-8")
        required_policy_fragments = [
            "resolveApiBaseUrl",
            "localhost",
            "127.0.0.1",
            "::1",
            "EXTERNAL_API_BASE_URL_BLOCKED",
            "SECRET_LIKE_API_BASE_URL_REJECTED",
            "containsSecretLike",
        ]
        for fragment in required_policy_fragments:
            if fragment not in text:
                failures.append(f"local backend API base policy is missing: {fragment}")
    else:
        failures.append("local backend API base policy is missing")
    if vite_config.exists():
        text = vite_config.read_text(encoding="utf-8")
        if 'target: "http://127.0.0.1:8000"' not in text:
            failures.append("Vite dev proxy must target only http://127.0.0.1:8000")
        if '"/control-center"' not in text or '"/runtime"' not in text:
            failures.append("Vite dev proxy must cover local Control Center and runtime read routes")
        if "changeOrigin: true" in text:
            failures.append("Vite dev proxy must not rewrite origin for local backend checks")

    return failures


def _tracked_artifact_failures(root: Path) -> list[str]:
    try:
        tracked = subprocess.check_output(["git", "ls-files"], cwd=root, text=True).splitlines()
    except (subprocess.SubprocessError, FileNotFoundError):
        tracked = [str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()]
    forbidden = [
        "apps/control-center/node_modules/",
        "apps/control-center/dist/",
        "apps/control-center/coverage/",
        "apps/control-center/.next/",
        "apps/control-center/.env",
        "apps/control-center/ios/",
        "apps/control-center/android/",
    ]
    return [f"forbidden tracked frontend artifact: {path}" for path in tracked if any(fragment in path for fragment in forbidden)]


def _package_failures(app_root: Path) -> list[str]:
    package = app_root / "package.json"
    if not package.exists():
        return []
    text = package.read_text(encoding="utf-8").lower()
    return [f"forbidden frontend dependency marker: {fragment}" for fragment in FORBIDDEN_FRONTEND_DEPENDENCIES if fragment in text]


def _implementation_files(app_root: Path) -> list[Path]:
    src_root = app_root / "src"
    if not src_root.exists():
        return []
    return [
        path
        for path in src_root.rglob("*")
        if path.is_file()
        and path.suffix in {".ts", ".tsx", ".css"}
        and ".test." not in path.name
        and "test" not in path.parts
    ]


def _button_label_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    for label in DANGEROUS_BUTTON_LABELS:
        pattern = re.compile(rf"<button\b[^>]*>\s*{re.escape(label)}\s*</button>", re.IGNORECASE)
        if pattern.search(text):
            failures.append(f"dangerous action control label in {rel}: {label}")
    return failures


def main() -> int:
    print("=== Ultimate AI Agent Control Center Frontend Safety Verification ===")
    failures = verify(ROOT)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Control Center frontend safety verification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
