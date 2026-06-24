from __future__ import annotations

import re
from typing import Iterable, List

EXPECTED_M16_OPENAPI_PATH_COUNT = 78
M16_FORBIDDEN_BACKEND_ROUTES = (
    "/events/timeline",
    "/control-center/events/timeline",
    "/timeline",
    "/trace",
    "/trace/export",
    "/events/raw",
    "/telemetry/export",
)
EXPECTED_M17_OPENAPI_PATH_COUNT = 78
M17_FORBIDDEN_BACKEND_ROUTES = (
    "/evidence/raw",
    "/evidence/payload",
    "/files/content",
    "/files/write",
    "/files/delete",
    "/filesystem/browse",
    "/memory/raw",
    "/memory/content",
    "/memory/write",
    "/memory/delete",
    "/memory/learn",
    "/memory/forget",
    "/control-center/evidence/raw",
    "/control-center/files/write",
    "/control-center/memory/write",
)
EXPECTED_M18_OPENAPI_PATH_COUNT = 78
M18_FORBIDDEN_BACKEND_ROUTES = (
    "/runtime/smoke-reports/execute",
    "/runtime/local/execute",
    "/runtime/local/run",
    "/runtime/local/start",
    "/runtime/local/stop",
    "/runtime/local/connect",
    "/runtime/manual-smoke/execute",
    "/runtime/manual-smoke/run",
    "/model-runtime/local/smoke/execute",
    "/control-center/runtime/execute",
    "/control-center/runtime/connect",
)
EXPECTED_M19_OPENAPI_PATH_COUNT = 78
M19_FORBIDDEN_BACKEND_ROUTES = (
    "/mobile",
    "/mobile/manifest",
    "/mobile/register",
    "/mobile/pair",
    "/mobile/sensors",
    "/mobile/camera",
    "/mobile/microphone",
    "/mobile/location",
    "/mobile/notifications",
    "/mobile/capture",
    "/mobile/permissions",
    "/mobile/approvals/execute",
    "/mobile/approvals/approve",
    "/mobile/approvals/deny",
    "/device-capability-broker",
    "/device-capability-broker/capabilities",
    "/device-capabilities",
    "/device-capabilities/execute",
    "/control-center/mobile/sensors",
    "/control-center/mobile/capture",
)
EXPECTED_M20_OPENAPI_PATH_COUNT = 78
M20_FORBIDDEN_BACKEND_ROUTES = (
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
    "/mobile/sensors",
    "/mobile/camera",
    "/mobile/microphone",
    "/mobile/location",
    "/mobile/notifications",
    "/mobile/capture",
    "/mobile/pair",
    "/mobile/background-service",
)
EXPECTED_M21_OPENAPI_PATH_COUNT = 78
M21_FORBIDDEN_BACKEND_ROUTES = (
    "/openwebui",
    "/openwebui/bridge",
    "/openwebui/chat",
    "/openwebui/execute",
    "/openwebui/bridge/run",
    "/openwebui/admin",
    "/openwebui/config",
    "/chat/execute",
    "/chat/run",
    "/runtime/execute",
    "/model-runtime/execute",
)
EXPECTED_M22_OPENAPI_PATH_COUNT = 78
M22_FORBIDDEN_BACKEND_ROUTES = (
    "/runtime/activate",
    "/runtime/probe",
    "/runtime/local/activate",
    "/runtime/local/probe",
    "/runtime/local/call",
    "/runtime/local/generate",
    "/model-runtime/activate",
    "/model-runtime/probe",
    "/model-runtime/local/activate",
    "/model-runtime/local/probe",
    "/model-runtime/local/call",
    "/model-runtime/local/generate",
    "/model-runtime/execute",
)
EXPECTED_M23_OPENAPI_PATH_COUNT = 78
M23_FORBIDDEN_BACKEND_ROUTES = (
    "/runtime/local/call",
    "/runtime/local/generate",
    "/runtime/model-call",
    "/runtime/execute",
    "/model-runtime/local/call",
    "/model-runtime/local/generate",
    "/model-runtime/call",
    "/model-runtime/execute",
    "/local-model/call",
    "/local-model/generate",
    "/local-model/activate",
    "/openwebui/bridge/run",
    "/control-center/runtime/execute",
)
EXPECTED_M24_OPENAPI_PATH_COUNT = 78
M24_FORBIDDEN_BACKEND_ROUTES = (
    "/memory/write",
    "/memory/delete",
    "/memory/learn",
    "/memory/forget",
    "/memory/raw",
    "/memory/import",
    "/memory/ingest",
    "/memory/vector-search",
    "/memory/embed",
    "/memory/inject",
    "/memory/context-pack/inject",
    "/control-center/memory/write",
    "/control-center/memory/delete",
)
EXPECTED_M25_OPENAPI_PATH_COUNT = 78
M25_FORBIDDEN_BACKEND_ROUTES = (
    "/truth/verify",
    "/claims/verify",
    "/evidence/verify",
    "/truth/search",
    "/truth/web-search",
    "/truth/model-verify",
)
EXPECTED_M26_OPENAPI_PATH_COUNT = 78
M26_FORBIDDEN_BACKEND_ROUTES = (
    "/recall/run",
    "/recall/search",
    "/recall/inject",
    "/recall/vector-search",
    "/recall/embed",
    "/recall/external-retrieve",
    "/context-pack/inject",
    "/context-pack/build-and-inject",
    "/memory/vector-search",
    "/memory/embed",
    "/memory/context-pack/inject",
    "/control-center/recall/run",
    "/control-center/context-pack/inject",
)
EXPECTED_M27_OPENAPI_PATH_COUNT = 78
M27_FORBIDDEN_BACKEND_ROUTES = (
    "/tools/execute",
    "/tools/run",
    "/tools/dispatch",
    "/tool-broker/execute",
    "/tool-broker/run",
    "/plugins/enable",
    "/browser/execute",
    "/computer-use/run",
    "/context-pack/inject",
    "/context-pack/build-and-inject",
    "/memory/write",
    "/memory/inject",
    "/remote/execute",
)
EXPECTED_M28_OPENAPI_PATH_COUNT = 78
M28_FORBIDDEN_BACKEND_ROUTES = (
    "/actions/execute",
    "/actions/run",
    "/approval/execute",
    "/approval/run",
    "/approvals/execute",
    "/approvals/run",
    "/action-policy/execute",
    "/action-policy/run",
    "/tools/execute",
    "/tools/run",
    "/tool-broker/execute",
    "/tool-broker/run",
    "/plugins/enable",
    "/shell/execute",
    "/model/execute",
    "/network/execute",
    "/browser/execute",
    "/mobile/execute",
    "/remote/execute",
    "/control-center/actions/execute",
)
EXPECTED_M29_OPENAPI_PATH_COUNT = 78
M29_FORBIDDEN_BACKEND_ROUTES = (
    "/tasks/execute",
    "/tasks/run",
    "/tasks/schedule",
    "/plans/execute",
    "/plans/run",
    "/plans/schedule",
    "/planner/execute",
    "/planner/run",
    "/scheduler/run",
    "/actions/execute",
    "/tools/execute",
    "/plugins/enable",
    "/memory/write",
    "/model/execute",
    "/network/execute",
    "/browser/execute",
    "/mobile/execute",
    "/remote/execute",
)
EXPECTED_M30_OPENAPI_PATH_COUNT = 78
M30_FORBIDDEN_BACKEND_ROUTES = (
    "/execution/run",
    "/execution/execute",
    "/execution/advance",
    "/runs/execute",
    "/runs/run",
    "/tasks/execute",
    "/tasks/run",
    "/plans/execute",
    "/plans/run",
    "/planner/execute",
    "/planner/run",
    "/agent/run",
    "/workflow/execute",
    "/actions/execute",
    "/tools/execute",
    "/plugins/enable",
    "/memory/write",
    "/model/execute",
    "/network/execute",
    "/browser/execute",
    "/mobile/execute",
    "/remote/execute",
)
EXPECTED_M31_OPENAPI_PATH_COUNT = 78
M31_FORBIDDEN_BACKEND_ROUTES = (
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/tool-broker/execute",
    "/tool-broker/run",
    "/actions/execute",
    "/runs/execute",
    "/plugins/enable",
    "/shell/execute",
    "/model/execute",
    "/network/execute",
    "/browser/execute",
    "/mobile/execute",
    "/remote/execute",
)
EXPECTED_M32_OPENAPI_PATH_COUNT = 78
M32_FORBIDDEN_BACKEND_ROUTES = (
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/write",
    "/files/delete",
    "/filesystem/read",
    "/filesystem/write",
    "/filesystem/delete",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/plugins/enable",
)
EXPECTED_M33_OPENAPI_PATH_COUNT = 78
M33_FORBIDDEN_BACKEND_ROUTES = (
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/read/full",
    "/files/write",
    "/files/delete",
    "/filesystem/read",
    "/filesystem/write",
    "/filesystem/delete",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/plugins/enable",
)
EXPECTED_M34_OPENAPI_PATH_COUNT = 78
M34_FORBIDDEN_BACKEND_ROUTES = (
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/read/full",
    "/files/review",
    "/files/review/approve",
    "/files/review/submit",
    "/files/review/approvals/capture",
    "/files/write",
    "/files/delete",
    "/filesystem/read",
    "/filesystem/write",
    "/filesystem/delete",
    "/context/propose",
    "/context/inject",
    "/memory/write",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/plugins/enable",
)
EXPECTED_M35_OPENAPI_PATH_COUNT = 78
M35_FORBIDDEN_BACKEND_ROUTES = (
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/read/full",
    "/files/review",
    "/files/review/approve",
    "/files/review/submit",
    "/files/review/persist",
    "/files/review/approvals/capture",
    "/files/write",
    "/files/delete",
    "/files/export",
    "/filesystem/read",
    "/filesystem/write",
    "/filesystem/delete",
    "/context/propose",
    "/context/inject",
    "/memory/write",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/plugins/enable",
)
EXPECTED_M36_OPENAPI_PATH_COUNT = 78
M36_FORBIDDEN_BACKEND_ROUTES = (
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/read/full",
    "/files/review/approve",
    "/files/review/submit",
    "/files/review/approvals/capture",
    "/files/write",
    "/files/delete",
    "/filesystem/read",
    "/filesystem/write",
    "/filesystem/delete",
    "/context/propose",
    "/context/inject",
    "/memory/write",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/plugins/enable",
)
EXPECTED_M37_OPENAPI_PATH_COUNT = 79
M37_ALLOWED_CAPTURE_ROUTE = "/files/review/approvals/capture"
M37_FORBIDDEN_BACKEND_ROUTES = (
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/read/full",
    "/files/review/approve",
    "/files/review/submit",
    "/files/review/approvals/persist",
    "/files/write",
    "/files/delete",
    "/filesystem/read",
    "/filesystem/write",
    "/filesystem/delete",
    "/context/propose",
    "/context/inject",
    "/memory/write",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/plugins/enable",
)
EXPECTED_M38_OPENAPI_PATH_COUNT = 79
M38_FORBIDDEN_BACKEND_ROUTES = (
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/read/full",
    "/files/write",
    "/files/delete",
    "/filesystem/read",
    "/filesystem/write",
    "/filesystem/delete",
    "/context/propose",
    "/context/inject",
    "/context/handoff",
    "/openwebui/handoff",
    "/memory/write",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/plugins/enable",
)
EXPECTED_M39_OPENAPI_PATH_COUNT = 79
M39_FORBIDDEN_BACKEND_ROUTES = (
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/read/full",
    "/files/write",
    "/files/delete",
    "/filesystem/read",
    "/filesystem/write",
    "/filesystem/delete",
    "/context/propose",
    "/context/inject",
    "/context/handoff",
    "/openwebui/handoff",
    "/memory/write",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/plugins/enable",
)
EXPECTED_M40_OPENAPI_PATH_COUNT = 79
M40_FORBIDDEN_BACKEND_ROUTES = (
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/read/full",
    "/files/write",
    "/files/delete",
    "/filesystem/read",
    "/filesystem/write",
    "/filesystem/delete",
    "/context/propose",
    "/context/proposals/approve",
    "/context/proposals/submit",
    "/context/handoff",
    "/context/handoff/approve",
    "/context/handoff/submit",
    "/context/inject",
    "/openwebui/handoff",
    "/memory/write",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/plugins/enable",
)
EXPECTED_M41_OPENAPI_PATH_COUNT = 79
M41_FORBIDDEN_BACKEND_ROUTES = (
    "/files/read",
    "/files/read/raw",
    "/files/read/content",
    "/files/read/full",
    "/files/export",
    "/files/write",
    "/files/delete",
    "/filesystem/read",
    "/filesystem/write",
    "/filesystem/delete",
    "/context/propose",
    "/context/proposals/approve",
    "/context/proposals/submit",
    "/context/handoff",
    "/context/handoff/approve",
    "/context/handoff/submit",
    "/context/inject",
    "/openwebui/handoff",
    "/memory/write",
    "/browser/execute",
    "/browser/run",
    "/remote/execute",
    "/remote/run",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-runtime/run",
    "/plugins/enable",
)
EXPECTED_M42_OPENAPI_PATH_COUNT = 79
M42_FORBIDDEN_BACKEND_ROUTES = M41_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile",
    "/mobile/manifest",
    "/mobile/api",
    "/mobile/register",
    "/mobile/pair",
    "/mobile/sensors",
    "/mobile/camera",
    "/mobile/microphone",
    "/mobile/location",
    "/mobile/notifications",
    "/mobile/capture",
    "/mobile/permissions",
    "/mobile/approvals/capture",
    "/mobile/approvals/execute",
    "/mobile/approvals/approve",
    "/mobile/approvals/deny",
    "/control-center/mobile",
    "/control-center/mobile/sensors",
    "/control-center/mobile/capture",
)
EXPECTED_M43_OPENAPI_PATH_COUNT = 79
M43_FORBIDDEN_BACKEND_ROUTES = M42_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/api/read",
    "/mobile/api/write",
    "/mobile/api/mutate",
    "/mobile/files",
    "/mobile/files/raw",
    "/mobile/files/read",
    "/mobile/files/content",
    "/mobile/raw-data",
    "/mobile/raw-payload",
    "/mobile/context",
    "/mobile/context/inject",
    "/mobile/memory/write",
    "/mobile/export",
    "/mobile/download",
    "/mobile/execute",
    "/mobile/tools/execute",
    "/mobile/plugins/execute",
)
EXPECTED_M44_OPENAPI_PATH_COUNT = 79
M44_FORBIDDEN_BACKEND_ROUTES = M43_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/app/build",
    "/mobile/ios",
    "/mobile/ios/build",
    "/mobile/ios/sign",
    "/mobile/ios/provision",
    "/mobile/ios/testflight",
    "/mobile/ios/sensors",
    "/mobile/ios/permissions",
    "/mobile/ios/background",
    "/mobile/ios/network",
    "/mobile/ios/approvals/capture",
    "/mobile/ios/approvals/execute",
    "/mobile/ios/context/inject",
    "/mobile/ios/memory/write",
    "/mobile/ios/files/raw",
    "/mobile/ios/export",
    "/mobile/ios/execute",
)
M44_FORBIDDEN_SWIFT_FRAGMENTS = (
    "URLSession",
    "Alamofire",
    "CLLocationManager",
    "AVCapture",
    "PHPhoto",
    "Contacts",
    "EventKit",
    "UserNotifications",
    "Keychain",
    "SecItem",
    "FileManager.default",
    "Process(",
    "WKWebView",
    "approvalCapture",
    "approvalExecution",
    "contextInjection",
    "memoryWrite",
)
EXPECTED_M45_OPENAPI_PATH_COUNT = 79
M45_FORBIDDEN_BACKEND_ROUTES = M44_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/ios/connection",
    "/mobile/ios/connect",
    "/mobile/ios/status/live",
    "/mobile/ios/sync",
    "/mobile/ios/poll",
    "/mobile/ios/collect",
    "/mobile/ios/approvals",
    "/mobile/ios/raw-data",
    "/mobile/ios/background",
)
M45_FORBIDDEN_SWIFT_FRAGMENTS = M44_FORBIDDEN_SWIFT_FRAGMENTS + (
    "URLRequest",
    "NWConnection",
    "backgroundTask",
)
EXPECTED_M46_OPENAPI_PATH_COUNT = 79
M46_FORBIDDEN_BACKEND_ROUTES = M45_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/ios/review-receipts",
    "/mobile/ios/reviews",
    "/mobile/ios/receipts",
    "/mobile/ios/review-receipts/live",
    "/mobile/ios/review-receipts/sync",
    "/mobile/ios/approvals/capture",
    "/mobile/ios/approvals/execute",
    "/mobile/ios/raw-data",
    "/mobile/ios/export",
    "/mobile/ios/background",
    "/mobile/ios/sensors",
    "/mobile/ios/testflight",
)
M46_FORBIDDEN_SWIFT_FRAGMENTS = M45_FORBIDDEN_SWIFT_FRAGMENTS + (
    "approvalCapture",
    "approvalExecution",
    "contextInjection",
    "memoryWrite",
    "ExportOptions",
)
EXPECTED_M47_OPENAPI_PATH_COUNT = 79
M47_FORBIDDEN_BACKEND_ROUTES = M46_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/ios/testflight/build",
    "/mobile/ios/testflight/upload",
    "/mobile/ios/testflight/distribute",
    "/mobile/ios/testflight/invite",
    "/mobile/ios/signing/assets",
    "/mobile/ios/signing/certificates",
    "/mobile/ios/provisioning-profiles",
    "/mobile/ios/app-store-connect",
    "/mobile/ios/app-store-connect/upload",
    "/mobile/ios/production",
)
M47_FORBIDDEN_SWIFT_FRAGMENTS = M46_FORBIDDEN_SWIFT_FRAGMENTS + (
    "AppStoreConnect",
    "TestFlightUpload",
    "xcodebuild",
    "altool",
    "notarytool",
)
EXPECTED_M48_OPENAPI_PATH_COUNT = 79
M48_FORBIDDEN_BACKEND_ROUTES = M47_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/ios/testflight/build/candidate",
    "/mobile/ios/testflight/builds",
    "/mobile/ios/testflight/upload/status",
    "/mobile/ios/testflight/artifacts",
    "/mobile/ios/signing/assets/upload",
    "/mobile/ios/signing/identities",
    "/mobile/ios/app-store-connect/upload",
    "/app-store-connect/upload",
    "/testflight/upload",
)
M48_FORBIDDEN_SWIFT_FRAGMENTS = M47_FORBIDDEN_SWIFT_FRAGMENTS + (
    "XCArchive",
    ".ipa",
    "mobileprovision",
    "App Store Connect",
)
EXPECTED_M49_OPENAPI_PATH_COUNT = 79
M49_FORBIDDEN_BACKEND_ROUTES = M48_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/review",
    "/mobile/review/approve",
    "/mobile/review/deny",
    "/mobile/review/submit",
    "/mobile/review/approvals",
    "/mobile/review/approvals/capture",
    "/mobile/review/approvals/execute",
    "/mobile/review/approvals/persist",
    "/mobile/approvals/capture",
    "/mobile/approvals/execute",
    "/mobile/context/propose",
    "/mobile/context/inject",
    "/mobile/memory/write",
    "/mobile/export",
    "/mobile/download",
    "/mobile/tools/execute",
    "/mobile/sensors",
    "/mobile/background",
)
M49_FORBIDDEN_SWIFT_FRAGMENTS = M48_FORBIDDEN_SWIFT_FRAGMENTS + (
    "MobileReviewApprovalCapture",
    "approvalCapture",
    "approvalExecution",
    "contextProposal",
    "contextInjection",
    "memoryWrite",
    "exportReview",
    "SensorAccess",
    "BackgroundCollection",
)
EXPECTED_M50_OPENAPI_PATH_COUNT = 79
M50_FORBIDDEN_BACKEND_ROUTES = M49_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/review/audit",
    "/mobile/review/audit/export",
    "/mobile/review/audit/raw",
    "/mobile/review/audit/write",
    "/mobile/approvals/audit",
    "/mobile/approvals/audit/write",
    "/mobile/approvals/audit/export",
    "/mobile/audit/export",
)
M50_FORBIDDEN_SWIFT_FRAGMENTS = M49_FORBIDDEN_SWIFT_FRAGMENTS + (
    "MobileApprovalAudit",
    "approvalAuditExport",
    "auditRaw",
    "auditWrite",
)
EXPECTED_M51_OPENAPI_PATH_COUNT = 79
M51_FORBIDDEN_BACKEND_ROUTES = (
    "/openwebui/handoff",
    "/openwebui/runtime/call",
    "/openwebui/provider/call",
    "/openwebui/model/call",
    "/openwebui/tools/execute",
    "/openwebui/memory/write",
    "/openwebui/context/inject",
    "/openwebui/raw-payload",
    "/openwebui/raw-prompt",
    "/openwebui/provider-payload",
)
EXPECTED_M52_OPENAPI_PATH_COUNT = 79
M52_FORBIDDEN_BACKEND_ROUTES = M51_FORBIDDEN_BACKEND_ROUTES + (
    "/openwebui/conversation",
    "/openwebui/conversation/send",
    "/openwebui/conversation/raw",
    "/openwebui/conversation/provider-payload",
    "/openwebui/conversation/context",
    "/openwebui/conversation/memory",
)
EXPECTED_M53_OPENAPI_PATH_COUNT = 79
M53_FORBIDDEN_BACKEND_ROUTES = M52_FORBIDDEN_BACKEND_ROUTES + (
    "/tools/expand",
    "/tools/register",
    "/tools/enable",
    "/tools/run",
    "/tools/execute",
    "/shell/execute",
    "/network/request",
    "/provider/call",
    "/models/call",
    "/browser/click",
    "/plugins/enable",
    "/memory/write",
    "/context/inject",
)
EXPECTED_M54_OPENAPI_PATH_COUNT = 79
M54_FORBIDDEN_BACKEND_ROUTES = M53_FORBIDDEN_BACKEND_ROUTES + (
    "/media/read/raw",
    "/media/read/content",
    "/media/read/full",
    "/media/full-read",
    "/media/export",
    "/media/download",
    "/media/original",
    "/media/write",
    "/media/delete",
    "/media/transform",
    "/media/transform/ocio",
    "/media/gamut/expand",
    "/media/ai/gamut",
    "/media/model/analyze",
)
EXPECTED_M55_OPENAPI_PATH_COUNT = 79
M55_FORBIDDEN_BACKEND_ROUTES = M54_FORBIDDEN_BACKEND_ROUTES + (
    "/observability/export",
    "/observability/export/raw",
    "/observability/export/prompts",
    "/observability/export/provider-payloads",
    "/observability/export/secrets",
    "/observability/export/saas",
    "/observability/export/network",
    "/otel/export",
    "/analytics/export",
)
EXPECTED_M56_OPENAPI_PATH_COUNT = 79
M56_FORBIDDEN_BACKEND_ROUTES = M55_FORBIDDEN_BACKEND_ROUTES + (
    "/evals/run",
    "/evals/execute",
    "/evals/model-call",
    "/evals/provider-call",
    "/evals/tool-execute",
    "/evals/export/raw",
    "/evals/export/prompts",
    "/evals/export/provider-payloads",
    "/models/call",
    "/provider/call",
)
EXPECTED_M57_OPENAPI_PATH_COUNT = 79
M57_FORBIDDEN_BACKEND_ROUTES = M56_FORBIDDEN_BACKEND_ROUTES + (
    "/sandbox/run",
    "/sandbox/execute",
    "/sandbox/subprocess",
    "/sandbox/process",
    "/process/spawn",
    "/subprocess/run",
    "/runtime/sandbox/run",
    "/runtime/sandbox/execute",
)
EXPECTED_M58_OPENAPI_PATH_COUNT = 79
M58_FORBIDDEN_BACKEND_ROUTES = M57_FORBIDDEN_BACKEND_ROUTES + (
    "/dry-run/run",
    "/dry-run/execute",
    "/dry-run/audit/run",
    "/dry-run/audit/execute",
    "/execution/audit/run",
    "/execution/audit/execute",
    "/execution/dry-run/run",
    "/execution/dry-run/execute",
)
EXPECTED_M59_OPENAPI_PATH_COUNT = 79
M59_FORBIDDEN_BACKEND_ROUTES = M58_FORBIDDEN_BACKEND_ROUTES + (
    "/github/publish",
    "/github/release",
    "/github/wiki/update",
    "/github/wiki/publish",
    "/public/artifacts/upload",
    "/public/release/publish",
    "/public/github/publish",
    "/release/upload",
)
EXPECTED_M60_OPENAPI_PATH_COUNT = 79
M60_FORBIDDEN_BACKEND_ROUTES = M59_FORBIDDEN_BACKEND_ROUTES + (
    "/public/beta/release",
    "/public/beta/publish",
    "/beta/release",
    "/beta/publish",
    "/release/public",
    "/production/enable",
    "/autonomy/enable",
    "/autonomy/run",
    "/post-m60/autonomy",
    "/tool-runtime/execute",
    "/plugins/execute",
    "/remote/execute",
)
EXPECTED_M61_OPENAPI_PATH_COUNT = 79
M61_FORBIDDEN_BACKEND_ROUTES = M60_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/session/start",
    "/autonomy/session/run",
    "/autonomy/execute",
    "/autonomy/authority/enable",
    "/autonomy/toggle/enable",
    "/background/start",
    "/background/run",
    "/network/fetch",
    "/network/request",
)
EXPECTED_M62_OPENAPI_PATH_COUNT = 79
M62_FORBIDDEN_BACKEND_ROUTES = M61_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/session/activate",
    "/autonomy/session/execute",
    "/autonomy/session/stop",
    "/autonomy/session/status",
    "/autonomy/session/background",
    "/autonomy/session/approval",
    "/autonomy/session/persist",
)
EXPECTED_M63_OPENAPI_PATH_COUNT = 79
M63_FORBIDDEN_BACKEND_ROUTES = M62_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/policy/evaluate",
    "/autonomy/policy/activate",
    "/autonomy/policy/run",
    "/autonomy/policy/execute",
    "/autonomy/policy/persist",
)
EXPECTED_M64_OPENAPI_PATH_COUNT = 79
M64_FORBIDDEN_BACKEND_ROUTES = M63_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/simulate",
    "/autonomy/simulator/run",
    "/autonomy/simulator/execute",
    "/autonomy/plan/simulate",
    "/autonomy/plan/execute",
)
EXPECTED_M65_OPENAPI_PATH_COUNT = 79
M65_FORBIDDEN_BACKEND_ROUTES = M64_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/audit/replay",
    "/autonomy/replay/run",
    "/autonomy/replay/execute",
    "/autonomy/audit/export",
    "/autonomy/replay/export",
)
EXPECTED_M66_OPENAPI_PATH_COUNT = 79
M66_FORBIDDEN_BACKEND_ROUTES = M65_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/approval-bundles",
    "/autonomy/approval-bundles/grant",
    "/autonomy/approval-bundles/activate",
    "/autonomy/approval-bundles/execute",
    "/autonomy/approval-bundles/export",
)
EXPECTED_M67_OPENAPI_PATH_COUNT = 79
M67_FORBIDDEN_BACKEND_ROUTES = M66_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/revoke",
    "/autonomy/revocation/execute",
    "/autonomy/kill-switch",
    "/autonomy/kill-switch/activate",
    "/autonomy/session/stop",
    "/autonomy/session/terminate",
    "/process/kill",
)
EXPECTED_M68_OPENAPI_PATH_COUNT = 79
M68_FORBIDDEN_BACKEND_ROUTES = M67_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/risk/classify",
    "/autonomy/risk/execute",
    "/autonomy/risk/activate",
    "/autonomy/session/start",
    "/autonomy/policy/activate",
)
EXPECTED_M69_OPENAPI_PATH_COUNT = 79
M69_FORBIDDEN_BACKEND_ROUTES = M68_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/dry-run/start",
    "/autonomy/dry-run/execute",
    "/autonomy/dry-run/activate",
    "/autonomy/dry-run/persist",
    "/autonomy/dry-run/session",
)
EXPECTED_M70_OPENAPI_PATH_COUNT = 79
M70_FORBIDDEN_BACKEND_ROUTES = M69_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/freeze/activate",
    "/autonomy/freeze/start",
    "/autonomy/foundation/activate",
    "/autonomy/session/start",
    "/autonomy/policy/activate",
    "/autonomy/dry-run/execute",
    "/autonomy/dry-run/start",
    "/context/inject",
    "/memory/write",
    "/tools/execute",
    "/shell/execute",
    "/browser/click",
    "/plugins/execute",
)
EXPECTED_M71_OPENAPI_PATH_COUNT = 79
M71_FORBIDDEN_BACKEND_ROUTES = M70_FORBIDDEN_BACKEND_ROUTES + (
    "/network/fetch",
    "/network/request",
    "/http/fetch",
    "/http/request",
    "/tools/network/execute",
    "/network/tools/execute",
    "/network/tools/review",
    "/tools/execute",
    "/tool-runtime/execute",
    "/browser/click",
    "/plugins/execute",
    "/memory/write",
    "/context/inject",
)
EXPECTED_M72_OPENAPI_PATH_COUNT = 79
M72_FORBIDDEN_BACKEND_ROUTES = M71_FORBIDDEN_BACKEND_ROUTES + (
    "/network/fetch/raw",
    "/network/fetch/full",
    "/network/request/authenticated",
    "/http/fetch/raw",
    "/http/fetch/full",
    "/http/request/authenticated",
)
EXPECTED_M73_OPENAPI_PATH_COUNT = 79
M73_FORBIDDEN_BACKEND_ROUTES = M72_FORBIDDEN_BACKEND_ROUTES + (
    "/browser/observe",
    "/browser/click",
    "/browser/navigate",
    "/browser/type",
    "/browser/screenshot",
    "/browser/execute",
    "/browser/run",
    "/browser/session/start",
    "/browser/profile/authenticated",
    "/tools/browser/execute",
)
EXPECTED_M74_OPENAPI_PATH_COUNT = 79
M74_FORBIDDEN_BACKEND_ROUTES = M73_FORBIDDEN_BACKEND_ROUTES + (
    "/browser/dom/raw",
    "/browser/download",
    "/browser/upload",
    "/browser/network/intercept",
)
EXPECTED_M75_OPENAPI_PATH_COUNT = 79
M75_FORBIDDEN_BACKEND_ROUTES = M74_FORBIDDEN_BACKEND_ROUTES + (
    "/browser/actions/plan",
    "/browser/actions/run",
    "/browser/actions/execute",
    "/browser/action/dry-run",
    "/browser/action/execute",
)
EXPECTED_M76_OPENAPI_PATH_COUNT = 79
M76_FORBIDDEN_BACKEND_ROUTES = M75_FORBIDDEN_BACKEND_ROUTES + (
    "/openwebui/runtime/bridge",
    "/openwebui/runtime/handoff",
    "/openwebui/runtime/execute",
    "/openwebui/chat/send",
    "/openwebui/model/call",
    "/openwebui/provider/call",
    "/openwebui/tools/execute",
    "/openwebui/memory/write",
    "/openwebui/context/inject",
    "/openwebui/raw-payload",
)
EXPECTED_M77_OPENAPI_PATH_COUNT = 79
M77_FORBIDDEN_BACKEND_ROUTES = M76_FORBIDDEN_BACKEND_ROUTES + (
    "/openwebui/handoff/execute",
)
EXPECTED_M78_OPENAPI_PATH_COUNT = 79
M78_FORBIDDEN_BACKEND_ROUTES = M77_FORBIDDEN_BACKEND_ROUTES + (
    "/plugins/install",
    "/plugins/enable",
    "/plugins/execute",
    "/plugin-runtime/import",
    "/plugin-runtime/execute",
    "/plugins/permissions/grant",
    "/plugins/revoke/execute",
)
EXPECTED_M79_OPENAPI_PATH_COUNT = 79
M79_FORBIDDEN_BACKEND_ROUTES = M78_FORBIDDEN_BACKEND_ROUTES + (
    "/plugins/review/install/submit",
    "/plugins/review/install/approve",
    "/plugins/review/install/execute",
    "/plugins/install/review/submit",
    "/plugins/install/perform",
)
EXPECTED_M80_OPENAPI_PATH_COUNT = 79
M80_FORBIDDEN_BACKEND_ROUTES = M79_FORBIDDEN_BACKEND_ROUTES + (
    "/network/fetch/unrestricted",
    "/network/fetch/raw",
    "/network/post",
    "/network/write",
    "/browser/navigate",
    "/browser/click",
    "/browser/screenshot",
    "/browser/dom/raw",
    "/openwebui/tools/execute",
    "/openwebui/context/inject",
    "/openwebui/memory/write",
    "/openwebui/model/authority",
    "/openwebui/raw-prompt",
    "/openwebui/raw-provider-payload",
    "/plugins/install",
    "/plugins/enable",
    "/plugins/execute",
    "/plugin-runtime/import",
    "/plugin-runtime/execute",
    "/tools/execute",
    "/shell/execute",
)
EXPECTED_M81_OPENAPI_PATH_COUNT = 79
M81_FORBIDDEN_BACKEND_ROUTES = M80_FORBIDDEN_BACKEND_ROUTES + (
    "/sandbox/run",
    "/sandbox/execute",
    "/sandbox/start",
    "/sandbox/spawn",
    "/commands/propose",
    "/commands/execute",
    "/process/spawn",
    "/filesystem/write",
    "/filesystem/mutate",
    "/remote/execute",
)
EXPECTED_M82_OPENAPI_PATH_COUNT = 79
M82_FORBIDDEN_BACKEND_ROUTES = M81_FORBIDDEN_BACKEND_ROUTES
EXPECTED_M83_OPENAPI_PATH_COUNT = 79
M83_FORBIDDEN_BACKEND_ROUTES = M82_FORBIDDEN_BACKEND_ROUTES + (
    "/shell/dry-run/classify",
    "/shell/dry-run/execute",
)
EXPECTED_M84_OPENAPI_PATH_COUNT = 79
M84_FORBIDDEN_BACKEND_ROUTES = M83_FORBIDDEN_BACKEND_ROUTES + (
    "/sandbox/echo",
    "/sandbox/noop",
    "/sandbox/commands/run",
    "/sandbox/commands/execute",
)
EXPECTED_M85_OPENAPI_PATH_COUNT = 79
M85_FORBIDDEN_BACKEND_ROUTES = M84_FORBIDDEN_BACKEND_ROUTES + (
    "/commands/allowlist",
    "/commands/allowlist/review",
    "/commands/allowlist/execute",
    "/sandbox/allowlist",
)
EXPECTED_M86_OPENAPI_PATH_COUNT = 79
M86_FORBIDDEN_BACKEND_ROUTES = M85_FORBIDDEN_BACKEND_ROUTES + (
    "/shell/approval",
    "/shell/approval/review",
    "/shell/approval/execute",
)
EXPECTED_M87_OPENAPI_PATH_COUNT = 79
M87_FORBIDDEN_BACKEND_ROUTES = M86_FORBIDDEN_BACKEND_ROUTES + (
    "/shell/replay",
    "/shell/replay/run",
    "/shell/replay/execute",
    "/commands/audit/replay",
    "/commands/audit/replay/run",
    "/sandbox/commands/replay",
)
EXPECTED_M88_OPENAPI_PATH_COUNT = 79
M88_FORBIDDEN_BACKEND_ROUTES = M87_FORBIDDEN_BACKEND_ROUTES + (
    "/commands/mutate",
    "/commands/mutate/propose",
    "/commands/mutate/run",
    "/commands/mutate/execute",
    "/sandbox/commands/mutate",
)
EXPECTED_M89_OPENAPI_PATH_COUNT = 79
M89_FORBIDDEN_BACKEND_ROUTES = M88_FORBIDDEN_BACKEND_ROUTES + (
    "/emergency/stop",
    "/emergency/kill",
    "/process/kill",
    "/process/signal",
    "/process/terminate",
    "/process/spawn",
    "/commands/execute",
    "/shell/execute",
    "/filesystem/write",
)
EXPECTED_M90_OPENAPI_PATH_COUNT = 79
M90_FORBIDDEN_BACKEND_ROUTES = M89_FORBIDDEN_BACKEND_ROUTES + (
    "/subprocess/execute",
    "/subprocess/run",
    "/shell/run",
    "/shell/subprocess",
    "/commands/run",
    "/process/terminate",
    "/emergency/execute",
)
EXPECTED_M91_OPENAPI_PATH_COUNT = 79
M91_FORBIDDEN_BACKEND_ROUTES = M90_FORBIDDEN_BACKEND_ROUTES + (
    "/tools/execute",
    "/tool-runtime/execute",
    "/autonomy/tools/execute",
    "/autonomy/tools/run",
    "/autonomy/session/start",
    "/autonomy/session/execute",
    "/tools/autonomous/execute",
)
EXPECTED_M92_OPENAPI_PATH_COUNT = 79
M92_FORBIDDEN_BACKEND_ROUTES = M91_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/session/run",
    "/autonomy/sessions",
)
EXPECTED_M93_OPENAPI_PATH_COUNT = 79
M93_FORBIDDEN_BACKEND_ROUTES = M92_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/promotion/approve",
    "/autonomy/promotion/execute",
    "/autonomy/promotion/run",
    "/autonomy/real-run/execute",
    "/autonomy/real-run/run",
    "/autonomy/dry-run/promote",
    "/tools/multi/execute",
)
EXPECTED_M94_OPENAPI_PATH_COUNT = 79
M94_FORBIDDEN_BACKEND_ROUTES = M93_FORBIDDEN_BACKEND_ROUTES + (
    "/browser/click",
    "/browser/form-submit",
    "/browser/download",
    "/browser/auth",
    "/browser/purchase",
    "/browser/upload",
    "/browser/type",
    "/autonomy/browser/click",
    "/autonomy/browser/run",
    "/tools/browser/execute",
)
EXPECTED_M95_OPENAPI_PATH_COUNT = 79
M95_FORBIDDEN_BACKEND_ROUTES = M94_FORBIDDEN_BACKEND_ROUTES + (
    "/network/get",
    "/network/fetch",
    "/network/request",
    "/network/post",
    "/network/put",
    "/network/patch",
    "/network/delete",
    "/network/auth",
    "/network/account",
    "/network/download",
    "/http/fetch",
    "/http/request",
    "/http/post",
    "/tools/network/execute",
    "/autonomy/network/execute",
)
EXPECTED_M96_OPENAPI_PATH_COUNT = 79
M96_FORBIDDEN_BACKEND_ROUTES = M95_FORBIDDEN_BACKEND_ROUTES + (
    "/plugins/execute",
    "/plugins/run",
    "/plugins/load",
    "/plugins/install",
    "/plugins/marketplace",
    "/plugin-runtime/execute",
    "/plugin-runtime/load",
    "/tools/plugins/execute",
    "/autonomy/plugins/execute",
)
EXPECTED_M97_OPENAPI_PATH_COUNT = 79
M97_FORBIDDEN_BACKEND_ROUTES = M96_FORBIDDEN_BACKEND_ROUTES + (
    "/automation/recurring/run",
    "/automation/recurring/start",
    "/automation/recurring/execute",
    "/automation/recurring/worker",
    "/automation/recurring/schedule",
    "/scheduler/start",
    "/scheduler/run",
    "/cron/run",
    "/cron/start",
    "/background-worker/start",
    "/background-worker/run",
)
EXPECTED_M98_OPENAPI_PATH_COUNT = 79
M98_FORBIDDEN_BACKEND_ROUTES = M97_FORBIDDEN_BACKEND_ROUTES + (
    "/automation/recurring/collect",
    "/automation/recurring/worker",
    "/automation/recurring/daemon",
    "/automation/recurring/scheduler",
    "/automation/recurring/approve-run",
    "/automation/recurring/mutate",
    "/automation/recurring/secrets",
)
EXPECTED_M99_OPENAPI_PATH_COUNT = 79
M99_FORBIDDEN_BACKEND_ROUTES = M98_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/global/enable",
    "/autonomy/global/autonomous",
    "/autonomy/run",
    "/autonomy/execute",
    "/autonomy/tools/execute",
    "/autonomy/browser/click",
    "/autonomy/network/post",
    "/autonomy/plugins/execute",
    "/browser/form-submit",
    "/network/post",
    "/mobile/sensors",
    "/mobile/background/collect",
    "/files/export/raw",
    "/files/read/full",
)
EXPECTED_M100_OPENAPI_PATH_COUNT = 79
M100_FORBIDDEN_BACKEND_ROUTES = M99_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/location",
    "/mobile/camera",
    "/mobile/photos",
    "/mobile/microphone",
    "/mobile/background/collect",
    "/mobile/push/execute",
    "/mobile/permissions/request",
    "/mobile/permissions/grant",
    "/mobile/permissions/prompt",
    "/mobile/native-permissions/request",
)
EXPECTED_M101_OPENAPI_PATH_COUNT = 79
M101_FORBIDDEN_BACKEND_ROUTES = M100_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/sensors/location",
    "/mobile/sensors/camera",
    "/mobile/sensors/photos",
    "/mobile/sensors/microphone",
    "/mobile/sensors/permission-state",
    "/mobile/sensors/audit",
    "/mobile/sensors/collect",
    "/mobile/sensors/runtime",
)
EXPECTED_M102_OPENAPI_PATH_COUNT = 79
M102_FORBIDDEN_BACKEND_ROUTES = M101_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/location/current",
    "/mobile/location/history",
    "/mobile/location/geofence",
    "/mobile/location/export",
    "/mobile/background/location",
    "/mobile/location/permission",
)
EXPECTED_M103_OPENAPI_PATH_COUNT = 79
M103_FORBIDDEN_BACKEND_ROUTES = M102_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/camera",
    "/mobile/camera/capture",
    "/mobile/photos",
    "/mobile/photos/read",
    "/mobile/photos/export",
    "/mobile/media/raw",
    "/mobile/media/export",
    "/mobile/background/media",
    "/mobile/media/metadata/extract",
    "/mobile/media/permission",
)
EXPECTED_M104_OPENAPI_PATH_COUNT = 79
M104_FORBIDDEN_BACKEND_ROUTES = M103_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/notifications",
    "/mobile/notifications/send",
    "/mobile/notifications/push",
    "/mobile/notifications/schedule",
    "/mobile/notifications/token",
    "/mobile/notifications/provider",
    "/mobile/background/tasks",
    "/mobile/background/notifications",
    "/mobile/permissions/prompt",
)
EXPECTED_M105_OPENAPI_PATH_COUNT = 79
M105_FORBIDDEN_BACKEND_ROUTES = M104_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/background/tasks/start",
    "/mobile/background/tasks/schedule",
    "/mobile/background/workers",
    "/mobile/background/daemon",
    "/mobile/background/runtime",
    "/mobile/background/execute",
    "/mobile/permissions/background/prompt",
    "/mobile/background/tokens",
    "/mobile/background/provider",
)
EXPECTED_M106_OPENAPI_PATH_COUNT = 79
M106_FORBIDDEN_BACKEND_ROUTES = M105_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/background/status-sync",
    "/mobile/background/status-sync/start",
    "/mobile/background/status-sync/schedule",
    "/mobile/background/status-sync/push",
    "/mobile/background/status-sync/network",
    "/mobile/background/status-sync/raw",
    "/mobile/background/fetch",
    "/mobile/background/status",
    "/mobile/background/status/raw",
)
EXPECTED_M107_OPENAPI_PATH_COUNT = 79
M107_FORBIDDEN_BACKEND_ROUTES = M106_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/approvals/renew",
    "/mobile/approvals/renew/start",
    "/mobile/approvals/renew/capture",
    "/mobile/approvals/renew/persist",
    "/mobile/approvals/renew/prompt",
    "/mobile/approvals/renew/execute",
    "/mobile/approvals/kill-switch",
    "/mobile/revocation/execute",
)
EXPECTED_M108_OPENAPI_PATH_COUNT = 79
M108_FORBIDDEN_BACKEND_ROUTES = M107_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/kill-switch",
    "/mobile/kill-switch/activate",
    "/mobile/kill-switch/execute",
    "/mobile/revocation",
    "/mobile/approvals/revoke",
    "/mobile/session/stop",
)
EXPECTED_M109_OPENAPI_PATH_COUNT = 79
M109_FORBIDDEN_BACKEND_ROUTES = M108_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/sensor-audit",
    "/mobile/sensor-audit/write",
    "/mobile/sensor-audit/raw",
    "/mobile/sensors/location",
    "/mobile/sensors/camera",
    "/mobile/sensors/photos",
    "/mobile/sensors/microphone",
    "/mobile/background/collect",
)
EXPECTED_M110_OPENAPI_PATH_COUNT = 79
M110_FORBIDDEN_BACKEND_ROUTES = M109_FORBIDDEN_BACKEND_ROUTES + (
    "/mobile/sensor-hardening",
    "/mobile/sensor-hardening/run",
    "/mobile/sensor-hardening/freeze",
    "/mobile/sensor-hardening/execute",
)
EXPECTED_M111_OPENAPI_PATH_COUNT = 79
M111_FORBIDDEN_BACKEND_ROUTES = M110_FORBIDDEN_BACKEND_ROUTES + (
    "/production/threat-model",
    "/production/threat-model/run",
    "/production/threat-model/approve",
    "/production/runtime",
    "/production/authority",
    "/production/deploy",
    "/credentials/read",
)
EXPECTED_M112_OPENAPI_PATH_COUNT = 79
M112_FORBIDDEN_BACKEND_ROUTES = M111_FORBIDDEN_BACKEND_ROUTES + (
    "/identity/user",
    "/identity/workspace",
    "/identity/session",
    "/identity/login",
    "/identity/persist",
    "/identity/auth",
    "/identity/account",
)
EXPECTED_M113_OPENAPI_PATH_COUNT = 79
M113_FORBIDDEN_BACKEND_ROUTES = M112_FORBIDDEN_BACKEND_ROUTES + (
    "/credentials/write",
    "/credentials/vault",
    "/credentials/vault/read",
    "/credentials/vault/write",
    "/credentials/vault/store",
    "/credentials/vault/export",
    "/secrets/read",
    "/secrets/write",
    "/secrets/export",
    "/vault/runtime",
    "/vault/unlock",
)
EXPECTED_M114_OPENAPI_PATH_COUNT = 79
M114_FORBIDDEN_BACKEND_ROUTES = M113_FORBIDDEN_BACKEND_ROUTES + (
    "/accounts/connect",
    "/accounts/oauth/start",
    "/accounts/oauth/callback",
    "/accounts/oauth/token",
    "/accounts/session",
    "/accounts/credentials",
    "/connectors/accounts/read",
    "/connectors/accounts/write",
    "/connectors/accounts/auth",
    "/connectors/accounts/connect",
    "/connectors/accounts/action",
    "/connectors/accounts/execute",
    "/connectors/accounts/export",
    "/credentials/read",
    "/credentials/write",
    "/context/inject",
    "/memory/write",
    "/tools/execute",
)
EXPECTED_M115_OPENAPI_PATH_COUNT = 79
M115_FORBIDDEN_BACKEND_ROUTES = M114_FORBIDDEN_BACKEND_ROUTES + (
    "/audit/retention",
    "/audit/export",
    "/audit/logs/raw",
    "/audit/logs/read",
    "/audit/store",
    "/audit/store/write",
    "/audit/retention/apply",
    "/logs/export",
    "/logs/raw",
    "/observability/export",
    "/observability/ship",
    "/siem/export",
    "/siem/ship",
    "/analytics/export",
    "/network/post",
)
EXPECTED_M116_OPENAPI_PATH_COUNT = 79
M116_FORBIDDEN_BACKEND_ROUTES = M115_FORBIDDEN_BACKEND_ROUTES + (
    "/authority/roles",
    "/authority/enforce",
    "/authority/permissions",
    "/authority/scopes",
    "/authority/runtime",
    "/rbac/enforce",
    "/rbac/roles",
    "/roles/assign",
    "/roles/enforce",
    "/permissions/enforce",
    "/auth/login",
    "/auth/session",
    "/auth/oauth",
    "/auth/token",
    "/credentials/read",
    "/credentials/write",
    "/account/action",
)
EXPECTED_M117_OPENAPI_PATH_COUNT = 79
M117_FORBIDDEN_BACKEND_ROUTES = M116_FORBIDDEN_BACKEND_ROUTES + (
    "/remote-agents/coordinate",
    "/remote-agents/dispatch",
    "/remote-agents/connect",
    "/remote-agents/spawn",
    "/remote/execute",
    "/agent-mesh/dispatch",
    "/agents/remote/handoff",
    "/context/inject",
    "/memory/write",
    "/tools/execute",
    "/network/post",
)
EXPECTED_M118_OPENAPI_PATH_COUNT = 79
M118_FORBIDDEN_BACKEND_ROUTES = M117_FORBIDDEN_BACKEND_ROUTES + (
    "/deployment/modes/apply",
    "/deployment/run",
    "/deployment/release",
    "/deployment/promote",
    "/deployment/rollback",
    "/production/deploy",
    "/ci-cd/run",
    "/infra/provision",
    "/remote-agents/dispatch",
    "/context/inject",
    "/memory/write",
    "/tools/execute",
    "/network/post",
)
EXPECTED_M119_OPENAPI_PATH_COUNT = 79
M119_FORBIDDEN_BACKEND_ROUTES = M118_FORBIDDEN_BACKEND_ROUTES + (
    "/red-team/run",
    "/red-team/execute",
    "/red-team/attack",
    "/red-team/probe",
    "/red-team/exploit",
    "/red-team/report/export",
    "/production/red-team/run",
    "/security/scan/run",
    "/context/inject",
    "/memory/write",
    "/tools/execute",
    "/network/post",
)
EXPECTED_M120_OPENAPI_PATH_COUNT = 79
M120_FORBIDDEN_BACKEND_ROUTES = M119_FORBIDDEN_BACKEND_ROUTES + (
    "/production/authority/enable",
    "/production/go-live",
    "/production/deploy",
    "/production/traffic/route",
    "/production/rollback/execute",
    "/production/readiness/approve",
    "/context/inject",
    "/memory/write",
    "/tools/execute",
    "/network/post",
)
EXPECTED_M121_OPENAPI_PATH_COUNT = 79
M121_FORBIDDEN_BACKEND_ROUTES = M120_FORBIDDEN_BACKEND_ROUTES + (
    "/connectors/email/auth",
    "/connectors/email/read",
    "/connectors/email/search",
    "/connectors/email/send",
    "/connectors/email/write",
    "/connectors/email/delete",
    "/connectors/email/attachments/download",
    "/email/send",
    "/network/post",
    "/memory/write",
    "/context/inject",
)
EXPECTED_M122_OPENAPI_PATH_COUNT = 79
M122_FORBIDDEN_BACKEND_ROUTES = M121_FORBIDDEN_BACKEND_ROUTES + (
    "/connectors/calendar/auth",
    "/connectors/calendar/read",
    "/connectors/calendar/search",
    "/connectors/calendar/events/create",
    "/connectors/calendar/events/update",
    "/connectors/calendar/events/delete",
    "/connectors/calendar/invites/send",
    "/connectors/calendar/attachments/download",
    "/calendar/events/create",
    "/network/post",
    "/memory/write",
    "/context/inject",
)
EXPECTED_M123_OPENAPI_PATH_COUNT = 79
M123_FORBIDDEN_BACKEND_ROUTES = M122_FORBIDDEN_BACKEND_ROUTES + (
    "/connectors/contacts/auth",
    "/connectors/contacts/read",
    "/connectors/contacts/search",
    "/connectors/contacts/lookup",
    "/connectors/contacts/create",
    "/connectors/contacts/update",
    "/connectors/contacts/delete",
    "/connectors/contacts/export",
    "/connectors/contacts/bulk-export",
    "/contacts/export",
    "/network/post",
    "/memory/write",
    "/context/inject",
)
EXPECTED_M124_OPENAPI_PATH_COUNT = 79
M124_FORBIDDEN_BACKEND_ROUTES = M123_FORBIDDEN_BACKEND_ROUTES + (
    "/connectors/messages/auth",
    "/connectors/messages/read",
    "/connectors/messages/search",
    "/connectors/messages/lookup",
    "/connectors/messages/send",
    "/connectors/messages/thread",
    "/connectors/messages/threads",
    "/connectors/messages/attachments/download",
    "/connectors/messages/create",
    "/connectors/messages/update",
    "/connectors/messages/delete",
    "/connectors/messages/export",
    "/connectors/messages/bulk-export",
    "/messages/export",
    "/network/post",
    "/memory/write",
    "/context/inject",
)
EXPECTED_M125_OPENAPI_PATH_COUNT = 79
M125_FORBIDDEN_BACKEND_ROUTES = M124_FORBIDDEN_BACKEND_ROUTES + (
    "/connectors/read",
    "/connectors/runtime/read",
    "/connectors/email/read",
    "/connectors/calendar/read",
    "/connectors/contacts/read",
    "/connectors/messages/read",
    "/connectors/messages/send",
    "/connectors/export",
    "/connectors/attachments/download",
    "/network/post",
    "/memory/write",
    "/context/inject",
    "/tools/execute",
)
EXPECTED_M126_OPENAPI_PATH_COUNT = 79
M126_FORBIDDEN_BACKEND_ROUTES = M125_FORBIDDEN_BACKEND_ROUTES + (
    "/connectors/approvals/capture",
    "/connectors/approve",
    "/connectors/approval",
    "/connectors/approval/capture",
    "/connectors/write",
    "/connectors/send",
    "/connectors/delete",
    "/connectors/bulk-export",
)
EXPECTED_M127_OPENAPI_PATH_COUNT = 79
M127_FORBIDDEN_BACKEND_ROUTES = M126_FORBIDDEN_BACKEND_ROUTES + (
    "/connectors/write/dry-run",
    "/connectors/dry-run/write",
    "/connectors/write/plan",
    "/connectors/write/execute",
    "/connectors/send/execute",
    "/connectors/messages/reply",
    "/connectors/email/draft",
    "/connectors/calendar/events/create",
    "/connectors/contacts/update",
)
EXPECTED_M128_OPENAPI_PATH_COUNT = 79
M128_FORBIDDEN_BACKEND_ROUTES = M127_FORBIDDEN_BACKEND_ROUTES + (
    "/connectors/write/low-risk",
    "/connectors/write/result",
    "/connectors/write/status",
    "/connectors/send",
    "/connectors/delete",
    "/connectors/export",
    "/connectors/audit/hardening",
    "/connectors/revocation/execute",
    "/connectors/kill-switch/execute",
)
EXPECTED_M129_OPENAPI_PATH_COUNT = 79
M129_FORBIDDEN_BACKEND_ROUTES = M128_FORBIDDEN_BACKEND_ROUTES + (
    "/connectors/audit",
    "/connectors/audit/export",
    "/connectors/audit/hardening",
    "/connectors/revocation",
    "/connectors/revocation/execute",
    "/connectors/kill-switch",
    "/connectors/kill-switch/execute",
    "/connectors/safety/freeze",
    "/connectors/freeze",
    "/connectors/export",
    "/connectors/send",
    "/connectors/delete",
    "/network/post",
    "/memory/write",
    "/context/inject",
    "/tools/execute",
)
EXPECTED_M130_OPENAPI_PATH_COUNT = 79
M130_FORBIDDEN_BACKEND_ROUTES = M129_FORBIDDEN_BACKEND_ROUTES + (
    "/connectors/safety/freeze",
    "/connectors/freeze",
    "/connectors/freeze/accept",
    "/connectors/runtime",
    "/connectors/auth",
    "/connectors/export",
    "/connectors/audit/export",
    "/connectors/revocation/execute",
    "/connectors/kill-switch/execute",
    "/autonomy/mode4",
    "/autonomy/scoped-work-session",
    "/automation/session/start",
    "/memory/write",
    "/context/inject",
    "/tools/execute",
)
EXPECTED_M131_OPENAPI_PATH_COUNT = 79
M131_FORBIDDEN_BACKEND_ROUTES = M130_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/mode4",
    "/autonomy/mode4/start",
    "/autonomy/scoped-work-session",
    "/autonomy/scoped-work-session/start",
    "/autonomy/session/start",
    "/autonomy/actions/execute",
    "/autonomy/tools/execute",
    "/automation/session/start",
    "/automation/mode4/start",
    "/shell/execute",
    "/commands/execute",
    "/browser/click",
    "/browser/form",
    "/browser/download",
    "/browser/upload",
    "/network/post",
    "/plugins/execute",
    "/connectors/runtime",
    "/connectors/auth",
    "/mobile/sensors",
    "/remote/execute",
    "/workers/start",
    "/scheduler/start",
    "/memory/write",
    "/context/inject",
    "/models/call",
)
EXPECTED_M132_OPENAPI_PATH_COUNT = 79
M132_FORBIDDEN_BACKEND_ROUTES = M131_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/mode5",
    "/autonomy/mode5/start",
    "/autonomy/trusted-recurring-workflow",
    "/autonomy/trusted-recurring-workflow/start",
    "/autonomy/workflow/start",
    "/autonomy/recurrence/start",
    "/automation/trusted-recurring/start",
    "/automation/recurring/start",
    "/scheduler/create",
    "/scheduler/start",
    "/background/start",
    "/workers/start",
    "/supervisor/start",
    "/supervisor/long-running/start",
)
EXPECTED_M133_OPENAPI_PATH_COUNT = 79
M133_FORBIDDEN_BACKEND_ROUTES = M132_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/long-running-supervisor",
    "/autonomy/long-running-supervisor/start",
    "/supervisor/long-running",
    "/supervisor/tasks/start",
    "/supervisor/heartbeat/start",
    "/supervisor/checkpoints/schedule",
    "/supervisor/resume",
    "/supervisor/recover",
    "/checkpoints/human/schedule",
    "/tasks/long-running/start",
    "/background/supervisor/start",
)
EXPECTED_M134_OPENAPI_PATH_COUNT = 79
M134_FORBIDDEN_BACKEND_ROUTES = M133_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/human-checkpoint-scheduling",
    "/autonomy/human-checkpoint-scheduling/start",
    "/checkpoints/human/schedule",
    "/checkpoints/human/prompt",
    "/checkpoints/human/notify",
    "/checkpoints/human/remind",
    "/calendar/write",
    "/approvals/capture",
    "/escalations/start",
    "/supervisor/recover",
    "/scheduler/start",
    "/background/start",
    "/workers/start",
)
EXPECTED_M135_OPENAPI_PATH_COUNT = 79
M135_FORBIDDEN_BACKEND_ROUTES = M134_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/autonomous-recovery-planner",
    "/autonomy/autonomous-recovery-planner/start",
    "/autonomy/recovery/execute",
    "/recovery/execute",
    "/recovery/retry",
    "/recovery/resume",
    "/recovery/rollback",
    "/supervisor/recover",
    "/supervisor/resume",
    "/supervisor/start",
    "/checkpoints/schedule",
    "/checkpoints/human/schedule",
    "/checkpoints/human/prompt",
    "/checkpoints/human/notify",
    "/scheduler/start",
    "/background/start",
    "/workers/start",
)
EXPECTED_M136_OPENAPI_PATH_COUNT = 79
M136_FORBIDDEN_BACKEND_ROUTES = M135_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/cross-tool-dependency-execution",
    "/autonomy/cross-tool-dependency-execution/start",
    "/autonomy/cross-tool-dependency-execution/run",
    "/dependency-execution/execute",
    "/dependency-execution/run",
    "/dependency-execution/resolve",
    "/dependency-resolver/start",
    "/cross-tool/runtime",
    "/cross-tool/run",
    "/tools/execute",
    "/tools/run",
    "/tool-runtime/execute",
    "/tool-state/handoff",
    "/tool-output/route",
    "/connectors/runtime",
    "/connectors/write",
    "/browser/click",
    "/browser/form",
    "/browser/download",
    "/browser/upload",
    "/network/post",
    "/plugins/execute",
    "/scheduler/start",
    "/background/start",
    "/workers/start",
)
EXPECTED_M137_OPENAPI_PATH_COUNT = 79
M137_FORBIDDEN_BACKEND_ROUTES = M136_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/browser-connector-combined-workflow",
    "/autonomy/browser-connector-combined-workflow/start",
    "/autonomy/browser-connector-combined-workflow/run",
    "/combined-workflows/run",
    "/combined-workflows/execute",
    "/browser/actions/run",
    "/browser/actions/execute",
    "/browser/navigate",
    "/browser/click",
    "/browser/form",
    "/browser/download",
    "/browser/upload",
    "/browser/authenticated",
    "/connectors/runtime",
    "/connectors/read",
    "/connectors/write",
    "/connectors/send",
    "/connectors/delete",
    "/connectors/auth",
    "/accounts/auth",
    "/dependency-execution/execute",
    "/dependency-resolver/start",
    "/tools/execute",
    "/network/post",
    "/plugins/execute",
)
EXPECTED_M138_OPENAPI_PATH_COUNT = 79
M138_FORBIDDEN_BACKEND_ROUTES = M137_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/error-handling-guardrails",
    "/autonomy/error-handling-guardrails/start",
    "/autonomy/error-handling-guardrails/run",
    "/error-handling/run",
    "/error-handling/execute",
    "/error-guardrails/run",
    "/error-guardrails/execute",
    "/recovery/retry",
    "/recovery/rollback",
    "/recovery/resume",
    "/recovery/execute",
    "/fallback/execute",
    "/escalation/execute",
    "/loop-recovery/run",
)
EXPECTED_M139_OPENAPI_PATH_COUNT = 79
M139_FORBIDDEN_BACKEND_ROUTES = M138_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/abuse-loop-detection",
    "/autonomy/abuse-loop-detection/start",
    "/autonomy/abuse-loop-detection/run",
    "/abuse-detection/run",
    "/abuse-detection/execute",
    "/loop-detection/run",
    "/loop-detection/execute",
    "/loop-detection/intervene",
    "/autonomy/loop-monitor/start",
    "/loop-monitor/start",
    "/loop-intervention/execute",
    "/loop-recovery/execute",
    "/recovery/execute",
    "/tools/execute",
    "/browser/click",
    "/connectors/write",
)
EXPECTED_M140_OPENAPI_PATH_COUNT = 79
M140_FORBIDDEN_BACKEND_ROUTES = M139_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/higher-autonomy-red-team-freeze",
    "/autonomy/higher-autonomy-red-team-freeze/start",
    "/autonomy/higher-autonomy-red-team-freeze/run",
    "/red-team/run",
    "/red-team/execute",
    "/red-team/harness/run",
    "/red-team/harness/execute",
    "/adversarial-tests/run",
    "/adversarial-tests/execute",
    "/autonomy/execute",
    "/autonomy/broad/enable",
    "/multi-user/enable",
    "/tenants/create",
    "/workspaces/share",
    "/production/authority/enable",
    "/tools/execute",
    "/browser/click",
    "/connectors/write",
)
EXPECTED_M141_OPENAPI_PATH_COUNT = 79
M141_FORBIDDEN_BACKEND_ROUTES = M140_FORBIDDEN_BACKEND_ROUTES + (
    "/multi-user",
    "/multi-user/enable",
    "/multi-user/start",
    "/multi-user/run",
    "/tenants",
    "/tenants/create",
    "/tenants/invite",
    "/workspaces/share",
    "/workspaces/members",
    "/identity/federation/enable",
    "/auth/login",
    "/auth/session",
    "/organizations/create",
    "/roles/assign",
    "/alpha/privacy-review/start",
    "/alpha/privacy-review/run",
    "/production/authority/enable",
    "/tools/execute",
    "/browser/click",
    "/connectors/write",
)
EXPECTED_M142_OPENAPI_PATH_COUNT = 79
M142_FORBIDDEN_BACKEND_ROUTES = M141_FORBIDDEN_BACKEND_ROUTES + (
    "/alpha/privacy-review",
    "/alpha/privacy-review/start",
    "/alpha/privacy-review/run",
    "/alpha/privacy-review/signoff",
    "/alpha/ui",
    "/alpha/ui/start",
    "/alpha/app-readiness/run",
    "/privacy-review/execute",
    "/privacy-review/run",
    "/privacy/raw-content",
    "/privacy/export",
    "/production/authority/enable",
    "/tools/execute",
    "/browser/click",
    "/connectors/write",
)
EXPECTED_M143_OPENAPI_PATH_COUNT = 79
M143_FORBIDDEN_BACKEND_ROUTES = M142_FORBIDDEN_BACKEND_ROUTES + (
    "/alpha/ui",
    "/alpha/ui/start",
    "/alpha/ui/run",
    "/alpha/app-readiness",
    "/alpha/app-readiness/run",
    "/alpha/app-readiness/signoff",
    "/app/readiness/execute",
    "/app/build",
    "/app/sign",
    "/app-store/connect",
    "/testflight/upload",
    "/alpha/release",
    "/beta/release",
    "/plugin-marketplace/policy",
    "/plugin-marketplace/publish",
    "/production/authority/enable",
    "/tools/execute",
    "/browser/click",
    "/connectors/write",
)
EXPECTED_M144_OPENAPI_PATH_COUNT = 79
M144_FORBIDDEN_BACKEND_ROUTES = M143_FORBIDDEN_BACKEND_ROUTES + (
    "/plugin-marketplace",
    "/plugin-marketplace/policy",
    "/plugin-marketplace/publish",
    "/plugin-marketplace/install",
    "/plugin-marketplace/enable",
    "/plugin-marketplace/execute",
    "/plugins/marketplace",
    "/plugins/install",
    "/plugins/enable",
    "/plugins/execute",
    "/plugins/load",
    "/plugin-runtime/import",
    "/plugin-runtime/load",
    "/plugin-runtime/execute",
    "/plugin-package/download",
    "/plugin-package/upload",
    "/marketplace/listings/write",
    "/tools/plugins/execute",
    "/network/fetch",
    "/network/request",
    "/production/authority/enable",
)
EXPECTED_M145_OPENAPI_PATH_COUNT = 79
M145_FORBIDDEN_BACKEND_ROUTES = M144_FORBIDDEN_BACKEND_ROUTES + (
    "/enterprise/runtime",
    "/enterprise/pro/enable",
    "/enterprise/safety-modes",
    "/pro/runtime",
    "/pro/enable",
    "/safety-modes/enable",
    "/safety-modes/enforce",
    "/plans/enforce",
    "/plans/upgrade",
    "/plans/downgrade",
    "/billing/runtime",
    "/billing/plans",
    "/billing/checkout",
    "/accounts/tenants",
    "/roles/runtime",
    "/workspace/share",
    "/auth/login",
    "/production/authority/enable",
)
EXPECTED_M146_OPENAPI_PATH_COUNT = 79
M146_FORBIDDEN_BACKEND_ROUTES = M145_FORBIDDEN_BACKEND_ROUTES + (
    "/billing",
    "/billing/runtime",
    "/billing/plans",
    "/billing/checkout",
    "/billing/subscriptions",
    "/billing/invoices",
    "/billing/webhooks",
    "/plans/enforce",
    "/plans/upgrade",
    "/plans/downgrade",
    "/plans/entitlements",
    "/pricing/runtime",
    "/pricing/update",
    "/payments/process",
    "/payment/checkout",
    "/checkout/session",
    "/subscriptions/manage",
    "/invoices/generate",
    "/entitlements/runtime",
    "/account/plans",
    "/external-billing-provider",
    "/stripe",
    "/production/authority/enable",
)
EXPECTED_M147_OPENAPI_PATH_COUNT = 79
M147_FORBIDDEN_BACKEND_ROUTES = M146_FORBIDDEN_BACKEND_ROUTES + (
    "/public-docs/publish",
    "/public-docs/deploy",
    "/docs/publish",
    "/docs/deploy",
    "/docs/site/deploy",
    "/wiki/publish",
    "/wiki/sync",
    "/wiki/automation",
    "/github/wiki",
    "/github/wiki/publish",
    "/artifacts/upload",
    "/release/publish",
    "/distribution/publish",
    "/external-distribution",
    "/production/authority/enable",
)
EXPECTED_M148_OPENAPI_PATH_COUNT = 79
M148_FORBIDDEN_BACKEND_ROUTES = M147_FORBIDDEN_BACKEND_ROUTES + (
    "/external-security-review",
    "/external-security-review/start",
    "/external-security-review/export",
    "/security/review/start",
    "/security/review/export",
    "/security/review/runtime",
    "/security/vendor",
    "/security/vendor/handoff",
    "/security/scanner/run",
    "/security/vulnerability-scan",
    "/security/findings/export",
    "/security/audit/upload",
    "/repository/export",
    "/source/export",
    "/issues/export",
    "/artifacts/export",
    "/production/authority/enable",
)
EXPECTED_M149_OPENAPI_PATH_COUNT = 79
M149_FORBIDDEN_BACKEND_ROUTES = M148_FORBIDDEN_BACKEND_ROUTES + (
    "/alpha-release-candidate-freeze",
    "/alpha-release-candidate-freeze/start",
    "/alpha-release-candidate-freeze/publish",
    "/release/publish",
    "/release/tag",
    "/release/create-tag",
    "/release/artifact/build",
    "/release/artifact/upload",
    "/release/artifact/export",
    "/distribution/publish",
    "/external-distribution",
    "/app-store/submit",
    "/testflight/submit",
    "/beta/release",
    "/v1-alpha/release",
    "/m150/release",
    "/release/automation",
    "/production/authority/enable",
)
EXPECTED_M150_OPENAPI_PATH_COUNT = 79
M150_FORBIDDEN_BACKEND_ROUTES = M149_FORBIDDEN_BACKEND_ROUTES + (
    "/ultimate-ai-agent-alpha",
    "/ultimate-ai-agent-alpha/publish",
    "/alpha/accept",
    "/alpha/release",
    "/v1.2.0-alpha/release",
)
M22_FORBIDDEN_LOCAL_RUNTIME_FRAGMENTS = (
    "import ollama",
    "from ollama import",
    "import llama_cpp",
    "from llama_cpp import",
    "import mlx",
    "from mlx import",
    "import vllm",
    "from vllm import",
    "import lmstudio",
    "import " + "requests",
    "import " + "httpx",
    "subprocess",
    "requests.get(",
    "requests.post(",
    "requests.request(",
    "httpx.get(",
    "httpx.post(",
    "httpx.request(",
    "urllib.request.urlopen(",
    "create_completion",
    "chat.completions.create(",
    "ollama.generate(",
    "ollama.pull(",
    "/api/generate",
    "/v1/chat/completions",
)
M22_LOCAL_RUNTIME_SCAN_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
M22_LOCAL_RUNTIME_ALLOWED_SOURCE_FILES = {
    "src/ultimate_ai_agent/core/model_runtime/local_adapter.py",
    "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
    "src/ultimate_ai_agent/core/model_runtime/smoke_policy.py",
    "src/ultimate_ai_agent/core/model_runtime/simulator.py",
    "src/ultimate_ai_agent/core/model_runtime/transports.py",
}
M21_FORBIDDEN_OPENWEBUI_CONFIG_PATH_FRAGMENTS = (
    "docker-compose.openwebui",
    "openwebui.config",
    "openwebui-config",
    "openwebui_plugins",
    "openwebui_pipelines",
    "openwebui_functions",
    "openwebui_tools",
    "apps/openwebui/",
    "openwebui/",
)
M21_FORBIDDEN_OPENWEBUI_RUNTIME_FRAGMENTS = (
    "openwebui_api_key",
    "openwebui_admin_token",
    "openwebui_cookie",
    "openwebui_session",
    "openwebui_base_url",
    "openwebui_plugin",
    "openwebui_function",
    "openwebui_pipeline",
    "openwebui_tool",
    "docker-compose",
    "/openwebui/execute",
    "/openwebui/bridge/run",
    "/chat/execute",
    "/chat/run",
    "/model-runtime/execute",
)
M21_FORBIDDEN_OPENWEBUI_RUNTIME_PATTERNS = (
    re.compile(r"(?m)^\s*import\s+openwebui\b"),
    re.compile(r"(?m)^\s*from\s+openwebui\b\s+import\b"),
)
M21_OPENWEBUI_SCAN_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
M21_OPENWEBUI_ALLOWED_FRAGMENT_SCAN_FILES = {
    "src/ultimate_ai_agent/core/gate/evaluators.py",
    "src/ultimate_ai_agent/core/hardening_freeze/__init__.py",
    "src/ultimate_ai_agent/core/hardening_freeze/network_browser_openwebui.py",
    "src/ultimate_ai_agent/core/local_model_management/contracts.py",
    "scripts/verify_all.py",
    "scripts/verification/run_all_legacy.py",
    "scripts/verify_control_center_frontend.py",
}
M21_OPENWEBUI_ALLOWED_FRAGMENT_SCAN_EXCEPTIONS = {
    "scripts/run_local_runtime_packaging_proof.py": frozenset({"docker-compose"}),
}
M151_LOCAL_OPENWEBUI_TEST_ROUTES = {
    "/v1/models",
    "/v1/chat/completions",
}
M167_REDACTED_OBSERVABILITY_ROUTES = {
    "/observability/client-errors",
    "/observability/session-events",
}
FOUNDER_LOOP_ACTION_DECISION_ROUTES = frozenset(
    {
        "/control-center/actions/{action_id}/approve",
        "/control-center/actions/{action_id}/defer",
        "/control-center/actions/{action_id}/edit",
        "/control-center/actions/{action_id}/reject",
    }
)
FOUNDER_LOOP_ACTION_ENVELOPE_ROUTES = frozenset(
    {
        "/control-center/today/action-envelope",
    }
)
FOUNDER_LOOP_CHAT_DURABLE_RECEIPT_ROUTES = frozenset(
    {
        "/control-center/chat/turns",
        "/control-center/chat/turns/{turn_ref}/handoff",
    }
)
FOUNDER_LOOP_MEMORY_REVIEW_DECISION_ROUTES = frozenset(
    {
        "/control-center/memory/review/{candidate_ref}/accept",
        "/control-center/memory/review/{candidate_ref}/correct",
        "/control-center/memory/review/{candidate_ref}/defer",
        "/control-center/memory/review/{candidate_ref}/forget-request",
        "/control-center/memory/review/{candidate_ref}/merge",
        "/control-center/memory/review/{candidate_ref}/reject",
        "/control-center/memory/review/{candidate_ref}/receipt",
        "/control-center/memory/review/{candidate_ref}/supersede",
        "/control-center/memory/review/manual-candidate",
    }
)
FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTES = frozenset(
    {"/control-center/actions/{action_id}/local-task/commit"}
)
FOUNDER_LOOP_MEMORY_CONTEXT_ROUTES = frozenset(
    {
        "/control-center/memory/context-packs",
        "/control-center/memory/l1-index",
        "/control-center/memory/l2-index",
        "/control-center/memory/l3-index",
        "/control-center/memory/search",
        "/control-center/memory/workbench",
    }
)
FOUNDER_LOOP_MEMORY_CONTEXT_ACTION_PROPOSAL_ROUTES = frozenset(
    {"/control-center/memory/context-packs/{context_pack_ref}/action-proposal"}
)
FOUNDER_LOOP_MEMORY_FEATURE_MINE_ROUTES = frozenset(
    {
        "/control-center/memory/contradictions",
        "/control-center/memory/feedback",
        "/control-center/memory/observation-candidates",
        "/control-center/memory/probe",
    }
)
FOUNDER_LOOP_CONTROL_CENTER_ROUTES = (
    frozenset(
        {
            "/control-center/actions/inbox",
            "/control-center/actions/{action_id}/receipt",
            "/control-center/chat/turns",
            "/control-center/chat/turns/{turn_ref}/handoff",
            "/control-center/chat/turns/{turn_ref}/receipt",
            "/control-center/evidence/timeline",
            "/control-center/memory/review",
            "/control-center/morning-briefing/summary",
            "/control-center/sources/readiness",
            "/control-center/storage/status",
            "/control-center/today/summary",
        }
    )
    | FOUNDER_LOOP_ACTION_DECISION_ROUTES
    | FOUNDER_LOOP_ACTION_ENVELOPE_ROUTES
    | FOUNDER_LOOP_CHAT_DURABLE_RECEIPT_ROUTES
    | FOUNDER_LOOP_MEMORY_REVIEW_DECISION_ROUTES
    | FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTES
    | FOUNDER_LOOP_MEMORY_CONTEXT_ROUTES
    | FOUNDER_LOOP_MEMORY_CONTEXT_ACTION_PROPOSAL_ROUTES
    | FOUNDER_LOOP_MEMORY_FEATURE_MINE_ROUTES
)
MATTERMOST_AGENT_ROOMS_ROUTES = {
    "/integrations/mattermost/audit",
    "/integrations/mattermost/events/message",
    "/integrations/mattermost/receipts",
    "/integrations/mattermost/roles/bind",
    "/integrations/mattermost/roles/catalog",
    "/integrations/mattermost/roles/suggest",
    "/integrations/mattermost/roles/unbind",
    "/integrations/mattermost/status",
}
CONTROL_CENTER_SETUP_ASSISTANT_ROUTES = {
    "/control-center/setup-assistant/summary",
}
CONTROL_CENTER_OPERATIONAL_STATUS_ROUTES = {
    "/control-center/local-models/status",
    "/control-center/settings/status",
}
PACKAGING_PROOF_ROUTE_BOUNDARY_ROUTES = frozenset()
VISUAL_PROOF_ROUTE_BOUNDARY_ROUTES = frozenset()
EXPECTED_M152_OPENAPI_PATH_COUNT = EXPECTED_M150_OPENAPI_PATH_COUNT
M152_FORBIDDEN_BACKEND_ROUTES = M150_FORBIDDEN_BACKEND_ROUTES + (
    "/hf/search",
    "/huggingface/search",
    "/local-models",
    "/local-models/search",
    "/local-models/acquire",
    "/local-models/download",
    "/local-models/import",
    "/local-models/load",
    "/local-models/unload",
    "/local-models/delete",
    "/local-models/serve",
    "/local-models/server",
    "/model-management",
    "/model-management/execute",
    "/model-management/download",
    "/models/download",
    "/models/pull",
    "/models/load",
    "/models/unload",
    "/models/delete",
    "/models/generate",
    "/models/complete",
    "/models/invoke",
    "/hardware/probe",
    "/system/probe",
    "/model-runtime/local/download",
    "/model-runtime/local/load",
    "/model-runtime/local/unload",
    "/model-runtime/local/serve",
    "/model-runtime/local/start",
    "/model-runtime/local/restart",
    "/llama-cpp/server",
    "/llama-cpp/settings/apply",
    "/v1/responses",
    "/v1/completions",
    "/v1/embeddings",
    "/providers/call",
    "/providers/invoke",
    "/control-center/local-models/execute",
    "/control-center/local-models/download",
    "/control-center/local-models/apply",
    "/control-center/local-models/start",
    "/control-center/model-management/execute",
    "/control-center/model-management/apply",
)
M152_FORBIDDEN_SOURCE_FRAGMENTS = (
    "import " + "subprocess",
    "from subprocess import",
    "subprocess" + ".run(",
    "subprocess" + ".Popen(",
    "import " + "requests",
    "from " + "requests import",
    "requests.get(",
    "requests.post(",
    "requests.request(",
    "import " + "httpx",
    "from " + "httpx import",
    "httpx.get(",
    "httpx.post(",
    "httpx.request(",
    "urllib.request.urlopen(",
    "import llama_cpp",
    "from llama_cpp import",
    "llama_cpp.Llama(",
    "llama_cpp.server",
    "llama-server",
    "llama_server",
    "import huggingface_hub",
    "from huggingface_hub import",
    "HfApi().list_models",
    "list_models(",
    "model_info(",
    "hf_hub_download(",
    "snapshot_download(",
    "HfApi(",
    "AutoModel.from_pretrained(",
    "AutoTokenizer.from_pretrained(",
    "pipeline(",
    "platform.uname(",
    "psutil.",
    "system_profiler",
    "nvidia-smi",
    "subprocess" + ".check_output(",
    "asyncio.create_subprocess",
    "os.system(",
    "openai.OpenAI(",
    "ollama.pull(",
    "ollama.generate(",
    "create_completion(",
    "chat.completions.create(",
    "download_enabled=True",
    "model_download_enabled=True",
    "download_performed=True",
    "settings_applied=True",
    "server_started=True",
    "model_load_enabled=True",
    "model_unload_enabled=True",
    "model_call_enabled=True",
    "model_loaded=True",
    "model_call_performed=True",
    "provider_call_enabled=True",
    "backend_route_added=True",
    "control_center_execute_control_added=True",
    "dependency_added=True",
    "production_authority_granted=True",
)
M152_FORBIDDEN_DEPENDENCY_FRAGMENTS = (
    "llama-cpp-python",
    "llama_cpp",
    "huggingface-hub",
    "huggingface_hub",
    "hf-transfer",
    "openai",
    "transformers",
    "torch",
    "accelerate",
    "sentence-transformers",
    "psutil",
    "pynvml",
    "ollama",
    "vllm",
    "mlx",
    "lmstudio",
)
M152_STATIC_SCAN_ALLOWED_FILES = {
    "src/ultimate_ai_agent/api/local_auth.py",
    "src/ultimate_ai_agent/api/openapi.py",
    "src/ultimate_ai_agent/core/gate/criteria.py",
    "src/ultimate_ai_agent/core/gate/evaluators.py",
    "src/ultimate_ai_agent/core/local_model_management/__init__.py",
    "src/ultimate_ai_agent/core/local_model_management/e2e_smoke.py",
    "src/ultimate_ai_agent/core/local_model_management/gateway.py",
    "src/ultimate_ai_agent/core/local_model_management/hf_search.py",
    "src/ultimate_ai_agent/core/local_model_management/llama_cpp_supervisor.py",
    "src/ultimate_ai_agent/core/local_model_management/model_acquisition.py",
    "src/ultimate_ai_agent/core/local_model_management/system_probe.py",
    "src/ultimate_ai_agent/core/local_model_management/tuning.py",
    "src/ultimate_ai_agent/core/production_readiness/live_model_hardening.py",
}
M152_STATIC_SCAN_ROOTS = (
    "src/ultimate_ai_agent",
    "apps/control-center/src",
    "apps/ccc-ios",
)

