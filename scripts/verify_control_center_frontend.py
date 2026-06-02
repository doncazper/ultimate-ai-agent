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
    "src/components/ApprovalQueuePanel.tsx",
    "src/components/ReceiptViewerPanel.tsx",
    "src/components/EventViewerPanel.tsx",
    "src/components/EventTimelineTracePanel.tsx",
    "src/components/EvidenceFileMemoryViewerPanel.tsx",
    "src/components/LocalRuntimeStatusPanel.tsx",
    "src/mocks/controlCenterData.ts",
    "src/App.test.tsx",
]

FORBIDDEN_ENDPOINTS = [
    "/control-center/actions/execute",
    "/approvals/approve",
    "/approvals/deny",
    "/control-center/approvals/execute",
    "/control-center/approvals/approve",
    "/control-center/approvals/deny",
    "/receipts/delete",
    "/events/raw",
    "/memory/raw",
    "/files/raw",
    "/control-center/plugins/enable",
    "/runtime/execute",
    "/control-center/runtime/execute",
    "/remote-workers/dispatch",
    "/control-center/remote-workers/dispatch",
    "/mobile/sensors",
    "/control-center/mobile/sensors",
    "/events/timeline/raw",
    "/events/timeline/export",
    "/traces/raw",
    "/traces/export",
    "/runs/execute",
    "/control-center/traces/raw",
    "/control-center/traces/export",
    "/evidence/raw",
    "/evidence/payload",
    "/files/content",
    "/files/write",
    "/files/delete",
    "/filesystem/browse",
    "/memory/content",
    "/memory/write",
    "/memory/delete",
    "/memory/learn",
    "/memory/forget",
    "/runtime/smoke-reports/execute",
    "/runtime/local/execute",
    "/runtime/local/run",
    "/runtime/local/start",
    "/runtime/local/stop",
    "/runtime/local/connect",
    "/runtime/manual-smoke/execute",
    "/runtime/manual-smoke/run",
    "/model-runtime/local/smoke/execute",
]

DANGEROUS_BUTTON_LABELS = [
    "Approve",
    "Deny",
    "Execute",
    "Run",
    "Send",
    "Deploy",
    "Enable",
    "Install",
    "Publish",
    "Edit memory",
    "Delete memory",
    "Save memory",
    "Learn this",
    "Forget this",
    "Open file",
    "Delete file",
    "Write file",
    "Browse filesystem",
    "Reveal raw",
    "Show raw",
    "Run smoke",
    "Execute smoke",
    "Start runtime",
    "Stop runtime",
    "Connect runtime",
    "Launch runtime",
    "Call model",
]

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
URL_CREDENTIALS = re.compile(r"https?://[^'\"\s/@]+:[^'\"\s/@]+@[^'\"\s]+", re.IGNORECASE)
SECRET_LIKE_API_BASE = re.compile(
    r"(?i)VITE_UAA_API_BASE_URL\s*=\s*[^#\n]*(api[_-]?key|auth|credential|key|password|secret|token)\s*[:=][^\s#]+"
)
RAW_M15_REVIEW_FIELD = re.compile(
    r"\b(raw(?:Prompt|File|Memory|Event|Receipt|Credential|Provider|Secret)[A-Za-z0-9_]*|"
    r"(?:prompt|file|memory|event|receipt|provider|secret)(?:Body|Payload|Content))\b"
)
CREDENTIAL_M15_REVIEW_FIELD = re.compile(r"\b(?:credentialRef|credentialHandle|apiKey|authToken|password|secretRef)\b")
RAW_M16_TRACE_FIELD = re.compile(
    r"\b(raw(?:Prompt|File|Memory|Event|Receipt|Credential|Provider|Secret)[A-Za-z0-9_]*|"
    r"(?:prompt|file|memory|event|receipt|provider|secret|trace)(?:Body|Payload|Content))\b"
)
CREDENTIAL_M16_TRACE_FIELD = re.compile(r"\b(?:credentialRef|credentialHandle|apiKey|authToken|password|secretRef)\b")
RAW_M17_KNOWLEDGE_FIELD = re.compile(
    r"\b(raw(?:Prompt|File|Memory|Evidence|Event|Receipt|Credential|Provider|Secret)[A-Za-z0-9_]*|"
    r"(?:prompt|file|memory|evidence|event|receipt|provider|secret)(?:Body|Payload|Content))\b"
)
CREDENTIAL_M17_KNOWLEDGE_FIELD = re.compile(r"\b(?:credentialRef|credentialHandle|apiKey|authToken|password|secretRef)\b")
PRIVATE_PATH_FRAGMENT = re.compile(r"(/Users/|/home/|[A-Za-z]:\\Users\\)")
RAW_M18_RUNTIME_FIELD = re.compile(
    r"\b(raw(?:Prompt|Response|Transcript|File|Memory|Credential|Provider|Secret)[A-Za-z0-9_]*|"
    r"(?:prompt|response|transcript|provider|secret)(?:Body|Payload|Content))\b"
)
CREDENTIAL_M18_RUNTIME_FIELD = re.compile(r"\b(?:credentialRef|credentialHandle|apiKey|authToken|password|secretRef)\b")

