#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _current_version(root: Path = ROOT) -> str:
    bare_version_file = root / "VERSION"
    if bare_version_file.exists():
        bare_version = bare_version_file.read_text(encoding="utf-8").strip()
        if re.fullmatch(r"\d+\.\d+\.\d+(?:-rc\.[1-9]\d*)?", bare_version):
            return f"v{bare_version}"
    version_file = root / "VERSION.md"
    if not version_file.exists():
        return "v0.0.0"
    for line in version_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("Current active baseline:") and "**" in stripped:
            return stripped.split("**", 2)[1]
    return "v0.0.0"


def _version_tuple(version: str) -> tuple[int, int, int]:
    match = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())

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
    "src/components/OperatorSurfaceStates.tsx",
    "src/components/FileReviewSurfacePanel.tsx",
    "src/components/ContextProposalSurfacePanel.tsx",
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
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/read/full",
    "/files/review/approve",
    "/files/review/submit",
    "/files/write",
    "/files/delete",
    "/filesystem/browse",
    "/memory/content",
    "/memory/write",
    "/memory/delete",
    "/context/propose",
    "/context/inject",
    "/tool-runtime/execute",
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
    "/device-capabilities",
    "/device-capabilities/execute",
    "/device-capabilities/camera",
    "/device-capabilities/microphone",
    "/device-capabilities/location",
    "/device-capabilities/notifications",
    "/device-capabilities/contacts",
    "/device-capabilities/calendar",
    "/device-capabilities/photos",
    "/device-capabilities/files",
    "/device-capabilities/clipboard",
    "/device-capabilities/bluetooth",
    "/device-capabilities/nfc",
    "/device-capabilities/biometrics",
    "/device-capabilities/local-network",
    "/device-capabilities/motion",
    "/device-capabilities/health",
    "/device-capabilities/screen-capture",
    "/device-capabilities/background-service",
    "/device-capability-broker",
    "/device-capability-broker/execute",
    "/device-capability-broker/capabilities",
    "/device-capability-broker/pair",
    "/mobile/permissions",
    "/mobile/camera",
    "/mobile/microphone",
    "/mobile/location",
    "/mobile/notifications",
    "/mobile/capture",
    "/mobile/pair",
    "/mobile/background-service",
    "/openwebui",
    "/openwebui/bridge",
    "/openwebui/chat",
    "/openwebui/execute",
    "/openwebui/bridge/run",
    "/chat/execute",
    "/chat/run",
    "/model-runtime/execute",
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
    "Open raw file",
    "Delete file",
    "Write file",
    "Browse filesystem",
    "File picker",
    "Browse",
    "Upload",
    "Root selector",
    "Submit",
    "Save",
    "Mark reviewed",
    "Export",
    "Download",
    "Copy raw",
    "Context proposal",
    "Inject",
    "Write memory",
    "Run tool",
    "Call model",
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
    "android.permission",
    "manifest.permission",
    "avcapture",
    "cllocation",
    "locationmanager",
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
    '"@capacitor/core"',
    '"cordova"',
    '"ionic"',
    '"flutter"',
    '"electron"',
    '"playwright"',
    '"puppeteer"',
    '"openwebui"',
    '"open-webui"',
]