TASK_DECOMPOSITION_CANONICAL_ROUTES = frozenset(
    {
        "/task-decomposition/approval-requests",
        "/task-decomposition/approvals",
        "/task-decomposition/approvals/grants/capture",
        "/task-decomposition/approvals/revoke",
        "/task-decomposition/audit",
        "/task-decomposition/capabilities/register",
        "/task-decomposition/catalog",
        "/task-decomposition/classify",
        "/task-decomposition/decompose",
        "/task-decomposition/examples/init",
        "/task-decomposition/metrics",
        "/task-decomposition/plans/execute",
        "/task-decomposition/plans/validate",
        "/task-decomposition/registry/export",
        "/task-decomposition/run",
        "/task-decomposition/status",
    }
)

POST_MILESTONE_SAFE_ROUTE_FAMILIES = {
    "founder_loop": FOUNDER_LOOP_CONTROL_CENTER_ROUTES,
    "control_center_setup_assistant": CONTROL_CENTER_SETUP_ASSISTANT_ROUTES,
    "control_center_operational_status": CONTROL_CENTER_OPERATIONAL_STATUS_ROUTES,
    "mattermost": MATTERMOST_AGENT_ROOMS_ROUTES,
    "packaging_proof": PACKAGING_PROOF_ROUTE_BOUNDARY_ROUTES,
    "redacted_observability": M167_REDACTED_OBSERVABILITY_ROUTES,
    "task_decomposition": TASK_DECOMPOSITION_CANONICAL_ROUTES,
    "visual_proof": VISUAL_PROOF_ROUTE_BOUNDARY_ROUTES,
    "v1_local_model_gateway": M151_LOCAL_OPENWEBUI_TEST_ROUTES,
}