M15_AUTHORITY_BOUNDARY_MARKERS = [
    "This UI cannot grant, deny, execute, or bypass approvals",
    "Approval refs are identifiers only and never authority",
    "Python Agent Core remains the only approval authority",
]

M16_TRACE_BOUNDARY_MARKERS = [
    "Timeline and trace views are read-only",
    "Trace detail is redacted summary metadata only",
    "No trace export or external telemetry is available",
]

M17_KNOWLEDGE_BOUNDARY_MARKERS = [
    "Evidence views are read-only",
    "File ref views are read-only",
    "Memory is recall, not authority",
    "Canonical files and governed source systems outrank memory",
    "No filesystem browsing is available",
]

M17_HARDENING_MOCK_MARKERS = [
    "mock_evidence_ref_002",
    "mock_file_ref_002",
    "mock_memory_ref_002",
    "memory_conflict_review_summary",
    "redacted-evidence-summary.json",
    "receipt_context",
]

M17_HARDENING_SELECTED_STATE_MARKERS = [
    "aria-current={selected ? \"true\" : undefined}",
    "evidence summary",
    "file ref summary",
    "memory summary",
]

M18_RUNTIME_BOUNDARY_MARKERS = [
    "Local runtime status is read-only",
    "No local runtime is started, stopped, connected, or executed from this UI",
    "Manual smoke reports are safe summaries",
    "Manual smoke execution remains CLI-only, fixed-prompt-only, approval-gated",
]

M18_RUNTIME_MOCK_MARKERS = [
    "m18Runtime",
    "mock_manual_smoke_report_ref_001",
    "runtime_readiness_report",
    "manual_loopback_smoke",
    "VALIDATION_ONLY",
    "NO_RUNTIME_EXECUTION",
    "modelOutputAuthoritative: false",
]


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
    failures.extend(_env_example_failures(app_root, root))

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
        for match in URL_CREDENTIALS.finditer(text):
            failures.append(f"forbidden URL credentials in {rel}: {match.group(0)}")
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
            "m15review",
            "m16trace",
            "m17knowledge",
            "non-authoritative",
            "redacted_summary_only",
            "approvalgrantallowed: false",
            "external_export_allowed: false",
            "no_external_export",
            "no_raw_content",
            "memory_not_authority",
            "m18runtime",
            "validation_only",
            "no_runtime_execution",
            "modeloutputauthoritative: false",
        ]
        normalized_mock = mock_lowered.replace("_", "").replace(" ", "")
        for fragment in required_mock_safety:
            normalized_fragment = fragment.lower().replace("_", "").replace(" ", "")
            if normalized_fragment not in normalized_mock and fragment not in mock_lowered:
                failures.append(f"mock fixture missing safety marker: {fragment}")
        failures.extend(_m15_review_field_failures(mock_path.relative_to(root), mock_text))
        failures.extend(_m16_trace_field_failures(mock_path.relative_to(root), mock_text))
        failures.extend(_m17_knowledge_field_failures(mock_path.relative_to(root), mock_text))
        failures.extend(_m18_runtime_field_failures(mock_path.relative_to(root), mock_text))
        for marker in M17_HARDENING_MOCK_MARKERS:
            if marker.lower() not in mock_lowered:
                failures.append(f"M17 hardening mock marker missing: {marker}")
        for marker in M18_RUNTIME_MOCK_MARKERS:
            if marker.lower() not in mock_lowered:
                failures.append(f"M18 runtime mock marker missing: {marker}")

    approval_panel = app_root / "src/components/ApprovalQueuePanel.tsx"
    if approval_panel.exists():
        text = approval_panel.read_text(encoding="utf-8")
        for marker in M15_AUTHORITY_BOUNDARY_MARKERS:
            if marker not in text:
                failures.append(f"approval authority boundary copy missing in {approval_panel.relative_to(root)}: {marker}")

    timeline_panel = app_root / "src/components/EventTimelineTracePanel.tsx"
    if timeline_panel.exists():
        text = timeline_panel.read_text(encoding="utf-8")
        for marker in M16_TRACE_BOUNDARY_MARKERS:
            if marker not in text:
                failures.append(f"M16 trace boundary copy missing in {timeline_panel.relative_to(root)}: {marker}")

    knowledge_panel = app_root / "src/components/EvidenceFileMemoryViewerPanel.tsx"
    if knowledge_panel.exists():
        text = knowledge_panel.read_text(encoding="utf-8")
        for marker in M17_KNOWLEDGE_BOUNDARY_MARKERS:
            if marker not in text:
                failures.append(f"M17 knowledge boundary copy missing in {knowledge_panel.relative_to(root)}: {marker}")
        for marker in M17_HARDENING_SELECTED_STATE_MARKERS:
            if marker not in text:
                failures.append(f"M17 hardening selected-state marker missing in {knowledge_panel.relative_to(root)}: {marker}")

    runtime_panel = app_root / "src/components/LocalRuntimeStatusPanel.tsx"
    if runtime_panel.exists():
        text = runtime_panel.read_text(encoding="utf-8")
        for marker in M18_RUNTIME_BOUNDARY_MARKERS:
            if marker not in text:
                failures.append(f"M18 runtime boundary copy missing in {runtime_panel.relative_to(root)}: {marker}")

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
        if 'runtimeSmokeReportValidate: "/runtime/smoke-reports/validate"' not in text:
            failures.append("runtime smoke report validation endpoint declaration is missing")
        if "isAllowedReadEndpoint" not in text or "isPreviewEndpoint" not in text:
            failures.append("endpoint allowlist helpers are missing")
        if "isRuntimeValidationEndpoint" not in text:
            failures.append("runtime validation endpoint allowlist helper is missing")
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
        required_proxy_routes = [
            '"/control-center"',
            '"/runtime/readiness"',
            '"/runtime/capability-matrix"',
            '"/runtime/smoke-reports"',
        ]
        for route in required_proxy_routes:
            if route not in text:
                failures.append(f"Vite dev proxy must cover local backend route: {route}")
        if re.search(r'["\']/runtime["\']\s*:', text):
            failures.append("Vite dev proxy must not proxy broad /runtime frontend route space")
        if "changeOrigin: true" in text:
            failures.append("Vite dev proxy must not rewrite origin for local backend checks")
        for match in ABSOLUTE_API_URL.finditer(text):
            failures.append(f"forbidden absolute external API URL in {vite_config.relative_to(root)}: {match.group(0)}")
        for match in URL_CREDENTIALS.finditer(text):
            failures.append(f"forbidden URL credentials in {vite_config.relative_to(root)}: {match.group(0)}")

    return failures