OPERATOR_SHELL_GAP_MAP = "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
ROUTE_STATUS_MANIFEST = "docs/control_center/route_status_manifest.json"
ROUTE_STATUS_MANIFEST_DOC = "docs/control_center/ROUTE_STATUS_MANIFEST.md"
PRODUCT_LANGUAGE_RULES_DOC = "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
BROWSER_SMOKE_DOC = "docs/control_center/LOCAL_BROWSER_SMOKE.md"
BROWSER_SMOKE_REPORTING_DOC = "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md"
BROWSER_SMOKE_TEST = "apps/control-center/src/App.test.tsx"
REQUIRED_OPERATOR_SHELL_SURFACES = [
    "Chat Shell",
    "Plans",
    "Models",
    "Approvals",
    "Files",
    "Runtime",
    "Evidence",
    "Settings",
]
ROUTE_STATUS_ACTION_FIELDS = {
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
ROUTE_STATUS_SURFACE_FIELDS = {
    "surface",
    "owner",
    "auth_posture",
    "side_effect_class",
    "risk_class",
    "release_status",
    "approval_requirement",
    "evidence_audit_output",
    "current_backend_routes",
    "missing_backend_routes",
}
PRODUCT_LANGUAGE_REQUIRED_FRAGMENTS = {
    "status: active uaa-p1-031 product language rules",
    "no hidden authority",
    "no fake completion",
    "no raw json as primary ui for operator-critical flows",
    "no production/public distribution claims without evidence",
    "no model/provider output as authority",
    "no completed-state language for blocked/skipped/pending work",
    "scripts/verify_control_center_frontend.py",
}
PRODUCT_LANGUAGE_FORBIDDEN_CLAIMS = [
    "production ready for external users",
    "public distribution is available",
    "public release is available",
    "control center executes actions",
    "control center grants approvals",
    "control center completes work",
    "control center runs tools",
    "control center launches runtime",
    "model output is authority",
    "provider output is authority",
    "blocked work is complete",
    "skipped work is complete",
    "pending work is complete",
    "unimplemented action is ready",
    "raw json is the primary ui",
]
PRODUCT_LANGUAGE_FORBIDDEN_FRONTEND_PHRASES = [
    "Production ready",
    "Public release",
    "Public distribution",
    "Completed successfully",
    "Execution completed",
    "Model output is authority",
    "Provider output is authority",
    "Raw JSON",
]
UNREADY_COMPLETION_WORDS = ["complete", "completed", "done", "finished", "succeeded"]
BROWSER_SMOKE_REQUIRED_DOC_FRAGMENTS = [
    "status: active uaa-p1-032 browser smoke readiness",
    "first product loop readiness",
    "real",
    "mocked",
    "skipped",
    "blocked",
    "open control center",
    "inspect runtime health and model readiness",
    "select or approve local gguf model",
    "use chat shell through uaa `/v1`",
    "create a task decomposition plan",
    "approve one safe registered capability",
    "inspect receipt/audit/latency/rollback status",
    "raw json must not be the primary ui",
]
BROWSER_SMOKE_REQUIRED_REPORT_FRAGMENTS = [
    "status: active uaa-p1-032 browser smoke readiness reporting",
    "first product loop",
    "real, mocked, skipped, or blocked",
    "open_control_center",
    "inspect_runtime_health_and_model_readiness",
    "select_or_approve_local_gguf_model",
    "chat_shell_through_uaa_v1",
    "create_task_decomposition_plan",
    "approve_safe_registered_capability",
    "inspect_receipt_audit_latency_rollback",
    "no_raw_json_primary_ui",
    "blocked_prerequisites_visible",
    "release_readiness_claimed: no",
]
BROWSER_SMOKE_REQUIRED_TEST_FRAGMENTS = [
    "covers first product loop browser smoke readiness with truthful mocked and blocked states",
    'openControlCenter: "mocked"',
    'selectOrApproveLocalGgufModel: "blocked"',
    'chatShellThroughUaaV1: "blocked"',
    'createTaskDecompositionPlan: "blocked"',
    "Preview only action request",
    "No approval was granted from this UI",
    "Trace detail is redacted summary metadata only",
]
OPERATOR_STATE_REQUIRED_COMPONENT_FRAGMENTS = [
    "OperatorSurfaceStates",
    "OperatorSurfacePlaceholderPanel",
    "Chat Shell",
    "Plans",
    "Models",
    "Approvals",
    "Files",
    "Runtime",
    "Evidence",
    "Settings",
    "loading",
    "error",
    "empty",
    "blocked",
    "denied",
    "Next safe action:",
    "role={role}",
    "does not run actions",
    "does not grant approvals",
    "does not change settings",
    "does not call models",
    "does not expose sensitive source material",
]
OPERATOR_STATE_REQUIRED_TEST_FRAGMENTS = [
    "renders accessible operator states for required Control Center surfaces",
    "/chat",
    "/plans",
    "/models",
    "/settings",
    "Blocked: dedicated chat shell not implemented",
    "Denied: no sensitive evidence display",
    "Denied: no authority toggle",
    "getAllByRole(\"status\")",
    "getAllByRole(\"alert\")",
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
M36_PRIVATE_OR_RAW_PATH_FRAGMENT = re.compile(
    r"(/Users/|/home/|[A-Za-z]:\\|\.\./|absolute_path|raw_absolute_path|raw file path)",
    re.IGNORECASE,
)
M36_MUTATING_FILE_REVIEW_REQUEST = re.compile(
    r"fetch\([^)]*(?:/files/review|/files/read|/context/propose|/context/inject|/memory/write|/tools/execute)[^)]*"
    r"method\s*:\s*['\"](?:POST|PUT|PATCH|DELETE)['\"]",
    re.IGNORECASE | re.DOTALL,
)
M36_SAFE_REF_PREFIXES = {
    "reviewPacketRef": "file-review-packet:",
    "previewResultRef": "redacted-file-preview-output:",
    "redactionSummaryRef": "file-review-redaction-summary:",
    "fileRef": "file-ref:",
    "safePathRef": "filesystem-preview-path:safe-root_",
}
M36_SAFE_REF_LABELS = {
    "reviewPacketRef": "review_packet_ref",
    "previewResultRef": "preview_result_ref",
    "redactionSummaryRef": "redaction_summary_ref",
    "fileRef": "file_ref",
    "safePathRef": "safe_path_ref",
}
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

M36_FILE_REVIEW_BOUNDARY_MARKERS = [
    "M37 review approval capture",
    "Review-only surface",
    "Redacted preview",
    "Redaction summary",
    "Exact binding refs",
    "Safe refs only",
    "Only the review approval capture route may persist safe refs",
    "Approval gate contract status",
    "Receipt plan metadata",
    "Approve review-only",
    "Deny review-only",
    "does not grant raw file access",
]

M36_FILE_REVIEW_MOCK_MARKERS = [
    "m36FileReview",
    "file-review-packet:mock_001",
    "redacted-file-preview-output:mock_001",
    "file-review-redaction-summary:mock_001",
    "file-ref:mock_review_001",
    "filesystem-preview-path:safe-root_m36/docs/review-summary.md",
    "REVIEW_ONLY_APPROVAL_CAPTURE",
    "SAFE_REF_PERSISTENCE_ONLY",
    "NO_RAW_FILE_DISPLAY",
    "SAFE_REFS_ONLY",
    "NO_AUTHORITY_GRANTED",
    "rawContentStored: false",
    "approvalCaptured: false",
    "approvalPersisted: false",
    "rawFileAccessAuthorized: false",
    "contextProposalAuthorized: false",
    "memoryWriteAuthorized: false",
    "exportAuthorized: false",
    "executionAuthorized: false",
    "contextProposalCreated: false",
    "contextInjectionPerformed: false",
    "memoryWritePerformed: false",
    "exportPerformed: false",
    "executionPerformed: false",
]
M39_CONTEXT_PROPOSAL_BOUNDARY_MARKERS = [
    "M39 CCC context proposal surface",
    "Context Proposal Surface",
    "Safe proposal sections",
    "Exact binding refs",
    "Source chain refs",
    "Control Center output is not authority",
    "does not hand off to OpenWebUI",
    "inject context",
    "write memory",
    "export data",
    "execute actions",
    "Receipt plan metadata",
    "OpenWebUI handoff authorized",
    "context injection authorized",
    "memory write authorized",
    "export authorized",
    "execution authorized",
]
M39_CONTEXT_PROPOSAL_MOCK_MARKERS = [
    "m39ContextProposals",
    "safe-context-proposal:mock_001",
    "safe-context-proposal-section:mock_001:redacted-preview",
    "file-review-approval-capture:mock_001",
    "file-review-packet:mock_001",
    "redacted-file-preview-output:mock_001",
    "file-review-redaction-summary:mock_001",
    "file-ref:mock_review_001",
    "filesystem-preview-path:safe-root_m39/docs/review-summary.md",
    "user:mock_reviewer_001",
    "PROPOSAL_ONLY",
    "SAFE_REFS_ONLY",
    "NO_CONTEXT_HANDOFF",
    "NO_CONTEXT_INJECTION",
    "NO_OPENWEBUI_HANDOFF",
    "NO_MEMORY_WRITE",
    "NO_EXPORT",
    "NO_EXECUTION",
    "NO_RAW_FILE_DISPLAY",
    "rawContentStored: false",
    "fullFileContentStored: false",
    "unredactedPreviewStored: false",
    "contextInjected: false",
    "openwebuiHandoffPerformed: false",
    "memoryWritePerformed: false",
    "exportPerformed: false",
    "executionPerformed: false",
    "contextInjectionAuthorized: false",
    "openwebuiHandoffAuthorized: false",
    "modelCallAuthorized: false",
    "memoryWriteAuthorized: false",
    "exportAuthorized: false",
    "executionAuthorized: false",
    "rawFileAccessAuthorized: false",
    "truthAuthorityClaimed: false",
]
M39_SAFE_REF_PREFIXES = {
    "proposalRef": "safe-context-proposal:",
    "approvalRef": "file-review-approval-capture:",
    "reviewPacketRef": "file-review-packet:",
    "previewResultRef": "redacted-file-preview-output:",
    "redactionSummaryRef": "file-review-redaction-summary:",
    "fileRef": "file-ref:",
    "safePathRef": "filesystem-preview-path:safe-root_",
    "actorRef": "user:",
}
M39_MUTATING_CONTEXT_PROPOSAL_REQUEST = re.compile(
    r"fetch\([^)]*(?:/context/propose|/context/inject|/context/handoff|/openwebui/handoff|/memory/write|/tools/execute)[^)]*"
    r"method\s*:\s*['\"](?:POST|PUT|PATCH|DELETE)['\"]",
    re.IGNORECASE | re.DOTALL,
)


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
    failures.extend(_operator_shell_gap_map_failures(root))
    failures.extend(_route_status_manifest_failures(root))
    failures.extend(_product_language_rule_failures(root))
    failures.extend(_browser_smoke_readiness_failures(root))
    failures.extend(_operator_surface_state_failures(root))

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
        failures.extend(_product_language_frontend_failures(rel, text))

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
            "m36filereview",
            "m39contextproposals",
            "validation_only",
            "no_runtime_execution",
            "modeloutputauthoritative: false",
            "no_raw_file_display",
            "no_context_injection",
            "no_openwebui_handoff",
        ]
        if _version_tuple(_current_version(root)) < _version_tuple("v0.41.0"):
            required_mock_safety.extend(["no_approval_capture", "no_approval_persistence"])
        else:
            required_mock_safety.extend(
                ["review_only_approval_capture", "safe_ref_persistence_only", "no_authority_granted"]
            )
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
        for marker in M36_FILE_REVIEW_MOCK_MARKERS:
            if marker.lower() not in mock_lowered:
                failures.append(f"M36 file review mock marker missing: {marker}")
        failures.extend(_m36_file_review_fixture_failures(mock_path.relative_to(root), mock_text))
        for marker in M39_CONTEXT_PROPOSAL_MOCK_MARKERS:
            if marker.lower() not in mock_lowered:
                failures.append(f"M39 context proposal mock marker missing: {marker}")
        failures.extend(_m39_context_proposal_fixture_failures(mock_path.relative_to(root), mock_text))

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

    file_review_panel = app_root / "src/components/FileReviewSurfacePanel.tsx"
    if file_review_panel.exists():
        text = file_review_panel.read_text(encoding="utf-8")
        for marker in M36_FILE_REVIEW_BOUNDARY_MARKERS:
            if marker not in text:
                failures.append(f"M36 file review boundary copy missing in {file_review_panel.relative_to(root)}: {marker}")
        failures.extend(_m36_file_review_component_failures(file_review_panel.relative_to(root), text))

    context_proposal_panel = app_root / "src/components/ContextProposalSurfacePanel.tsx"
    if context_proposal_panel.exists():
        text = context_proposal_panel.read_text(encoding="utf-8")
        for marker in M39_CONTEXT_PROPOSAL_BOUNDARY_MARKERS:
            if marker not in text:
                failures.append(f"M39 context proposal boundary copy missing in {context_proposal_panel.relative_to(root)}: {marker}")
        failures.extend(_m39_context_proposal_component_failures(context_proposal_panel.relative_to(root), text))

    routes = app_root / "src/routes.tsx"
    if routes.exists():
        text = routes.read_text(encoding="utf-8")
        if '"/files/review"' not in text or "FileReviewSurfacePanel" not in text:
            failures.append("M36 file review route is missing from Control Center routes")
        if '"/context/proposals"' not in text or "ContextProposalSurfacePanel" not in text:
            failures.append("M39 context proposal route is missing from Control Center routes")

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


def _frontend_nav_routes(app_root: Path) -> set[str]:
    routes_file = app_root / "src/routes.tsx"
    if not routes_file.exists():
        return set()
    text = routes_file.read_text(encoding="utf-8")
    return set(re.findall(r'\{\s*path:\s*"([^"]+)",\s*label:', text))


def _frontend_api_endpoint_paths(app_root: Path) -> set[str]:
    endpoints_file = app_root / "src/api/endpoints.ts"
    if not endpoints_file.exists():
        return set()
    text = endpoints_file.read_text(encoding="utf-8")
    return set(re.findall(r':\s*"(/[^"]+)"', text))


def _route_status_manifest_failures(root: Path) -> list[str]:
    failures: list[str] = []
    app_root = root / "apps/control-center"
    manifest_path = root / ROUTE_STATUS_MANIFEST
    manifest_doc_path = root / ROUTE_STATUS_MANIFEST_DOC
    if not manifest_path.exists():
        return [f"missing Control Center route status manifest: {ROUTE_STATUS_MANIFEST}"]
    if not manifest_doc_path.exists():
        failures.append(f"missing Control Center route status manifest doc: {ROUTE_STATUS_MANIFEST_DOC}")
    else:
        doc_text = manifest_doc_path.read_text(encoding="utf-8").lower()
        for fragment in [
            "status: active uaa-p1-030 route status manifest",
            "docs/control_center/route_status_manifest.json",
            "docs/control_center/product_language_rules.md",
            "visible actions",
            "verification",
        ]:
            if fragment not in doc_text:
                failures.append(f"route status manifest doc missing fragment: {fragment}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid route status manifest JSON: {exc}"]

    if manifest.get("schema_version") != "uaa-control-center-route-status.v1":
        failures.append("route status manifest schema version is not current")
    if manifest.get("status") != "active UAA-P1-030 route status manifest":
        failures.append("route status manifest status is not current")
    if manifest.get("openapi_path_count") != 93:
        failures.append("route status manifest must record the 93-path OpenAPI boundary")

    allowed_statuses = set(manifest.get("allowed_release_statuses", []))
    required_statuses = {
        "status_available_not_completion",
        "preview_available_not_execution",
        "partial_backend_not_product_ready",
        "mock_only_not_product_ready",
        "local_ui_state_only_not_evidence",
        "blocked_missing_backend",
    }
    if not required_statuses.issubset(allowed_statuses):
        failures.append("route status manifest missing required release status values")

    surfaces = manifest.get("surfaces", [])
    visible_actions = manifest.get("visible_actions", [])
    surface_names = {surface.get("surface") for surface in surfaces}
    for surface in REQUIRED_OPERATOR_SHELL_SURFACES:
        if surface not in surface_names:
            failures.append(f"route status manifest missing surface: {surface}")

    for surface in surfaces:
        missing_fields = ROUTE_STATUS_SURFACE_FIELDS.difference(surface)
        if missing_fields:
            failures.append(
                f"route status manifest surface {surface.get('surface', '<unknown>')} "
                f"missing fields: {sorted(missing_fields)}"
            )
        if surface.get("release_status") not in allowed_statuses:
            failures.append(f"route status manifest surface has unknown status: {surface.get('surface')}")

    action_ids = [action.get("action_id") for action in visible_actions]
    if len(action_ids) != len(set(action_ids)):
        failures.append("route status manifest action ids must be unique")
    action_routes = {action.get("frontend_route") for action in visible_actions}
    for route in _frontend_nav_routes(app_root):
        if route not in action_routes:
            failures.append(f"route status manifest missing frontend route: {route}")

    backend_paths = {
        route.get("path")
        for section_name, route_key in [
            ("surfaces", "current_backend_routes"),
            ("visible_actions", "backend_routes"),
        ]
        for item in manifest.get(section_name, [])
        for route in item.get(route_key, [])
    }
    for endpoint_path in _frontend_api_endpoint_paths(app_root):
        if endpoint_path not in backend_paths:
            failures.append(f"route status manifest missing frontend API endpoint: {endpoint_path}")

    available_statuses = {"status_available_not_completion", "preview_available_not_execution"}
    for action in visible_actions:
        missing_fields = ROUTE_STATUS_ACTION_FIELDS.difference(action)
        if missing_fields:
            failures.append(
                f"route status manifest action {action.get('action_id', '<unknown>')} "
                f"missing fields: {sorted(missing_fields)}"
            )
        if action.get("release_status") not in allowed_statuses:
            failures.append(f"route status manifest action has unknown status: {action.get('action_id')}")
        if (not action.get("backend_routes") or action.get("missing_backend_routes")) and (
            action.get("release_status") in available_statuses
        ):
            failures.append(
                "route status manifest marks unready action as available: "
                f"{action.get('action_id')}"
            )

    for required_action in [
        "submit-action-preview",
        "select-local-detail-card",
        "toggle-review-only-file-decision",
    ]:
        if required_action not in action_ids:
            failures.append(f"route status manifest missing visible action: {required_action}")

    serialized = json.dumps(manifest).lower()
    for unsafe in [
        "production_ready",
        "public_release_ready",
        "broad_autonomy_enabled",
        "shell_authority_enabled",
        "connector_writes_enabled",
        "plugin_runtime_enabled",
    ]:
        if unsafe in serialized:
            failures.append(f"route status manifest contains unsafe status claim: {unsafe}")

    return failures


def _product_language_rule_failures(root: Path) -> list[str]:
    failures: list[str] = []
    doc_path = root / PRODUCT_LANGUAGE_RULES_DOC
    if not doc_path.exists():
        return [f"missing Control Center product language rules: {PRODUCT_LANGUAGE_RULES_DOC}"]

    doc_text = doc_path.read_text(encoding="utf-8")
    doc_lowered = doc_text.lower()
    doc_compact = " ".join(doc_lowered.split())
    for fragment in PRODUCT_LANGUAGE_REQUIRED_FRAGMENTS:
        if fragment not in doc_compact:
            failures.append(f"product language rules doc missing fragment: {fragment}")

    link = PRODUCT_LANGUAGE_RULES_DOC.lower()
    for rel_path in [
        "README.md",
        "docs/README.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
        "docs/control_center/OPERATOR_SHELL_GAP_MAP.md",
        "docs/control_center/ROUTE_STATUS_MANIFEST.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
        "docs/kanban/current_board.md",
    ]:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing product language link target: {rel_path}")
            continue
        if link not in path.read_text(encoding="utf-8").lower():
            failures.append(f"{rel_path} must link Control Center product language rules")

    for rel_path in [
        "README.md",
        "docs/README.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
        "docs/control_center/OPERATOR_SHELL_GAP_MAP.md",
        "docs/control_center/ROUTE_STATUS_MANIFEST.md",
        PRODUCT_LANGUAGE_RULES_DOC,
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
        "docs/kanban/current_board.md",
    ]:
        text = (root / rel_path).read_text(encoding="utf-8").lower()
        for claim in PRODUCT_LANGUAGE_FORBIDDEN_CLAIMS:
            if claim in text:
                failures.append(f"{rel_path} contains unsafe product language claim: {claim}")

    manifest_path = root / ROUTE_STATUS_MANIFEST
    if not manifest_path.exists():
        failures.append(f"missing route status manifest for product language checks: {ROUTE_STATUS_MANIFEST}")
        return failures
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid route status manifest JSON for product language checks: {exc}")
        return failures

    for section_name, items in [
        ("surface", manifest.get("surfaces", [])),
        ("visible action", manifest.get("visible_actions", [])),
    ]:
        for item in items:
            status = item.get("release_status", "")
            if not any(marker in status for marker in ["blocked", "partial", "mock", "local_ui_state"]):
                continue
            identifier = item.get("surface") or item.get("action_id") or "<unknown>"
            checked_text = " ".join(
                str(item.get(field, ""))
                for field in ["label", "approval_requirement", "evidence_audit_output"]
            ).lower()
            for word in UNREADY_COMPLETION_WORDS:
                if re.search(rf"\b{re.escape(word)}\b", checked_text):
                    failures.append(
                        f"route status manifest {section_name} {identifier} uses "
                        f"completed-state wording while {status}: {word}"
                    )

    return failures


def _browser_smoke_readiness_failures(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path, required_fragments, label in [
        (BROWSER_SMOKE_DOC, BROWSER_SMOKE_REQUIRED_DOC_FRAGMENTS, "browser smoke doc"),
        (
            BROWSER_SMOKE_REPORTING_DOC,
            BROWSER_SMOKE_REQUIRED_REPORT_FRAGMENTS,
            "browser smoke reporting doc",
        ),
        (BROWSER_SMOKE_TEST, BROWSER_SMOKE_REQUIRED_TEST_FRAGMENTS, "browser smoke test"),
    ]:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing {label}: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        compact = " ".join(text.split())
        for fragment in required_fragments:
            if fragment.lower() not in compact and fragment.lower() not in text:
                failures.append(f"{label} missing UAA-P1-032 fragment: {fragment}")

    smoke_doc_text = (root / BROWSER_SMOKE_DOC).read_text(encoding="utf-8").lower()
    smoke_report_text = (root / BROWSER_SMOKE_REPORTING_DOC).read_text(encoding="utf-8").lower()
    for unsafe in [
        "production ready for external users",
        "public distribution is available",
        "browser smoke proves production readiness",
        "raw json is the primary ui",
        "hidden authority",
        "model output is authority",
        "provider output is authority",
    ]:
        if unsafe in smoke_doc_text or unsafe in smoke_report_text:
            failures.append(f"browser smoke readiness docs contain unsafe claim: {unsafe}")
    return failures


def _operator_shell_gap_map_failures(root: Path) -> list[str]:
    failures: list[str] = []
    doc_path = root / OPERATOR_SHELL_GAP_MAP
    if not doc_path.exists():
        return [f"missing Control Center operator-shell gap map: {OPERATOR_SHELL_GAP_MAP}"]
    text = doc_path.read_text(encoding="utf-8")
    lowered = text.lower()
    compact = " ".join(lowered.split())
    required_fragments = {
        "operator-shell gap map must identify UAA-P0-007": (
            "status: active uaa-p0-007 operator-shell gap map"
        ),
        "operator-shell gap map must include current API count": (
            "api boundary: current fastapi manifest has 93 openapi paths"
        ),
        "operator-shell gap map must include exact matrix columns": (
            "| surface | current frontend component/page | current backend route(s) | "
            "missing backend route(s) | authority boundary | side-effect class | "
            "approval requirement | evidence/audit output | readiness status | "
            "production-readiness blocker |"
        ),
        "operator-shell gap map must include visible action map": "## visible action map",
        "operator-shell gap map must include first product loop gaps": (
            "## first product loop gaps"
        ),
        "operator-shell gap map must include product language rules": (
            "## product language rules"
        ),
        "operator-shell gap map must require no hidden authority": "no hidden authority",
        "operator-shell gap map must require no fake completion": "no fake completion",
        "operator-shell gap map must forbid raw JSON primary UI": (
            "no raw json as primary ui for operator-critical flows"
        ),
        "operator-shell gap map must name route status manifest gap": (
            "route status manifest"
        ),
        "operator-shell gap map must name GGUF selection gap": "gguf selection",
        "operator-shell gap map must name loopback llama.cpp settings gap": (
            "loopback llama.cpp settings"
        ),
        "operator-shell gap map must map /v1 models": "`get /v1/models`",
        "operator-shell gap map must map /v1 chat": "`post /v1/chat/completions`",
        "operator-shell gap map must map task classify": (
            "`post /task-decomposition/classify`"
        ),
        "operator-shell gap map must map bounded file preview": (
            "`post /files/read/preview`"
        ),
    }
    for message, fragment in required_fragments.items():
        if fragment not in compact:
            failures.append(message)
    for surface in REQUIRED_OPERATOR_SHELL_SURFACES:
        if f"| {surface.lower()} |" not in compact:
            failures.append(f"operator-shell gap map missing surface: {surface}")
    for unsafe in [
        "production ready for external users",
        "public distribution is available",
        "control center executes actions",
        "plugin runtime import is enabled",
        "connector writes are enabled",
    ]:
        if unsafe in lowered:
            failures.append(f"operator-shell gap map contains unsafe claim: {unsafe}")
    return failures


def _operator_surface_state_failures(root: Path) -> list[str]:
    failures: list[str] = []
    component_path = root / "apps/control-center/src/components/OperatorSurfaceStates.tsx"
    routes_path = root / "apps/control-center/src/routes.tsx"
    test_path = root / "apps/control-center/src/App.test.tsx"
    if not component_path.exists():
        return ["missing accessible operator surface states component"]

    component_text = component_path.read_text(encoding="utf-8")
    component_compact = " ".join(component_text.split())
    for fragment in OPERATOR_STATE_REQUIRED_COMPONENT_FRAGMENTS:
        if fragment not in component_text and fragment not in component_compact:
            failures.append(f"operator surface states component missing fragment: {fragment}")

    if routes_path.exists():
        routes_text = routes_path.read_text(encoding="utf-8")
        for route in ["/chat", "/plans", "/models", "/settings"]:
            if route not in routes_text:
                failures.append(f"operator surface route missing from routes.tsx: {route}")
    else:
        failures.append("missing Control Center routes.tsx")

    if test_path.exists():
        test_text = test_path.read_text(encoding="utf-8")
        for fragment in OPERATOR_STATE_REQUIRED_TEST_FRAGMENTS:
            if fragment not in test_text:
                failures.append(f"operator surface state test missing fragment: {fragment}")
    else:
        failures.append("missing Control Center App.test.tsx")

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


def _product_language_frontend_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    for phrase in PRODUCT_LANGUAGE_FORBIDDEN_FRONTEND_PHRASES:
        if phrase in text:
            failures.append(f"unsafe product language in {rel}: {phrase}")
    return failures


def _m15_review_field_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    m15_index = text.lower().find("m15review")
    if m15_index == -1:
        return failures
    m16_index = text.lower().find("m16trace", m15_index)
    m15_text = text[m15_index:m16_index] if m16_index != -1 else text[m15_index:]
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
    m17_index = text.lower().find("m17knowledge", m16_index)
    m16_text = text[m16_index:m17_index] if m17_index != -1 else text[m16_index:]
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
    m18_index = text.lower().find("m18runtime", m17_index)
    m17_text = text[m17_index:m18_index] if m18_index != -1 else text[m17_index:]
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
    m36_index = text.lower().find("m36filereview", m18_index)
    m18_text = text[m18_index:m36_index] if m36_index != -1 else text[m18_index:]
    for match in RAW_M18_RUNTIME_FIELD.finditer(m18_text):
        failures.append(f"raw M18 runtime field in {rel}: {match.group(0)}")
    for match in CREDENTIAL_M18_RUNTIME_FIELD.finditer(m18_text):
        failures.append(f"credential-like M18 runtime field in {rel}: {match.group(0)}")
    return failures


def _m36_file_review_fixture_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    m36_index = text.lower().find("m36filereview")
    if m36_index == -1:
        return failures
    m36_text = text[m36_index:]
    for match in M36_PRIVATE_OR_RAW_PATH_FRAGMENT.finditer(m36_text):
        failures.append(f"private path fragment in M36 file review fixture in {rel}: {match.group(0)}")

    for field_name, prefix in M36_SAFE_REF_PREFIXES.items():
        for match in re.finditer(rf"{field_name}\s*:\s*['\"]([^'\"]+)['\"]", m36_text):
            value = match.group(1)
            if not value.startswith(prefix):
                label = M36_SAFE_REF_LABELS[field_name]
                failures.append(f"unsafe M36 {label} value in {rel}: expected prefix {prefix}")
    return failures


def _m36_file_review_component_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    for match in M36_MUTATING_FILE_REVIEW_REQUEST.finditer(text):
        failures.append(f"mutating M36 file review request in {rel}: {match.group(0).strip()}")
    return failures


def _m39_context_proposal_fixture_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    m39_index = text.lower().find("m39contextproposals")
    if m39_index == -1:
        return failures
    m39_text = text[m39_index:]
    for match in M36_PRIVATE_OR_RAW_PATH_FRAGMENT.finditer(m39_text):
        failures.append(f"private path fragment in M39 context proposal fixture in {rel}: {match.group(0)}")

    for field_name, prefix in M39_SAFE_REF_PREFIXES.items():
        for match in re.finditer(rf"{field_name}\s*:\s*['\"]([^'\"]+)['\"]", m39_text):
            value = match.group(1)
            if not value.startswith(prefix):
                failures.append(f"unsafe M39 {field_name} value in {rel}: expected prefix {prefix}")
    return failures


def _m39_context_proposal_component_failures(rel: Path, text: str) -> list[str]:
    failures: list[str] = []
    for match in M39_MUTATING_CONTEXT_PROPOSAL_REQUEST.finditer(text):
        failures.append(f"mutating M39 context proposal request in {rel}: {match.group(0).strip()}")
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