def post_milestone_safe_route_paths() -> set[str]:
    paths: set[str] = set()
    for route_family in POST_MILESTONE_SAFE_ROUTE_FAMILIES.values():
        paths.update(route_family)
    return paths


def _post_m151_route_boundary_path_set(paths: Iterable[str]) -> set[str]:
    """Normalize current OpenAPI paths for route-boundary contract gates."""
    path_set = {path for path in paths}
    path_set.difference_update(post_milestone_safe_route_paths())
    return path_set


def _historical_openapi_path_set(paths: Iterable[str]) -> set[str]:
    """Normalize current OpenAPI paths for historical route-count gates."""
    path_set = _post_m151_route_boundary_path_set(paths)
    if len(path_set) > EXPECTED_M36_OPENAPI_PATH_COUNT:
        path_set.discard(M37_ALLOWED_CAPTURE_ROUTE)
    return path_set


def m16_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M16_OPENAPI_PATH_COUNT) -> List[str]:
    failures: List[str] = []
    path_set = _historical_openapi_path_set(paths)
    if len(path_set) != expected_path_count:
        failures.append(f"M16 OpenAPI path count changed: expected {expected_path_count}, found {len(path_set)}")
    forbidden_present = sorted(path for path in M16_FORBIDDEN_BACKEND_ROUTES if path in path_set)
    if forbidden_present:
        failures.append(f"M16 forbidden backend route(s) present: {', '.join(forbidden_present)}")
    return failures