def _tracked_artifact_failures(root: Path) -> list[str]:
    try:
        tracked = subprocess.check_output(["git", "ls-files"], cwd=root, text=True).splitlines()
    except (subprocess.SubprocessError, FileNotFoundError):
        tracked = [str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()]
    forbidden = [
        "apps/control-center/node_modules/",
        "apps/control-center/dist/",
        "apps/control-center/build/",
        "apps/control-center/coverage/",
        "apps/control-center/logs/",
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


def _env_example_failures(app_root: Path, root: Path) -> list[str]:
    failures: list[str] = []
    for name in [".env.example", "env.example"]:
        path = app_root / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)
        if SECRET_LIKE_API_BASE.search(text):
            failures.append(f"secret-like API base env example in {rel}")
        for match in ABSOLUTE_API_URL.finditer(text):
            failures.append(f"forbidden absolute external API URL in {rel}: {match.group(0)}")
        for match in URL_CREDENTIALS.finditer(text):
            failures.append(f"forbidden URL credentials in {rel}: {match.group(0)}")
    return failures


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


def _m15_review_field_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    m15_index = text.lower().find("m15review")
    if m15_index == -1:
        return failures
    m15_text = text[m15_index:]
    for match in RAW_M15_REVIEW_FIELD.finditer(m15_text):
        failures.append(f"raw M15 review field in {rel}: {match.group(0)}")
    for match in CREDENTIAL_M15_REVIEW_FIELD.finditer(m15_text):
        failures.append(f"credential-like M15 review field in {rel}: {match.group(0)}")
    return failures


def _m16_trace_field_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    m16_index = text.lower().find("m16trace")
    if m16_index == -1:
        return failures
    m16_text = text[m16_index:]
    for match in RAW_M16_TRACE_FIELD.finditer(m16_text):
        failures.append(f"raw M16 trace field in {rel}: {match.group(0)}")
    for match in CREDENTIAL_M16_TRACE_FIELD.finditer(m16_text):
        failures.append(f"credential-like M16 trace field in {rel}: {match.group(0)}")
    return failures


def _m17_knowledge_field_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    m17_index = text.lower().find("m17knowledge")
    if m17_index == -1:
        return failures
    m17_text = text[m17_index:]
    for match in RAW_M17_KNOWLEDGE_FIELD.finditer(m17_text):
        failures.append(f"raw M17 knowledge field in {rel}: {match.group(0)}")
    for match in CREDENTIAL_M17_KNOWLEDGE_FIELD.finditer(m17_text):
        failures.append(f"credential-like M17 knowledge field in {rel}: {match.group(0)}")
    for match in PRIVATE_PATH_FRAGMENT.finditer(m17_text):
        failures.append(f"private path fragment in M17 knowledge fixture in {rel}: {match.group(0)}")
    return failures


def _m18_runtime_field_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    m18_index = text.lower().find("m18runtime")
    if m18_index == -1:
        return failures
    m18_text = text[m18_index:]
    for match in RAW_M18_RUNTIME_FIELD.finditer(m18_text):
        failures.append(f"raw M18 runtime field in {rel}: {match.group(0)}")
    for match in CREDENTIAL_M18_RUNTIME_FIELD.finditer(m18_text):
        failures.append(f"credential-like M18 runtime field in {rel}: {match.group(0)}")
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