def m17_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M17_OPENAPI_PATH_COUNT) -> List[str]:
    failures: List[str] = []
    path_set = _historical_openapi_path_set(paths)
    if len(path_set) != expected_path_count:
        failures.append(f"M17 OpenAPI path count changed: expected {expected_path_count}, found {len(path_set)}")
    forbidden_present = sorted(path for path in M17_FORBIDDEN_BACKEND_ROUTES if path in path_set)
    if forbidden_present:
        failures.append(f"M17 forbidden backend route(s) present: {', '.join(forbidden_present)}")
    return failures


def m18_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M18_OPENAPI_PATH_COUNT) -> List[str]:
    failures: List[str] = []
    path_set = _historical_openapi_path_set(paths)
    if len(path_set) != expected_path_count:
        failures.append(f"M18 OpenAPI path count changed: expected {expected_path_count}, found {len(path_set)}")
    forbidden_present = sorted(path for path in M18_FORBIDDEN_BACKEND_ROUTES if path in path_set)
    if forbidden_present:
        failures.append(f"M18 forbidden backend route(s) present: {', '.join(forbidden_present)}")
    return failures


def m19_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M19_OPENAPI_PATH_COUNT) -> List[str]:
    failures: List[str] = []
    path_set = _historical_openapi_path_set(paths)
    if len(path_set) != expected_path_count:
        failures.append(f"M19 OpenAPI path count changed: expected {expected_path_count}, found {len(path_set)}")
    forbidden_present = sorted(path for path in M19_FORBIDDEN_BACKEND_ROUTES if path in path_set)
    if forbidden_present:
        failures.append(f"M19 forbidden backend route(s) present: {', '.join(forbidden_present)}")
    return failures


def m20_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M20_OPENAPI_PATH_COUNT) -> List[str]:
    failures: List[str] = []
    path_set = _historical_openapi_path_set(paths)
    if len(path_set) != expected_path_count:
        failures.append(f"M20 OpenAPI path count changed: expected {expected_path_count}, found {len(path_set)}")
    forbidden_present = sorted(path for path in M20_FORBIDDEN_BACKEND_ROUTES if path in path_set)
    if forbidden_present:
        failures.append(f"M20 forbidden backend route(s) present: {', '.join(forbidden_present)}")
    return failures


def m21_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M21_OPENAPI_PATH_COUNT) -> List[str]:
    failures: List[str] = []
    path_set = _historical_openapi_path_set(paths)
    if len(path_set) != expected_path_count:
        failures.append(f"M21 OpenAPI path count changed: expected {expected_path_count}, found {len(path_set)}")
    forbidden_present = sorted(path for path in M21_FORBIDDEN_BACKEND_ROUTES if path in path_set)
    if forbidden_present:
        failures.append(f"M21 forbidden backend route(s) present: {', '.join(forbidden_present)}")
    return failures


def m22_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M22_OPENAPI_PATH_COUNT) -> List[str]:
    failures: List[str] = []
    path_set = _historical_openapi_path_set(paths)
    if len(path_set) != expected_path_count:
        failures.append(f"M22 OpenAPI path count changed: expected {expected_path_count}, found {len(path_set)}")
    forbidden_present = sorted(path for path in M22_FORBIDDEN_BACKEND_ROUTES if path in path_set)
    if forbidden_present:
        failures.append(f"M22 forbidden backend route(s) present: {', '.join(forbidden_present)}")
    return failures


def m23_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M23_OPENAPI_PATH_COUNT) -> List[str]:
    failures: List[str] = []
    path_set = _historical_openapi_path_set(paths)
    if len(path_set) != expected_path_count:
        failures.append(f"M23 OpenAPI path count changed: expected {expected_path_count}, found {len(path_set)}")
    forbidden_present = sorted(path for path in M23_FORBIDDEN_BACKEND_ROUTES if path in path_set)
    if forbidden_present:
        failures.append(f"M23 forbidden backend route(s) present: {', '.join(forbidden_present)}")
    return failures


def m24_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M24_OPENAPI_PATH_COUNT) -> List[str]:
    failures: List[str] = []
    path_set = _historical_openapi_path_set(paths)
    if len(path_set) != expected_path_count:
        failures.append(f"M24 OpenAPI path count changed: expected {expected_path_count}, found {len(path_set)}")
    forbidden_present = sorted(path for path in M24_FORBIDDEN_BACKEND_ROUTES if path in path_set)
    if forbidden_present:
        failures.append(f"M24 forbidden backend route(s) present: {', '.join(forbidden_present)}")
    return failures


def m25_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M25_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M25_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M25 forbidden backend route present: {route}")
    return failures


def m26_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M26_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M26_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M26 forbidden backend route present: {route}")
    return failures


def m27_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M27_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M27_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M27 forbidden backend route present: {route}")
    return failures


def m28_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M28_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M28_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M28 forbidden backend route present: {route}")
    return failures


def m29_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M29_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M29_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M29 forbidden backend route present: {route}")
    return failures


def m30_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M30_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M30_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M30 forbidden backend route present: {route}")
    return failures


def m31_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M31_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M31_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M31 forbidden backend route present: {route}")
    return failures


def m32_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M32_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M32_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M32 forbidden backend route present: {route}")
    return failures


def m33_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M33_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M33_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M33 forbidden backend route present: {route}")
    return failures


def m34_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M34_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M34_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M34 forbidden backend route present: {route}")
    return failures


def m35_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M35_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M35_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M35 forbidden backend route present: {route}")
    return failures


def m36_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M36_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _historical_openapi_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    for route in M36_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M36 forbidden backend route present: {route}")
    return failures


def m37_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M37_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M37_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M37 forbidden backend route present: {route}")
    return failures


def m38_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M38_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M38_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M38 forbidden backend route present: {route}")
    return failures


def m39_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M39_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M39_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M39 forbidden backend route present: {route}")
    return failures


def m40_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M40_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M40_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M40 forbidden backend route present: {route}")
    return failures


def m41_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M41_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M41_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M41 forbidden backend route present: {route}")
    return failures


def m42_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M42_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M42_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M42 forbidden backend route present: {route}")
    return failures


def m43_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M43_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M43_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M43 forbidden backend route present: {route}")
    return failures


def m44_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M44_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M44_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M44 forbidden backend route present: {route}")
    return failures


def m45_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M45_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M45_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M45 forbidden backend route present: {route}")
    return failures


def m46_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M46_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M46_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M46 forbidden backend route present: {route}")
    return failures


def m47_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M47_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M47_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M47 forbidden backend route present: {route}")
    return failures


def m48_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M48_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M48_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M48 forbidden backend route present: {route}")
    return failures


def m49_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M49_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M49_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M49 forbidden backend route present: {route}")
    return failures


def m50_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M50_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M50_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M50 forbidden backend route present: {route}")
    return failures


def m51_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M51_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M51_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M51 forbidden OpenWebUI backend route present: {route}")
    return failures


def m52_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M52_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M52_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M52 forbidden OpenWebUI conversation backend route present: {route}")
    return failures


def m53_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M53_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M53_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M53 forbidden tool expansion/runtime backend route present: {route}")
    return failures


def m54_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M54_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M54_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M54 forbidden raw media/transform/model/backend route present: {route}")
    return failures


def m55_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M55_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M55_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M55 forbidden observability export/raw/SaaS/backend route present: {route}")
    return failures


def m56_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M56_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M56_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M56 forbidden eval execution/raw/model/backend route present: {route}")
    return failures


def m57_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M57_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M57_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M57 forbidden runtime sandbox execution/backend route present: {route}")
    return failures


def m58_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M58_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M58_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M58 forbidden dry-run execution/backend route present: {route}")
    return failures


def m59_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M59_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M59_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M59 forbidden public publication/backend route present: {route}")
    return failures


def m60_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M60_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M60_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M60 forbidden beta/public/autonomy/backend route present: {route}")
    return failures


def m61_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M61_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M61_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M61 forbidden autonomy/execution/backend route present: {route}")
    return failures


def m62_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M62_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M62_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M62 forbidden autonomy session/execution/backend route present: {route}")
    return failures


def m63_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M63_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M63_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M63 forbidden autonomy policy/execution/backend route present: {route}")
    return failures


def m64_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M64_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M64_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M64 forbidden autonomy simulation/execution/backend route present: {route}")
    return failures


def m65_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M65_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M65_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M65 forbidden autonomy audit/replay/execution/backend route present: {route}")
    return failures


def m66_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M66_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M66_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M66 forbidden scoped approval bundle/execution/backend route present: {route}")
    return failures


def m67_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M67_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M67_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M67 forbidden revocation/kill-switch/execution/backend route present: {route}")
    return failures


def m68_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M68_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M68_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M68 forbidden risk-classifier/execution/backend route present: {route}")
    return failures


def m69_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M69_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M69_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M69 forbidden dry-run/execution/backend route present: {route}")
    return failures


def m70_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M70_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M70_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M70 forbidden freeze/execution/backend route present: {route}")
    return failures


def m71_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M71_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M71_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M71 forbidden network/runtime/backend route present: {route}")
    return failures


def m72_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M72_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M72_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M72 forbidden network/runtime/backend route present: {route}")
    return failures


def m73_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M73_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M73_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M73 forbidden browser/runtime/backend route present: {route}")
    return failures


def m74_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M74_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M74_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M74 forbidden browser observe/control/runtime route present: {route}")
    return failures


def m75_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M75_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M75_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M75 forbidden browser action/runtime route present: {route}")
    return failures


def m76_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M76_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M76_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M76 forbidden OpenWebUI runtime/backend route present: {route}")
    return failures


def m77_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M77_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M77: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M77_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M77 forbidden OpenWebUI handoff/backend route present: {route}")
    return failures


def m78_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M78_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M78: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M78_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M78 forbidden plugin/backend route present: {route}")
    return failures


def m79_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M79_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M79: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M79_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M79 forbidden plugin install/backend route present: {route}")
    return failures


def m80_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M80_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M80: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M80_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M80 forbidden network/browser/OpenWebUI/plugin route present: {route}")
    return failures


def m81_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M81_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M81: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M81_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M81 forbidden runtime sandbox/command/backend route present: {route}")
    return failures


def m82_openapi_route_failures(paths: Iterable[str], expected_path_count: int = EXPECTED_M82_OPENAPI_PATH_COUNT) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M82: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M82_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M82 forbidden command execution/backend route present: {route}")
    return failures


def m83_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M83_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M83: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M83_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M83 forbidden shell dry-run/backend route present: {route}")
    return failures


def m84_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M84_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M84: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M84_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M84 forbidden sandboxed command/backend route present: {route}")
    return failures


def m85_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M85_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M85: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M85_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M85 forbidden command allowlist/backend route present: {route}")
    return failures


def m86_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M86_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M86: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M86_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M86 forbidden shell approval/backend route present: {route}")
    return failures


def m87_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M87_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M87: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M87_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M87 forbidden command audit replay/backend route present: {route}")
    return failures


def m88_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M88_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M88: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M88_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M88 forbidden mutating command/backend route present: {route}")
    return failures


def m89_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M89_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M89: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M89_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M89 forbidden emergency/process/backend route present: {route}")
    return failures


def m90_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M90_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M90: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M90_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M90 forbidden shell/subprocess/process/backend route present: {route}")
    return failures


def m91_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M91_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M91: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M91_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M91 forbidden tool/autonomy execution backend route present: {route}")
    return failures


def m92_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M92_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M92: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M92_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M92 forbidden low-risk tool autonomy backend route present: {route}")
    return failures


def m93_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M93_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M93: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M93_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M93 forbidden dry-run promotion/backend execution route present: {route}")
    return failures


def m94_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M94_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M94: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M94_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M94 forbidden browser click/backend execution route present: {route}")
    return failures


def m95_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M95_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M95: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M95_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M95 forbidden network/backend execution route present: {route}")
    return failures


def m96_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M96_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M96: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M96_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M96 forbidden plugin/backend execution route present: {route}")
    return failures


def m97_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M97_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M97: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M97_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M97 forbidden recurring automation runtime route present: {route}")
    return failures


def m98_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M98_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M98: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M98_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M98 forbidden recurring automation runtime route present: {route}")
    return failures


def m99_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M99_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M99: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M99_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M99 forbidden autonomy/runtime route present: {route}")
    return failures


def m100_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M100_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M100: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M100_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M100 forbidden mobile permission runtime route present: {route}")
    return failures


def m101_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M101_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M101: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M101_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M101 forbidden mobile sensor runtime route present: {route}")
    return failures


def m102_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M102_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M102: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M102_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M102 forbidden location runtime route present: {route}")
    return failures


def m103_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M103_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M103: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M103_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M103 forbidden camera/photos runtime route present: {route}")
    return failures


def m104_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M104_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M104: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M104_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M104 forbidden notification runtime route present: {route}")
    return failures


def m105_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M105_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M105: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M105_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M105 forbidden background runtime route present: {route}")
    return failures


def m106_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M106_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M106: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M106_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M106 forbidden background status sync route present: {route}")
    return failures


def m107_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M107_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M107: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M107_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M107 forbidden approval renewal UX route present: {route}")
    return failures


def m108_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M108_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M108: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M108_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M108 forbidden kill-switch/revocation route present: {route}")
    return failures


def m109_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M109_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M109: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M109_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M109 forbidden sensor audit route present: {route}")
    return failures


def m110_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M110_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M110: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M110_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M110 forbidden sensor hardening route present: {route}")
    return failures


def m111_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M111_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M111: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M111_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M111 forbidden production threat model route present: {route}")
    return failures


def m112_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M112_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M112: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M112_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M112 forbidden identity runtime route present: {route}")
    return failures


def m113_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M113_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M113: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M113_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M113 forbidden secrets/credential route present: {route}")
    return failures


def m114_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M114_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M114: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M114_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M114 forbidden account connector route present: {route}")
    return failures


def m115_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M115_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M115: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M115_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M115 forbidden audit retention route present: {route}")
    return failures


def m116_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M116_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M116: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M116_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M116 forbidden role authority route present: {route}")
    return failures


def m117_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M117_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M117: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M117_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M117 forbidden remote agent coordination route present: {route}"
            )
    return failures


def m118_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M118_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M118: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M118_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M118 forbidden deployment mode matrix route present: {route}"
            )
    return failures


def m119_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M119_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M119: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M119_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M119 forbidden production red-team harness route present: {route}"
            )
    return failures


def m120_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M120_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M120: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M120_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M120 forbidden production authority readiness route present: {route}"
            )
    return failures


def m121_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M121_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M121: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M121_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M121 forbidden email connector runtime route present: {route}"
            )
    return failures


def m122_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M122_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M122: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M122_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M122 forbidden calendar connector runtime route present: {route}"
            )
    return failures


def m123_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M123_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M123: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M123_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M123 forbidden contacts connector runtime route present: {route}"
            )
    return failures


def m124_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M124_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M124: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M124_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M124 forbidden messages connector runtime route present: {route}"
            )
    return failures


def m125_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M125_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M125: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M125_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M125 forbidden connector read-only runtime route present: {route}"
            )
    return failures


def m126_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M126_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M126: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M126_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M126 forbidden connector approval capture route present: {route}"
            )
    return failures


def m127_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M127_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M127: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M127_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M127 forbidden connector write dry-run or execution route present: {route}"
            )
    return failures


def m128_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M128_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M128: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M128_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M128 forbidden connector write execution or audit route present: {route}"
            )
    return failures


def m129_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M129_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M129: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M129_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M129 forbidden connector audit, revocation, or freeze route present: {route}"
            )
    return failures


def m130_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M130_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M130: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M130_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M130 forbidden connector freeze, runtime, autonomy, or execution route present: {route}"
            )
    return failures


def m131_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M131_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M131: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M131_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M131 forbidden Mode 4 session, execution, runtime, or authority route present: {route}"
            )
    return failures


def m132_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M132_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M132: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M132_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M132 forbidden Mode 5 recurring workflow, scheduler, supervisor, execution, runtime, or authority route present: {route}"
            )
    return failures


def m133_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M133_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M133: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M133_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M133 forbidden long-running supervisor, scheduling, recovery, execution, runtime, or authority route present: {route}"
            )
    return failures


def m134_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M134_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M134: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M134_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M134 forbidden human checkpoint scheduling, prompt, notification, scheduler, recovery, execution, runtime, or authority route present: {route}"
            )
    return failures


def m135_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M135_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M135: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M135_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M135 forbidden autonomous recovery planner, recovery, retry, resume, rollback, scheduler, execution, runtime, or authority route present: {route}"
            )
    return failures


def m136_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M136_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M136: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M136_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M136 forbidden cross-tool dependency execution, resolver, tool, connector, browser, scheduler, execution, runtime, or authority route present: {route}"
            )
    return failures


def m137_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M137_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M137: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M137_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M137 forbidden browser, connector, combined workflow, execution, runtime, or authority route present: {route}"
            )
    return failures


def m138_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M138_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M138: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M138_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M138 forbidden error handling, retry, rollback, recovery, execution, runtime, or authority route present: {route}"
            )
    return failures


def m139_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M139_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M139: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M139_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M139 forbidden abuse/loop detection, monitor, intervention, execution, runtime, or authority route present: {route}"
            )
    return failures


def m140_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M140_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M140: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M140_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M140 forbidden red-team freeze, red-team runtime, multi-user, execution, browser, connector, or authority route present: {route}"
            )
    return failures


def m141_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M141_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M141: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M141_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M141 forbidden multi-user runtime, tenancy, auth, workspace sharing, execution, browser, connector, alpha, or authority route present: {route}"
            )
    return failures


def m142_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M142_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M142: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M142_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M142 forbidden alpha privacy review, alpha UI, raw privacy, execution, browser, connector, or authority route present: {route}"
            )
    return failures


def m143_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M143_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M143: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M143_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M143 forbidden alpha UI, app readiness, app build, app store, release, plugin marketplace, execution, browser, connector, or authority route present: {route}"
            )
    return failures


def m144_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M144_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M144: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M144_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M144 forbidden marketplace runtime, publishing, plugin install/enable/execute, package import/download/upload, network, or authority route present: {route}"
            )
    return failures


def m145_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M145_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M145: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M145_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M145 forbidden enterprise/pro runtime, plan enforcement, billing, account/auth, or authority route present: {route}"
            )
    return failures


def m146_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M146_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M146: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M146_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M146 forbidden billing runtime, payment, checkout, subscription, invoice, entitlement, plan enforcement, account-plan, external billing provider, or authority route present: {route}"
            )
    return failures


def m147_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M147_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M147: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M147_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M147 forbidden public docs, wiki, publishing, deploy, artifact upload, distribution, auth, or authority route present: {route}"
            )
    return failures


def m148_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M148_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M148: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M148_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M148 forbidden external security review, vendor handoff, scanner, vulnerability scan, repository export, artifact export, issue export, auth, or authority route present: {route}"
            )
    return failures


def m149_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M149_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M149: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M149_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M149 forbidden release candidate, release publication, tag, artifact, distribution, submission, beta, M150 release, automation, auth, or authority route present: {route}"
            )
    return failures


def m150_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M150_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M150: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M150_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M150 forbidden alpha target, release publication, tag, artifact, distribution, submission, beta, automation, auth, or authority route present: {route}"
            )
    return failures


def m152_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M152_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M152: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M152_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M152 forbidden local model management runtime, download, load, server, provider, or Control Center authority route present: {route}"
            )
    return failures


EXPECTED_M166_OPENAPI_PATH_COUNT = EXPECTED_M152_OPENAPI_PATH_COUNT
M166_FORBIDDEN_BACKEND_ROUTES = M120_FORBIDDEN_BACKEND_ROUTES + (
    "/production/release-gate/apply",
    "/production/release-gate/run",
    "/production/release-gate/execute",
    "/production/release-gate/approve",
    "/production/readiness/run",
    "/production/readiness/execute",
    "/production/load-test/run",
    "/production/package/build",
    "/production/security-scan/run",
    "/production/openwebui/e2e/run",
)


def m166_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M166_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M166: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M166_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M166 forbidden production readiness, release gate, go-live, rollback, packaging, load test, security scan, OpenWebUI E2E, or authority route present: {route}"
            )
    return failures


EXPECTED_M167_OPENAPI_PATH_COUNT = EXPECTED_M166_OPENAPI_PATH_COUNT
M167_FORBIDDEN_BACKEND_ROUTES = M166_FORBIDDEN_BACKEND_ROUTES + (
    "/production/live-model-hardening/run",
    "/production/live-model-hardening/apply",
    "/production/live-model-hardening/execute",
    "/production/model-matrix/run",
    "/production/model-matrix/execute",
    "/production/openwebui/e2e/run",
    "/production/openwebui/e2e/execute",
    "/production/load-soak/run",
    "/production/load-soak/execute",
    "/production/llama-server/install",
    "/production/llama-server/update",
    "/production/model-selection/calibrate",
    "/production/tuning/apply",
)


def m167_openapi_route_failures(
    paths: Iterable[str], expected_path_count: int = EXPECTED_M167_OPENAPI_PATH_COUNT
) -> List[str]:
    path_set = _post_m151_route_boundary_path_set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(
            f"OpenAPI path count changed for M167: expected {expected_path_count}, got {len(path_set)}"
        )
    for route in M167_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(
                f"M167 forbidden live hardening, model matrix, llama-server install, selection calibration, tuning apply, load soak, OpenWebUI E2E, or authority route present: {route}"
            )
    return failures

__all__ = [
    name
    for name in globals()
    if not name.startswith("__")
    and name not in {"re", "Iterable", "List"}
]
