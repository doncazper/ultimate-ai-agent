from pathlib import Path
import json
import re
import tempfile
from typing import Callable, Dict, Iterable, List, Optional

from pydantic import ValidationError

from ultimate_ai_agent.core.consent import ConsentLedger
from ultimate_ai_agent.core.consent.enums import DataBoundary
from ultimate_ai_agent.core.files import FileKind, FileRef, FileSensitivity
from ultimate_ai_agent.core.gate.criteria import FoundationGateCriterion, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.reports import FoundationGateReport, FoundationGateResult, build_foundation_gate_report
from ultimate_ai_agent.core.gate.shadow_replay import run_m5_shadow_replay
from ultimate_ai_agent.core.context_budget import ContextBudget
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.costs import BudgetScope, BudgetStatus, CostBudget, CostEstimate, CostGovernor
from ultimate_ai_agent.core.model_router import (
    ModelCapabilityProfile,
    ModelPrivacyClass,
    ModelProviderKind,
    ModelRouteStatus,
    ModelRouter,
    ModelRouteRequest,
    ModelRoutingPolicy,
    ModelTaskCapability,
)
from ultimate_ai_agent.core.memory import MemoryRecord
from ultimate_ai_agent.core.memory.enums import MemoryAuthority, MemoryScope, MemorySensitivity, MemoryType
from ultimate_ai_agent.core.memory.records import MemorySourceRef
from ultimate_ai_agent.core.tools import (
    CapabilityFirewallPolicy,
    ToolBroker,
    ToolCategory,
    ToolDecisionStatus,
    ToolExecutionMode,
    ToolManifest,
    ToolRegistry,
    ToolRequest,
    ToolRiskLevel,
)
from ultimate_ai_agent.core.truth import EvidenceItem, EvidenceManifest, TruthSourceManifest
from ultimate_ai_agent.core.truth.claims import ClaimEvidence
from ultimate_ai_agent.core.truth.enums import (
    ClaimVerificationStatus,
    SourceFreshnessStatus,
    TruthAuthorityLevel,
    TruthSourceType,
)


EXPECTED_M16_OPENAPI_PATH_COUNT = 74
M16_FORBIDDEN_BACKEND_ROUTES = (
    "/events/timeline",
    "/control-center/events/timeline",
    "/timeline",
    "/trace",
    "/trace/export",
    "/events/raw",
    "/telemetry/export",
)
EXPECTED_M17_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M18_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M19_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M20_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M21_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M22_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M23_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M24_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M25_OPENAPI_PATH_COUNT = 74
M25_FORBIDDEN_BACKEND_ROUTES = (
    "/truth/verify",
    "/claims/verify",
    "/evidence/verify",
    "/truth/search",
    "/truth/web-search",
    "/truth/model-verify",
)
EXPECTED_M26_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M27_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M28_OPENAPI_PATH_COUNT = 74
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
)
EXPECTED_M29_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M30_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M31_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M32_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M33_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M34_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M35_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M36_OPENAPI_PATH_COUNT = 74
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
EXPECTED_M37_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M38_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M39_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M40_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M41_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M42_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M43_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M44_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M45_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M46_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M47_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M48_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M49_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M50_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M51_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M52_OPENAPI_PATH_COUNT = 75
M52_FORBIDDEN_BACKEND_ROUTES = M51_FORBIDDEN_BACKEND_ROUTES + (
    "/openwebui/conversation",
    "/openwebui/conversation/send",
    "/openwebui/conversation/raw",
    "/openwebui/conversation/provider-payload",
    "/openwebui/conversation/context",
    "/openwebui/conversation/memory",
)
EXPECTED_M53_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M54_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M55_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M56_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M57_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M58_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M59_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M60_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M61_OPENAPI_PATH_COUNT = 75
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
EXPECTED_M62_OPENAPI_PATH_COUNT = 75
M62_FORBIDDEN_BACKEND_ROUTES = M61_FORBIDDEN_BACKEND_ROUTES + (
    "/autonomy/session/activate",
    "/autonomy/session/execute",
    "/autonomy/session/stop",
    "/autonomy/session/status",
    "/autonomy/session/background",
    "/autonomy/session/approval",
    "/autonomy/session/persist",
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
    "scripts/verify_all.py",
    "scripts/verify_control_center_frontend.py",
}


def _historical_openapi_path_set(paths: Iterable[str]) -> set[str]:
    """Normalize current OpenAPI paths for historical route-count gates."""
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
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
    path_set = set(paths)
    failures: List[str] = []
    if len(path_set) != expected_path_count:
        failures.append(f"OpenAPI path count expected {expected_path_count}, found {len(path_set)}")
    if M37_ALLOWED_CAPTURE_ROUTE not in path_set:
        failures.append("M37 capture route missing: /files/review/approvals/capture")
    for route in M62_FORBIDDEN_BACKEND_ROUTES:
        if route in path_set:
            failures.append(f"M62 forbidden autonomy session/execution/backend route present: {route}")
    return failures


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
M36_PRIVATE_OR_RAW_PATH_FRAGMENT = re.compile(
    r"(/Users/|/home/|[A-Za-z]:\\|\.\./|absolute_path|raw_absolute_path|raw file path)",
    re.IGNORECASE,
)
M36_MUTATING_FILE_REVIEW_REQUEST = re.compile(
    r"fetch\([^)]*(?:/files/review|/files/read|/context/propose|/context/inject|/memory/write|/tools/execute)[^)]*"
    r"method\s*:\s*['\"](?:POST|PUT|PATCH|DELETE)['\"]",
    re.IGNORECASE | re.DOTALL,
)


def m36_file_review_surface_failures(component_text: str, mock_text: str) -> List[str]:
    failures: List[str] = []
    for match in M36_MUTATING_FILE_REVIEW_REQUEST.finditer(component_text):
        failures.append(f"mutating M36 file review request: {match.group(0).strip()}")

    m36_index = mock_text.lower().find("m36filereview")
    m36_text = mock_text[m36_index:] if m36_index != -1 else mock_text
    for match in M36_PRIVATE_OR_RAW_PATH_FRAGMENT.finditer(m36_text):
        failures.append(f"private path fragment in M36 file review fixture: {match.group(0)}")
    for field_name, prefix in M36_SAFE_REF_PREFIXES.items():
        for match in re.finditer(rf"{field_name}\s*:\s*['\"]([^'\"]+)['\"]", m36_text):
            value = match.group(1)
            if not value.startswith(prefix):
                label = M36_SAFE_REF_LABELS[field_name]
                failures.append(f"unsafe M36 {label} value: expected prefix {prefix}")
    return failures


def m37_control_center_surface_failures(component_text: str) -> List[str]:
    failures: List[str] = []
    lowered = component_text.lower()
    required = {
        "approve review-only control missing": "approve review-only",
        "deny review-only control missing": "deny review-only",
        "review-only persistence copy missing": "review-only persistence",
        "exact packet binding copy missing": "exact selected packet",
        "raw authority denial missing": "raw file access",
        "context proposal denial missing": "context proposal",
        "memory write denial missing": "memory writes",
        "export denial missing": "export",
        "execution denial missing": "execution",
    }
    for message, fragment in required.items():
        if fragment not in lowered:
            failures.append(message)
    for fragment in (
        "export raw",
        "download",
        "copy raw",
        "file picker",
        "root selector",
        "open raw file",
        "inject context",
        "write memory",
        "execute tool",
        "run tool",
        "call model",
    ):
        if fragment in lowered:
            failures.append(f"M37 component exposes forbidden control/copy: {fragment}")
    return failures


def _normalize_m34_active_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("|", " | ").lower()).strip()


def m34_active_currentness_failures(active_docs: Dict[str, str]) -> List[str]:
    failures: List[str] = []
    readme = _normalize_m34_active_text(active_docs.get("README.md", ""))
    if "v0.38.0 | m34 - broader file capability review | planned/provisional" in readme:
        failures.append("README.md must not list v0.38.0/M34 as planned/provisional")

    stale_m33_docs = sorted(
        rel_path
        for rel_path, text in active_docs.items()
        if rel_path.startswith(("docs/tools/REDACTED_FILE_PREVIEW_", "docs/files/LOCAL_FILE_REDACTED_PREVIEW_"))
        and "m34 remains planned/provisional" in text.lower()
    )
    if stale_m33_docs:
        failures.append(
            "active M33 docs must not say M34 remains planned/provisional after v0.38.0: "
            + ", ".join(stale_m33_docs)
        )

    return failures


def m22_local_runtime_forbidden_fragment_failures(root: Path) -> List[str]:
    failures: List[str] = []
    runtime_root = root / "src" / "ultimate_ai_agent" / "core" / "model_runtime"
    if not runtime_root.exists():
        return failures
    for path in runtime_root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if any(part in M22_LOCAL_RUNTIME_SCAN_EXCLUDED_DIRS for part in path.parts):
            continue
        if rel in M22_LOCAL_RUNTIME_ALLOWED_SOURCE_FILES:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in M22_FORBIDDEN_LOCAL_RUNTIME_FRAGMENTS:
            if fragment in text:
                failures.append(f"M22 forbidden local runtime fragment in {rel}: {fragment}")
    return failures


def _is_doc_path(rel_path: str) -> bool:
    return rel_path == "docs" or rel_path.startswith("docs/")


def _iter_m21_openwebui_non_doc_paths(root: Path) -> Iterable[Path]:
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue
        for path in children:
            rel = path.relative_to(root).as_posix()
            if path.name in M21_OPENWEBUI_SCAN_EXCLUDED_DIRS or _is_doc_path(rel):
                continue
            yield path
            if path.is_dir():
                pending.append(path)


def m21_forbidden_openwebui_config_path_matches(root: Path) -> List[str]:
    matches: set[str] = set()
    for path in _iter_m21_openwebui_non_doc_paths(root):
        rel = path.relative_to(root).as_posix()
        lowered = rel.lower()
        if any(fragment in lowered for fragment in M21_FORBIDDEN_OPENWEBUI_CONFIG_PATH_FRAGMENTS):
            matches.add(rel)
    return sorted(matches)


def m21_forbidden_openwebui_runtime_fragment_failures(root: Path) -> List[str]:
    failures: List[str] = []
    implementation_roots = [root / "src", root / "apps", root / "scripts"]
    for implementation_root in implementation_roots:
        if not implementation_root.exists():
            continue
        candidate_files: list[Path] = []
        if implementation_root.name in {"src", "scripts"}:
            candidate_files.extend(implementation_root.rglob("*.py"))
        else:
            candidate_files.extend(implementation_root.rglob("*.ts"))
            candidate_files.extend(implementation_root.rglob("*.tsx"))
            candidate_files.extend(implementation_root.rglob("*.js"))
            candidate_files.extend(implementation_root.rglob("*.jsx"))
            candidate_files.extend(implementation_root.rglob("*.json"))
        for path in candidate_files:
            rel = path.relative_to(root).as_posix()
            if not path.is_file() or any(part in M21_OPENWEBUI_SCAN_EXCLUDED_DIRS for part in path.parts):
                continue
            if rel in M21_OPENWEBUI_ALLOWED_FRAGMENT_SCAN_FILES:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for pattern in M21_FORBIDDEN_OPENWEBUI_RUNTIME_PATTERNS:
                if pattern.search(text):
                    failures.append(f"M21 forbidden OpenWebUI runtime/config import in {rel}: {pattern.pattern}")
            for fragment in M21_FORBIDDEN_OPENWEBUI_RUNTIME_FRAGMENTS:
                if fragment in text:
                    failures.append(f"M21 forbidden OpenWebUI runtime/config fragment in {rel}: {fragment}")
    return failures


class FoundationGateEvaluator:
    def __init__(self, root: Optional[Path] = None):
        self.root = root or Path(__file__).resolve().parents[4]
        self.src_root = self.root / "src" / "ultimate_ai_agent"

    def evaluate(self, criteria: Optional[List[FoundationGateCriterion]] = None) -> FoundationGateReport:
        criteria = criteria or default_foundation_gate_criteria()
        evaluator_map: Dict[str, Callable[[FoundationGateCriterion], FoundationGateResult]] = {
            "versioning_consistent": self.check_versioning_consistent,
            "release_docs_present": self.check_release_docs_present,
            "foundation_modules_present": self.check_foundation_modules_present,
            "blocked_modules_absent": self.check_blocked_modules_absent,
            "forbidden_runtime_integrations_absent": self.check_forbidden_runtime_integrations_absent,
            "shell_execution_absent": self.check_shell_execution_absent,
            "broad_filesystem_scanning_absent": self.check_broad_filesystem_scanning_absent,
            "secret_hygiene_clean": self.check_secret_hygiene_clean,
            "tool_broker_blocks_advanced_adapters": self.check_tool_broker_blocks_advanced_adapters,
            "truth_evidence_contracts_valid": self.check_truth_evidence_contracts_valid,
            "memory_file_contracts_valid": self.check_memory_file_contracts_valid,
            "m5_shadow_replay_passes": self.check_m5_shadow_replay_passes,
            "m7_modules_present": self.check_m7_modules_present,
            "model_router_decision_only": self.check_model_router_decision_only,
            "cost_governor_blocks_over_budget": self.check_cost_governor_blocks_over_budget,
            "m7_arbitrary_approval_ref_rejected": self.check_m7_arbitrary_approval_ref_rejected,
            "m7_context_budget_exhaustion_blocks_route": self.check_m7_context_budget_exhaustion_blocks_route,
            "m7_soft_budget_warning_allows_route": self.check_m7_soft_budget_warning_allows_route,
            "m7_hard_budget_denies_route": self.check_m7_hard_budget_denies_route,
            "m7_cost_warnings_visible_in_route_decision": self.check_m7_cost_warnings_visible_in_route_decision,
            "api_manifest_endpoint_present": self.check_api_manifest_endpoint_present,
            "openapi_contract_valid": self.check_openapi_contract_valid,
            "api_operation_ids_unique": self.check_api_operation_ids_unique,
            "forbidden_runtime_routes_absent": self.check_forbidden_runtime_routes_absent,
            "agents_md_guidance_present": self.check_agents_md_guidance_present,
            "runtime_agent_config_loading_absent": self.check_runtime_agent_config_loading_absent,
            "m8_model_runtime_files_present": self.check_m8_model_runtime_files_present,
            "m8_runtime_kinds_stub_only": self.check_m8_runtime_kinds_stub_only,
            "m8_model_runtime_no_real_calls": self.check_m8_model_runtime_no_real_calls,
            "m8_simulation_endpoint_safe": self.check_m8_simulation_endpoint_safe,
            "m8_runtime_responses_simulated_only": self.check_m8_runtime_responses_simulated_only,
            "m8_runtime_secret_prompt_blocked": self.check_m8_runtime_secret_prompt_blocked,
            "m8_api_validation_secret_echo_absent": self.check_m8_api_validation_secret_echo_absent,
            "m85_approval_authority_files_present": self.check_m85_approval_authority_files_present,
            "m85_arbitrary_approval_refs_rejected": self.check_m85_arbitrary_approval_refs_rejected,
            "m85_local_approval_grant_validates": self.check_m85_local_approval_grant_validates,
            "m85_expired_revoked_approval_denies": self.check_m85_expired_revoked_approval_denies,
            "m85_router_uses_valid_approval_grant": self.check_m85_router_uses_valid_approval_grant,
            "m85_runtime_factory_rejects_arbitrary_approval": self.check_m85_runtime_factory_rejects_arbitrary_approval,
            "m85_tool_broker_rejects_arbitrary_approval": self.check_m85_tool_broker_rejects_arbitrary_approval,
            "m85_no_real_auth_oauth_network": self.check_m85_no_real_auth_oauth_network,
            "m85_approval_api_secret_echo_absent": self.check_m85_approval_api_secret_echo_absent,
            "m9_loopback_runtime_files_present": self.check_m9_loopback_runtime_files_present,
            "m9_non_loopback_endpoints_denied": self.check_m9_non_loopback_endpoints_denied,
            "m9_non_loopback_policy_override_denied": self.check_m9_non_loopback_policy_override_denied,
            "m9_loopback_policy_model_rejects_hostile_inputs": self.check_m9_loopback_policy_model_rejects_hostile_inputs,
            "m9_public_and_private_ip_endpoints_denied": self.check_m9_public_and_private_ip_endpoints_denied,
            "m9_approval_api_uses_public_authority_helper": self.check_m9_approval_api_uses_public_authority_helper,
            "m9_arbitrary_approval_refs_denied": self.check_m9_arbitrary_approval_refs_denied,
            "m9_fake_transport_only_in_gate": self.check_m9_fake_transport_only_in_gate,
            "m9_simulated_fallback_available": self.check_m9_simulated_fallback_available,
            "m9_model_output_not_truth_authority": self.check_m9_model_output_not_truth_authority,
            "m10_manual_smoke_files_present": self.check_m10_manual_smoke_files_present,
            "m10_stdlib_network_isolated": self.check_m10_stdlib_network_isolated,
            "m10_gate_and_verify_do_not_call_smoke_script": self.check_m10_gate_and_verify_do_not_call_smoke_script,
            "m10_public_api_has_no_smoke_execute_endpoint": self.check_m10_public_api_has_no_smoke_execute_endpoint,
            "m10_fixed_prompt_and_loopback_policy_enforced": self.check_m10_fixed_prompt_and_loopback_policy_enforced,
            "m10_smoke_approval_required": self.check_m10_smoke_approval_required,
            "m10_smoke_response_not_truth_authority": self.check_m10_smoke_response_not_truth_authority,
            "m105_remote_worker_files_present": self.check_m105_remote_worker_files_present,
            "m105_remote_capabilities_default_safe": self.check_m105_remote_capabilities_default_safe,
            "m105_unknown_node_and_transport_denied": self.check_m105_unknown_node_and_transport_denied,
            "m105_planned_transports_disabled": self.check_m105_planned_transports_disabled,
            "m105_dry_run_dispatches_nothing": self.check_m105_dry_run_dispatches_nothing,
            "m105_no_remote_network_or_background_execution": self.check_m105_no_remote_network_or_background_execution,
            "m105_no_remote_subagents_tools_or_approvals": self.check_m105_no_remote_subagents_tools_or_approvals,
            "m105_remote_output_untrusted": self.check_m105_remote_output_untrusted,
            "m105_api_routes_are_dry_run_only": self.check_m105_api_routes_are_dry_run_only,
            "m105_docs_foundation_only": self.check_m105_docs_foundation_only,
            "m105_remote_tailnet_enable_flag_rejected": self.check_m105_remote_tailnet_enable_flag_rejected,
            "m105_remote_personal_data_enable_flag_rejected": self.check_m105_remote_personal_data_enable_flag_rejected,
            "m105_remote_worker_api_extra_fields_forbidden": self.check_m105_remote_worker_api_extra_fields_forbidden,
            "m143_private_mesh_taxonomy_open_source_first": self.check_m143_private_mesh_taxonomy_open_source_first,
            "m143_planned_mesh_transports_disabled": self.check_m143_planned_mesh_transports_disabled,
            "m143_no_live_mesh_integrations": self.check_m143_no_live_mesh_integrations,
            "m11_runtime_readiness_files_present": self.check_m11_runtime_readiness_files_present,
            "m11_runtime_capability_matrix_safe": self.check_m11_runtime_capability_matrix_safe,
            "m11_manual_smoke_report_validation_safe": self.check_m11_manual_smoke_report_validation_safe,
            "m11_no_production_readiness_claim": self.check_m11_no_production_readiness_claim,
            "m11_runtime_api_status_validation_only": self.check_m11_runtime_api_status_validation_only,
            "m11_no_smoke_script_execution_in_gate": self.check_m11_no_smoke_script_execution_in_gate,
            "m11_no_runtime_expansion_imports": self.check_m11_no_runtime_expansion_imports,
            "m11_no_remote_mesh_mobile_or_plugin_enablement": self.check_m11_no_remote_mesh_mobile_or_plugin_enablement,
            "m12_control_center_files_present": self.check_m12_control_center_files_present,
            "m12_control_center_manifest_read_only": self.check_m12_control_center_manifest_read_only,
            "m12_control_center_dashboard_secret_safe": self.check_m12_control_center_dashboard_secret_safe,
            "m12_control_center_action_preview_no_execution": self.check_m12_control_center_action_preview_no_execution,
            "m12_control_center_api_read_only": self.check_m12_control_center_api_read_only,
            "m12_no_frontend_dependencies": self.check_m12_no_frontend_dependencies,
            "m12_no_runtime_network_mobile_plugin_expansion": self.check_m12_no_runtime_network_mobile_plugin_expansion,
            "m13_web_control_center_files_present": self.check_m13_web_control_center_files_present,
            "m13_web_shell_read_only_preview_only": self.check_m13_web_shell_read_only_preview_only,
            "m13_action_preview_ui_posts_only_to_preview": self.check_m13_action_preview_ui_posts_only_to_preview,
            "m13_mock_data_safe_non_authoritative": self.check_m13_mock_data_safe_non_authoritative,
            "m13_no_tracked_generated_or_native_artifacts": self.check_m13_no_tracked_generated_or_native_artifacts,
            "m13_backend_api_contract_unchanged": self.check_m13_backend_api_contract_unchanged,
            "m13_frontend_no_sensitive_browser_apis": self.check_m13_frontend_no_sensitive_browser_apis,
            "m13_control_center_frontend_safety_verifier_passes": self.check_m13_control_center_frontend_safety_verifier_passes,
            "m13_frontend_ci_covers_local_checks": self.check_m13_frontend_ci_covers_local_checks,
            "m13_browser_smoke_readiness_manual_local_only": self.check_m13_browser_smoke_readiness_manual_local_only,
            "m13_browser_smoke_readiness_verifier_passes": self.check_m13_browser_smoke_readiness_verifier_passes,
            "m14_local_backend_api_base_policy": self.check_m14_local_backend_api_base_policy,
            "m14_connection_states_visible_and_safe": self.check_m14_connection_states_visible_and_safe,
            "m14_backend_api_contract_unchanged": self.check_m14_backend_api_contract_unchanged,
            "m15_approval_receipt_event_ui_safe": self.check_m15_approval_receipt_event_ui_safe,
            "m16_event_timeline_trace_viewer_safe": self.check_m16_event_timeline_trace_viewer_safe,
            "m17_evidence_file_memory_viewer_safe": self.check_m17_evidence_file_memory_viewer_safe,
            "m17_evidence_file_memory_viewer_hardening_safe": self.check_m17_evidence_file_memory_viewer_hardening_safe,
            "m18_local_runtime_manual_smoke_surface_safe": self.check_m18_local_runtime_manual_smoke_surface_safe,
            "m19_mobile_companion_contract_planning_safe": self.check_m19_mobile_companion_contract_planning_safe,
            "m20_device_capability_broker_contract_safe": self.check_m20_device_capability_broker_contract_safe,
            "m21_openwebui_bridge_contract_safe": self.check_m21_openwebui_bridge_contract_safe,
            "m22_local_model_runtime_activation_contract_safe": (
                self.check_m22_local_model_runtime_activation_contract_safe
            ),
            "m23_first_local_llm_call_safe": self.check_m23_first_local_llm_call_safe,
            "m24_memory_provider_local_store_safe": self.check_m24_memory_provider_local_store_safe,
            "m25_truth_source_router_contracts_valid": self.check_m25_truth_source_router_contracts_valid,
            "m25_truth_openapi_routes_unchanged": self.check_m25_truth_openapi_routes_unchanged,
            "v0292_local_dev_api_authority_and_preview_safe": (
                self.check_v0292_local_dev_api_authority_and_preview_safe
            ),
            "m25_m26_remains_future": self.check_m25_m26_remains_future,
            "m26_grounded_recall_context_pack_safe": self.check_m26_grounded_recall_context_pack_safe,
            "m26_recall_openapi_routes_unchanged": self.check_m26_recall_openapi_routes_unchanged,
            "m26_m27_remains_future": self.check_m26_m27_remains_future,
            "m27_tool_broker_v2_contract_safe": self.check_m27_tool_broker_v2_contract_safe,
            "m27_tool_broker_v2_openapi_routes_unchanged": self.check_m27_tool_broker_v2_openapi_routes_unchanged,
            "m27_m28_remains_future": self.check_m27_m28_remains_future,
            "m28_approval_authority_v2_action_policy_safe": self.check_m28_approval_authority_v2_action_policy_safe,
            "m28_action_policy_openapi_routes_unchanged": self.check_m28_action_policy_openapi_routes_unchanged,
            "m28_m29_remains_future": self.check_m28_m29_remains_future,
            "m29_task_planning_engine_contract_safe": self.check_m29_task_planning_engine_contract_safe,
            "m29_task_planning_openapi_routes_unchanged": self.check_m29_task_planning_openapi_routes_unchanged,
            "m29_m30_remains_future": self.check_m29_m30_remains_future,
            "m30_execution_framework_contract_safe": self.check_m30_execution_framework_contract_safe,
            "m30_execution_openapi_routes_unchanged": self.check_m30_execution_openapi_routes_unchanged,
            "m30_m31_remains_future": self.check_m30_m31_remains_future,
            "m31_tool_runtime_noop_contract_safe": self.check_m31_tool_runtime_noop_contract_safe,
            "m31_tool_runtime_openapi_routes_unchanged": self.check_m31_tool_runtime_openapi_routes_unchanged,
            "m31_m32_remains_future": self.check_m31_m32_remains_future,
            "m32_filesystem_metadata_tool_safe": self.check_m32_filesystem_metadata_tool_safe,
            "m32_filesystem_metadata_openapi_routes_unchanged": self.check_m32_filesystem_metadata_openapi_routes_unchanged,
            "m32_m33_remains_future": self.check_m32_m33_remains_future,
            "m33_redacted_file_preview_tool_safe": self.check_m33_redacted_file_preview_tool_safe,
            "m33_redacted_file_preview_openapi_routes_unchanged": (
                self.check_m33_redacted_file_preview_openapi_routes_unchanged
            ),
            "m33_m34_remains_future": self.check_m33_m34_remains_future,
            "m34_broader_file_capability_review_docs_present": (
                self.check_m34_broader_file_capability_review_docs_present
            ),
            "m34_file_capability_openapi_routes_unchanged": (
                self.check_m34_file_capability_openapi_routes_unchanged
            ),
            "m34_m35_m36_remain_future": self.check_m34_m35_m36_remain_future,
            "m35_safe_file_review_workflow_contract_safe": (
                self.check_m35_safe_file_review_workflow_contract_safe
            ),
            "m35_file_review_openapi_routes_unchanged": self.check_m35_file_review_openapi_routes_unchanged,
            "m35_m36_m37_m38_remain_future": self.check_m35_m36_m37_m38_remain_future,
            "m36_ccc_file_review_surface_safe": self.check_m36_ccc_file_review_surface_safe,
            "m36_file_review_openapi_routes_unchanged": self.check_m36_file_review_openapi_routes_unchanged,
            "m36_m37_m38_remain_future": self.check_m36_m37_m38_remain_future,
            "m37_file_review_approval_capture_contracts": self.check_m37_file_review_approval_capture_contracts,
            "m37_file_review_approval_capture_route_boundary": self.check_m37_file_review_approval_capture_route_boundary,
            "m37_control_center_review_only_approval_capture": (
                self.check_m37_control_center_review_only_approval_capture
            ),
            "m37_roadmap_currentness": self.check_m37_roadmap_currentness,
            "m38_safe_context_proposal_contracts": self.check_m38_safe_context_proposal_contracts,
            "m38_safe_context_proposal_route_boundary": self.check_m38_safe_context_proposal_route_boundary,
            "m38_no_control_center_context_surface": self.check_m38_no_control_center_context_surface,
            "m38_roadmap_currentness": self.check_m38_roadmap_currentness,
            "m39_ccc_context_proposal_surface_safe": self.check_m39_ccc_context_proposal_surface_safe,
            "m39_context_proposal_route_boundary": self.check_m39_context_proposal_route_boundary,
            "m39_roadmap_currentness": self.check_m39_roadmap_currentness,
            "m40_context_handoff_approval_contracts": self.check_m40_context_handoff_approval_contracts,
            "m40_context_handoff_route_boundary": self.check_m40_context_handoff_route_boundary,
            "m40_roadmap_currentness": self.check_m40_roadmap_currentness,
            "m41_local_prototype_safety_freeze": self.check_m41_local_prototype_safety_freeze,
            "m41_local_prototype_route_boundary": self.check_m41_local_prototype_route_boundary,
            "m41_roadmap_currentness": self.check_m41_roadmap_currentness,
            "m42_mobile_product_contract_refresh": self.check_m42_mobile_product_contract_refresh,
            "m42_mobile_route_boundary": self.check_m42_mobile_route_boundary,
            "m42_roadmap_currentness": self.check_m42_roadmap_currentness,
            "m43_mobile_api_boundary_read_only": self.check_m43_mobile_api_boundary_read_only,
            "m43_mobile_route_boundary": self.check_m43_mobile_route_boundary,
            "m43_roadmap_currentness": self.check_m43_roadmap_currentness,
            "m44_ccc_ios_skeleton_no_authority": self.check_m44_ccc_ios_skeleton_no_authority,
            "m44_ios_skeleton_static_safety": self.check_m44_ios_skeleton_static_safety,
            "m44_mobile_route_boundary": self.check_m44_mobile_route_boundary,
            "m44_roadmap_currentness": self.check_m44_roadmap_currentness,
            "m45_ccc_ios_local_read_only_connection": self.check_m45_ccc_ios_local_read_only_connection,
            "m45_ios_local_connection_static_safety": self.check_m45_ios_local_connection_static_safety,
            "m45_mobile_route_boundary": self.check_m45_mobile_route_boundary,
            "m45_roadmap_currentness": self.check_m45_roadmap_currentness,
            "m46_ccc_ios_review_receipt_read_only_surfaces": (
                self.check_m46_ccc_ios_review_receipt_read_only_surfaces
            ),
            "m46_ios_review_receipt_static_safety": self.check_m46_ios_review_receipt_static_safety,
            "m46_mobile_route_boundary": self.check_m46_mobile_route_boundary,
            "m46_roadmap_currentness": self.check_m46_roadmap_currentness,
            "m47_internal_testflight_pipeline_contract": (
                self.check_m47_internal_testflight_pipeline_contract
            ),
            "m47_testflight_static_safety": self.check_m47_testflight_static_safety,
            "m47_mobile_route_boundary": self.check_m47_mobile_route_boundary,
            "m47_roadmap_currentness": self.check_m47_roadmap_currentness,
            "m48_first_internal_testflight_build_candidate": (
                self.check_m48_first_internal_testflight_build_candidate
            ),
            "m48_testflight_build_static_safety": self.check_m48_testflight_build_static_safety,
            "m48_mobile_route_boundary": self.check_m48_mobile_route_boundary,
            "m48_roadmap_currentness": self.check_m48_roadmap_currentness,
            "m49_mobile_review_approval_capture": self.check_m49_mobile_review_approval_capture,
            "m49_mobile_approval_static_safety": self.check_m49_mobile_approval_static_safety,
            "m49_mobile_route_boundary": self.check_m49_mobile_route_boundary,
            "m49_roadmap_currentness": self.check_m49_roadmap_currentness,
            "m50_mobile_approval_audit_hardening": self.check_m50_mobile_approval_audit_hardening,
            "m50_mobile_audit_static_safety": self.check_m50_mobile_audit_static_safety,
            "m50_mobile_audit_route_boundary": self.check_m50_mobile_audit_route_boundary,
            "m50_roadmap_currentness": self.check_m50_roadmap_currentness,
            "m51_openwebui_bridge_adapter_pilot": self.check_m51_openwebui_bridge_adapter_pilot,
            "m51_openwebui_adapter_static_safety": self.check_m51_openwebui_adapter_static_safety,
            "m51_openwebui_adapter_route_boundary": self.check_m51_openwebui_adapter_route_boundary,
            "m51_roadmap_currentness": self.check_m51_roadmap_currentness,
            "m52_openwebui_safe_conversation_surface": self.check_m52_openwebui_safe_conversation_surface,
            "m52_openwebui_safe_conversation_static_safety": (
                self.check_m52_openwebui_safe_conversation_static_safety
            ),
            "m52_openwebui_safe_conversation_route_boundary": (
                self.check_m52_openwebui_safe_conversation_route_boundary
            ),
            "m52_roadmap_currentness": self.check_m52_roadmap_currentness,
            "m53_controlled_tool_expansion_review": self.check_m53_controlled_tool_expansion_review,
            "m53_controlled_tool_expansion_static_safety": (
                self.check_m53_controlled_tool_expansion_static_safety
            ),
            "m53_controlled_tool_expansion_route_boundary": (
                self.check_m53_controlled_tool_expansion_route_boundary
            ),
            "m53_roadmap_currentness": self.check_m53_roadmap_currentness,
            "m54_safe_media_metadata_inspector": self.check_m54_safe_media_metadata_inspector,
            "m54_safe_media_metadata_static_safety": (
                self.check_m54_safe_media_metadata_static_safety
            ),
            "m54_safe_media_metadata_route_boundary": (
                self.check_m54_safe_media_metadata_route_boundary
            ),
            "m54_roadmap_currentness": self.check_m54_roadmap_currentness,
            "m55_redacted_observability_export": self.check_m55_redacted_observability_export,
            "m55_observability_export_static_safety": (
                self.check_m55_observability_export_static_safety
            ),
            "m55_observability_export_route_boundary": (
                self.check_m55_observability_export_route_boundary
            ),
            "m55_roadmap_currentness": self.check_m55_roadmap_currentness,
            "m56_agent_eval_regression_harness": self.check_m56_agent_eval_regression_harness,
            "m56_eval_regression_static_safety": self.check_m56_eval_regression_static_safety,
            "m56_eval_regression_route_boundary": self.check_m56_eval_regression_route_boundary,
            "m56_roadmap_currentness": self.check_m56_roadmap_currentness,
            "m57_runtime_sandbox_architecture_review": (
                self.check_m57_runtime_sandbox_architecture_review
            ),
            "m57_runtime_sandbox_static_safety": self.check_m57_runtime_sandbox_static_safety,
            "m57_runtime_sandbox_route_boundary": self.check_m57_runtime_sandbox_route_boundary,
            "m57_roadmap_currentness": self.check_m57_roadmap_currentness,
            "m58_dry_run_execution_audit_harness": (
                self.check_m58_dry_run_execution_audit_harness
            ),
            "m58_dry_run_execution_static_safety": self.check_m58_dry_run_execution_static_safety,
            "m58_dry_run_execution_route_boundary": self.check_m58_dry_run_execution_route_boundary,
            "m58_roadmap_currentness": self.check_m58_roadmap_currentness,
            "m59_public_github_readiness_review": self.check_m59_public_github_readiness_review,
            "m59_public_github_readiness_static_safety": (
                self.check_m59_public_github_readiness_static_safety
            ),
            "m59_public_github_readiness_route_boundary": (
                self.check_m59_public_github_readiness_route_boundary
            ),
            "m59_roadmap_currentness": self.check_m59_roadmap_currentness,
            "m60_local_developer_beta_freeze_review": (
                self.check_m60_local_developer_beta_freeze_review
            ),
            "m60_local_developer_beta_freeze_static_safety": (
                self.check_m60_local_developer_beta_freeze_static_safety
            ),
            "m60_local_developer_beta_freeze_route_boundary": (
                self.check_m60_local_developer_beta_freeze_route_boundary
            ),
            "m60_final_roadmap_currentness": self.check_m60_final_roadmap_currentness,
            "m61_autonomy_mode_charter_review": self.check_m61_autonomy_mode_charter_review,
            "m61_autonomy_mode_charter_static_safety": (
                self.check_m61_autonomy_mode_charter_static_safety
            ),
            "m61_autonomy_mode_charter_route_boundary": (
                self.check_m61_autonomy_mode_charter_route_boundary
            ),
            "m61_roadmap_currentness": self.check_m61_roadmap_currentness,
            "m62_scoped_autonomy_session_contract_review": (
                self.check_m62_scoped_autonomy_session_contract_review
            ),
            "m62_scoped_autonomy_session_static_safety": (
                self.check_m62_scoped_autonomy_session_static_safety
            ),
            "m62_scoped_autonomy_session_route_boundary": (
                self.check_m62_scoped_autonomy_session_route_boundary
            ),
            "m62_roadmap_currentness": self.check_m62_roadmap_currentness,
            "open_design_governance_docs_present": self.check_open_design_governance_docs_present,
            "openwebui_ccc_strategy_docs_present": self.check_openwebui_ccc_strategy_docs_present,
            "post_m20_roadmap_projection_present": self.check_post_m20_roadmap_projection_present,
            "roadmap_milestone_charters_current": self.check_roadmap_milestone_charters_current,
            "documentation_integrity_current": self.check_documentation_integrity_current,
            "codex_plugin_governance_docs_present": self.check_codex_plugin_governance_docs_present,
        }
        results = [
            evaluator_map.get(criterion.criterion_id, self._skipped)(criterion)
            for criterion in criteria
        ]
        version = self._active_version() or "unknown"
        return build_foundation_gate_report(version=version, results=results, trace_id="trace_foundation_gate")

    def check_versioning_consistent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        version = self._active_version()
        if not version:
            failures.append("VERSION.md active baseline missing")
        else:
            pyproject_version = self._regex_first(self.root / "pyproject.toml", r"(?m)^version\s*=\s*['\"]([^'\"]+)['\"]")
            init_version = self._regex_first(
                self.root / "src/ultimate_ai_agent/__init__.py",
                r"(?m)^__version__\s*=\s*['\"]([^'\"]+)['\"]",
            )
            readme = self._read(self.root / "README.md")
            expected_underscored = version.replace(".", "_")
            expected_import = f"docs/archive/releases/v{expected_underscored}/README_IMPORT.md"
            expected_master = f"docs/archive/releases/v{expected_underscored}/master_plan.md"
            if pyproject_version != version:
                failures.append("pyproject.toml version mismatch")
            if init_version != version:
                failures.append("package __version__ mismatch")
            if f"v{version}" not in readme:
                failures.append("README.md missing active version")
            if expected_import not in readme:
                failures.append("README.md missing active archived import README")
            if expected_master not in readme:
                failures.append("README.md missing active archived master plan")
        return self._result(criterion, failures, ["VERSION.md", "pyproject.toml", "README.md"])

    def check_release_docs_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        version = self._active_version()
        version_key = (version or "0.0.0").replace(".", "_")
        required = [
            f"docs/archive/releases/v{version_key}/README_IMPORT.md",
            f"docs/archive/releases/v{version_key}/master_plan.md",
            f"docs/release_notes/v{version_key}.md",
            f"docs/implementation/foundation_gate_implementation_plan_v{version_key}.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_foundation_modules_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/contracts/execution_contract.py",
            "src/ultimate_ai_agent/core/contracts/context_pack.py",
            "src/ultimate_ai_agent/core/ledger/events.py",
            "src/ultimate_ai_agent/core/world_state/models.py",
            "src/ultimate_ai_agent/core/context_budget/models.py",
            "src/ultimate_ai_agent/core/runtime/local_runtime.py",
            "src/ultimate_ai_agent/core/adapters/sdk_manifest.py",
            "src/ultimate_ai_agent/core/consent/grants.py",
            "src/ultimate_ai_agent/core/tools/broker.py",
            "src/ultimate_ai_agent/core/secrets/broker.py",
            "src/ultimate_ai_agent/core/providers/registry.py",
            "src/ultimate_ai_agent/core/memory/store.py",
            "src/ultimate_ai_agent/core/files/manager.py",
            "src/ultimate_ai_agent/core/truth/evidence.py",
            "src/ultimate_ai_agent/core/kernel/runner.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/gate/shadow_replay.py",
            "scripts/run_foundation_gate.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m7_modules_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_router/__init__.py",
            "src/ultimate_ai_agent/core/model_router/enums.py",
            "src/ultimate_ai_agent/core/model_router/profiles.py",
            "src/ultimate_ai_agent/core/model_router/policies.py",
            "src/ultimate_ai_agent/core/model_router/requests.py",
            "src/ultimate_ai_agent/core/model_router/decisions.py",
            "src/ultimate_ai_agent/core/model_router/router.py",
            "src/ultimate_ai_agent/core/model_router/validation.py",
            "src/ultimate_ai_agent/core/costs/__init__.py",
            "src/ultimate_ai_agent/core/costs/enums.py",
            "src/ultimate_ai_agent/core/costs/budgets.py",
            "src/ultimate_ai_agent/core/costs/estimates.py",
            "src/ultimate_ai_agent/core/costs/decisions.py",
            "src/ultimate_ai_agent/core/costs/governor.py",
            "src/ultimate_ai_agent/core/costs/validation.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_blocked_modules_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        blocked_paths = [
            "src/ultimate_ai_agent/core/scanners",
            "src/ultimate_ai_agent/core/companion",
            "src/ultimate_ai_agent/core/skill_factory",
            "src/ultimate_ai_agent/core/self_improvement",
            "src/ultimate_ai_agent/core/autopilot",
            "src/ultimate_ai_agent/core/browser_automation",
            "src/ultimate_ai_agent/core/sdk_runtime_delegation",
            "src/ultimate_ai_agent/core/a2a_runtime_delegation",
        ]
        failures = [f"blocked module exists: {path}" for path in blocked_paths if (self.root / path).exists()]
        return self._result(criterion, failures, blocked_paths)

    def check_forbidden_runtime_integrations_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden_starts = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "urllib.request",
            "from " + "urllib import request",
            "import " + "boto3",
            "import " + "ollama",
            "import " + "vllm",
            "import " + "llama_cpp",
            "import " + "sglang",
            "import " + "openai",
            "import " + "anthropic",
            "import " + "google.generativeai",
            "import " + "chromadb",
            "import " + "faiss",
            "import " + "pgvector",
            "import " + "pinecone",
            "import " + "psycopg",
            "import " + "sentence_transformers",
            "import " + "weaviate",
        ]
        forbidden_contains = [
            "from " + "openai import",
            "from " + "anthropic import",
            "http" + "://",
            "https" + "://",
        ]
        failures = []
        allowed_manual_smoke_network_files = {
            "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
            "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py",
        }
        for path, line_no, stripped in self._runtime_lines():
            if self._is_static_scanner_text(stripped):
                continue
            if any(stripped.startswith(pattern) for pattern in forbidden_starts):
                if path in allowed_manual_smoke_network_files and stripped.startswith(
                    ("import urllib.request", "from urllib import request", "from urllib import error")
                ):
                    continue
                failures.append(f"{path}:{line_no} forbidden import")
            if any(pattern in stripped for pattern in forbidden_contains):
                failures.append(f"{path}:{line_no} forbidden integration reference")
            if ".get(" in stripped and any(marker in stripped for marker in forbidden_contains[-2:]):
                failures.append(f"{path}:{line_no} possible network call")
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_shell_execution_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden = [
            "import " + "subprocess",
            "from " + "subprocess import",
            "os." + "system(",
            "po" + "pen(",
            "sub" + "process.",
        ]
        failures = [
            f"{path}:{line_no} shell execution"
            for path, line_no, stripped in self._runtime_lines()
            if not self._is_static_scanner_text(stripped) and any(fragment in stripped for fragment in forbidden)
        ]
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_broad_filesystem_scanning_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden = [
            ".rglob(" + '"*"' + ")",
            ".rglob(" + "'*'" + ")",
            "os." + "walk(",
            "Path." + "home(",
        ]
        failures = [
            f"{path}:{line_no} broad filesystem scan"
            for path, line_no, stripped in self._runtime_lines()
            if not self._is_static_scanner_text(stripped) and any(fragment in stripped for fragment in forbidden)
        ]
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_secret_hygiene_clean(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        secret_assignment = re.compile(
            r"(?i)(api_key|password|client_secret|private_key|token|auth_token)\s*=\s*['\"][A-Za-z0-9_\-.:/]{16,}['\"]"
        )
        failures = []
        private_key_begin = "-----" + "BEGIN"
        private_key_end = "PRIVATE" + " KEY-----"
        for rel_path in self._tracked_runtime_files():
            content = self._read(self.root / rel_path)
            if private_key_begin in content and private_key_end in content:
                failures.append(f"{rel_path}: private key header")
            for match in secret_assignment.finditer(content):
                value = match.group(0).lower()
                if any(
                    marker in value
                    for marker in ["mock", "dummy", "example", "placeholder", "oauth_refresh_token", "token_secret"]
                ):
                    continue
                failures.append(f"{rel_path}: secret-like assignment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_tool_broker_blocks_advanced_adapters(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        for category in (ToolCategory.mcp, ToolCategory.a2a, ToolCategory.sdk_adapter, ToolCategory.skill):
            registry = ToolRegistry()
            tool_id = f"{category.value}.gate_check"
            registry.register_tool(
                ToolManifest(
                    tool_id=tool_id,
                    display_name="Gate Check",
                    category=category,
                    description="Foundation Gate category block check.",
                    execution_mode=ToolExecutionMode.mock,
                    risk_level=ToolRiskLevel.low,
                    capability_flag=f"{category.value}_gate_check",
                    owner="core.gate",
                    source="local",
                    version="0.0.0",
                )
            )
            decision = ToolBroker(registry, CapabilityFirewallPolicy()).evaluate_request(
                ToolRequest(
                    request_id=f"req_{category.value}_gate",
                    run_id="run_foundation_gate",
                    tool_id=tool_id,
                    actor_context=self._actor(),
                    requested_action="execute",
                    purpose="foundation_gate_check",
                    data_classification=DataBoundary.project_private,
                ),
                ConsentLedger(),
            )
            if decision.status != ToolDecisionStatus.blocked_by_foundation_gate:
                failures.append(f"{category.value} was not blocked")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/tools/broker.py"])

    def check_truth_evidence_contracts_valid(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        try:
            source = TruthSourceManifest(
                source_id="truth_gate",
                source_type=TruthSourceType.canonical_file,
                authority_level=TruthAuthorityLevel.authoritative,
                display_name="Gate Truth Source",
                owner="core.gate",
                data_classification="project_private",
            )
            item = EvidenceItem(
                evidence_id="evidence_gate",
                source_id=source.source_id,
                source_type=TruthSourceType.canonical_file,
                summary="Gate evidence contract check.",
                freshness_status=SourceFreshnessStatus.current,
            )
            claim = ClaimEvidence(
                claim_id="claim_gate",
                claim_text="Foundation Gate is verification only.",
                verification_status=ClaimVerificationStatus.supported,
                evidence_refs=[item.evidence_id],
                source_ids=[source.source_id],
                freshness_status=SourceFreshnessStatus.current,
            )
            EvidenceManifest(
                manifest_id="evm_gate",
                run_id="run_foundation_gate",
                claims=[claim],
                evidence_items=[item],
            )
        except (ValidationError, ValueError) as exc:
            failures.append(str(exc))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/truth"])

    def check_memory_file_contracts_valid(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        try:
            MemoryRecord(
                memory_id="mem_gate",
                memory_type=MemoryType.artifact_summary,
                scope=MemoryScope.project,
                scope_id="workspace_gate",
                authority=MemoryAuthority.event_ledger_derived,
                sensitivity=MemorySensitivity.project_private,
                content="Recall only: gate check. Canonical files and event ledger outrank memory.",
                source_refs=[
                    MemorySourceRef(
                        source_id="notes/m5.md",
                        source_type="file_change",
                        file_ref="notes/m5.md",
                        event_ref="evt_gate",
                    )
                ],
            )
            FileRef(
                file_ref="file_gate",
                path="notes/m5.md",
                kind=FileKind.generated,
                sensitivity=FileSensitivity.project_private,
                source_event_ref="evt_gate",
            )
        except (ValidationError, ValueError) as exc:
            failures.append(str(exc))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/memory", "src/ultimate_ai_agent/core/files"])

    def check_m5_shadow_replay_passes(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        replay = run_m5_shadow_replay()
        failures = list(replay.failures)
        warnings = list(replay.warnings)
        if not replay.passed and not failures:
            failures.append("shadow replay did not pass")
        status = FoundationGateStatus.passed if not failures else FoundationGateStatus.failed
        return FoundationGateResult(
            criterion_id=criterion.criterion_id,
            status=status,
            safe_message="M5 shadow replay passed." if status == FoundationGateStatus.passed else criterion.failure_message,
            evidence_refs=[*replay.event_ids, replay.receipt_ref or "receipt_missing"],
            failures=failures,
            warnings=warnings,
        )

    def check_model_router_decision_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        try:
            profile = ModelCapabilityProfile(
                model_profile_id="m7_gate_local",
                provider_kind=ModelProviderKind.local_runtime,
                runtime_id="rt_gate",
                model_id="local_policy_model",
                display_name="Local Policy Model",
                capabilities=[ModelTaskCapability.chat, ModelTaskCapability.coding],
                privacy_class=ModelPrivacyClass.local_only,
                max_context_tokens=8192,
                enabled=True,
                owner="core.gate",
                source="foundation_gate",
                version="0.0.0",
            )
            request = ModelRouteRequest(
                request_id="m7_gate_route",
                run_id="run_foundation_gate",
                actor_context=self._actor(),
                task_class="coding",
                prompt_summary="Foundation Gate model routing metadata check.",
                data_classification=DataClassification(classification=ClassificationValue.project_private, source="foundation_gate"),
                required_capabilities=[ModelTaskCapability.chat],
                estimated_input_tokens=256,
                estimated_output_tokens=128,
                routing_policy=ModelRoutingPolicy(
                    policy_id="m7_gate_policy",
                    required_capabilities=[ModelTaskCapability.chat],
                    prefer_local=True,
                    allow_cloud=False,
                    allow_paid=False,
                ),
                available_profiles=[profile],
            )
            decision = ModelRouter().route(request)
            if decision.status != ModelRouteStatus.selected:
                failures.append(f"route status was {decision.status}")
            if decision.selected_profile_id != profile.model_profile_id:
                failures.append("local policy profile was not selected")
        except (ValidationError, ValueError) as exc:
            failures.append(str(exc))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_router"])

    def check_cost_governor_blocks_over_budget(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        decision = CostGovernor().evaluate(
            CostEstimate(
                estimate_id="m7_gate_estimate",
                input_tokens=100,
                output_tokens=100,
                total_tokens=200,
                estimated_cost_usd=2,
            ),
            [CostBudget(budget_id="m7_gate_budget", scope=BudgetScope.run, max_cost_usd=1)],
        )
        if decision.status != BudgetStatus.denied or decision.allowed:
            failures.append("over-budget route was not denied")
        if "COST_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("cost denial reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/costs"])

    def check_m7_arbitrary_approval_ref_rejected(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        profile = self._gate_cloud_profile()
        request = self._gate_route_request(
            profile,
            data_classification=ClassificationValue.sensitive_personal,
            approval_ref="arbitrary-string",
            policy=ModelRoutingPolicy(
                policy_id="m7_gate_approval_policy",
                required_capabilities=[ModelTaskCapability.chat],
                allow_cloud=True,
                allow_paid=True,
                require_human_approval_for_cloud=True,
            ),
        )
        decision = ModelRouter().route(request)
        if decision.status != ModelRouteStatus.approval_required:
            failures.append(f"route status was {decision.status}")
        if decision.selected_profile_id is not None:
            failures.append("arbitrary approval_ref selected a cloud profile")
        if "APPROVAL_REF_UNVALIDATED" not in decision.reason_codes:
            failures.append("unvalidated approval reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"])

    def check_m7_context_budget_exhaustion_blocks_route(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        profile = self._gate_local_profile()
        request = self._gate_route_request(
            profile,
            context_budget=ContextBudget(
                model_context_limit=4096,
                system_prompt_tokens=1000,
                tool_schema_tokens=1000,
                world_state_tokens=1000,
                context_pack_tokens=1000,
                completion_reserve_tokens=96,
                safety_margin_tokens=0,
            ),
        )
        decision = ModelRouter().route(request)
        if decision.status != ModelRouteStatus.context_too_small:
            failures.append(f"route status was {decision.status}")
        if decision.selected_profile_id is not None:
            failures.append("exhausted context budget selected a profile")
        if "CONTEXT_BUDGET_EXHAUSTED" not in decision.reason_codes:
            failures.append("context budget exhaustion reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"])

    def check_m7_soft_budget_warning_allows_route(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        decision = CostGovernor().evaluate(
            CostEstimate(
                estimate_id="m7_gate_soft_estimate",
                input_tokens=100,
                output_tokens=100,
                total_tokens=200,
                estimated_cost_usd=2,
            ),
            [CostBudget(budget_id="m7_gate_soft_budget", scope=BudgetScope.run, max_cost_usd=1, hard_limit=False)],
        )
        if not decision.allowed or decision.status != BudgetStatus.warning:
            failures.append("soft budget overage was not allowed with warning")
        if "SOFT_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("soft budget reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/costs/governor.py"])

    def check_m7_hard_budget_denies_route(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        decision = CostGovernor().evaluate(
            CostEstimate(
                estimate_id="m7_gate_hard_estimate",
                input_tokens=100,
                output_tokens=100,
                total_tokens=200,
                estimated_cost_usd=2,
            ),
            [CostBudget(budget_id="m7_gate_hard_budget", scope=BudgetScope.run, max_cost_usd=1, hard_limit=True)],
        )
        if decision.allowed or decision.status != BudgetStatus.denied:
            failures.append("hard budget overage was not denied")
        if "HARD_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("hard budget reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/costs/governor.py"])

    def check_m7_cost_warnings_visible_in_route_decision(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        profile = self._gate_local_profile(cost_per_1k_input_tokens=0.02, cost_per_1k_output_tokens=0.02)
        request = self._gate_route_request(
            profile,
            policy=ModelRoutingPolicy(
                policy_id="m7_gate_soft_route_policy",
                required_capabilities=[ModelTaskCapability.chat],
                prefer_local=True,
                allow_paid=True,
                max_estimated_cost_usd=0.01,
                max_estimated_cost_hard_limit=False,
            ),
        )
        decision = ModelRouter().route(request)
        if decision.status != ModelRouteStatus.selected:
            failures.append(f"route status was {decision.status}")
        if "SOFT_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("soft budget warning was not visible in route decision")
        if "with policy warnings" not in decision.safe_message:
            failures.append("route decision safe_message did not mention warnings")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"])

    def check_api_manifest_endpoint_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import build_api_manifest

        failures: List[str] = []
        manifest = build_api_manifest(app)
        paths = {route.path for route in manifest.routes}
        if "/api/manifest" not in paths:
            failures.append("/api/manifest missing from route inventory")
        if manifest.api_version != (self._active_version() or ""):
            failures.append("manifest api_version does not match active baseline")
        if not manifest.no_runtime_integrations:
            failures.append("manifest does not declare no_runtime_integrations")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/manifest.py", "src/ultimate_ai_agent/api/app.py"])

    def check_openapi_contract_valid(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.openapi import verify_openapi_contract

        status = verify_openapi_contract(app)
        failures = list(status.errors)
        if not status.openapi_generated:
            failures.append("OpenAPI schema was not generated")
        if not status.version_consistent:
            failures.append("OpenAPI version mismatch")
        if not status.route_inventory_valid:
            failures.append("route inventory invalid")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/openapi.py"], status.warnings)

    def check_api_operation_ids_unique(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items

        routes = iter_api_route_items(app)
        operation_ids = [route.operation_id for route in routes]
        duplicates = sorted({operation_id for operation_id in operation_ids if operation_ids.count(operation_id) > 1})
        failures = [f"duplicate operation ID: {operation_id}" for operation_id in duplicates]
        if any(not operation_id for operation_id in operation_ids):
            failures.append("missing operation ID")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/openapi.py"])

    def check_forbidden_runtime_routes_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items
        from ultimate_ai_agent.api.openapi import FORBIDDEN_ROUTE_FRAGMENTS

        failures = []
        for route in iter_api_route_items(app):
            if any(fragment in route.path for fragment in FORBIDDEN_ROUTE_FRAGMENTS):
                failures.append(f"forbidden route: {route.method} {route.path}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/openapi.py"])

    def check_agents_md_guidance_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "AGENTS.md",
            "docs/api/README.md",
            "docs/api/openapi_contract.md",
            "docs/api/route_inventory.md",
            "docs/standards/agents_md_support.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        agents_md = self._read(self.root / "AGENTS.md")
        for marker in ["Ultimate AI Agent", "/api/manifest", "OpenAPI", "Do not add runtime model calls"]:
            if marker not in agents_md:
                failures.append(f"AGENTS.md missing marker: {marker}")
        return self._result(criterion, failures, required)

    def check_runtime_agent_config_loading_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden = [
            "AGENTS" + ".md",
            "agent_config",
            "agent-config",
            "runtime_config",
            "workspace_config",
            "load_agent_config",
        ]
        failures = [
            f"{path}:{line_no} runtime agent config loading reference"
            for path, line_no, stripped in self._runtime_lines()
            if path not in {"src/ultimate_ai_agent/api/openapi.py", "src/ultimate_ai_agent/core/gate/evaluators.py"}
            and not self._is_static_scanner_text(stripped)
            and any(fragment in stripped for fragment in forbidden)
        ]
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_m8_model_runtime_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_runtime/__init__.py",
            "src/ultimate_ai_agent/core/model_runtime/enums.py",
            "src/ultimate_ai_agent/core/model_runtime/manifests.py",
            "src/ultimate_ai_agent/core/model_runtime/requests.py",
            "src/ultimate_ai_agent/core/model_runtime/responses.py",
            "src/ultimate_ai_agent/core/model_runtime/simulator.py",
            "src/ultimate_ai_agent/core/model_runtime/adapters.py",
            "src/ultimate_ai_agent/core/model_runtime/validation.py",
            "src/ultimate_ai_agent/core/model_runtime/redaction.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m8_runtime_kinds_stub_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeKind

        allowed = {"simulated", "local_stub", "cloud_stub", "openai_compatible_stub", "sdk_adapter_stub"}
        actual = {kind.value for kind in ModelRuntimeKind}
        failures = [f"unexpected runtime kind: {kind}" for kind in sorted(actual - allowed)]
        missing = allowed - actual
        failures.extend(f"missing runtime kind: {kind}" for kind in sorted(missing))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/enums.py"])

    def check_m8_model_runtime_no_real_calls(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        runtime_root = self.src_root / "core" / "model_runtime"
        forbidden = [
            "import " + "openai",
            "from " + "openai import",
            "import " + "anthropic",
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "socket",
            "sub" + "process",
            "token" + "izer",
            "tiktoken",
            "sentencepiece",
            "bill" + "ing",
            "api" + "_key",
            "API" + "_KEY",
        ]
        failures = []
        for path in sorted(runtime_root.rglob("*.py")):
            rel_path = str(path.relative_to(self.root))
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(f"{rel_path}:{line_no} real runtime fragment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime"])

    def check_m8_simulation_endpoint_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app

        schema = app.openapi()
        failures = []
        route = schema.get("paths", {}).get("/model-runtime/simulate", {}).get("post")
        if not route:
            failures.append("/model-runtime/simulate missing")
        elif route.get("operationId") != "post_model_runtime_simulate":
            failures.append("simulate endpoint operation ID is not stable")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m8_runtime_responses_simulated_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import (
            ModelRuntimeOutputFormat,
            ModelRuntimeResponse,
            ModelRuntimeResponseStatus,
            response_is_truth_authority,
        )

        failures = []
        response = ModelRuntimeResponse(
            runtime_response_id="m8_gate_response",
            runtime_request_id="m8_gate_request",
            run_id="run_foundation_gate",
            status=ModelRuntimeResponseStatus.simulated_success,
            output_format=ModelRuntimeOutputFormat.text,
            output_summary="Simulated response for request m8_gate_request; no model was called.",
            model_profile_id="m8_gate_profile",
            adapter_id="m8_gate_adapter",
            metadata={"simulated": True, "truth_authority": False},
        )
        if response.status != ModelRuntimeResponseStatus.simulated_success:
            failures.append("response status was not simulated_success")
        if response_is_truth_authority(response):
            failures.append("response became truth authority")
        if "no model was called" not in response.output_summary:
            failures.append("simulated response marker missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/responses.py"])

    def check_m8_runtime_secret_prompt_blocked(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeOutputFormat, ModelRuntimeRequest, ModelRuntimeSafetyMode

        failures = []
        try:
            ModelRuntimeRequest(
                runtime_request_id="m8_gate_secret_request",
                run_id="run_foundation_gate",
                model_profile_id="m8_gate_profile",
                model_id="m8_gate_model",
                adapter_id="m8_gate_adapter",
                actor_context=self._actor(),
                prompt_summary="api_" + "key='ABCDEFGHIJKLMNOP'",
                input_refs=["context_pack:m8_gate"],
                output_format=ModelRuntimeOutputFormat.text,
                estimated_input_tokens=10,
                max_output_tokens=10,
                safety_mode=ModelRuntimeSafetyMode.simulated,
                data_classification=DataClassification(
                    classification=ClassificationValue.project_private,
                    source="foundation_gate",
                ),
            )
            failures.append("secret-like prompt summary was accepted")
        except (ValidationError, ValueError):
            pass
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/requests.py"])

    def check_m8_api_validation_secret_echo_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from fastapi.testclient import TestClient

        from ultimate_ai_agent.api.app import app

        failures = []
        client = TestClient(app)
        secret = "sk_" + "test_" + "secret_" + "value"
        assignment = "api_" + "key=" + secret
        manifest = self._m8_gate_manifest()
        manifest_with_secret = {**manifest, "metadata": {"note": assignment}}
        request = self._m8_gate_request()
        cases = [
            ("/model-runtime/manifests/validate", manifest_with_secret),
            ("/model-runtime/manifests/validate", {**manifest, "api_" + "key": secret}),
            ("/model-runtime/requests/validate", {"request": request, "manifest": manifest_with_secret}),
            ("/model-runtime/simulate", {"request": request, "manifest": manifest_with_secret}),
        ]
        for path, payload in cases:
            response = client.post(path, json=payload)
            if response.status_code not in {200, 422}:
                failures.append(f"{path} returned unexpected status {response.status_code}")
            if secret in response.text or assignment in response.text:
                failures.append(f"{path} echoed secret-like input")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m85_approval_authority_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/approvals/__init__.py",
            "src/ultimate_ai_agent/core/approvals/enums.py",
            "src/ultimate_ai_agent/core/approvals/requests.py",
            "src/ultimate_ai_agent/core/approvals/grants.py",
            "src/ultimate_ai_agent/core/approvals/decisions.py",
            "src/ultimate_ai_agent/core/approvals/authority.py",
            "src/ultimate_ai_agent/core/approvals/policies.py",
            "src/ultimate_ai_agent/core/approvals/validation.py",
            "src/ultimate_ai_agent/core/approvals/receipts.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m85_arbitrary_approval_refs_rejected(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, LocalApprovalAuthority

        request = self._m85_gate_approval_request()
        authority = LocalApprovalAuthority()
        authority.create_request(request)
        decision = authority.validate_for_request(request, "human_approved_ref_123")
        failures = []
        if decision.allowed:
            failures.append("arbitrary approval_ref was allowed")
        if decision.status != ApprovalDecisionStatus.invalid:
            failures.append("arbitrary approval_ref did not return invalid")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/approvals/authority.py"])

    def check_m85_local_approval_grant_validates(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, LocalApprovalAuthority

        request = self._m85_gate_approval_request()
        authority = LocalApprovalAuthority()
        authority.create_request(request)
        grant = authority.grant(request.approval_request_id, approved_by_actor_id="foundation_gate")
        decision = authority.validate_for_request(request, grant.approval_ref)
        failures = []
        if not decision.allowed:
            failures.append("valid approval grant was denied")
        if decision.status != ApprovalDecisionStatus.approved:
            failures.append("valid approval grant did not return approved")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/approvals/authority.py"])

    def check_m85_expired_revoked_approval_denies(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from datetime import timedelta

        from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, LocalApprovalAuthority
        from ultimate_ai_agent.core.time import utc_now

        failures = []
        expired_request = self._m85_gate_approval_request("m85_gate_expired")
        expired_authority = LocalApprovalAuthority()
        expired_authority.create_request(expired_request)
        expired = expired_authority.grant(
            expired_request.approval_request_id,
            approved_by_actor_id="foundation_gate",
            expires_at=utc_now() - timedelta(seconds=1),
        )
        expired_decision = expired_authority.validate_for_request(expired_request, expired.approval_ref)
        if expired_decision.allowed or expired_decision.status != ApprovalDecisionStatus.expired:
            failures.append("expired approval was accepted")

        revoked_request = self._m85_gate_approval_request("m85_gate_revoked")
        revoked_authority = LocalApprovalAuthority()
        revoked_authority.create_request(revoked_request)
        revoked = revoked_authority.grant(revoked_request.approval_request_id, approved_by_actor_id="foundation_gate")
        revoked_authority.revoke(revoked.approval_ref, "foundation gate check")
        revoked_decision = revoked_authority.validate_for_request(revoked_request, revoked.approval_ref)
        if revoked_decision.allowed or revoked_decision.status != ApprovalDecisionStatus.revoked:
            failures.append("revoked approval was accepted")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/approvals/authority.py"])

    def check_m85_router_uses_valid_approval_grant(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority

        profile = self._gate_cloud_profile()
        request = self._gate_route_request(
            profile,
            data_classification=ClassificationValue.sensitive_personal,
            policy=ModelRoutingPolicy(
                policy_id="m85_gate_cloud_policy",
                required_capabilities=[ModelTaskCapability.chat],
                prefer_local=False,
                allow_cloud=True,
                allow_paid=True,
                require_human_approval_for_cloud=True,
            ),
        )
        authority = LocalApprovalAuthority()
        approval_request = authority.create_request(LocalApprovalAuthority.request_for_model_route(request, resource_refs=[profile.model_profile_id]))
        grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="foundation_gate")
        decision = ModelRouter(approval_authority=authority).route(request.model_copy(update={"approval_ref": grant.approval_ref}))
        failures = []
        if decision.status != ModelRouteStatus.selected:
            failures.append("valid approval grant did not permit selected route")
        if "APPROVAL_VALIDATED" not in decision.reason_codes:
            failures.append("route decision did not expose approval validation reason")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"])

    def check_m85_runtime_factory_rejects_arbitrary_approval(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeRequestFactory

        route = self._gate_route_request(self._gate_cloud_profile(), approval_ref="human_approved_ref_123")
        decision = ModelRouter().route(route.model_copy(update={"approval_ref": None}))
        failures = []
        try:
            ModelRuntimeRequestFactory.from_route_decision(decision, route, self._m85_runtime_manifest())
            failures.append("runtime factory accepted arbitrary approval_ref")
        except ValueError:
            pass
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/adapters.py"])

    def check_m85_tool_broker_rejects_arbitrary_approval(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.consent import ConsentGrant, ConsentScopeType, ConsentSubjectType
        from ultimate_ai_agent.core.consent.enums import PermissionAction
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority

        registry = ToolRegistry()
        registry.register_tool(
            ToolManifest(
                tool_id="m85_gate_tool",
                display_name="M8.5 Gate Tool",
                category=ToolCategory.mock,
                description="Approval authority gate check.",
                execution_mode=ToolExecutionMode.dry_run,
                risk_level=ToolRiskLevel.high,
                capability_flag="m85_gate_tool",
                owner="core.gate",
                source="foundation_gate",
                version="0.0.0",
            )
        )
        ledger = ConsentLedger()
        ledger.add_grant(
            ConsentGrant(
                consent_id="m85_gate_consent",
                subject_type=ConsentSubjectType.tool,
                subject_id="m85_gate_tool",
                granted_to_actor="foundation_gate",
                on_behalf_of_user_id="foundation_gate",
                scope_type=ConsentScopeType.project,
                allowed_actions=[PermissionAction.execute],
                source="foundation_gate",
            )
        )
        decision = ToolBroker(
            registry,
            CapabilityFirewallPolicy(max_risk_level=ToolRiskLevel.high),
            approval_authority=LocalApprovalAuthority(),
        ).evaluate_request(
            ToolRequest(
                request_id="m85_gate_tool_request",
                run_id="run_foundation_gate",
                tool_id="m85_gate_tool",
                actor_context=self._actor(),
                requested_action="execute",
                purpose="foundation_gate_check",
                data_classification=DataBoundary.project_private,
                approval_ref="human_approved_ref_123",
            ),
            ledger,
        )
        failures = []
        if decision.status != ToolDecisionStatus.approval_required:
            failures.append("tool broker did not keep arbitrary approval_ref approval-required")
        if "APPROVAL_REF_UNKNOWN" not in decision.reason_codes:
            failures.append("tool broker did not report unknown approval ref")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/tools/broker.py"])

    def check_m85_no_real_auth_oauth_network(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        approval_root = self.src_root / "core" / "approvals"
        forbidden = [
            "import " + "requests",
            "import " + "httpx",
            "urllib",
            "socket",
            "oauth",
            "OAuth",
            "OpenID",
            "session_cookie",
            "jwt",
            "sqlite",
            "psycopg",
            "sub" + "process",
        ]
        failures = []
        for path in sorted(approval_root.rglob("*.py")):
            rel_path = str(path.relative_to(self.root))
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(f"{rel_path}:{line_no} forbidden auth/network/persistence fragment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/approvals"])

    def check_m85_approval_api_secret_echo_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from fastapi.testclient import TestClient

        from ultimate_ai_agent.api.app import app

        client = TestClient(app)
        secret = "sk_" + "test_" + "secret_" + "value"
        assignment = "api_" + "key=" + secret
        payload = self._m85_gate_approval_request().model_dump(mode="json")
        payload["metadata"] = {"note": assignment}
        response = client.post("/approvals/requests/validate", json=payload)
        failures = []
        if response.status_code not in {200, 422}:
            failures.append(f"unexpected approval API status {response.status_code}")
        if secret in response.text or assignment in response.text or "api_key" in response.text:
            failures.append("approval API echoed secret-like input")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m9_loopback_runtime_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_runtime/loopback.py",
            "src/ultimate_ai_agent/core/model_runtime/execution_policy.py",
            "src/ultimate_ai_agent/core/model_runtime/transports.py",
            "src/ultimate_ai_agent/core/model_runtime/local_adapter.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m9_non_loopback_endpoints_denied(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter, LoopbackRuntimeEndpoint, LoopbackRuntimePolicy, ModelRuntimeKind

        adapter = LocalLoopbackModelRuntimeAdapter()
        policy = LoopbackRuntimePolicy(policy_id="m9_gate_policy", allow_real_loopback_execution=True)
        def endpoint(base_url: str):
            return LoopbackRuntimeEndpoint(
                endpoint_id="m9_gate_endpoint",
                base_url=base_url,
                allowed_hosts=["127.0.0.1", "localhost", "::1"],
                runtime_kind=ModelRuntimeKind.local_stub,
                model_id="m9_gate_model",
                enabled=True,
                owner="foundation_gate",
                source="foundation_gate",
                version="0.0.0",
            )

        failures = []
        remote = adapter.validate_endpoint(endpoint("http" + "://example.com/api/generate"), policy)
        credentials = adapter.validate_endpoint(endpoint("http" + "://user:pass@127.0.0.1:11434/api/generate"), policy)
        query = adapter.validate_endpoint(endpoint("http" + "://127.0.0.1:11434/api/generate?token=abc"), policy)
        if remote.allowed or "NON_LOOPBACK_HOST_DENIED" not in remote.reason_codes:
            failures.append("remote host was not denied")
        if credentials.allowed or "URL_CREDENTIALS_DENIED" not in credentials.reason_codes:
            failures.append("URL credentials were not denied")
        if query.allowed or "SECRET_QUERY_DENIED" not in query.reason_codes:
            failures.append("secret-like query parameter was not denied")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"])

    def check_m9_non_loopback_policy_override_denied(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter, LoopbackRuntimeEndpoint, LoopbackRuntimePolicy, ModelRuntimeKind

        adapter = LocalLoopbackModelRuntimeAdapter()
        policy = LoopbackRuntimePolicy(
            policy_id="m9_gate_override_policy",
            allow_real_loopback_execution=True,
        ).model_copy(
            update={
                "allowed_hosts": ["example.com"],
                "deny_non_loopback": False,
            }
        )
        endpoint = LoopbackRuntimeEndpoint(
            endpoint_id="m9_gate_override_endpoint",
            base_url="http" + "://example.com/api/generate",
            allowed_hosts=["example.com"],
            runtime_kind=ModelRuntimeKind.local_stub,
            model_id="m9_gate_model",
            enabled=True,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
        )
        decision = adapter.validate_endpoint(endpoint, policy)
        failures = []
        if decision.allowed:
            failures.append("caller override allowed a remote endpoint")
        for reason in ("NON_LOOPBACK_HOST_DENIED", "POLICY_CANNOT_DISABLE_LOOPBACK_GUARD"):
            if reason not in decision.reason_codes:
                failures.append(f"override decision missing {reason}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"])

    def check_m9_loopback_policy_model_rejects_hostile_inputs(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LoopbackRuntimePolicy

        failures = []
        hostile_inputs = [
            {"deny_non_loopback": False},
            {"allowed_hosts": ["example.com"]},
            {"allowed_hosts": ["192.168.1.5"]},
            {"allowed_hosts": ["10.0.0.5"]},
            {"allowed_hosts": ["8.8.8.8"]},
            {"allowed_hosts": ["127.0.0.1", "example.com"]},
        ]
        for payload in hostile_inputs:
            try:
                LoopbackRuntimePolicy(policy_id="m9_gate_hostile_policy", **payload)
            except ValueError:
                continue
            failures.append(f"hostile policy accepted: {payload}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/execution_policy.py"])

    def check_m9_public_and_private_ip_endpoints_denied(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter, LoopbackRuntimeEndpoint, LoopbackRuntimePolicy, ModelRuntimeKind

        adapter = LocalLoopbackModelRuntimeAdapter()
        policy = LoopbackRuntimePolicy(policy_id="m9_gate_ip_policy", allow_real_loopback_execution=True)
        failures = []
        for host in ["192.168.1.5", "10.0.0.5", "8.8.8.8"]:
            endpoint = LoopbackRuntimeEndpoint(
                endpoint_id=f"m9_gate_{host.replace('.', '_')}",
                base_url="http" + f"://{host}/api/generate",
                allowed_hosts=[host],
                runtime_kind=ModelRuntimeKind.local_stub,
                model_id="m9_gate_model",
                enabled=True,
                owner="foundation_gate",
                source="foundation_gate",
                version="0.0.0",
            )
            decision = adapter.validate_endpoint(endpoint, policy)
            if decision.allowed or "NON_LOOPBACK_HOST_DENIED" not in decision.reason_codes:
                failures.append(f"{host} was not denied")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"])

    def check_m9_approval_api_uses_public_authority_helper(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        app_source = self._read(self.root / "src/ultimate_ai_agent/api/app.py")
        authority_source = self._read(self.root / "src/ultimate_ai_agent/core/approvals/authority.py")
        failures = []
        if "authority._grants" in app_source:
            failures.append("approval API mutates private _grants")
        if "load_grant_for_validation" not in app_source:
            failures.append("approval API does not use public grant-loading helper")
        if "def load_grant_for_validation" not in authority_source:
            failures.append("LocalApprovalAuthority helper is missing")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/api/app.py", "src/ultimate_ai_agent/core/approvals/authority.py"],
        )

    def check_m9_arbitrary_approval_refs_denied(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter

        request = self._m9_runtime_request(approval_ref="human_approved_ref_123")
        decision = LocalLoopbackModelRuntimeAdapter().validate_execution(
            request,
            self._m9_runtime_manifest(),
            self._m9_loopback_endpoint(),
            self._m9_loopback_policy(),
            approval_decision=None,
        )
        failures = []
        if decision.allowed:
            failures.append("arbitrary approval_ref allowed execution")
        if "APPROVAL_DECISION_REQUIRED" not in decision.reason_codes:
            failures.append("arbitrary approval_ref did not require validated approval decision")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"])

    def check_m9_fake_transport_only_in_gate(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        runtime_root = self.src_root / "core" / "model_runtime"
        forbidden = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "openai",
            "import " + "anthropic",
            "tiktoken",
            "tokenizers",
            "billing",
            "sub" + "process",
        ]
        failures = []
        for path in sorted(runtime_root.rglob("*.py")):
            rel_path = str(path.relative_to(self.root))
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(f"{rel_path}:{line_no} forbidden M9 runtime fragment")
                if "DisabledNetworkTransport().send(" in stripped:
                    failures.append(f"{rel_path}:{line_no} disabled transport send call in gate path")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime"])

    def check_m9_simulated_fallback_available(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter, ModelRuntimeResponseStatus

        response = LocalLoopbackModelRuntimeAdapter().execute_dev(
            self._m9_runtime_request(approval_ref="human_approved_ref_123"),
            self._m9_runtime_manifest(),
            self._m9_loopback_endpoint(),
            self._m9_loopback_policy(),
            approval_decision=None,
        )
        failures = []
        if response.status != ModelRuntimeResponseStatus.simulated_success:
            failures.append("blocked execution did not return simulated fallback")
        if response.response_origin != "simulated":
            failures.append("fallback response origin was not simulated")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"])

    def check_m9_model_output_not_truth_authority(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import ApprovalRiskLevel, ApprovalSubjectType, LocalApprovalAuthority
        from ultimate_ai_agent.core.model_runtime import FakeModelRuntimeTransport, LocalLoopbackModelRuntimeAdapter, response_is_truth_authority

        request = self._m9_runtime_request()
        approval_request = LocalApprovalAuthority.request_for_model_route(
            self._gate_route_request(self._gate_local_profile()),
            subject_type=ApprovalSubjectType.model_runtime_request,
            subject_id=request.runtime_request_id,
            requested_action="execute_local_loopback_model",
            resource_refs=[request.adapter_id, request.model_profile_id],
            risk_level=ApprovalRiskLevel.high,
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="foundation_gate")
        approval = authority.validate_for_request(approval_request, grant.approval_ref)
        response = LocalLoopbackModelRuntimeAdapter().execute_dev(
            request.model_copy(update={"approval_ref": grant.approval_ref}),
            self._m9_runtime_manifest(),
            self._m9_loopback_endpoint(),
            self._m9_loopback_policy(),
            approval,
            transport=FakeModelRuntimeTransport(),
        )
        failures = []
        if response_is_truth_authority(response):
            failures.append("local loopback response is truth authority")
        if response.metadata.get("truth_authority") is not False:
            failures.append("local loopback metadata did not mark non-authoritative")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/responses.py"])

    def check_m10_manual_smoke_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_runtime/smoke_policy.py",
            "src/ultimate_ai_agent/core/model_runtime/smoke.py",
            "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
            "scripts/local_loopback_smoke.py",
            "tests/test_manual_loopback_smoke_policy.py",
            "tests/test_manual_loopback_smoke_transport.py",
            "tests/test_manual_loopback_smoke_script.py",
            "tests/test_manual_loopback_smoke_api_routes.py",
            "tests/test_m10_gate_integration.py",
        ]
        failures = [f"missing {rel_path}" for rel_path in required if not (self.root / rel_path).exists()]
        return self._result(criterion, failures, required)

    def check_m10_stdlib_network_isolated(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        allowed = {
            "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
            "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py",
            "scripts/local_loopback_smoke.py",
            "scripts/manual_local_model_call.py",
        }
        forbidden = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "openai",
            "import " + "anthropic",
            "tiktoken",
            "tokenizers",
            "billing",
            "socket",
            "subprocess",
        ]
        failures = []
        paths = [
            *list((self.root / "src/ultimate_ai_agent/core/model_runtime").rglob("*.py")),
            self.root / "scripts/local_loopback_smoke.py",
            self.root / "scripts/manual_local_model_call.py",
        ]
        for path in paths:
            if not path.exists():
                continue
            rel_path = str(path.relative_to(self.root))
            source = self._read(path)
            if ("urllib.request" in source or "from urllib import request" in source) and rel_path not in allowed:
                failures.append(f"urllib request outside isolated smoke file: {rel_path}")
            for line in source.splitlines():
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(f"forbidden runtime fragment in {rel_path}: {stripped}")
        return self._result(criterion, failures, sorted(allowed))

    def check_m10_gate_and_verify_do_not_call_smoke_script(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        for rel_path in ["scripts/run_foundation_gate.py", "scripts/verify_all.py"]:
            source = self._read(self.root / rel_path)
            if "scripts/local_loopback_smoke.py" in source:
                failures.append(f"{rel_path} references manual smoke script")
        return self._result(criterion, failures, ["scripts/run_foundation_gate.py", "scripts/verify_all.py"])

    def check_m10_public_api_has_no_smoke_execute_endpoint(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app

        paths = {route.path for route in app.routes}
        failures = []
        if "/model-runtime/local/smoke/validate" not in paths:
            failures.append("smoke validation endpoint missing")
        for forbidden in ["/model-runtime/local/smoke/execute", "/model-runtime/local/execute"]:
            if forbidden in paths:
                failures.append(f"forbidden execute endpoint present: {forbidden}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m10_fixed_prompt_and_loopback_policy_enforced(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        try:
            self._m10_smoke_request(fixed_prompt="Summarize this user file content.")
            failures.append("arbitrary user-content prompt accepted")
        except ValueError:
            pass
        try:
            self._m10_smoke_request(endpoint=self._m10_smoke_endpoint(base_url="http" + "://example.com/api/generate", allowed_hosts=["example.com"]))
            failures.append("remote smoke endpoint accepted")
        except ValueError:
            pass
        try:
            self._m10_smoke_request()
        except ValueError as exc:
            failures.append(f"safe fixed smoke request rejected: {exc}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/smoke_policy.py"])

    def check_m10_smoke_approval_required(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
        from ultimate_ai_agent.core.model_runtime import smoke_approval_request, validate_manual_loopback_smoke_request

        request = self._m10_smoke_request()
        missing = validate_manual_loopback_smoke_request(request.model_copy(update={"approval_ref": None}), None)
        arbitrary = validate_manual_loopback_smoke_request(request.model_copy(update={"approval_ref": "human_approved_ref_123"}), None)
        approval = smoke_approval_request(request)
        authority = LocalApprovalAuthority()
        authority.create_request(approval)
        grant = authority.grant(approval.approval_request_id, approved_by_actor_id="human_reviewer")
        decision = authority.validate_for_request(approval, grant.approval_ref)
        allowed = validate_manual_loopback_smoke_request(request.model_copy(update={"approval_ref": grant.approval_ref}), decision)
        failures = []
        if missing.allowed or "APPROVAL_REQUIRED" not in missing.reason_codes:
            failures.append("missing approval was not denied")
        if arbitrary.allowed or "APPROVAL_DECISION_REQUIRED" not in arbitrary.reason_codes:
            failures.append("arbitrary approval ref was not denied")
        if not allowed.allowed:
            failures.append("valid scoped approval did not permit smoke validation")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/smoke.py"])

    def check_m10_smoke_response_not_truth_authority(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
        from ultimate_ai_agent.core.model_runtime import FakeManualLoopbackSmokeTransport, smoke_approval_request

        request = self._m10_smoke_request()
        approval = smoke_approval_request(request)
        authority = LocalApprovalAuthority()
        authority.create_request(approval)
        grant = authority.grant(approval.approval_request_id, approved_by_actor_id="human_reviewer")
        decision = authority.validate_for_request(approval, grant.approval_ref)
        result = FakeManualLoopbackSmokeTransport().send_smoke(request.model_copy(update={"approval_ref": grant.approval_ref}), decision)
        failures = []
        if result.metadata.get("truth_authority") is not False:
            failures.append("smoke result metadata does not mark truth_authority false")
        if result.response_preview == request.fixed_prompt or request.fixed_prompt in result.model_dump_json():
            failures.append("smoke result leaked fixed prompt content")
        if result.response_origin != "fake_manual_loopback_smoke":
            failures.append("gate did not use fake manual smoke transport")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/smoke.py"])

    def check_m105_remote_worker_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/remote_workers/__init__.py",
            "src/ultimate_ai_agent/core/remote_workers/enums.py",
            "src/ultimate_ai_agent/core/remote_workers/nodes.py",
            "src/ultimate_ai_agent/core/remote_workers/transports.py",
            "src/ultimate_ai_agent/core/remote_workers/registry.py",
            "src/ultimate_ai_agent/core/remote_workers/policy.py",
            "src/ultimate_ai_agent/core/remote_workers/jobs.py",
            "src/ultimate_ai_agent/core/remote_workers/results.py",
            "src/ultimate_ai_agent/core/remote_workers/audit.py",
            "src/ultimate_ai_agent/core/remote_workers/status.py",
            "src/ultimate_ai_agent/core/remote_workers/validation.py",
            "src/ultimate_ai_agent/core/remote_workers/dry_run.py",
            "tests/test_remote_worker_models.py",
            "tests/test_remote_worker_registry.py",
            "tests/test_remote_worker_policy.py",
            "tests/test_remote_worker_transports.py",
            "tests/test_remote_worker_dry_run.py",
            "tests/test_remote_worker_api_routes.py",
            "tests/test_remote_worker_no_network.py",
            "tests/test_remote_worker_gate_integration.py",
        ]
        failures = [f"missing {rel_path}" for rel_path in required if not (self.root / rel_path).exists()]
        return self._result(criterion, failures, required)

    def check_m105_remote_capabilities_default_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import NodeCapabilitySet

        capabilities = NodeCapabilitySet()
        failures = []
        for name, value in capabilities.model_dump().items():
            if value is not False:
                failures.append(f"{name} defaulted to {value}")
        for field, value in {"can_approve_actions": True, "can_run_critical": True}.items():
            try:
                NodeCapabilitySet(**{field: value})
                failures.append(f"{field} accepted true")
            except ValueError:
                pass
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/nodes.py"])

    def check_m105_unknown_node_and_transport_denied(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteNodeRegistry, RemoteTransportRegistry

        node = RemoteNodeRegistry().validate_node("missing_node")
        transport = RemoteTransportRegistry().validate_transport("missing_transport")
        failures = []
        if node.allowed or "REMOTE_NODE_UNKNOWN" not in node.reason_codes:
            failures.append("unknown node was not denied")
        if transport.allowed or "REMOTE_TRANSPORT_UNKNOWN" not in transport.reason_codes:
            failures.append("unknown transport was not denied")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/registry.py"])

    def check_m105_planned_transports_disabled(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import default_remote_transport_registry

        registry = default_remote_transport_registry()
        failures = []
        for transport_id in ["tailnet_planned", "lan_planned"]:
            descriptor = registry.get_transport(transport_id)
            decision = registry.validate_transport(transport_id)
            if descriptor is None:
                failures.append(f"{transport_id} missing")
                continue
            if descriptor.enabled:
                failures.append(f"{transport_id} enabled")
            if decision.allowed:
                failures.append(f"{transport_id} allowed")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/registry.py"])

    def check_m105_dry_run_dispatches_nothing(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            RemoteDryRunBuilder,
            RemoteExecutionPolicy,
            default_remote_node_registry,
            default_remote_transport_registry,
        )

        policy = RemoteExecutionPolicy(
            policy_id="m105_gate_policy",
            remote_workers_enabled=True,
            remote_transports_enabled=True,
            remote_accept_jobs=True,
        )
        envelope = RemoteDryRunBuilder().build_envelope(
            task_summary="Validate remote worker dry-run metadata.",
            node_id="mock_node",
            transport_id="mock_metadata",
            actor_context=self._actor(),
            policy=policy,
        )
        result = RemoteDryRunBuilder().dry_run(envelope, default_remote_node_registry(), default_remote_transport_registry(), policy)
        failures = []
        if result.dispatch_performed:
            failures.append("dry-run marked dispatch performed")
        if result.remote_execution_performed:
            failures.append("dry-run marked remote execution performed")
        if result.subagent_launched:
            failures.append("dry-run launched subagent")
        if result.tools_executed:
            failures.append("dry-run executed tools")
        if result.network_connections_opened:
            failures.append("dry-run opened network connections")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/dry_run.py"])

    def check_m105_no_remote_network_or_background_execution(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        root = self.root / "src/ultimate_ai_agent/core/remote_workers"
        forbidden_imports = {"socket", "subprocess", "threading", "asyncio", "requests", "httpx", "urllib"}
        forbidden_fragments = ["Popen", "os.system", "Thread(", "urlopen", "dispatch_job(", "execute_remote(", "launch_subagent("]
        failures = []
        for path in root.rglob("*.py"):
            source = self._read(path)
            for line in source.splitlines():
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    if any(fragment in stripped for fragment in forbidden_imports):
                        failures.append(f"{path.relative_to(self.root)} forbidden import: {stripped}")
                if any(fragment in stripped for fragment in forbidden_fragments):
                    failures.append(f"{path.relative_to(self.root)} forbidden fragment: {stripped}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers"])

    def check_m105_no_remote_subagents_tools_or_approvals(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteExecutionPolicy, evaluate_remote_job_policy

        failures = []
        policy = RemoteExecutionPolicy(
            policy_id="m105_gate_policy",
            remote_workers_enabled=True,
            remote_transports_enabled=True,
            remote_accept_jobs=True,
        )
        for capability, reason in [
            ("subagent", "REMOTE_SUBAGENT_DENIED"),
            ("tools", "REMOTE_TOOL_EXECUTION_DENIED"),
            ("approve", "REMOTE_APPROVAL_DENIED"),
            ("personal_data", "REMOTE_PERSONAL_DATA_DENIED"),
            ("write", "REMOTE_WRITE_DENIED"),
            ("send", "REMOTE_SEND_DENIED"),
        ]:
            envelope = self._m105_remote_job(requested_capabilities=[capability])
            decision = evaluate_remote_job_policy(envelope, self._m105_node_registry(), self._m105_transport_registry(), policy)
            if decision.allowed or reason not in decision.reason_codes:
                failures.append(f"{capability} not denied")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/policy.py"])

    def check_m105_remote_output_untrusted(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteDryRunBuilder, RemoteExecutionPolicy, RemoteOutputTrustLevel

        policy = RemoteExecutionPolicy(
            policy_id="m105_gate_policy",
            remote_workers_enabled=True,
            remote_transports_enabled=True,
            remote_accept_jobs=True,
        )
        result = RemoteDryRunBuilder().dry_run(
            self._m105_remote_job(),
            self._m105_node_registry(),
            self._m105_transport_registry(),
            policy,
        )
        failures = []
        if result.output_trust_level != RemoteOutputTrustLevel.untrusted_remote_output:
            failures.append("remote output not marked untrusted")
        if result.metadata.get("foundation_only") is not True:
            failures.append("remote result missing foundation_only marker")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/results.py"])

    def check_m105_api_routes_are_dry_run_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app

        paths = {route.path for route in app.routes}
        failures = []
        required = {
            "/remote-workers/nodes/validate",
            "/remote-workers/transports/validate",
            "/remote-workers/policy/validate",
            "/remote-workers/jobs/validate",
            "/remote-workers/dry-run",
            "/remote-workers/status",
            "/remote-workers/tailnet/status",
            "/remote-workers/mesh/status",
        }
        for path in required:
            if path not in paths:
                failures.append(f"missing route {path}")
        for forbidden in ["/remote-workers/dispatch", "/remote-workers/execute", "/remote-workers/subagents/launch"]:
            if forbidden in paths:
                failures.append(f"forbidden route present: {forbidden}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m105_docs_foundation_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        docs = [
            "docs/remote/REMOTE_WORKER_FOUNDATION.md",
            "docs/remote/REMOTE_NODE_SECURITY_MODEL.md",
            "docs/remote/REMOTE_JOB_ENVELOPE.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/decisions/remote_worker_tailnet_foundation.md",
            "docs/release_notes/v0_14_2.md",
        ]
        failures = []
        required_phrases = ["foundation-only", "No live networking", "No job dispatch", "No remote approvals"]
        for rel_path in docs:
            path = self.root / rel_path
            if not path.exists():
                failures.append(f"missing {rel_path}")
                continue
            source = self._read(path)
            for phrase in required_phrases:
                if phrase not in source:
                    failures.append(f"{rel_path} missing phrase: {phrase}")
        return self._result(criterion, failures, docs)

    def check_m105_remote_tailnet_enable_flag_rejected(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteExecutionPolicy

        failures = []
        try:
            RemoteExecutionPolicy(policy_id="m105_tailnet_policy", remote_tailnet_enabled=True)
            failures.append("remote_tailnet_enabled=true was accepted")
        except ValueError as exc:
            if "REMOTE_TAILNET_NOT_SUPPORTED_IN_M10_5" not in str(exc):
                failures.append("remote_tailnet_enabled=true failed without the expected reason code")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/policy.py"])

    def check_m105_remote_personal_data_enable_flag_rejected(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteExecutionPolicy

        failures = []
        try:
            RemoteExecutionPolicy(policy_id="m105_personal_data_policy", remote_personal_data_enabled=True)
            failures.append("remote_personal_data_enabled=true was accepted")
        except ValueError as exc:
            if "REMOTE_PERSONAL_DATA_NOT_SUPPORTED_IN_M10_5" not in str(exc):
                failures.append("remote_personal_data_enabled=true failed without the expected reason code")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/policy.py"])

    def check_m105_remote_worker_api_extra_fields_forbidden(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from fastapi.testclient import TestClient

        from ultimate_ai_agent.api.app import app

        failures = []
        client = TestClient(app)
        response = client.post(
            "/remote-workers/policy/validate",
            json={"policy": {"policy_id": "m105_extra_policy"}, "api_key": "sk_secret_value_123456"},
        )
        body = response.json()
        if response.status_code != 422:
            failures.append(f"extra top-level field returned status {response.status_code}")
        if body.get("success") is not False:
            failures.append("extra top-level field did not produce failure envelope")
        if "api_key" in response.text or "sk_secret_value_123456" in response.text:
            failures.append("extra top-level secret-like field leaked in validation response")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m143_private_mesh_taxonomy_open_source_first(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            PrivateMeshProviderKind,
            RemoteTransportSelectionPolicy,
            default_remote_transport_registry,
        )

        policy = RemoteTransportSelectionPolicy(policy_id="m143_private_mesh_policy")
        registry = default_remote_transport_registry()
        failures = []
        for transport_id in ["headscale_planned", "generic_wireguard_planned", "tailscale_planned", "private_mesh_planned"]:
            if registry.get_transport(transport_id) is None:
                failures.append(f"{transport_id} missing")
        if policy.prefer_open_source_first is not True:
            failures.append("open-source-first preference disabled")
        if policy.prefer_self_hosted_control_plane is not True:
            failures.append("self-hosted control-plane preference disabled")
        if policy.allow_proprietary_control_plane:
            failures.append("proprietary control plane allowed by default")
        if policy.allowed_provider_kinds[:2] != [
            PrivateMeshProviderKind.headscale_planned,
            PrivateMeshProviderKind.generic_wireguard_planned,
        ]:
            failures.append("planned provider order does not evaluate Headscale and generic WireGuard first")
        if PrivateMeshProviderKind.tailscale_planned not in policy.blocked_provider_kinds:
            failures.append("Tailscale planned provider was not blocked by default")
        docs = [
            "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/decisions/ADR-open-source-first-private-networking.md",
            "docs/release_notes/v0_14_3.md",
        ]
        required_phrases = ["open-source-first", "Headscale", "generic WireGuard", "Tailscale", "planned"]
        for rel_path in docs:
            source = self._read(self.root / rel_path)
            if not source:
                failures.append(f"missing {rel_path}")
                continue
            for phrase in required_phrases:
                if phrase.lower() not in source.lower():
                    failures.append(f"{rel_path} missing phrase: {phrase}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers", *docs])

    def check_m143_planned_mesh_transports_disabled(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import default_remote_transport_registry

        registry = default_remote_transport_registry()
        failures = []
        for transport_id in ["private_mesh_planned", "headscale_planned", "generic_wireguard_planned", "tailscale_planned", "tailnet_planned", "lan_planned"]:
            descriptor = registry.get_transport(transport_id)
            decision = registry.validate_transport(transport_id)
            if descriptor is None:
                failures.append(f"{transport_id} missing")
                continue
            if descriptor.enabled:
                failures.append(f"{transport_id} enabled")
            if descriptor.requires_network:
                failures.append(f"{transport_id} requires network")
            if descriptor.requires_credentials:
                failures.append(f"{transport_id} requires credentials")
            if descriptor.supports_dispatch:
                failures.append(f"{transport_id} supports dispatch")
            if decision.allowed:
                failures.append(f"{transport_id} allowed")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/registry.py"])

    def check_m143_no_live_mesh_integrations(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        forbidden_runtime_fragments = [
            "tailscaled",
            "tailscale.",
            "tailscale(",
            "headscale.",
            "headscale(",
            "wireguard.",
            "wireguard(",
            "wg ",
            "wg-quick",
            "serve",
            "funnel",
            "urlopen",
            "socket.",
            "dispatch_job(",
            "execute_remote(",
            "launch_subagent(",
        ]
        for path in (self.root / "src/ultimate_ai_agent/core/remote_workers").rglob("*.py"):
            source = self._read(path).lower()
            for fragment in forbidden_runtime_fragments:
                if fragment in source:
                    failures.append(f"{path.relative_to(self.root)} contains live mesh fragment: {fragment}")
        docs_to_scan = [
            self.root / "docs/remote",
            self.root / "docs/decisions",
            self.root / "docs/release_notes",
            self.root / "docs/implementation",
        ]
        tracked = "\n".join(self._read(path) for path in (self.root / "src/ultimate_ai_agent/core/remote_workers").rglob("*.py"))
        for doc_root in docs_to_scan:
            tracked += "\n" + "\n".join(self._read(path) for path in doc_root.rglob("*.md"))
        private_ip = re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b")
        if private_ip.search(tracked):
            failures.append("private IP literal found in runtime/docs")
        for forbidden_secretish in ["authkey-", "nodekey:", "tailnet name:", "oauth_client_secret"]:
            if forbidden_secretish in tracked.lower():
                failures.append(f"secret/private mesh config marker found: {forbidden_secretish}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers", "docs/remote"])

    def check_documentation_integrity_current(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        version = self._active_version()
        version_key = (version or "0.0.0").replace(".", "_")
        required = [
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/maintenance/documentation_integrity_checklist.md",
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
            f"docs/archive/releases/v{version_key}/README_IMPORT.md",
            f"docs/archive/releases/v{version_key}/master_plan.md",
            f"docs/release_notes/v{version_key}.md",
            f"docs/implementation/foundation_gate_implementation_plan_v{version_key}.md",
            "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
            "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
            "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        readme = self._read(self.root / "README.md")
        if version and f"docs/archive/releases/v{version_key}/README_IMPORT.md" not in readme:
            failures.append("README.md missing active archived import README")
        if version and f"docs/archive/releases/v{version_key}/master_plan.md" not in readme:
            failures.append("README.md missing active archived master plan")
        if "docs/DOCUMENTATION_INDEX.md" not in readme:
            failures.append("README.md missing documentation index")
        if "docs/canonical/CANONICAL_DOC_MAP.md" not in readme:
            failures.append("README.md missing canonical doc map")

        unsafe_claims = [
            "tailscale integration is implemented",
            "headscale integration is implemented",
            "remote execution is supported",
            "mobile camera access is implemented",
            "microphone capture is implemented",
            "gps access is implemented",
            "skill factory is implemented",
            "scanner runtime is implemented",
            "production_ready=true",
            "real_model_runtime_ready=true",
            "remote_execution_ready=true",
            "mobile_sensor_ready=true",
            "plugin_or_native_build_ready=true",
        ]
        active_docs = [
            "README.md",
            "VERSION.md",
            "AGENTS.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/api/README.md",
            "docs/api/openapi_contract.md",
            "docs/api/route_inventory.md",
            "docs/runtime/model_runtime_adapter_harness.md",
            "docs/runtime/local_loopback_model_runtime.md",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
            "docs/remote/REMOTE_WORKER_FOUNDATION.md",
            "docs/remote/REMOTE_NODE_SECURITY_MODEL.md",
            "docs/remote/REMOTE_JOB_ENVELOPE.md",
            "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
            "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/mobile_companion_backlog.md",
            "docs/backlog/device_capability_broker_backlog.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
        ]
        for rel_path in active_docs:
            path = self.root / rel_path
            if not path.exists():
                continue
            source = self._read(path).lower()
            for phrase in unsafe_claims:
                if phrase in source:
                    failures.append(f"{rel_path} contains unsafe implementation claim: {phrase}")
        return self._result(criterion, failures, required)

    def check_roadmap_milestone_charters_current(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/canonical/09_roadmap.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        if failures:
            return self._result(criterion, failures, required)

        charter = self._read(self.root / "docs/roadmap/MILESTONE_CHARTERS.md").lower()
        sequence = self._read(self.root / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md").lower()
        roadmap = self._read(self.root / "docs/canonical/09_roadmap.md").lower()
        for field in [
            "version",
            "milestone code",
            "title",
            "status",
            "purpose",
            "allowed scope",
            "must not add",
            "dependencies",
            "acceptance criteria",
            "review prompt required",
            "hardening patch expectation",
            "source-of-truth docs",
            "notes",
        ]:
            if field not in charter:
                failures.append(f"charter template missing {field}")
        if "m14" not in sequence or "web control center local backend connection stabilization" not in sequence:
            failures.append("M14 sequence is not local backend connection stabilization")
        if "m15" not in sequence or "approval queue + receipt/event viewer ui" not in sequence:
            failures.append("M15 sequence is not approval queue + receipt/event viewer UI")
        if "v0.17.4" not in sequence or "local browser smoke" not in sequence or "not m14" not in sequence:
            failures.append("v0.17.4 browser smoke boundary is not preserved")
        if "m14 is web control center local backend connection stabilization" not in roadmap:
            failures.append("canonical roadmap does not resolve M14")
        if "approval queue + receipt/event viewer ui moves to m15" not in roadmap:
            failures.append("canonical roadmap does not move approval/receipt UI to M15")
        if "v0.18.0 / m14" not in roadmap or "implemented" not in roadmap:
            failures.append("canonical roadmap does not mark M14 connection stabilization as implemented in v0.18.0")
        forbidden = [
            "m14 - local browser smoke",
            "m14 — local browser smoke",
            "m14: local browser smoke",
            "m14 - ux polish",
            "m14 — ux polish",
            "m14: ux polish",
        ]
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple < (0, 19, 0):
            forbidden.extend(
                [
                    "m15 is implemented",
                    "m15 has been implemented",
                    "implemented m15",
                    "m15 implementation complete",
                ]
            )
        combined = "\n".join([sequence, roadmap])
        for phrase in forbidden:
            if phrase in combined:
                failures.append(f"ambiguous or unsafe M14 claim: {phrase}")
        return self._result(criterion, failures, required)

    def check_codex_plugin_governance_docs_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        combined = "\n".join(self._read(self.root / path).lower() for path in required if (self.root / path).exists())
        expectations = {
            "iOS/macOS build plugins disabled": ["build ios apps", "build macos apps", "disabled"],
            "Computer Use disabled": ["computer use", "disabled"],
            "Chrome authenticated profile disabled": ["chrome authenticated", "disabled"],
            "plugin/skill installers disabled": ["plugin/skill installers", "disabled"],
            "Browser + Build Web Apps approval boundary": ["browser + build web apps", "approval"],
        }
        for label, fragments in expectations.items():
            if not all(fragment in combined for fragment in fragments):
                failures.append(f"missing policy phrase: {label}")
        forbidden_enablement_claims = [
            "plugins are enabled",
            "xcode workflow is enabled",
            "computer use is enabled",
            "chrome authenticated profile control is enabled",
            "plugin installers are enabled",
        ]
        for phrase in forbidden_enablement_claims:
            if phrase in combined:
                failures.append(f"unsafe plugin enablement claim: {phrase}")
        return self._result(criterion, failures, required)

    def check_m11_runtime_readiness_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/runtime_readiness/__init__.py",
            "src/ultimate_ai_agent/core/runtime_readiness/enums.py",
            "src/ultimate_ai_agent/core/runtime_readiness/matrix.py",
            "src/ultimate_ai_agent/core/runtime_readiness/reports.py",
            "src/ultimate_ai_agent/core/runtime_readiness/smoke_reports.py",
            "src/ultimate_ai_agent/core/runtime_readiness/validators.py",
            "src/ultimate_ai_agent/core/runtime_readiness/gate.py",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
            "tests/test_runtime_capability_matrix.py",
            "tests/test_manual_smoke_report_validation.py",
            "tests/test_runtime_readiness_report.py",
            "tests/test_runtime_readiness_api_routes.py",
            "tests/test_runtime_readiness_no_execution.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m11_runtime_capability_matrix_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.runtime_readiness import RuntimeCapabilityStatus, RuntimeSurface, build_matrix

        matrix = build_matrix()
        entries = {entry.surface: entry for entry in matrix.entries}
        expected = {
            RuntimeSurface.remote_worker_foundation.value: RuntimeCapabilityStatus.dry_run_only.value,
            RuntimeSurface.private_mesh_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.tailnet_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.headscale_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.generic_wireguard_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.tailscale_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.cloud_provider_runtime.value: RuntimeCapabilityStatus.blocked.value,
            RuntimeSurface.manual_loopback_smoke.value: RuntimeCapabilityStatus.manual_only.value,
            RuntimeSurface.mobile_companion_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.device_capability_broker_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.codex_plugin_governance.value: RuntimeCapabilityStatus.planned_disabled.value,
        }
        failures = []
        for surface, status in expected.items():
            entry = entries.get(surface)
            if entry is None:
                failures.append(f"missing matrix surface: {surface}")
            elif entry.status != status:
                failures.append(f"{surface} status is {entry.status}, expected {status}")
        if not matrix.assert_no_runtime_expansion():
            failures.append("matrix allows runtime expansion")
        if not matrix.assert_foundation_gate_coverage():
            failures.append("matrix entry missing Foundation Gate coverage")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/runtime_readiness/matrix.py"])

    def check_m11_manual_smoke_report_validation_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.runtime_readiness import validate_manual_smoke_report
        from ultimate_ai_agent.core.runtime_readiness.gate import m11_gate_safe_smoke_report_payload

        safe = validate_manual_smoke_report(m11_gate_safe_smoke_report_payload())
        unsafe_payloads = [
            ("raw prompt", {**m11_gate_safe_smoke_report_payload(), "raw_prompt": "user prompt"}),
            (
                "secret response",
                {**m11_gate_safe_smoke_report_payload(), "response_preview": "api" + "_key='abcdefghijklmnop'"},
            ),
            ("remote endpoint", {**m11_gate_safe_smoke_report_payload(), "endpoint_summary": "https" + "://api.example.com"}),
            (
                "cloud claim",
                {**m11_gate_safe_smoke_report_payload(), "metadata": {"claim": "cloud provider model call executed"}},
            ),
            (
                "authoritative output",
                {**m11_gate_safe_smoke_report_payload(), "model_output_authoritative": True},
            ),
        ]
        failures = []
        if not safe.allowed:
            failures.append("safe manual smoke report was rejected")
        for label, payload in unsafe_payloads:
            validation = validate_manual_smoke_report(payload)
            if validation.allowed:
                failures.append(f"unsafe manual smoke report accepted: {label}")
            if "abcdefghijklmnop" in validation.safe_message:
                failures.append("unsafe secret echoed in validation message")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/runtime_readiness/smoke_reports.py"])

    def check_m11_no_production_readiness_claim(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.runtime_readiness import build_readiness_report

        report = build_readiness_report()
        failures = []
        checks = {
            "production_ready": report.production_ready,
            "real_model_runtime_ready": report.real_model_runtime_ready,
            "remote_execution_ready": report.remote_execution_ready,
            "mobile_sensor_ready": report.mobile_sensor_ready,
            "plugin_or_native_build_ready": report.plugin_or_native_build_ready,
            "model_output_authoritative": report.model_output_authoritative,
        }
        failures.extend(f"{name} is true" for name, value in checks.items() if value is True)
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/runtime_readiness/reports.py"])

    def check_m11_runtime_api_status_validation_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items
        from ultimate_ai_agent.api.openapi import FORBIDDEN_ROUTE_FRAGMENTS

        routes = iter_api_route_items(app)
        paths = {route.path: route for route in routes}
        required = {
            "/runtime/readiness",
            "/runtime/capability-matrix",
            "/runtime/smoke-reports/validate",
        }
        failures = [f"missing runtime route: {path}" for path in sorted(required - set(paths))]
        for path in sorted(path for path in paths if path.startswith("/runtime")):
            route = paths[path]
            if "runtime-readiness" not in route.tags:
                failures.append(f"{path} has unexpected tags {route.tags}")
            if not route.validation_only:
                failures.append(f"{path} is not validation/status only")
        unsafe_routes = [
            path
            for path in paths
            if path.startswith("/runtime") and any(fragment in path for fragment in FORBIDDEN_ROUTE_FRAGMENTS)
        ]
        failures.extend(f"forbidden runtime route present: {path}" for path in sorted(unsafe_routes))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py", "src/ultimate_ai_agent/api/openapi.py"])

    def check_m11_no_smoke_script_execution_in_gate(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        for rel_path in ["scripts/verify_all.py", "scripts/run_foundation_gate.py"]:
            source = self._read(self.root / rel_path)
            if "local_loopback_smoke.py" in source:
                failures.append(f"{rel_path} references local_loopback_smoke.py")
        return self._result(criterion, failures, ["scripts/verify_all.py", "scripts/run_foundation_gate.py"])

    def check_m11_no_runtime_expansion_imports(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        package = self.root / "src/ultimate_ai_agent/core/runtime_readiness"
        forbidden_starts = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "urllib",
            "from " + "urllib import",
            "import " + "socket",
            "import " + "subprocess",
            "import " + "openai",
            "import " + "anthropic",
            "import " + "tiktoken",
            "import " + "tokenizers",
        ]
        forbidden_fragments = ["billing", "eval(", "exec("]
        failures = []
        for path in sorted(package.glob("*.py")):
            rel_path = str(path.relative_to(self.root))
            for line_no, stripped in enumerate(self._read(path).splitlines(), start=1):
                stripped = stripped.strip()
                if self._is_static_scanner_text(stripped) or stripped.startswith("["):
                    continue
                if any(stripped.startswith(pattern) for pattern in forbidden_starts):
                    failures.append(f"{rel_path}:{line_no} forbidden import")
                if any(fragment in stripped for fragment in forbidden_fragments):
                    failures.append(f"{rel_path}:{line_no} forbidden runtime fragment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/runtime_readiness"])

    def check_m11_no_remote_mesh_mobile_or_plugin_enablement(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        sources = [
            "src/ultimate_ai_agent/core/runtime_readiness",
            "src/ultimate_ai_agent/api/app.py",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
        ]
        forbidden_claims = [
            "remote_execution_ready=true",
            "live mesh is enabled",
            "tailnet is enabled",
            "headscale is connected",
            "wireguard is connected",
            "mobile sensors are enabled",
            "camera access is implemented",
            "plugin enablement is implemented",
            "native build execution is enabled",
            "computer use automation is enabled",
        ]
        combined = ""
        for source in sources:
            path = self.root / source
            if path.is_dir():
                combined += "\n".join(self._read(child) for child in path.glob("*.py"))
            else:
                combined += "\n" + self._read(path)
        lowered = combined.lower()
        failures = [f"unsafe enablement claim: {phrase}" for phrase in forbidden_claims if phrase in lowered]
        return self._result(criterion, failures, sources)

    def check_m12_control_center_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/control_center/__init__.py",
            "src/ultimate_ai_agent/core/control_center/enums.py",
            "src/ultimate_ai_agent/core/control_center/manifest.py",
            "src/ultimate_ai_agent/core/control_center/dashboard.py",
            "src/ultimate_ai_agent/core/control_center/actions.py",
            "src/ultimate_ai_agent/core/control_center/summaries.py",
            "src/ultimate_ai_agent/core/control_center/validation.py",
            "src/ultimate_ai_agent/core/control_center/policy.py",
            "tests/test_control_center_manifest.py",
            "tests/test_control_center_dashboard.py",
            "tests/test_control_center_action_preview.py",
            "tests/test_control_center_api_routes.py",
            "tests/test_control_center_no_execution.py",
            "tests/test_m12_gate_integration.py",
            "docs/control_center/CONTROL_CENTER_CONTRACT.md",
            "docs/control_center/DASHBOARD_SNAPSHOT.md",
            "docs/control_center/ACTION_PREVIEW_POLICY.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m12_control_center_manifest_read_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.control_center import ControlCenterCapabilityStatus, build_control_center_manifest

        manifest = build_control_center_manifest()
        allowed_statuses = {
            ControlCenterCapabilityStatus.available_read_only.value,
            ControlCenterCapabilityStatus.preview_only.value,
            ControlCenterCapabilityStatus.validation_only.value,
            ControlCenterCapabilityStatus.planned_disabled.value,
            ControlCenterCapabilityStatus.blocked.value,
            ControlCenterCapabilityStatus.not_implemented.value,
        }
        failures = []
        for surface in manifest.surfaces:
            if surface.status not in allowed_statuses:
                failures.append(f"{surface.surface} has unsafe status {surface.status}")
            if surface.execution_allowed:
                failures.append(f"{surface.surface} allows execution")
        for capability in [
            "runtime_execution",
            "model_execution",
            "provider_invocation",
            "remote_dispatch",
            "mobile_sensor_access",
            "plugin_enablement",
            "frontend_build_tooling",
        ]:
            if capability not in manifest.blocked_capabilities:
                failures.append(f"missing blocked capability: {capability}")
        if manifest.metadata.get("frontend_implemented") is not False:
            failures.append("manifest does not mark frontend unimplemented")
        if manifest.metadata.get("production_control_center") is not False:
            failures.append("manifest implies production Control Center")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/control_center/manifest.py"])

    def check_m12_control_center_dashboard_secret_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.control_center import build_control_center_dashboard
        from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like

        snapshot = build_control_center_dashboard(api_route_count=74, foundation_gate_status="passed")
        failures = []
        if contains_secret_like(snapshot.model_dump(mode="json")):
            failures.append("dashboard contains secret-like values")
        if snapshot.runtime_readiness_summary.production_ready:
            failures.append("dashboard claims production runtime readiness")
        if snapshot.remote_worker_summary.execution_enabled:
            failures.append("dashboard enables remote worker execution")
        if snapshot.mobile_planning_summary.sensor_access_enabled:
            failures.append("dashboard enables mobile sensors")
        if snapshot.plugin_governance_summary.plugin_enablement_allowed:
            failures.append("dashboard enables plugins")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/control_center/dashboard.py"])

    def check_m12_control_center_action_preview_no_execution(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.control_center import (
            ControlCenterActionKind,
            ControlCenterRiskLevel,
            preview_control_center_action,
        )

        base = {
            "request_id": "m12_gate_preview",
            "actor_context": {"actor_type": "user", "actor_id": "local_operator"},
            "action_kind": ControlCenterActionKind.view_status,
            "target_ref": "dashboard",
            "purpose": "review status",
            "risk_level": ControlCenterRiskLevel.safe,
            "data_classification": "system_internal",
            "consent_refs": [],
        }
        failures = []
        safe = preview_control_center_action(base)
        if not safe.allowed:
            failures.append("safe preview was not allowed")
        unsafe_cases = [
            ("execute action", {**base, "action_kind": ControlCenterActionKind.disabled_execute}),
            ("runtime execute", {**base, "target_ref": "runtime/execute/model"}),
            ("remote dispatch", {**base, "target_ref": "remote-workers/dispatch/job"}),
            ("plugin enable", {**base, "target_ref": "plugins/enable/build-web-apps"}),
            ("mobile sensor", {**base, "target_ref": "mobile/sensors/camera"}),
            ("provider invocation", {**base, "metadata": {"claim": "provider invocation requested"}}),
            ("credential use", {**base, "metadata": {"claim": "credential use requested"}}),
            ("mutation", {**base, "metadata": {"claim": "mutate file requested"}}),
            ("arbitrary approval", {**base, "approval_ref": "approval_any_string"}),
        ]
        for label, payload in unsafe_cases:
            decision = preview_control_center_action(payload)
            if decision.allowed:
                failures.append(f"unsafe preview allowed: {label}")
            if decision.metadata.get("executed") is not False:
                failures.append(f"preview execution marker unsafe: {label}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/control_center/actions.py"])

    def check_m12_control_center_api_read_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items
        from ultimate_ai_agent.api.openapi import FORBIDDEN_ROUTE_FRAGMENTS

        routes = iter_api_route_items(app)
        paths = {route.path: route for route in routes}
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
        failures = [f"missing control-center route: {path}" for path in sorted(required - set(paths))]
        for path in sorted(path for path in paths if path.startswith("/control-center")):
            route = paths[path]
            if "control-center" not in route.tags:
                failures.append(f"{path} has unexpected tags {route.tags}")
            if not route.validation_only:
                failures.append(f"{path} is not read-only/preview-only")
        unsafe_routes = [
            path
            for path in paths
            if path.startswith("/control-center") and any(fragment in path for fragment in FORBIDDEN_ROUTE_FRAGMENTS)
        ]
        failures.extend(f"forbidden control-center route present: {path}" for path in sorted(unsafe_routes))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py", "src/ultimate_ai_agent/api/openapi.py"])

    def check_m12_no_frontend_dependencies(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden_paths = [
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "vite.config.ts",
            "vite.config.js",
            "next.config.js",
            "next.config.ts",
            "tailwind.config.js",
            "tailwind.config.ts",
            "components.json",
            "node_modules",
        ]
        failures = [f"frontend artifact exists: {path}" for path in forbidden_paths if (self.root / path).exists()]
        pyproject = self._read(self.root / "pyproject.toml").lower()
        for dependency in ["react", "next", "vite", "tailwind", "shadcn"]:
            if dependency in pyproject:
                failures.append(f"frontend dependency marker in pyproject: {dependency}")
        return self._result(criterion, failures, forbidden_paths + ["pyproject.toml"])

    def check_m12_no_runtime_network_mobile_plugin_expansion(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        package = self.root / "src/ultimate_ai_agent/core/control_center"
        forbidden_starts = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "urllib",
            "from " + "urllib import",
            "import " + "socket",
            "from " + "socket import",
            "import " + "subprocess",
            "from " + "subprocess import",
            "import " + "openai",
            "from " + "openai import",
            "import " + "anthropic",
            "from " + "anthropic import",
            "import " + "tiktoken",
            "import " + "tokenizers",
        ]
        forbidden_fragments = [
            "urlopen",
            "billing",
            "eval(",
            "exec(",
            "enable_plugin(",
            "dispatch_remote",
            "mobile_sensor_access=true",
            "runtime_execution=true",
            "provider_invocation=true",
            "browser automation is enabled",
        ]
        failures = []
        for path in sorted(package.glob("*.py")):
            rel_path = str(path.relative_to(self.root))
            for line_no, stripped in enumerate(self._read(path).splitlines(), start=1):
                stripped = stripped.strip().lower()
                if stripped.startswith("[") or self._is_static_scanner_text(stripped):
                    continue
                if any(stripped.startswith(pattern) for pattern in forbidden_starts):
                    failures.append(f"{rel_path}:{line_no} forbidden import")
                if any(fragment in stripped for fragment in forbidden_fragments):
                    failures.append(f"{rel_path}:{line_no} forbidden runtime expansion fragment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/control_center"])

    def check_m13_web_control_center_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "apps/control-center/package.json",
            "apps/control-center/package-lock.json",
            "apps/control-center/index.html",
            "apps/control-center/vite.config.ts",
            "apps/control-center/tsconfig.json",
            "apps/control-center/src/App.tsx",
            "apps/control-center/src/main.tsx",
            "apps/control-center/src/api/client.ts",
            "apps/control-center/src/api/endpoints.ts",
            "apps/control-center/src/api/redaction.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "apps/control-center/src/components/ActionPreviewForm.tsx",
            "apps/control-center/src/App.test.tsx",
            "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
            "docs/control_center/FRONTEND_SAFETY_POLICY.md",
            "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m13_web_shell_read_only_preview_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        app_root = self.root / "apps/control-center"
        package = json.loads(self._read(app_root / "package.json") or "{}")
        deps = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))
        allowed_deps = {
            "react",
            "react-dom",
            "@vitejs/plugin-react",
            "vite",
            "typescript",
            "@types/react",
            "@types/react-dom",
            "@types/node",
            "vitest",
            "@testing-library/react",
            "@testing-library/jest-dom",
            "jsdom",
        }
        forbidden_deps = {
            "next",
            "tailwindcss",
            "stripe",
            "@stripe/stripe-js",
            "@supabase/supabase-js",
            "firebase",
            "auth0-js",
            "openai",
            "anthropic",
            "expo",
            "react-native",
            "electron",
            "playwright",
            "puppeteer",
        }
        failures = [f"unexpected frontend dependency: {dep}" for dep in sorted(deps - allowed_deps)]
        failures.extend(f"forbidden frontend dependency: {dep}" for dep in sorted(deps & forbidden_deps))
        source_paths = [
            *sorted((app_root / "src").rglob("*.ts")),
            *sorted((app_root / "src").rglob("*.tsx")),
            *sorted((app_root / "src").rglob("*.css")),
        ]
        source_text = "\n".join(
            self._read(path).lower()
            for path in source_paths
            if path.is_file() and ".test." not in path.name
        )
        forbidden = [
            "/control-center/actions/execute",
            "/control-center/plugins/enable",
            "/control-center/runtime/execute",
            "/control-center/remote-workers/dispatch",
            "/control-center/mobile/sensors",
            "/model-runtime/execute",
            "document.cookie",
            "localstorage",
            "sessionstorage",
            "navigator.geolocation",
            "mediadevices",
            "getusermedia",
            "chrome.",
            "computer use",
            "xcode",
            "app store connect",
            "keychain",
        ]
        failures.extend(f"forbidden frontend source fragment: {fragment}" for fragment in forbidden if fragment in source_text)
        if "no authority to run actions" not in source_text:
            failures.append("frontend does not visibly mark no action authority")
        return self._result(criterion, failures, ["apps/control-center/package.json", "apps/control-center/src"])

    def check_m13_action_preview_ui_posts_only_to_preview(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        app_root = self.root / "apps/control-center/src"
        endpoints = self._read(app_root / "api/endpoints.ts")
        client = self._read(app_root / "api/client.ts")
        failures = []
        if 'actionPreview: "/control-center/actions/preview"' not in endpoints:
            failures.append("action preview endpoint declaration missing")
        if endpoints.count("/control-center/actions/preview") != 1:
            failures.append("action preview endpoint should appear exactly once in endpoint declarations")
        if "method: \"POST\"" not in client:
            failures.append("frontend client does not declare preview POST")
        if "API_ENDPOINTS.actionPreview" not in client:
            failures.append("frontend client does not post to actionPreview endpoint constant")
        post_count = sum(1 for path in app_root.rglob("*.ts*") if "method: \"POST\"" in self._read(path))
        if post_count != 1:
            failures.append(f"unexpected frontend POST declaration count: {post_count}")
        return self._result(criterion, failures, ["apps/control-center/src/api/endpoints.ts", "apps/control-center/src/api/client.ts"])

    def check_m13_mock_data_safe_non_authoritative(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        mock_path = self.root / "apps/control-center/src/mocks/controlCenterData.ts"
        text = self._read(mock_path).lower()
        failures = []
        required_safe_fragments = [
            "mock: true",
            "production_control_center: false",
            "production_ready: false",
            "real_model_runtime_ready: false",
            "remote_execution_ready: false",
            "mobile_sensor_ready: false",
            "plugin_or_native_build_ready: false",
            "execution_enabled: false",
            "dispatch_enabled: false",
            "sensor_access_enabled: false",
            "plugin_enablement_allowed: false",
            "native_build_tools_enabled: false",
            "model_output_authoritative: false",
        ]
        for fragment in required_safe_fragments:
            if fragment not in text:
                failures.append(f"mock data missing safe fragment: {fragment}")
        forbidden = [
            "production_ready: true",
            "real_model_runtime_ready: true",
            "remote_execution_ready: true",
            "mobile_sensor_ready: true",
            "plugin_or_native_build_ready: true",
            "execution_enabled: true",
            "dispatch_enabled: true",
            "sensor_access_enabled: true",
            "plugin_enablement_allowed: true",
            "native_build_tools_enabled: true",
            "api_key",
            "password",
            "authorization",
            "cookie",
        ]
        failures.extend(f"unsafe mock data fragment: {fragment}" for fragment in forbidden if fragment in text)
        return self._result(criterion, failures, ["apps/control-center/src/mocks/controlCenterData.ts"])

    def check_m13_no_tracked_generated_or_native_artifacts(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden_paths = [
            "apps/control-center/.next",
            "apps/control-center/ios",
            "apps/control-center/android",
            "apps/control-center/Podfile",
            "apps/control-center/Package.swift",
            "apps/control-center/electron",
        ]
        failures = [f"forbidden frontend/native artifact exists: {path}" for path in forbidden_paths if (self.root / path).exists()]
        gitignore = self._read(self.root / ".gitignore")
        for required_ignore in ["node_modules/", "dist/", "coverage/", ".env"]:
            if required_ignore not in gitignore:
                failures.append(f".gitignore missing frontend artifact guard: {required_ignore}")
        return self._result(criterion, failures, forbidden_paths + [".gitignore"])

    def check_m13_backend_api_contract_unchanged(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items

        routes = iter_api_route_items(app)
        paths = {route.path: route for route in routes}
        historical_paths = dict(paths)
        historical_paths.pop(M37_ALLOWED_CAPTURE_ROUTE, None)
        failures = []
        if len(historical_paths) != 74:
            failures.append(f"API path count changed from M12 contract: {len(historical_paths)}")
        control_center_routes = [path for path in paths if path.startswith("/control-center")]
        if len(control_center_routes) != 8:
            failures.append(f"unexpected Control Center route count: {len(control_center_routes)}")
        forbidden = [
            "/control-center/actions/execute",
            "/control-center/plugins/enable",
            "/control-center/runtime/execute",
            "/control-center/remote-workers/dispatch",
            "/control-center/mobile/sensors",
            "/control-center/frontend",
        ]
        failures.extend(f"forbidden Control Center route present: {path}" for path in forbidden if path in paths)
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py", "apps/control-center"])

    def check_m13_frontend_no_sensitive_browser_apis(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        app_root = self.root / "apps/control-center/src"
        forbidden = [
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
        failures = []
        for path in [*app_root.rglob("*.ts"), *app_root.rglob("*.tsx")]:
            if ".test." in path.name or "test" in path.parts:
                continue
            lowered = self._read(path).lower()
            rel = path.relative_to(self.root)
            failures.extend(f"{rel} forbidden browser API: {fragment}" for fragment in forbidden if fragment in lowered)
        return self._result(criterion, failures, ["apps/control-center/src"])

    def check_m13_control_center_frontend_safety_verifier_passes(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        import importlib.util

        script = self.root / "scripts/verify_control_center_frontend.py"
        failures = []
        if not script.exists():
            failures.append("scripts/verify_control_center_frontend.py missing")
            return self._result(criterion, failures, [str(script.relative_to(self.root))])
        spec = importlib.util.spec_from_file_location("verify_control_center_frontend", script)
        if spec is None or spec.loader is None:
            failures.append("could not load frontend safety verifier")
            return self._result(criterion, failures, [str(script.relative_to(self.root))])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        failures.extend(module.verify(self.root))
        return self._result(criterion, failures, ["scripts/verify_control_center_frontend.py", "apps/control-center"])

    def check_m13_frontend_ci_covers_local_checks(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        workflow = self.root / ".github/workflows/ci.yml"
        text = self._read(workflow).lower()
        required = [
            "apps/control-center",
            "npm ci",
            "npm run typecheck --if-present",
            "npm run lint --if-present",
            "npm run test --if-present -- --run",
            "npm run build --if-present",
        ]
        forbidden = [
            "playwright",
            "puppeteer",
            "selenium",
            "webdriver",
            "chrome --user-data-dir",
            "computer use",
            "xcodebuild",
            "app-store-connect",
            "fastlane",
            "vercel",
            "netlify",
            "firebase deploy",
        ]
        failures = [f"CI missing frontend check fragment: {fragment}" for fragment in required if fragment not in text]
        failures.extend(f"CI includes forbidden browser/native/deploy fragment: {fragment}" for fragment in forbidden if fragment in text)
        return self._result(criterion, failures, [".github/workflows/ci.yml"])

    def check_m13_browser_smoke_readiness_manual_local_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        doc = self.root / "docs/control_center/LOCAL_BROWSER_SMOKE.md"
        text = self._read(doc).lower()
        required = [
            "manual local browser smoke",
            "local-only",
            "localhost",
            "127.0.0.1",
            "::1",
            "no authenticated browser profile",
            "no chrome authenticated profile control",
            "no computer use",
            "no external sites",
            "no production backend",
            "no screenshots with secrets",
            "preview-only",
            "non-authoritative",
        ]
        failures = [f"browser smoke doc missing safety fragment: {fragment}" for fragment in required if fragment not in text]
        return self._result(criterion, failures, ["docs/control_center/LOCAL_BROWSER_SMOKE.md"])

    def check_m13_browser_smoke_readiness_verifier_passes(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util

        script = self.root / "scripts/verify_control_center_browser_smoke_readiness.py"
        failures = []
        if not script.exists():
            failures.append("scripts/verify_control_center_browser_smoke_readiness.py missing")
            return self._result(criterion, failures, [str(script.relative_to(self.root))])
        spec = importlib.util.spec_from_file_location("verify_control_center_browser_smoke_readiness", script)
        if spec is None or spec.loader is None:
            failures.append("could not load browser smoke readiness verifier")
            return self._result(criterion, failures, [str(script.relative_to(self.root))])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        failures.extend(module.verify(self.root))
        return self._result(
            criterion,
            failures,
            ["scripts/verify_control_center_browser_smoke_readiness.py", "docs/control_center/LOCAL_BROWSER_SMOKE.md"],
        )

    def check_m14_local_backend_api_base_policy(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        app_root = self.root / "apps/control-center/src"
        base_url = self._read(app_root / "api/baseUrl.ts")
        client = self._read(app_root / "api/client.ts")
        tests = self._read(app_root / "api/baseUrl.test.ts")
        vite_config = self._read(self.root / "apps/control-center/vite.config.ts")
        failures = []
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
            if fragment not in base_url:
                failures.append(f"API base policy missing fragment: {fragment}")
        external_fixture = "https" + "://api.example.com"
        for fragment in [
            external_fixture,
            "http://8.8.8.8:8000",
            "http://10.0.0.5:8000",
            "http://172.16.0.2:8000",
            "http://192.168.1.10:8000",
            "supersecretvalue123",
            '"tok" + "en"',
            "api_key",
            "credential",
        ]:
            if fragment not in tests:
                failures.append(f"API base policy tests missing unsafe case: {fragment}")
        if "resolveApiBaseUrl" not in client:
            failures.append("frontend client does not use resolveApiBaseUrl")
        local_proxy_target = 'target: "' + "http" + '://127.0.0.1:8000"'
        if local_proxy_target not in vite_config:
            failures.append("Vite dev proxy is not pinned to local backend loopback")
        required_proxy_routes = [
            '"/control-center"',
            '"/runtime/readiness"',
            '"/runtime/capability-matrix"',
            '"/runtime/smoke-reports"',
        ]
        for route in required_proxy_routes:
            if route not in vite_config:
                failures.append(f"Vite dev proxy does not cover local backend route: {route}")
        if re.search(r'["\']/runtime["\']\s*:', vite_config):
            failures.append("Vite dev proxy must not proxy broad /runtime frontend route space")
        if "changeOrigin: true" in vite_config:
            failures.append("Vite dev proxy rewrites origin")
        forbidden_client_fragments = [
            "Authorization",
            "Bearer ",
            "api_key",
            "document.cookie",
            "localStorage",
            "sessionStorage",
        ]
        failures.extend(
            f"frontend client contains forbidden connection fragment: {fragment}"
            for fragment in forbidden_client_fragments
            if fragment in client
        )
        return self._result(
            criterion,
            failures,
            [
                "apps/control-center/src/api/baseUrl.ts",
                "apps/control-center/src/api/client.ts",
                "apps/control-center/vite.config.ts",
            ],
        )

    def check_m14_connection_states_visible_and_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        app = self._read(self.root / "apps/control-center/src/App.tsx")
        types = self._read(self.root / "apps/control-center/src/api/types.ts")
        client = self._read(self.root / "apps/control-center/src/api/client.ts")
        data_state = self._read(self.root / "apps/control-center/src/components/DataState.tsx")
        mock = self._read(self.root / "apps/control-center/src/mocks/controlCenterData.ts")
        tests = self._read(self.root / "apps/control-center/src/App.test.tsx")
        combined = "\n".join([app, types, client, data_state, mock, tests])
        failures = []
        required_fragments = [
            "BackendConnectionSummary",
            "unknown",
            "checking",
            "online",
            "degraded",
            "offline",
            "mock_fallback",
            "Backend state unknown",
            "Checking backend connection",
            "Backend online",
            "Backend degraded",
            "Mock fallback active",
            "Checking local backend connection state",
            "non-authoritative mock fallback",
            "API base:",
            "usingMockData",
            "LOCAL_BACKEND_DEGRADED",
            "PARTIAL_MOCK_FALLBACK",
            "MOCK_DATA_ONLY",
        ]
        for fragment in required_fragments:
            if fragment not in combined:
                failures.append(f"connection state fragment missing: {fragment}")
        forbidden_fragments = [
            "production_authority: true",
            "productionControlCenter: true",
            "approval_grants_created: true",
            "Authorization",
            "document.cookie",
        ]
        failures.extend(
            f"unsafe connection state fragment: {fragment}"
            for fragment in forbidden_fragments
            if fragment in combined
        )
        return self._result(
            criterion,
            failures,
            [
                "apps/control-center/src/App.tsx",
                "apps/control-center/src/api/client.ts",
                "apps/control-center/src/api/types.ts",
                "apps/control-center/src/components/DataState.tsx",
                "apps/control-center/src/mocks/controlCenterData.ts",
            ],
        )

    def check_m14_backend_api_contract_unchanged(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        result = self.check_m13_backend_api_contract_unchanged(criterion)
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items

        paths = {route.path for route in iter_api_route_items(app)}
        forbidden = [
            "/control-center/approvals",
            "/control-center/approval-queue",
            "/control-center/events",
            "/control-center/receipts",
            "/control-center/actions/execute",
            "/control-center/runtime/connect",
        ]
        failures = list(result.failures)
        failures.extend(f"out-of-scope M14 route present: {path}" for path in forbidden if path in paths)
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/api/app.py", "src/ultimate_ai_agent/api/manifest.py"],
        )

    def check_m15_approval_receipt_event_ui_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        import importlib.util

        required_files = [
            "apps/control-center/src/components/ApprovalQueuePanel.tsx",
            "apps/control-center/src/components/ReceiptViewerPanel.tsx",
            "apps/control-center/src/components/EventViewerPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "scripts/verify_control_center_frontend.py",
        ]
        implementation_files = [
            "apps/control-center/src/components/ApprovalQueuePanel.tsx",
            "apps/control-center/src/components/ReceiptViewerPanel.tsx",
            "apps/control-center/src/components/EventViewerPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        failures = [f"missing M15 frontend file: {path}" for path in required_files if not (self.root / path).exists()]
        components = "\n".join(self._read(self.root / path) for path in implementation_files if (self.root / path).exists())
        lowered = components.lower()

        required_fragments = [
            "ApprovalQueuePanel",
            "ReceiptViewerPanel",
            "EventViewerPanel",
            'path: "/approvals"',
            'path: "/receipts"',
            'path: "/events"',
            "Approval Queue",
            "Receipt Viewer",
            "Event Viewer",
            "read-only",
            "preview-only",
            "Approval Authority handles final decision",
            "This UI cannot grant, deny, execute, or bypass approvals",
            "Approval refs are identifiers only and never authority",
            "Python Agent Core remains the only approval authority",
            "Receipt detail is redacted summary metadata only",
            "Event detail is redacted summary metadata only",
            "redacted_summary_only",
            "MOCK_DATA_ONLY",
            "nonAuthoritative",
            "approvalQueue",
            "receipts",
            "events",
        ]
        failures.extend(f"M15 UI missing required fragment: {fragment}" for fragment in required_fragments if fragment not in components)

        forbidden_fragments = [
            "/approvals/approve",
            "/approvals/deny",
            "/control-center/approvals/execute",
            "/control-center/approvals/approve",
            "/control-center/approvals/deny",
            "/receipts/delete",
            "/events/raw",
            "/memory/raw",
            "/files/raw",
            "<button>approve</button>",
            "<button>deny</button>",
            "<button>execute</button>",
            "<button>run</button>",
            "<button>send</button>",
            "<button>deploy</button>",
            "<button>enable</button>",
            "localstorage",
            "sessionstorage",
            "document.cookie",
            'type="password"',
            'name="apikey"',
            'name="token"',
            "rawpromptbody",
            "rawfilebody",
            "rawmemorycontent",
            "raweventpayload",
            "rawreceiptpayload",
            "credentialref",
            "credentialhandle",
        ]
        failures.extend(f"M15 UI contains forbidden fragment: {fragment}" for fragment in forbidden_fragments if fragment in lowered)

        script = self.root / "scripts/verify_control_center_frontend.py"
        if script.exists():
            spec = importlib.util.spec_from_file_location("verify_control_center_frontend", script)
            if spec is None or spec.loader is None:
                failures.append("could not load frontend safety verifier")
            else:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                failures.extend(module.verify(self.root))

        return self._result(criterion, failures, required_files)

    def check_m16_event_timeline_trace_viewer_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        import importlib.util
        from ultimate_ai_agent.api.app import app

        required_files = [
            "apps/control-center/src/components/EventTimelineTracePanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "scripts/verify_control_center_frontend.py",
            "docs/control_center/EVENT_TIMELINE_UI.md",
            "docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md",
            "docs/control_center/TRACE_REDACTION_POLICY.md",
        ]
        implementation_files = [
            "apps/control-center/src/components/EventTimelineTracePanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        failures = [f"missing M16 timeline trace file: {path}" for path in required_files if not (self.root / path).exists()]
        components = "\n".join(self._read(self.root / path) for path in implementation_files if (self.root / path).exists())
        lowered = components.lower().replace(" ", "")

        required_fragments = [
            "EventTimelineTracePanel",
            'path: "/events/timeline"',
            "Event Timeline",
            "M16 trace surface",
            "Timeline and trace views are read-only",
            "Trace detail is redacted summary metadata only",
            "No trace export or external telemetry is available",
            "mock_run_ref_001",
            "mock_correlation_ref_001",
            "mock_event_ref_001",
            "mock_receipt_ref_001",
            "mock_evidence_ref_gate_001",
            "redacted_summary_only",
            "m16Trace",
            "traceRelations",
            "foundationGateEvidence",
            "NO_EXTERNAL_EXPORT",
            "external_export_allowed: false",
        ]
        failures.extend(f"M16 UI missing required fragment: {fragment}" for fragment in required_fragments if fragment not in components)

        forbidden_fragments = [
            "/events/timeline/raw",
            "/events/timeline/export",
            "/traces/raw",
            "/traces/export",
            "/runs/execute",
            "/control-center/traces/raw",
            "/control-center/traces/export",
            "<button>approve</button>",
            "<button>deny</button>",
            "<button>execute</button>",
            "<button>run</button>",
            "<button>send</button>",
            "<button>deploy</button>",
            "<button>enable</button>",
            "localstorage",
            "sessionstorage",
            "document.cookie",
            'type="password"',
            'name="apikey"',
            'name="token"',
            "rawpromptbody",
            "rawfilecontent",
            "rawmemorycontent",
            "raweventpayload",
            "rawreceiptpayload",
            "rawproviderpayload",
            "credentialref",
            "credentialhandle",
        ]
        failures.extend(f"M16 UI contains forbidden fragment: {fragment}" for fragment in forbidden_fragments if fragment in lowered)

        docs_text = "\n".join(self._read(self.root / path) for path in required_files if path.startswith("docs/"))
        doc_fragments = [
            "read-only",
            "summary-only",
            "safe refs",
            "No backend route is added",
            "no raw prompts",
            "no raw secrets",
            "no raw file contents",
            "no raw memory contents",
            "no raw credentials",
            "no raw provider payloads",
            "no execution controls",
            "no external telemetry export",
        ]
        failures.extend(f"M16 docs missing required fragment: {fragment}" for fragment in doc_fragments if fragment not in docs_text)

        try:
            openapi_paths = app.openapi().get("paths", {})
        except Exception as exc:
            failures.append(f"M16 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m16_openapi_route_failures(openapi_paths))

        script = self.root / "scripts/verify_control_center_frontend.py"
        if script.exists():
            spec = importlib.util.spec_from_file_location("verify_control_center_frontend", script)
            if spec is None or spec.loader is None:
                failures.append("could not load frontend safety verifier")
            else:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                failures.extend(module.verify(self.root))

        return self._result(criterion, failures, required_files)

    def check_m17_evidence_file_memory_viewer_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        import importlib.util
        from ultimate_ai_agent.api.app import app

        required_files = [
            "apps/control-center/src/components/EvidenceFileMemoryViewerPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "scripts/verify_control_center_frontend.py",
            "docs/control_center/EVIDENCE_VIEWER.md",
            "docs/control_center/FILE_REFERENCE_VIEWER.md",
            "docs/control_center/MEMORY_VIEWER.md",
            "docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md",
        ]
        implementation_files = [
            "apps/control-center/src/components/EvidenceFileMemoryViewerPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        failures = [f"missing M17 evidence/file/memory file: {path}" for path in required_files if not (self.root / path).exists()]
        components = "\n".join(self._read(self.root / path) for path in implementation_files if (self.root / path).exists())
        lowered = components.lower().replace(" ", "")

        required_fragments = [
            "EvidenceViewerPanel",
            "FileReferenceViewerPanel",
            "MemoryViewerPanel",
            'path: "/evidence"',
            'path: "/files"',
            'path: "/memory"',
            "Evidence Viewer",
            "File Reference Viewer",
            "Memory Viewer",
            "M17 knowledge surface",
            "Evidence views are read-only",
            "File ref views are read-only",
            "Memory is recall, not authority",
            "Canonical files and governed source systems outrank memory",
            "mock_evidence_ref_001",
            "mock_file_ref_001",
            "mock_memory_ref_001",
            "redacted_summary_only",
            "NO_RAW_CONTENT",
            "MEMORY_NOT_AUTHORITY",
            "No filesystem browsing is available",
            "File writes are not available from this UI",
            "Memory detail is redacted summary metadata only",
            "Evidence detail is redacted summary metadata only",
            "File ref detail is redacted summary metadata only",
        ]
        failures.extend(f"M17 UI missing required fragment: {fragment}" for fragment in required_fragments if fragment not in components)

        forbidden_fragments = [
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
            "<button>editmemory</button>",
            "<button>deletememory</button>",
            "<button>savememory</button>",
            "<button>learnthis</button>",
            "<button>forgetthis</button>",
            "<button>openfile</button>",
            "<button>deletefile</button>",
            "<button>writefile</button>",
            "<button>browsefilesystem</button>",
            "<button>revealraw</button>",
            "<button>showraw</button>",
            "<button>execute</button>",
            "<button>run</button>",
            "localstorage",
            "sessionstorage",
            "document.cookie",
            'type="password"',
            'name="apikey"',
            'name="token"',
            "rawpromptbody",
            "rawfilecontent",
            "rawmemorycontent",
            "rawevidencepayload",
            "rawproviderpayload",
            "authoritativetruth",
            "credentialref",
            "credentialhandle",
            "/users/",
            "/home/",
        ]
        failures.extend(f"M17 UI contains forbidden fragment: {fragment}" for fragment in forbidden_fragments if fragment in lowered)

        docs_text = "\n".join(self._read(self.root / path) for path in required_files if path.startswith("docs/"))
        doc_fragments = [
            "read-only",
            "summary-only",
            "redacted",
            "safe refs",
            "No backend route is added",
            "memory is recall, not authority",
            "canonical files and governed source systems outrank memory",
            "no raw prompts",
            "no raw secrets",
            "no raw file contents",
            "no raw memory contents",
            "no raw evidence payloads",
            "no raw credentials",
            "no raw provider payloads",
            "no file mutation",
            "no memory mutation",
            "no filesystem browsing",
            "no execution controls",
        ]
        failures.extend(f"M17 docs missing required fragment: {fragment}" for fragment in doc_fragments if fragment not in docs_text)

        try:
            openapi_paths = app.openapi().get("paths", {})
        except Exception as exc:
            failures.append(f"M17 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m17_openapi_route_failures(openapi_paths))

        script = self.root / "scripts/verify_control_center_frontend.py"
        if script.exists():
            spec = importlib.util.spec_from_file_location("verify_control_center_frontend", script)
            if spec is None or spec.loader is None:
                failures.append("could not load frontend safety verifier")
            else:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                failures.extend(module.verify(self.root))

        return self._result(criterion, failures, required_files)

    def check_m17_evidence_file_memory_viewer_hardening_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util
        from ultimate_ai_agent.api.app import app

        required_files = [
            "apps/control-center/src/App.test.tsx",
            "apps/control-center/src/components/EvidenceFileMemoryViewerPanel.tsx",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "scripts/verify_control_center_frontend.py",
            "tests/test_control_center_frontend_safety_verifier.py",
            "docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_21_1.md",
            "docs/release_notes/v0_21_1.md",
        ]
        failures = [
            f"missing M17 hardening file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        mock_text = self._read(self.root / "apps/control-center/src/mocks/controlCenterData.ts")
        panel_text = self._read(self.root / "apps/control-center/src/components/EvidenceFileMemoryViewerPanel.tsx")
        test_text = self._read(self.root / "apps/control-center/src/App.test.tsx")
        verifier_text = self._read(self.root / "scripts/verify_control_center_frontend.py")
        docs_text = "\n".join(
            self._read(self.root / path)
            for path in [
                "docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md",
                "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md",
                "docs/implementation/foundation_gate_implementation_plan_v0_21_1.md",
                "docs/release_notes/v0_21_1.md",
            ]
        )

        mock_fragments = [
            "mock_evidence_ref_002",
            "mock_file_ref_002",
            "mock_memory_ref_002",
            "memory_conflict_review_summary",
            "redacted-evidence-summary.json",
            "receipt_context",
            "redacted_summary_only",
            "MOCK_DATA_ONLY",
            "NO_RAW_CONTENT",
            "MEMORY_NOT_AUTHORITY",
        ]
        failures.extend(
            f"M17 hardening mock fixture missing fragment: {fragment}"
            for fragment in mock_fragments
            if fragment not in mock_text
        )

        selected_state_fragments = [
            "aria-current={selected ? \"true\" : undefined}",
            "evidence summary",
            "file ref summary",
            "memory summary",
        ]
        failures.extend(
            f"M17 hardening selected-state UI missing fragment: {fragment}"
            for fragment in selected_state_fragments
            if fragment not in panel_text
        )

        test_fragments = [
            "keeps alternate M17 metadata selection read-only and redacted",
            "mock_evidence_ref_002",
            "mock_file_ref_002",
            "mock_memory_ref_002",
            "aria-current",
            "redacted_summary_only",
        ]
        failures.extend(
            f"M17 hardening frontend test missing fragment: {fragment}"
            for fragment in test_fragments
            if fragment not in test_text
        )

        verifier_fragments = [
            "M17_HARDENING_MOCK_MARKERS",
            "M17_HARDENING_SELECTED_STATE_MARKERS",
            "M17 hardening mock marker missing",
            "M17 hardening selected-state marker missing",
        ]
        failures.extend(
            f"M17 hardening verifier missing fragment: {fragment}"
            for fragment in verifier_fragments
            if fragment not in verifier_text
        )

        doc_fragments = [
            "v0.21.1",
            "hardening",
            "read-only",
            "redacted summary-only",
            "visibly mock",
            "non-authoritative",
            "OpenAPI path count remains `74`",
            "no backend API route",
            "no raw file",
            "no raw memory",
            "no raw evidence",
            "no file mutation",
            "no memory mutation",
            "browser smoke",
        ]
        failures.extend(
            f"M17 hardening docs missing fragment: {fragment}"
            for fragment in doc_fragments
            if fragment not in docs_text
        )

        forbidden_fragments = [
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
            "rawEvidencePayload",
            "rawFileContent",
            "rawMemoryContent",
            "credentialRef",
            "/Users/",
            "/home/",
        ]
        combined = "\n".join([mock_text, panel_text])
        failures.extend(
            f"M17 hardening implementation contains forbidden fragment: {fragment}"
            for fragment in forbidden_fragments
            if fragment in combined
        )

        try:
            openapi_paths = app.openapi().get("paths", {})
        except Exception as exc:
            failures.append(f"M17 hardening OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m17_openapi_route_failures(openapi_paths))

        script = self.root / "scripts/verify_control_center_frontend.py"
        if script.exists():
            spec = importlib.util.spec_from_file_location("verify_control_center_frontend", script)
            if spec is None or spec.loader is None:
                failures.append("could not load frontend safety verifier")
            else:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                failures.extend(module.verify(self.root))

        return self._result(criterion, failures, required_files)

    def check_m18_local_runtime_manual_smoke_surface_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util
        from ultimate_ai_agent.api.app import app

        required_files = [
            "apps/control-center/src/App.test.tsx",
            "apps/control-center/src/components/LocalRuntimeStatusPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/endpoints.ts",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "scripts/verify_control_center_frontend.py",
            "tests/test_control_center_frontend_safety_verifier.py",
            "docs/control_center/LOCAL_RUNTIME_STATUS_UI.md",
            "docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md",
            "docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_22_0.md",
            "docs/release_notes/v0_22_0.md",
        ]
        failures = [
            f"missing M18 local runtime/manual smoke file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        implementation_files = [
            "apps/control-center/src/App.test.tsx",
            "apps/control-center/src/components/LocalRuntimeStatusPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/endpoints.ts",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        runtime_implementation_files = [
            "apps/control-center/src/components/LocalRuntimeStatusPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/endpoints.ts",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        implementation_text = "\n".join(
            self._read(self.root / path) for path in implementation_files if (self.root / path).exists()
        )
        runtime_implementation_text = "\n".join(
            self._read(self.root / path) for path in runtime_implementation_files if (self.root / path).exists()
        )
        lowered = runtime_implementation_text.lower().replace(" ", "")

        required_fragments = [
            "LocalRuntimeStatusPanel",
            "ManualSmokeControlSurfacePanel",
            'path: "/runtime/local"',
            'path: "/runtime/manual-smoke"',
            'runtimeSmokeReportValidate: "/runtime/smoke-reports/validate"',
            "isRuntimeValidationEndpoint",
            "M18 local runtime surface",
            "Local runtime status is read-only",
            "No local runtime is started, stopped, connected, or executed from this UI",
            "Manual smoke reports are safe summaries",
            "Manual smoke execution remains CLI-only, fixed-prompt-only, approval-gated",
            "m18Runtime",
            "mock_manual_smoke_report_ref_001",
            "runtime_readiness_report",
            "manual_loopback_smoke",
            "fixed_prompt_hash_mock_001",
            "responsePreviewShown: false",
            "modelOutputAuthoritative: false",
            "NO_RUNTIME_EXECUTION",
            "VALIDATION_ONLY",
            "redacted_summary_only",
        ]
        failures.extend(f"M18 UI missing required fragment: {fragment}" for fragment in required_fragments if fragment not in implementation_text)

        forbidden_fragments = [
            "/runtime/smoke-reports/execute",
            "/runtime/local/execute",
            "/runtime/local/run",
            "/runtime/local/start",
            "/runtime/local/stop",
            "/runtime/local/connect",
            "/runtime/manual-smoke/execute",
            "/runtime/manual-smoke/run",
            "/model-runtime/local/smoke/execute",
            "<button>execute</button>",
            "<button>run</button>",
            "<button>runsmoke</button>",
            "<button>executesmoke</button>",
            "<button>startruntime</button>",
            "<button>stopruntime</button>",
            "<button>connectruntime</button>",
            "<button>callmodel</button>",
            "localstorage",
            "sessionstorage",
            "document.cookie",
            'type="password"',
            'name="apikey"',
            'name="token"',
            "rawpromptbody",
            "rawresponsebody",
            "rawtranscript",
            "rawproviderpayload",
            "credentialref",
            "credentialhandle",
            "apikey",
            "authtoken",
        ]
        failures.extend(f"M18 implementation contains forbidden fragment: {fragment}" for fragment in forbidden_fragments if fragment in lowered)

        docs_text = "\n".join(
            self._read(self.root / path)
            for path in [
                "docs/control_center/LOCAL_RUNTIME_STATUS_UI.md",
                "docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md",
                "docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md",
                "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
                "docs/control_center/FRONTEND_SAFETY_POLICY.md",
                "docs/implementation/foundation_gate_implementation_plan_v0_22_0.md",
                "docs/release_notes/v0_22_0.md",
            ]
        )
        doc_fragments = [
            "v0.22.0",
            "M18",
            "read-only",
            "validation-only",
            "No backend route is added",
            "OpenAPI path count remains `74`",
            "no runtime execution",
            "no model/provider calls",
            "no manual smoke execution",
            "no raw smoke report",
            "no raw prompts",
            "no raw response bodies",
            "no credentials",
            "visibly mock",
            "non-authoritative",
        ]
        failures.extend(f"M18 docs missing required fragment: {fragment}" for fragment in doc_fragments if fragment not in docs_text)

        try:
            openapi_paths = app.openapi().get("paths", {})
        except Exception as exc:
            failures.append(f"M18 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m18_openapi_route_failures(openapi_paths))

        script = self.root / "scripts/verify_control_center_frontend.py"
        if script.exists():
            spec = importlib.util.spec_from_file_location("verify_control_center_frontend", script)
            if spec is None or spec.loader is None:
                failures.append("could not load frontend safety verifier")
            else:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                failures.extend(module.verify(self.root))

        return self._result(criterion, failures, required_files)

    def check_m19_mobile_companion_contract_planning_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.mobile_companion import (
            MobileCapabilityKind,
            MobileCapabilityStatus,
            build_default_mobile_companion_manifest,
            build_default_mobile_permission_manifest,
        )
        from ultimate_ai_agent.core.mobile_companion.planning import (
            assert_mobile_contract_only,
        )

        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/permissions.py",
            "src/ultimate_ai_agent/core/mobile_companion/receipts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "tests/test_mobile_companion_contracts.py",
            "tests/test_mobile_companion_permissions.py",
            "tests/test_mobile_companion_no_sensor_access.py",
            "tests/test_mobile_companion_no_authority.py",
            "tests/test_m19_gate_integration.py",
            "docs/mobile/MOBILE_COMPANION_CONTRACT.md",
            "docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md",
            "docs/mobile/MOBILE_API_PLANNING.md",
            "docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md",
            "docs/mobile/MOBILE_SENSOR_BOUNDARY.md",
            "docs/mobile/MOBILE_SECURITY_MODEL.md",
            "docs/mobile/MOBILE_CAPTURE_POLICY.md",
            "docs/mobile/CCC_IOS_ANDROID_STRATEGY.md",
            "docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md",
            "docs/mobile/MOBILE_COMPANION_NON_GOALS.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_23_1.md",
            "docs/release_notes/v0_23_1.md",
        ]
        failures = [
            f"missing M19 mobile companion contract/planning file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            manifest = build_default_mobile_companion_manifest()
            permission_manifest = build_default_mobile_permission_manifest()
            assert_mobile_contract_only(manifest)
            if not manifest.contract_only:
                failures.append("default mobile companion manifest is not contract-only")
            if manifest.mobile_client_is_authority:
                failures.append("default mobile companion manifest claims mobile authority")
            if manifest.sensor_access_enabled:
                failures.append("default mobile companion manifest enables sensor access")
            if manifest.mobile_approval_execution_implemented:
                failures.append("default manifest enables mobile approval execution")
            if not manifest.device_capability_broker_required:
                failures.append("default manifest does not require Device Capability Broker")
            if not permission_manifest.contract_only:
                failures.append("default mobile permission manifest is not contract-only")
            if permission_manifest.os_permission_integration_implemented:
                failures.append("default permission manifest enables OS permissions")
            capabilities_by_kind = {
                capability.capability: capability
                for capability in manifest.capabilities
            }
            for capability_kind in [
                MobileCapabilityKind.contacts_planned,
                MobileCapabilityKind.calendar_planned,
            ]:
                capability = capabilities_by_kind.get(capability_kind)
                if capability is None:
                    failures.append(f"default manifest missing {capability_kind.value}")
                    continue
                if capability.status != MobileCapabilityStatus.future_requires_device_capability_broker:
                    failures.append(f"{capability_kind.value} must remain future-broker-only")
                if capability.allowed_now:
                    failures.append(f"{capability_kind.value} is enabled")
                if capability.os_permission_integrated:
                    failures.append(f"{capability_kind.value} integrates OS permissions")
                if capability.background_service_enabled:
                    failures.append(f"{capability_kind.value} enables background services")
                if not capability.requires_device_capability_broker:
                    failures.append(f"{capability_kind.value} must require Device Capability Broker")
        except Exception as exc:
            failures.append(f"M19 mobile companion default contract failed validation: {exc}")

        try:
            openapi_paths = app.openapi().get("paths", {})
        except Exception as exc:
            failures.append(f"M19 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m19_openapi_route_failures(openapi_paths))

        forbidden_dirs = [
            "ios",
            "android",
            "mobile-app",
            "react-native",
            "expo",
            "flutter",
            "capacitor",
            "ionic",
            "src/ultimate_ai_agent/core/device_capability_broker",
        ]
        for rel_path in forbidden_dirs:
            if (self.root / rel_path).exists():
                failures.append(f"M19 forbidden native/mobile implementation directory exists: {rel_path}")

        forbidden_files = [
            "build.gradle",
            "settings.gradle",
            "gradlew",
            "AndroidManifest.xml",
            "Info.plist",
            "Package.swift",
            "Podfile",
            "pubspec.yaml",
            "app.json",
            "app.config.js",
            "capacitor.config.ts",
            "ionic.config.json",
        ]
        for file_name in forbidden_files:
            for rel in [
                file_name,
                f"apps/{file_name}",
                f"apps/control-center/{file_name}",
                f"src/{file_name}",
            ]:
                if (self.root / rel).exists():
                    failures.append(f"M19 forbidden native/mobile implementation file exists: {rel}")

        scan_roots = ["src", "apps", "scripts", "tests"]
        forbidden_fragments = [
            "navigator.geolocation",
            "navigator.mediaDevices",
            "Notification.requestPermission",
            "PushManager",
            "android.permission",
            "Manifest.permission",
            "CLLocation",
            "AVCapture",
            "LocationManager",
            "CameraManager",
        ]
        for rel_root in scan_roots:
            root = self.root / rel_root
            if not root.exists():
                continue
            candidate_files = []
            if rel_root in {"src", "scripts", "tests"}:
                candidate_files.extend(root.rglob("*.py"))
            if rel_root == "apps":
                candidate_files.extend(root.rglob("*.ts"))
                candidate_files.extend(root.rglob("*.tsx"))
                candidate_files.extend(root.rglob("*.js"))
                candidate_files.extend(root.rglob("*.jsx"))
            for path in candidate_files:
                rel = path.relative_to(self.root).as_posix()
                if not path.is_file() or "__pycache__" in rel or "node_modules/" in rel:
                    continue
                if rel in {
                    "src/ultimate_ai_agent/core/gate/evaluators.py",
                    "scripts/verify_all.py",
                    "scripts/verify_control_center_frontend.py",
                    "tests/test_control_center_frontend_safety_verifier.py",
                }:
                    continue
                text = self._read(path)
                for fragment in forbidden_fragments:
                    if fragment in text:
                        failures.append(f"M19 forbidden mobile sensor fragment in {rel}: {fragment}")

        return self._result(criterion, failures, required_files)

    def check_m20_device_capability_broker_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.device_capabilities import (
            DeviceCapabilityKind,
            DeviceCapabilityStatus,
            build_default_device_capability_manifest,
        )
        from ultimate_ai_agent.core.device_capabilities.validation import (
            assert_device_contract_only,
        )

        required_files = [
            "src/ultimate_ai_agent/core/device_capabilities/__init__.py",
            "src/ultimate_ai_agent/core/device_capabilities/enums.py",
            "src/ultimate_ai_agent/core/device_capabilities/contracts.py",
            "src/ultimate_ai_agent/core/device_capabilities/manifests.py",
            "src/ultimate_ai_agent/core/device_capabilities/validation.py",
            "src/ultimate_ai_agent/core/device_capabilities/policy.py",
            "src/ultimate_ai_agent/core/device_capabilities/receipts.py",
            "tests/test_device_capability_contracts.py",
            "tests/test_device_capability_manifest.py",
            "tests/test_device_capability_validation.py",
            "tests/test_device_capability_no_sensor_access.py",
            "tests/test_device_capability_no_authority.py",
            "tests/test_m20_gate_integration.py",
            "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md",
            "docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md",
            "docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md",
            "docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md",
            "docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md",
            "docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md",
            "docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md",
            "docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md",
            "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_24_0.md",
            "docs/release_notes/v0_24_0.md",
        ]
        failures = [
            f"missing M20 Device Capability Broker contract file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            manifest = build_default_device_capability_manifest()
            assert_device_contract_only(manifest)
            if not manifest.contract_only:
                failures.append("default device capability manifest is not contract-only")
            if manifest.sensor_access_enabled:
                failures.append("default device capability manifest enables sensor access")
            if manifest.os_permission_integration_implemented:
                failures.append("default device capability manifest enables OS permissions")
            if manifest.backend_routes_added:
                failures.append("default device capability manifest adds backend routes")
            if manifest.runtime_broker_implemented:
                failures.append("default device capability manifest implements runtime broker")
            if manifest.native_client_implemented:
                failures.append("default device capability manifest implements native clients")
            if manifest.device_clients_are_authority:
                failures.append("default device capability manifest claims device authority")
            if manifest.device_output_is_trusted_control_input:
                failures.append("default device output is trusted control input")
            if manifest.automatic_memory_write_allowed:
                failures.append("default manifest allows automatic memory write")
            if manifest.external_send_allowed:
                failures.append("default manifest allows external sends")
            if manifest.raw_payload_allowed:
                failures.append("default manifest allows raw payloads")
            capabilities_by_kind = {
                capability.kind: capability
                for capability in manifest.capabilities
            }
            for capability_kind in [
                DeviceCapabilityKind.camera,
                DeviceCapabilityKind.microphone,
                DeviceCapabilityKind.location,
                DeviceCapabilityKind.notifications,
                DeviceCapabilityKind.contacts,
                DeviceCapabilityKind.calendar,
                DeviceCapabilityKind.photos,
                DeviceCapabilityKind.files,
                DeviceCapabilityKind.clipboard,
                DeviceCapabilityKind.bluetooth,
                DeviceCapabilityKind.nfc,
                DeviceCapabilityKind.biometrics,
                DeviceCapabilityKind.local_network,
                DeviceCapabilityKind.motion,
                DeviceCapabilityKind.health,
                DeviceCapabilityKind.screen_capture,
            ]:
                capability = capabilities_by_kind.get(capability_kind)
                if capability is None:
                    failures.append(f"default manifest missing {capability_kind.value}")
                    continue
                if capability.status not in {
                    DeviceCapabilityStatus.planned_disabled,
                    DeviceCapabilityStatus.future_requires_broker,
                    DeviceCapabilityStatus.blocked,
                }:
                    failures.append(f"{capability_kind.value} is not future-broker-only")
                if capability.allowed_now:
                    failures.append(f"{capability_kind.value} is enabled")
                if capability.implemented_now:
                    failures.append(f"{capability_kind.value} is implemented")
                if not capability.requires_device_capability_broker:
                    failures.append(f"{capability_kind.value} must require Device Capability Broker")
            background_service = capabilities_by_kind.get(DeviceCapabilityKind.background_service)
            if background_service is None:
                failures.append("default manifest missing background_service")
            elif background_service.status != DeviceCapabilityStatus.blocked:
                failures.append("background_service must remain blocked")
        except Exception as exc:
            failures.append(f"M20 device capability default contract failed validation: {exc}")

        try:
            openapi_paths = app.openapi().get("paths", {})
        except Exception as exc:
            failures.append(f"M20 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m20_openapi_route_failures(openapi_paths))

        forbidden_dirs = [
            "ios",
            "android",
            "mobile-app",
            "react-native",
            "expo",
            "flutter",
            "capacitor",
            "ionic",
            "src/ultimate_ai_agent/core/device_capability_broker",
        ]
        for rel_path in forbidden_dirs:
            if (self.root / rel_path).exists():
                failures.append(f"M20 forbidden native/mobile implementation directory exists: {rel_path}")

        forbidden_files = [
            "build.gradle",
            "settings.gradle",
            "gradlew",
            "AndroidManifest.xml",
            "Info.plist",
            "Package.swift",
            "Podfile",
            "pubspec.yaml",
            "app.json",
            "app.config.js",
            "capacitor.config.ts",
            "ionic.config.json",
        ]
        for file_name in forbidden_files:
            for rel in [
                file_name,
                f"apps/{file_name}",
                f"apps/control-center/{file_name}",
                f"src/{file_name}",
            ]:
                if (self.root / rel).exists():
                    failures.append(f"M20 forbidden native/mobile implementation file exists: {rel}")

        scan_roots = ["src", "apps", "scripts", "tests"]
        forbidden_fragments = [
            "navigator.geolocation",
            "navigator.mediaDevices",
            "Notification.requestPermission",
            "PushManager",
            "android.permission",
            "Manifest.permission",
            "CLLocation",
            "AVCapture",
            "LocationManager",
            "CameraManager",
            "AudioRecord",
        ]
        for rel_root in scan_roots:
            root = self.root / rel_root
            if not root.exists():
                continue
            candidate_files = []
            if rel_root in {"src", "scripts", "tests"}:
                candidate_files.extend(root.rglob("*.py"))
            if rel_root == "apps":
                candidate_files.extend(root.rglob("*.ts"))
                candidate_files.extend(root.rglob("*.tsx"))
                candidate_files.extend(root.rglob("*.js"))
                candidate_files.extend(root.rglob("*.jsx"))
            for path in candidate_files:
                rel = path.relative_to(self.root).as_posix()
                if not path.is_file() or "__pycache__" in rel or "node_modules/" in rel:
                    continue
                if rel in {
                    "src/ultimate_ai_agent/core/gate/evaluators.py",
                    "scripts/verify_all.py",
                    "scripts/verify_control_center_frontend.py",
                    "tests/test_control_center_frontend_safety_verifier.py",
                }:
                    continue
                text = self._read(path)
                for fragment in forbidden_fragments:
                    if fragment in text:
                        failures.append(f"M20 forbidden device/sensor fragment in {rel}: {fragment}")

        roadmap_text = self._read(self.root / "docs/canonical/09_roadmap.md").lower()
        if "v0.24.0 / m20" not in roadmap_text or "implemented" not in roadmap_text:
            failures.append("canonical roadmap must mark v0.24.0 / M20 implemented")
        if "v0.25.0 / m21" not in roadmap_text or "planned/provisional" not in roadmap_text:
            failures.append("canonical roadmap must keep M21 planned/provisional")

        return self._result(criterion, failures, required_files)

    def check_m21_openwebui_bridge_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.openwebui_bridge import (
            OpenWebUIAuthorityBoundary,
            OpenWebUIBridgeStatus,
            build_default_openwebui_bridge_manifest,
            build_default_openwebui_bridge_plan,
        )
        from ultimate_ai_agent.core.openwebui_bridge.validation import (
            assert_agent_core_authority_boundary,
            assert_no_approval_grant,
            assert_no_memory_write,
            assert_no_provider_call,
            assert_no_raw_content,
            assert_no_runtime_execution,
            assert_no_tool_execution,
            assert_openwebui_contract_only,
        )

        required_files = [
            "src/ultimate_ai_agent/core/openwebui_bridge/__init__.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/enums.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/manifests.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/policy.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/receipts.py",
            "tests/test_openwebui_bridge_contracts.py",
            "tests/test_openwebui_bridge_validation.py",
            "tests/test_openwebui_bridge_no_authority.py",
            "tests/test_openwebui_bridge_no_execution.py",
            "tests/test_openwebui_bridge_no_raw_content.py",
            "tests/test_m21_gate_integration.py",
            "docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md",
            "docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md",
            "docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md",
            "docs/openwebui/OPENWEBUI_SECURITY_MODEL.md",
            "docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md",
            "docs/openwebui/OPENWEBUI_NON_GOALS.md",
            "docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_25_0.md",
            "docs/release_notes/v0_25_0.md",
        ]
        failures = [
            f"missing M21 OpenWebUI bridge contract file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            manifest = build_default_openwebui_bridge_manifest()
            plan = build_default_openwebui_bridge_plan()
            assert_openwebui_contract_only(manifest)
            assert_agent_core_authority_boundary(manifest)
            assert_no_raw_content(manifest)
            assert_no_tool_execution(manifest)
            assert_no_memory_write(manifest)
            assert_no_runtime_execution(manifest)
            assert_no_provider_call(manifest)
            assert_no_approval_grant(manifest)
            if manifest.status != OpenWebUIBridgeStatus.contract_only:
                failures.append("default OpenWebUI manifest is not contract-only")
            if plan.status != OpenWebUIBridgeStatus.planned_disabled:
                failures.append("default OpenWebUI bridge plan is not planned-disabled")
            if not manifest.openwebui_is_preferred_conversational_shell:
                failures.append("OpenWebUI must remain the preferred conversational shell")
            if manifest.openwebui_is_agent_brain:
                failures.append("OpenWebUI must not be the agent brain")
            if not manifest.agent_core_remains_authority:
                failures.append("Agent Core must remain authority")
            for boundary in [
                OpenWebUIAuthorityBoundary.agent_core_authority,
                OpenWebUIAuthorityBoundary.no_direct_tool_execution,
                OpenWebUIAuthorityBoundary.no_direct_memory_write,
                OpenWebUIAuthorityBoundary.no_direct_runtime_execution,
                OpenWebUIAuthorityBoundary.no_direct_provider_call,
            ]:
                if boundary not in manifest.authority_boundaries:
                    failures.append(f"default OpenWebUI manifest missing boundary: {boundary.value}")
            if "M22" not in plan.required_future_milestones:
                failures.append("M22 must remain a future required milestone")
            if "M23" not in plan.required_future_milestones:
                failures.append("M23 must remain a future required milestone")
        except Exception as exc:
            failures.append(f"M21 OpenWebUI bridge default contract failed validation: {exc}")

        try:
            openapi_paths = app.openapi().get("paths", {})
        except Exception as exc:
            failures.append(f"M21 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m21_openapi_route_failures(openapi_paths))

        for rel_path in m21_forbidden_openwebui_config_path_matches(self.root):
            failures.append(f"M21 forbidden OpenWebUI deployment/config path exists: {rel_path}")

        failures.extend(m21_forbidden_openwebui_runtime_fragment_failures(self.root))

        roadmap_text = self._read(self.root / "docs/canonical/09_roadmap.md").lower()
        if "v0.25.0 / m21" not in roadmap_text or "implemented" not in roadmap_text:
            failures.append("canonical roadmap must mark v0.25.0 / M21 implemented")
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple >= (0, 26, 0):
            if "v0.26.0 / m22" not in roadmap_text or "implemented" not in roadmap_text:
                failures.append("canonical roadmap must mark v0.26.0 / M22 implemented")
        elif "v0.26.0 / m22" not in roadmap_text or "planned/provisional" not in roadmap_text:
            failures.append("canonical roadmap must keep M22 planned/provisional")
        if version_tuple >= (0, 27, 0):
            if "v0.27.0 / m23" not in roadmap_text or "implemented" not in roadmap_text:
                failures.append("canonical roadmap must mark v0.27.0 / M23 implemented")
        elif "v0.27.0 / m23" not in roadmap_text or "planned/provisional" not in roadmap_text:
            failures.append("canonical roadmap must keep M23 planned/provisional")

        return self._result(criterion, failures, required_files)

    def check_m22_local_model_runtime_activation_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.model_runtime import (
            LocalModelRuntimeKind,
            LocalModelRuntimeStatus,
            build_default_local_runtime_activation_manifest,
            validate_local_runtime_activation_manifest,
        )

        required_files = [
            "src/ultimate_ai_agent/core/model_runtime/activation.py",
            "src/ultimate_ai_agent/core/model_runtime/provider_profiles.py",
            "src/ultimate_ai_agent/core/model_runtime/endpoint_policy.py",
            "src/ultimate_ai_agent/core/model_runtime/health_plan.py",
            "src/ultimate_ai_agent/core/model_runtime/activation_manifest.py",
            "tests/test_local_runtime_activation_contracts.py",
            "tests/test_local_runtime_provider_profiles.py",
            "tests/test_local_runtime_endpoint_policy.py",
            "tests/test_local_runtime_activation_validation.py",
            "tests/test_local_runtime_health_probe_plan.py",
            "tests/test_local_runtime_no_execution.py",
            "tests/test_m22_gate_integration.py",
            "docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md",
            "docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md",
            "docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md",
            "docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md",
            "docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md",
            "docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md",
            "docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_26_0.md",
            "docs/release_notes/v0_26_0.md",
        ]
        failures = [
            f"missing M22 local runtime activation contract file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            manifest = build_default_local_runtime_activation_manifest()
            validate_local_runtime_activation_manifest(manifest)
            if manifest.status != LocalModelRuntimeStatus.contract_only:
                failures.append("default local runtime activation manifest is not contract-only")
            if manifest.activation_allowed_now:
                failures.append("default local runtime activation manifest allows activation")
            if manifest.real_model_call_allowed:
                failures.append("default local runtime activation manifest allows a real model call")
            if manifest.runtime_execution_allowed:
                failures.append("default local runtime activation manifest allows runtime execution")
            if manifest.provider_call_allowed:
                failures.append("default local runtime activation manifest allows provider call")
            if manifest.endpoint_probe_allowed:
                failures.append("default local runtime activation manifest allows endpoint probe")
            if manifest.user_content_allowed:
                failures.append("default local runtime activation manifest allows user content")
            if manifest.tool_call_allowed:
                failures.append("default local runtime activation manifest allows tool call")
            if manifest.memory_write_allowed:
                failures.append("default local runtime activation manifest allows memory write")
            if manifest.secret_material_allowed:
                failures.append("default local runtime activation manifest allows secret material")
            if not manifest.no_model_called:
                failures.append("default manifest must record no model was called")
            if not manifest.no_runtime_activated:
                failures.append("default manifest must record no runtime was activated")
            if not manifest.no_endpoint_contacted:
                failures.append("default manifest must record no endpoint was contacted")
            kinds = {profile.kind for profile in manifest.provider_profiles}
            expected_kinds = {
                LocalModelRuntimeKind.ollama_planned,
                LocalModelRuntimeKind.llama_cpp_planned,
                LocalModelRuntimeKind.mlx_planned,
                LocalModelRuntimeKind.vllm_planned,
                LocalModelRuntimeKind.lm_studio_planned,
                LocalModelRuntimeKind.openai_compatible_local_planned,
                LocalModelRuntimeKind.generic_loopback_http_planned,
            }
            if kinds != expected_kinds:
                failures.append("default local runtime activation manifest missing provider profiles")
        except Exception as exc:
            failures.append(f"M22 local runtime activation default contract failed validation: {exc}")

        try:
            openapi_paths = app.openapi().get("paths", {})
        except Exception as exc:
            failures.append(f"M22 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m22_openapi_route_failures(openapi_paths))

        failures.extend(m22_local_runtime_forbidden_fragment_failures(self.root))

        roadmap_text = self._read(self.root / "docs/canonical/09_roadmap.md").lower()
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if "v0.26.0 / m22" not in roadmap_text or "implemented" not in roadmap_text:
            failures.append("canonical roadmap must mark v0.26.0 / M22 implemented")
        if version_tuple >= (0, 27, 0):
            if "v0.27.0 / m23" not in roadmap_text or "implemented" not in roadmap_text:
                failures.append("canonical roadmap must mark v0.27.0 / M23 implemented")
        elif "v0.27.0 / m23" not in roadmap_text or "planned/provisional" not in roadmap_text:
            failures.append("canonical roadmap must keep M23 planned/provisional")

        return self._result(criterion, failures, required_files)

    def check_m23_first_local_llm_call_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/model_runtime/local_call_contracts.py",
            "src/ultimate_ai_agent/core/model_runtime/local_call_policy.py",
            "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py",
            "src/ultimate_ai_agent/core/model_runtime/local_call.py",
            "scripts/manual_local_model_call.py",
            "tests/test_m23_local_model_call_contracts.py",
            "tests/test_m23_local_model_endpoint_policy.py",
            "tests/test_m23_local_model_fake_transport.py",
            "tests/test_m23_manual_cli_dry_run.py",
            "docs/runtime/FIRST_LOCAL_LLM_CALL.md",
            "docs/runtime/M23_FIXED_PROMPT_POLICY.md",
            "docs/runtime/M23_LOCAL_MODEL_CALL_SAFETY.md",
            "docs/runtime/M23_LOCAL_MODEL_CALL_RECEIPTS.md",
            "docs/runtime/M23_NON_AUTHORITATIVE_OUTPUT_POLICY.md",
            "docs/runtime/M23_MANUAL_CLI_USAGE.md",
            "docs/runtime/M23_TO_M24_BOUNDARY.md",
        ]
        failures = [
            f"missing M23 local model call file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            from ultimate_ai_agent.api.app import app
            from ultimate_ai_agent.core.approvals import (
                ApprovalDecisionStatus,
                ApprovalValidationDecision,
                LocalApprovalAuthority,
            )
            from ultimate_ai_agent.core.model_runtime import (
                M23_FIXED_LOCAL_MODEL_PROMPT_ID,
                FakeLocalModelCallTransport,
                LocalModelCallRequest,
                LocalModelRuntimeKind,
                build_dry_run_local_model_call_result,
                build_m23_fixed_prompt,
                local_model_call_approval_request,
                run_local_model_call,
                validate_fixed_prompt,
                validate_local_model_endpoint,
                validate_local_model_call_request,
            )

            prompt = validate_fixed_prompt(build_m23_fixed_prompt())
            if prompt.prompt_id != M23_FIXED_LOCAL_MODEL_PROMPT_ID:
                failures.append("M23 fixed prompt id is not allowlisted")
            request = LocalModelCallRequest(
                request_id="m23_gate_req",
                run_id="run_m23_gate",
                runtime_kind=LocalModelRuntimeKind.ollama_planned,
                endpoint_url="".join(["http", "://127.0.0.1:11434"]),
                safe_endpoint_label="loopback gate endpoint",
                model_ref="local_gate_model",
                fixed_prompt_id=prompt.prompt_id,
                prompt_text=prompt.prompt_text,
            )
            validate_local_model_call_request(request)
            try:
                hostile_query_key = "to" + "ken"
                hostile_endpoint = "".join(
                    ["http", "://localhost:11434/api", "/generate?", hostile_query_key, "=abc"]
                )
                validate_local_model_endpoint(hostile_endpoint)
                failures.append("M23 accepted secret-like endpoint query key")
            except ValueError:
                pass
            try:
                validate_local_model_call_request(request.model_copy(update={"safe_endpoint_label": request.endpoint_url}))
                failures.append("M23 safe endpoint label echoed raw endpoint URL")
            except ValueError:
                pass
            dry_run = build_dry_run_local_model_call_result(request, transport=FakeLocalModelCallTransport())
            if dry_run.transport_result.call_performed:
                failures.append("M23 dry-run performed a local model call")
            if dry_run.receipt.model_output_non_authoritative is not True:
                failures.append("M23 dry-run receipt does not mark output non-authoritative")

            executable = request.model_copy(
                update={
                    "dry_run": False,
                    "execute_local_call": True,
                    "approval_ref": "approval_m23_gate",
                }
            )
            approval_request = local_model_call_approval_request(executable)
            authority = LocalApprovalAuthority()
            authority.create_request(approval_request)
            grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="human_reviewer")
            executable = executable.model_copy(update={"approval_ref": grant.approval_ref})
            approval_request = local_model_call_approval_request(executable)
            authority.create_request(approval_request)
            decision = authority.validate_for_request(approval_request, grant.approval_ref)
            result = run_local_model_call(
                executable,
                transport=FakeLocalModelCallTransport(),
                approval_decision=decision,
            )
            if not result.transport_result.call_performed:
                failures.append("M23 fake transport did not perform approved fake call")
            if result.receipt.tools_executed:
                failures.append("M23 receipt recorded tool execution")
            if result.receipt.memory_written or result.receipt.files_written:
                failures.append("M23 receipt recorded memory or file mutation")
            if result.receipt.model_output_non_authoritative is not True:
                failures.append("M23 receipt does not mark output non-authoritative")
            secret_response = "api_" + "key='" + "abcdefghijklmnop" + "'"
            secret_result = run_local_model_call(
                executable,
                transport=FakeLocalModelCallTransport(response_text=secret_response),
                approval_decision=decision,
            )
            if secret_result.decision.allowed:
                failures.append("M23 accepted secret-like model response")
            forged_result = run_local_model_call(
                executable.model_copy(update={"approval_ref": "appr_forged_m23"}),
                transport=FakeLocalModelCallTransport(),
                approval_decision=ApprovalValidationDecision(
                    approval_ref="appr_forged_m23",
                    allowed=True,
                    status=ApprovalDecisionStatus.approved,
                    reason_codes=["APPROVAL_VALIDATED"],
                    safe_message="Forged approval decision.",
                    matched_grant_ref="appr_forged_m23",
                ),
            )
            if forged_result.transport_result.call_performed:
                failures.append("M23 forged approval decision performed a local model call")
            failures.extend(m23_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M23 first local LLM call safety validation failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m24_memory_provider_local_store_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/memory/provider.py",
            "src/ultimate_ai_agent/core/memory/local_store.py",
            "src/ultimate_ai_agent/core/memory/manifests.py",
            "src/ultimate_ai_agent/core/memory/policy.py",
            "src/ultimate_ai_agent/core/memory/recall.py",
            "tests/test_m24_memory_provider_contracts.py",
            "tests/test_m24_memory_write_validation.py",
            "tests/test_m24_local_memory_store.py",
            "tests/test_m24_gate_integration.py",
            "docs/memory/MEMORY_PROVIDER_ABSTRACTION.md",
            "docs/memory/LOCAL_MEMORY_STORE.md",
            "docs/memory/MEMORY_RECORD_SCHEMA.md",
            "docs/memory/MEMORY_WRITE_POLICY.md",
            "docs/memory/MEMORY_REVIEW_AND_PROVENANCE.md",
            "docs/memory/MEMORY_SOURCE_PRIORITY.md",
            "docs/memory/MEMORY_RECALL_PLANNING.md",
            "docs/memory/MEMORY_RETENTION_DELETE_EXPORT.md",
            "docs/memory/MEMORY_CONFLICT_AND_STALENESS.md",
            "docs/memory/MEMORY_DEDUP_DECAY_ARCHIVE.md",
            "docs/memory/MEMORY_SECURITY_MODEL.md",
            "docs/memory/MEMORY_NON_GOALS.md",
            "docs/memory/MEMORYOS_REVIEW_INCORPORATION.md",
            "docs/memory/M24_TO_M25_BOUNDARY.md",
        ]
        failures = [
            f"missing M24 memory provider file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            from ultimate_ai_agent.api.app import app
            from ultimate_ai_agent.core.memory import (
                LocalMemoryStore,
                MemoryAuthorityLevel,
                MemoryDataClassification,
                MemoryLayer,
                MemoryProviderKind,
                MemoryRecordKind,
                MemoryWriteDecisionStatus,
            )
            from ultimate_ai_agent.core.memory.manifests import build_default_memory_provider_manifest
            from ultimate_ai_agent.core.memory.provider import MemoryExportRequest, MemoryWriteRequest
            from ultimate_ai_agent.core.memory.validation import (
                assert_no_background_memory_workers,
                assert_no_context_injection_runtime,
                assert_no_vector_or_embedding_memory,
                validate_memory_provider_manifest,
                validate_memory_write_request,
            )

            manifest = build_default_memory_provider_manifest(baseline_version="0.28.0")
            validate_memory_provider_manifest(manifest)
            assert_no_vector_or_embedding_memory(manifest)
            assert_no_context_injection_runtime(manifest)
            assert_no_background_memory_workers(manifest)
            if manifest.cloud_providers_enabled:
                failures.append("M24 manifest enabled cloud memory providers")
            if manifest.automatic_writes_enabled:
                failures.append("M24 manifest enabled automatic memory writes")

            safe = MemoryWriteRequest(
                request_id="m24_gate_safe",
                provider_ref="local_dev_memory",
                memory_kind=MemoryRecordKind.structured_fact,
                memory_layer=MemoryLayer.record,
                provider_kind=MemoryProviderKind.local_in_memory,
                safe_summary="Reviewed M24 gate memory summary.",
                source_refs=["source:m24:gate"],
                event_refs=["event:m24:gate"],
                receipt_refs=["receipt:m24:gate"],
                user_reviewed=True,
                data_classification=MemoryDataClassification.internal,
            )
            safe_decision = validate_memory_write_request(safe)
            if safe_decision.status != MemoryWriteDecisionStatus.allowed_for_local_store:
                failures.append("M24 reviewed safe write was not allowed for local store")

            blocked_checks = [
                ("automatic_write", "automatic memory write"),
                ("model_output_source", "model-output memory write"),
                ("local_llm_output_source", "local LLM output memory write"),
                ("openwebui_source", "OpenWebUI memory write"),
                ("mobile_capture_source", "mobile capture memory write"),
                ("tool_output_source", "tool output memory write"),
                ("contains_raw_prompt", "raw prompt memory write"),
                ("contains_raw_model_output", "raw model output memory write"),
                ("contains_raw_file_content", "raw file content memory write"),
                ("contains_raw_transcript", "raw transcript memory write"),
            ]
            for field, label in blocked_checks:
                if field not in MemoryWriteRequest.model_fields:
                    failures.append(f"M24 missing required guard field for {label}: {field}")
                    continue
                decision = validate_memory_write_request(safe.model_copy(update={field: True}))
                if decision.allowed:
                    failures.append(f"M24 allowed blocked {label}")

            store = LocalMemoryStore()
            write = store.put_record(safe)
            if not write.allowed or not write.memory_id:
                failures.append("M24 local store did not retain reviewed safe memory")
            else:
                record = store.get_record(write.memory_id)
                if record is None:
                    failures.append("M24 local store could not read retained memory")
                elif record.authority_level != MemoryAuthorityLevel.recall_only:
                    failures.append("M24 memory record was not recall-only")

            raw_export = store.export_records(
                MemoryExportRequest(
                    request_id="m24_gate_export_raw",
                    provider_ref="local_dev_memory",
                    include_raw_content=True,
                    redacted_only=False,
                )
            )
            if raw_export.allowed:
                failures.append("M24 allowed raw memory export")

            failures.extend(m24_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M24 memory provider local store validation failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m25_truth_source_router_contracts_valid(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/truth/enums.py",
            "src/ultimate_ai_agent/core/truth/sources.py",
            "src/ultimate_ai_agent/core/truth/claims.py",
            "src/ultimate_ai_agent/core/truth/evidence.py",
            "src/ultimate_ai_agent/core/truth/verification.py",
            "src/ultimate_ai_agent/core/truth/manifests.py",
            "tests/test_truth_source_contracts.py",
            "tests/test_claim_verification_decisions.py",
            "tests/test_truth_no_memory_authority.py",
            "tests/test_truth_no_model_output_authority.py",
        ]
        failures = [f"missing M25 truth/evidence file: {path}" for path in required_files if not (self.root / path).exists()]

        try:
            from ultimate_ai_agent.core.truth import (
                Claim,
                ClaimRiskLevel,
                ClaimStatus,
                EvidenceChain,
                EvidenceRef,
                EvidenceStrength,
                TruthSourceKind,
                VerificationDecisionStatus,
                VerificationRequest,
                assert_memory_not_truth,
                assert_model_output_not_truth,
                build_truth_router_manifest,
                verify_claim_against_evidence_chain,
            )

            manifest = build_truth_router_manifest("0.29.0")
            if manifest.external_verification_enabled:
                failures.append("M25 manifest enables external verification")
            if manifest.web_search_enabled:
                failures.append("M25 manifest enables web search")
            if manifest.model_verification_enabled:
                failures.append("M25 manifest enables model verification")
            if manifest.memory_as_authority_enabled:
                failures.append("M25 manifest enables memory authority")
            if manifest.automatic_claim_verification_enabled:
                failures.append("M25 manifest enables automatic claim verification")

            claim = Claim(
                claim_id="claim:m25-gate",
                safe_claim_summary="M25 safe gate claim.",
                claim_text_hash="sha256:m25",
                claim_status=ClaimStatus.unverified,
                claim_risk=ClaimRiskLevel.low,
                data_classification="public",
            )
            safe_chain = EvidenceChain(
                chain_id="chain:m25-gate",
                claim_ref="claim:m25-gate",
                source_refs=["canonical:m25"],
                evidence_refs=["evidence:m25"],
                evidence_strength=EvidenceStrength.evidence_supported,
                source_priority_summary="canonical source",
                safe_summary="Safe canonical evidence summary.",
            )
            safe_request = VerificationRequest(
                request_id="verify:m25-gate",
                claim=claim,
                evidence_chain=safe_chain,
                evidence_refs=[
                    EvidenceRef(
                        evidence_ref="evidence:m25",
                        source_ref="canonical:m25",
                        source_kind=TruthSourceKind.canonical_document,
                        evidence_strength=EvidenceStrength.evidence_supported,
                        data_classification="public",
                        redaction_status="redacted",
                        safe_summary="Safe canonical evidence summary.",
                    )
                ],
                requested_status=ClaimStatus.verified_by_primary_source,
            )
            safe_decision = verify_claim_against_evidence_chain(safe_request)
            if not safe_decision.allowed or safe_decision.status != VerificationDecisionStatus.allowed:
                failures.append("M25 primary-source-backed evidence was not allowed")

            memory_chain = safe_chain.model_copy(
                update={
                    "chain_id": "chain:m25-memory",
                    "source_refs": ["memory:m25"],
                    "evidence_refs": ["evidence:m25-memory"],
                    "memory_refs": ["memory:m25"],
                    "source_priority_summary": "memory only",
                }
            )
            memory_request = safe_request.model_copy(
                update={
                    "request_id": "verify:m25-memory",
                    "evidence_chain": memory_chain,
                    "evidence_refs": [
                        EvidenceRef(
                            evidence_ref="evidence:m25-memory",
                            source_ref="memory:m25",
                            source_kind=TruthSourceKind.reviewed_memory,
                            evidence_strength=EvidenceStrength.source_linked,
                            data_classification="public",
                            redaction_status="redacted",
                            safe_summary="Safe memory summary.",
                        )
                    ],
                }
            )
            memory_decision = verify_claim_against_evidence_chain(memory_request)
            if memory_decision.allowed:
                failures.append("M25 allowed memory-only verification")
            try:
                assert_memory_not_truth(memory_chain)
                failures.append("M25 memory assertion helper did not reject memory refs")
            except ValueError:
                pass

            model_chain = safe_chain.model_copy(
                update={
                    "chain_id": "chain:m25-model",
                    "source_refs": ["model:m25"],
                    "evidence_refs": ["evidence:m25-model"],
                    "evidence_strength": EvidenceStrength.blocked,
                    "source_priority_summary": "blocked model output",
                }
            )
            model_request = safe_request.model_copy(
                update={
                    "request_id": "verify:m25-model",
                    "evidence_chain": model_chain,
                    "evidence_refs": [
                        EvidenceRef(
                            evidence_ref="evidence:m25-model",
                            source_ref="model:m25",
                            source_kind=TruthSourceKind.model_output,
                            evidence_strength=EvidenceStrength.blocked,
                            data_classification="public",
                            redaction_status="redacted",
                            safe_summary="Blocked model output summary.",
                        )
                    ],
                }
            )
            model_decision = verify_claim_against_evidence_chain(model_request)
            if model_decision.allowed:
                failures.append("M25 allowed model-output verification")
            try:
                assert_model_output_not_truth(model_chain)
                failures.append("M25 model-output assertion helper did not reject model refs")
            except ValueError:
                pass

            unknown_chain = safe_chain.model_copy(
                update={
                    "chain_id": "chain:m25-unknown",
                    "source_refs": ["random:m25"],
                    "evidence_refs": ["evidence:m25-unknown"],
                    "source_priority_summary": "unknown source",
                }
            )
            unknown_request = safe_request.model_copy(
                update={
                    "request_id": "verify:m25-unknown",
                    "evidence_chain": unknown_chain,
                    "evidence_refs": [],
                    "requested_status": ClaimStatus.evidence_supported,
                }
            )
            unknown_decision = verify_claim_against_evidence_chain(unknown_request)
            if unknown_decision.allowed or "ARBITRARY_SOURCE_REF_DENIED" not in unknown_decision.reason_codes:
                failures.append("M25 allowed inferred unknown/arbitrary truth refs")

            explicit_unknown_request = safe_request.model_copy(
                update={
                    "request_id": "verify:m25-explicit-unknown",
                    "evidence_chain": unknown_chain,
                    "evidence_refs": [
                        EvidenceRef(
                            evidence_ref="evidence:m25-unknown",
                            source_ref="unknown:m25",
                            source_kind=TruthSourceKind.unknown,
                            evidence_strength=EvidenceStrength.evidence_supported,
                            data_classification="public",
                            redaction_status="redacted",
                            safe_summary="Unknown source kind summary.",
                        )
                    ],
                    "requested_status": ClaimStatus.evidence_supported,
                }
            )
            explicit_unknown_decision = verify_claim_against_evidence_chain(explicit_unknown_request)
            if explicit_unknown_decision.allowed or "UNKNOWN_SOURCE_KIND_DENIED" not in explicit_unknown_decision.reason_codes:
                failures.append("M25 allowed explicit unknown truth source kind")

            unknown_primary_request = unknown_request.model_copy(
                update={
                    "request_id": "verify:m25-unknown-primary",
                    "requested_status": ClaimStatus.verified_by_primary_source,
                }
            )
            unknown_primary_decision = verify_claim_against_evidence_chain(unknown_primary_request)
            if unknown_primary_decision.allowed or "PRIMARY_SOURCE_EVIDENCE_REQUIRED" not in unknown_primary_decision.reason_codes:
                failures.append("M25 allowed unknown refs to verify primary-source truth")

            try:
                EvidenceChain(
                    chain_id="chain:m25-self",
                    claim_ref="claim:m25-gate",
                    source_refs=["claim:m25-gate"],
                    evidence_refs=["evidence:m25-self"],
                    evidence_strength=EvidenceStrength.evidence_supported,
                    source_priority_summary="self source",
                    safe_summary="Self-verifying source.",
                )
                failures.append("M25 allowed claim self-verification")
            except (ValueError, ValidationError):
                pass

            truth_source = "\n".join(
                self._read(path)
                for path in (self.root / "src" / "ultimate_ai_agent" / "core" / "truth").glob("*.py")
            )
            forbidden_fragments = (
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "openai.",
                "anthropic.",
                "ollama.",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
            )
            failures.extend(
                f"M25 truth module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in truth_source
            )
        except Exception as exc:
            failures.append(f"M25 truth/evidence contract validation failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m25_truth_openapi_routes_unchanged(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m25_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M25 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m26_grounded_recall_context_pack_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/recall/__init__.py",
            "src/ultimate_ai_agent/core/recall/enums.py",
            "src/ultimate_ai_agent/core/recall/candidates.py",
            "src/ultimate_ai_agent/core/recall/router.py",
            "src/ultimate_ai_agent/core/recall/context_pack.py",
            "src/ultimate_ai_agent/core/recall/manifests.py",
            "src/ultimate_ai_agent/core/recall/policy.py",
            "src/ultimate_ai_agent/core/recall/validation.py",
            "tests/test_grounded_recall_contracts.py",
            "tests/test_grounded_recall_router.py",
            "tests/test_context_pack_builder.py",
            "tests/test_context_pack_no_injection.py",
            "tests/test_recall_source_priority.py",
            "tests/test_recall_no_raw_content.py",
            "tests/test_recall_no_vector_embeddings.py",
            "tests/test_recall_no_memory_writes.py",
            "tests/test_m26_gate_integration.py",
            "docs/recall/GROUNDED_RECALL_ROUTER.md",
            "docs/recall/CONTEXT_PACK_BUILDER.md",
            "docs/recall/RECALL_SOURCE_PRIORITY.md",
            "docs/recall/RECALL_CANDIDATE_POLICY.md",
            "docs/recall/CONTEXT_PACK_SAFETY.md",
            "docs/recall/RECALL_NON_GOALS.md",
            "docs/recall/M26_TO_M27_BOUNDARY.md",
        ]
        failures = [f"missing M26 recall/context-pack file: {path}" for path in required_files if not (self.root / path).exists()]
        try:
            from ultimate_ai_agent.core.recall import (
                ContextPackBuildRequest,
                GroundedRecallManifest,
                GroundedRecallRequest,
                RecallCandidate,
                RecallCandidateStatus,
                RecallDecisionStatus,
                RecallSourceKind,
                build_evidence_linked_context_pack,
                recall_source_priority_rank,
                route_grounded_recall,
            )

            manifest = GroundedRecallManifest(baseline_version="0.30.1")
            if manifest.context_injection_enabled:
                failures.append("M26 manifest enables context injection")
            if manifest.vector_search_enabled or manifest.embeddings_enabled or manifest.semantic_search_enabled:
                failures.append("M26 manifest enables vector, embedding, or semantic search")
            if manifest.external_retrieval_enabled or manifest.web_search_enabled or manifest.source_crawling_enabled:
                failures.append("M26 manifest enables external retrieval, web search, or source crawling")
            if manifest.automatic_memory_write_enabled:
                failures.append("M26 manifest enables automatic memory writes")
            if manifest.backend_routes_added:
                failures.append("M26 manifest adds backend routes")
            if manifest.model_provider_calls_enabled or manifest.tool_execution_enabled:
                failures.append("M26 manifest enables model/provider calls or tool execution")

            request = GroundedRecallRequest(
                request_id="recall:req:m26-gate",
                query_summary="Need safe M26 context.",
                candidates=[
                    RecallCandidate(
                        candidate_ref="recall:candidate:memory",
                        source_ref="memory:m26",
                        source_kind=RecallSourceKind.reviewed_memory,
                        safe_summary="Reviewed memory reminder.",
                        memory_refs=["memory:m26"],
                        token_estimate=6,
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:canonical",
                        source_ref="canonical:m26",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="Canonical M26 summary.",
                        evidence_refs=["evidence:m26"],
                        token_estimate=5,
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:random",
                        source_ref="random:m26",
                        source_kind=RecallSourceKind.unknown,
                        safe_summary="Unknown source summary.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:model",
                        source_ref="model:m26",
                        source_kind=RecallSourceKind.model_output,
                        safe_summary="Blocked model output summary.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:memory-as-canonical",
                        source_ref="memory:m26",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="Memory source priority upgrade attempt.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:model-as-canonical",
                        source_ref="model:m26",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="Model output source priority upgrade attempt.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:runtime-as-canonical",
                        source_ref="runtime:m26",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="Runtime output source priority upgrade attempt.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:openwebui-as-canonical",
                        source_ref="openwebui:m26",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="OpenWebUI output source priority upgrade attempt.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:memory-as-evidence",
                        source_ref="memory:m26",
                        source_kind=RecallSourceKind.evidence_manifest,
                        safe_summary="Memory evidence priority upgrade attempt.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:stale",
                        source_ref="canonical:stale",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="Stale source summary.",
                        status=RecallCandidateStatus.stale,
                    ),
                ],
                max_context_tokens=100,
            )
            decision = route_grounded_recall(request)
            if decision.status != RecallDecisionStatus.allowed:
                failures.append("M26 grounded recall did not allow safe selected candidates")
            if [item.candidate_ref for item in decision.selected] != [
                "recall:candidate:canonical",
                "recall:candidate:memory",
            ]:
                failures.append("M26 grounded recall did not preserve source priority over memory")
            excluded_reasons = {reason for item in decision.excluded for reason in item.reason_codes}
            for reason in [
                "UNKNOWN_SOURCE_KIND_DENIED",
                "ARBITRARY_SOURCE_REF_DENIED",
                "SOURCE_REF_KIND_MISMATCH_DENIED",
                "MEMORY_SOURCE_PRIORITY_UPGRADE_DENIED",
                "MODEL_OUTPUT_RECALL_DENIED",
                "RUNTIME_OUTPUT_RECALL_DENIED",
                "OPENWEBUI_OUTPUT_RECALL_DENIED",
                "MODEL_OUTPUT_EXCLUDED",
                "RUNTIME_OUTPUT_EXCLUDED",
                "OPENWEBUI_OUTPUT_EXCLUDED",
                "STALE_SOURCE_EXCLUDED",
            ]:
                if reason not in excluded_reasons:
                    failures.append(f"M26 grounded recall missing exclusion reason: {reason}")
            excluded_refs = {item.candidate_ref for item in decision.excluded}
            for candidate_ref in [
                "recall:candidate:memory-as-canonical",
                "recall:candidate:model-as-canonical",
                "recall:candidate:runtime-as-canonical",
                "recall:candidate:openwebui-as-canonical",
                "recall:candidate:memory-as-evidence",
            ]:
                if candidate_ref not in excluded_refs:
                    failures.append(f"M26 grounded recall selected mismatched source identity: {candidate_ref}")
            if not decision.no_memory_write_performed:
                failures.append("M26 grounded recall performed a memory write")
            if not decision.no_external_retrieval_performed:
                failures.append("M26 grounded recall performed external retrieval")
            if not decision.no_vector_search_performed:
                failures.append("M26 grounded recall performed vector search")
            if not decision.no_context_injection_performed:
                failures.append("M26 grounded recall performed context injection")

            pack = build_evidence_linked_context_pack(
                ContextPackBuildRequest(
                    pack_id="ctxpack:m26-gate",
                    request_id="ctxpack:req:m26-gate",
                    recall_decision=decision,
                    max_context_tokens=100,
                )
            )
            if not pack.items or pack.context_injection_performed or pack.raw_content_included:
                failures.append("M26 context pack is empty or includes forbidden runtime/raw behavior")
            pack_refs = {item.candidate_ref for item in pack.items}
            if any(ref.endswith("as-canonical") or ref.endswith("as-evidence") for ref in pack_refs):
                failures.append("M26 context pack included mismatched source identity")
            if pack.memory_write_performed or pack.external_retrieval_performed:
                failures.append("M26 context pack performed memory write or external retrieval")
            if recall_source_priority_rank(RecallSourceKind.canonical_document) >= recall_source_priority_rank(
                RecallSourceKind.reviewed_memory
            ):
                failures.append("M26 source priority lets memory outrank canonical sources")

            recall_source = "\n".join(
                self._read(path)
                for path in (self.root / "src" / "ultimate_ai_agent" / "core" / "recall").glob("*.py")
            ).lower()
            forbidden_fragments = (
                "import chromadb",
                "import faiss",
                "import pgvector",
                "import qdrant",
                "import weaviate",
                "import pinecone",
                "import tokenizers",
                "import tiktoken",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "import " + "openai",
                "import " + "anthropic",
                "import " + "ollama",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
                "localmemorystore",
                "memorywriterequest",
            )
            failures.extend(
                f"M26 recall module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in recall_source
            )
        except Exception as exc:
            failures.append(f"M26 grounded recall/context-pack validation failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m26_recall_openapi_routes_unchanged(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m26_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M26 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m26_m27_remains_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
        ]
        failures = [f"missing M26 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.30.0" in text and "grounded recall router + evidence-linked context pack builder" in text:
            if "implemented/released" not in text:
                failures.append("M26 docs do not mark v0.30.0 implemented/released")
        else:
            failures.append("M26 docs do not mention v0.30.0 Grounded Recall Router + Evidence-Linked Context Pack Builder")
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple >= (0, 32, 0):
            if "v0.32.0" in text and "approval authority v2 + action policy expansion" in text:
                if "implemented/released" not in text:
                    failures.append("M28 docs must mark v0.32.0 implemented/released after M28")
            else:
                failures.append("M28 docs do not mention v0.32.0 Approval Authority v2 + Action Policy Expansion")
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append("M34-M60 must remain planned/provisional after v0.37.4")
            elif "m29-m40 remain planned/provisional" not in text:
                failures.append("M29-M40 must remain planned/provisional after M28")
        elif version_tuple >= (0, 31, 0):
            if "v0.31.0" in text and "tool broker v2 + safe tool intent contracts" in text:
                if "implemented/released" not in text:
                    failures.append("M27 docs must mark v0.31.0 implemented/released after M27")
            else:
                failures.append("M27 docs do not mention v0.31.0 Tool Broker v2 + Safe Tool Intent Contracts")
        else:
            if "v0.31.0 | m27" in text and "planned/provisional" not in text:
                failures.append("M27 roadmap row is not planned/provisional")
            forbidden_m27_fragments = (
                "m27 is implemented",
                "v0.31.0 implements m27",
                "mcp runtime is implemented",
                "agent skills runtime is implemented",
                "agents.md runtime loading is implemented",
                "plugin enablement is implemented",
            )
            failures.extend(
                f"M26 docs imply M27 implementation: {fragment}"
                for fragment in forbidden_m27_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m27_tool_broker_v2_contract_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/v2/__init__.py",
            "src/ultimate_ai_agent/core/tools/v2/enums.py",
            "src/ultimate_ai_agent/core/tools/v2/contracts.py",
            "src/ultimate_ai_agent/core/tools/v2/catalog.py",
            "src/ultimate_ai_agent/core/tools/v2/broker.py",
            "src/ultimate_ai_agent/core/tools/v2/validation.py",
            "tests/test_tool_broker_v2_contracts.py",
            "tests/test_m27_gate_integration.py",
            "docs/tools/TOOL_BROKER_V2.md",
            "docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md",
            "docs/tools/TOOL_AUTHORITY_BOUNDARY.md",
            "docs/tools/TOOL_INTENT_RECEIPT_PLAN.md",
            "docs/tools/M27_TO_M28_BOUNDARY.md",
        ]
        failures = [f"missing M27 Tool Broker v2 file: {path}" for path in required_files if not (self.root / path).exists()]
        try:
            from pydantic import ValidationError

            from ultimate_ai_agent.core.tools.v2 import (
                ToolApprovalRequirement,
                ToolAuthorityLevel,
                ToolBrokerV2Manifest,
                ToolCatalogEntry,
                ToolExecutionMode,
                ToolInputBoundary,
                ToolInputTrustLevel,
                ToolIntent,
                ToolIntentDecisionStatus,
                ToolRiskClass,
                ToolSideEffectKind,
                ToolTargetKind,
                ToolTargetRef,
                build_default_tool_catalog,
                evaluate_tool_intent,
            )

            manifest = ToolBrokerV2Manifest(baseline_version="0.31.0")
            if manifest.tool_execution_enabled or manifest.backend_execution_routes_added:
                failures.append("M27 manifest enables tool execution or backend routes")
            if manifest.shell_execution_enabled or manifest.network_calls_enabled or manifest.browser_automation_enabled:
                failures.append("M27 manifest enables shell, network, or browser automation")
            if manifest.plugin_enablement_enabled or manifest.memory_writes_enabled or manifest.event_ledger_mutation_enabled:
                failures.append("M27 manifest enables plugin, memory, or Event Ledger mutation")
            if manifest.model_provider_calls_enabled or manifest.context_pack_authority_enabled:
                failures.append("M27 manifest enables model calls or context-pack authority")

            def safe_intent(**overrides):
                data = {
                    "intent_id": "tool-intent:m27-gate",
                    "tool_id": "file.metadata_preview",
                    "intent_summary": "Preview safe file metadata.",
                    "target": ToolTargetRef(target_ref="file:m27", target_kind=ToolTargetKind.file_ref),
                    "input_boundary": ToolInputBoundary(
                        input_refs=["file:m27"],
                        input_trust_level=ToolInputTrustLevel.user_provided_refs,
                    ),
                    "requested_execution_mode": ToolExecutionMode.preview_only,
                    "declared_risk_class": ToolRiskClass.low,
                    "declared_side_effects": [ToolSideEffectKind.none],
                    "approval_requirement": ToolApprovalRequirement.not_required,
                    "authority_level": ToolAuthorityLevel.validation_only,
                }
                data.update(overrides)
                return ToolIntent(**data)

            safe_decision = evaluate_tool_intent(safe_intent(), catalog=build_default_tool_catalog())
            if safe_decision.status != ToolIntentDecisionStatus.preview_allowed:
                failures.append("M27 safe metadata preview intent was not allowed for preview")
            if safe_decision.execution_allowed or not safe_decision.no_tool_execution_performed:
                failures.append("M27 safe preview decision allowed or performed execution")
            if not safe_decision.receipt_plan or safe_decision.receipt_plan.execution_performed:
                failures.append("M27 safe preview receipt plan is missing or executable")

            side_effect_catalog = {
                "file.write_preview": ToolCatalogEntry(
                    tool_id="file.write_preview",
                    display_name="Write preview",
                    target_kind=ToolTargetKind.file_ref,
                    allowed_execution_modes=[ToolExecutionMode.preview_only],
                    risk_class=ToolRiskClass.high,
                    side_effects=[ToolSideEffectKind.file_write],
                    approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
                )
            }
            side_effect_decision = evaluate_tool_intent(
                safe_intent(
                    tool_id="file.write_preview",
                    declared_risk_class=ToolRiskClass.high,
                    declared_side_effects=[ToolSideEffectKind.file_write],
                    approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
                    approval_ref="approval_test_m27",
                ),
                catalog=side_effect_catalog,
            )
            for reason in ["TOOL_SIDE_EFFECTS_DENIED", "APPROVAL_REF_NOT_AUTHORITY"]:
                if reason not in side_effect_decision.reason_codes:
                    failures.append(f"M27 side-effect probe missing reason: {reason}")
            if side_effect_decision.execution_allowed or side_effect_decision.status == ToolIntentDecisionStatus.preview_allowed:
                failures.append("M27 side-effecting tool intent was allowed")

            context_pack_decision = evaluate_tool_intent(
                safe_intent(
                    tool_id="file.write_preview",
                    declared_risk_class=ToolRiskClass.high,
                    declared_side_effects=[ToolSideEffectKind.file_write],
                    context_pack_refs=["context-pack:m26"],
                ),
                catalog=side_effect_catalog,
            )
            if "CONTEXT_PACK_NOT_AUTHORITY" not in context_pack_decision.reason_codes:
                failures.append("M27 context-pack authority probe did not deny context pack refs as authority")

            mismatch_decision = evaluate_tool_intent(
                safe_intent(target=ToolTargetRef(target_ref="memory:m27", target_kind=ToolTargetKind.file_ref)),
                catalog=build_default_tool_catalog(),
            )
            if "TOOL_TARGET_KIND_MISMATCH_DENIED" not in mismatch_decision.reason_codes:
                failures.append("M27 target mismatch probe did not deny mismatched target ref/kind")

            unknown_decision = evaluate_tool_intent(
                safe_intent(target=ToolTargetRef(target_ref="random:m27", target_kind=ToolTargetKind.unknown)),
                catalog=build_default_tool_catalog(),
            )
            if "UNKNOWN_TOOL_TARGET_DENIED" not in unknown_decision.reason_codes:
                failures.append("M27 unknown target probe did not deny unknown target")

            risk_decision = evaluate_tool_intent(
                safe_intent(
                    tool_id="file.write_preview",
                    declared_risk_class=ToolRiskClass.low,
                    declared_side_effects=[ToolSideEffectKind.none],
                ),
                catalog=side_effect_catalog,
            )
            for reason in ["TOOL_RISK_DOWNGRADE_DENIED", "TOOL_SIDE_EFFECTS_HIDDEN_DENIED"]:
                if reason not in risk_decision.reason_codes:
                    failures.append(f"M27 risk/side-effect downgrade probe missing reason: {reason}")

            try:
                ToolInputBoundary(input_refs=["file:m27"], contains_model_output=True)
                failures.append("M27 input boundary allowed model output")
            except ValidationError:
                pass

            v2_source = "\n".join(
                self._read(path)
                for path in (self.root / "src" / "ultimate_ai_agent" / "core" / "tools" / "v2").glob("*.py")
            ).lower()
            forbidden_fragments = (
                "subprocess",
                "os.system(",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
                "chat.completions.create(",
                "import " + "openai",
                "import " + "anthropic",
                "import " + "ollama",
            )
            failures.extend(
                f"M27 Tool Broker v2 module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in v2_source
            )
        except Exception as exc:
            failures.append(f"M27 Tool Broker v2 validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m27_tool_broker_v2_openapi_routes_unchanged(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m27_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M27 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m27_m28_remains_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/tools/M27_TO_M28_BOUNDARY.md",
        ]
        failures = [f"missing M27 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.31.0" in text and "tool broker v2 + safe tool intent contracts" in text:
            if "implemented/released" not in text:
                failures.append("M27 docs do not mark v0.31.0 implemented/released")
        else:
            failures.append("M27 docs do not mention v0.31.0 Tool Broker v2 + Safe Tool Intent Contracts")
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple >= (0, 32, 0):
            if "approval authority v2 + action policy expansion" not in text:
                failures.append("M27 docs do not describe the M28 Approval Authority v2 handoff")
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append("M34-M60 must remain planned/provisional after v0.37.4")
            elif "m29-m40 remain planned/provisional" not in text:
                failures.append("M29-M40 must remain planned/provisional after M28")
        else:
            if "m28-m40 remain planned/provisional" not in text:
                failures.append("M28-M40 must remain planned/provisional after M27")
            forbidden_m28_fragments = (
                "m28 is implemented",
                "v0.32.0 implements m28",
                "real tool execution is implemented",
                "durable action registry runtime is implemented",
                "production tool authority is implemented",
            )
            failures.extend(
                f"M27 docs imply M28 implementation: {fragment}"
                for fragment in forbidden_m28_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m28_approval_authority_v2_action_policy_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/approvals/v2/__init__.py",
            "src/ultimate_ai_agent/core/approvals/v2/enums.py",
            "src/ultimate_ai_agent/core/approvals/v2/contracts.py",
            "src/ultimate_ai_agent/core/approvals/v2/policies.py",
            "src/ultimate_ai_agent/core/approvals/v2/validation.py",
            "tests/test_approval_authority_v2_contracts.py",
            "tests/test_m28_gate_integration.py",
            "docs/approvals/APPROVAL_AUTHORITY_V2.md",
            "docs/approvals/ACTION_POLICY.md",
            "docs/approvals/APPROVAL_GRANT_BINDING.md",
            "docs/approvals/APPROVAL_EXPIRY_REVOCATION_REPLAY.md",
            "docs/approvals/ACTION_RISK_AND_SIDE_EFFECT_POLICY.md",
            "docs/approvals/APPROVAL_REF_NOT_AUTHORITY.md",
            "docs/approvals/ACTION_POLICY_DECISION_ENVELOPE.md",
            "docs/approvals/APPROVAL_RECEIPT_PLAN.md",
            "docs/approvals/APPROVAL_AUTHORITY_V2_NON_GOALS.md",
            "docs/approvals/M28_TO_M29_BOUNDARY.md",
        ]
        failures = [
            f"missing M28 Approval Authority v2 file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from datetime import timedelta

            from ultimate_ai_agent.core.approvals.v2 import (
                ActionIntent,
                ActionKind,
                ActionRef,
                ActionRiskLevel,
                ActionSideEffectClass,
                ActorRef,
                ActorTrustLevel,
                ApprovalAuthorityV2Manifest,
                ApprovalDecisionStatus,
                ApprovalGrant,
                ApprovalGrantStatus,
                ApprovalScope,
                ApprovalScopeKind,
                ResourceRef,
                ResourceRefKind,
                ActionPolicy,
                build_approval_authority_v2_manifest,
                evaluate_action_policy,
            )
            from ultimate_ai_agent.core.time import utc_now

            manifest = build_approval_authority_v2_manifest(baseline_version="0.32.1")
            if not isinstance(manifest, ApprovalAuthorityV2Manifest):
                failures.append("M28 manifest builder did not return ApprovalAuthorityV2Manifest")
            manifest_flags = [
                manifest.action_execution_enabled,
                manifest.execution_authorized,
                manifest.execution_performed,
                manifest.tool_execution_enabled,
                manifest.filesystem_mutation_enabled,
                manifest.memory_write_enabled,
                manifest.network_action_enabled,
                manifest.browser_action_enabled,
                manifest.mobile_action_enabled,
                manifest.remote_execution_enabled,
                manifest.plugin_enable_enabled,
                manifest.model_action_enabled,
                manifest.wildcard_approval_enabled,
                manifest.approval_test_refs_enabled,
                manifest.backend_execution_routes_added,
                manifest.control_center_execute_controls_enabled,
                manifest.production_authority_enabled,
            ]
            if any(manifest_flags):
                failures.append("M28 manifest enables forbidden runtime/action authority")

            actor = ActorRef(actor_ref="actor:gate-m28", trust_level=ActorTrustLevel.user)
            action = ActionRef(
                action_ref="action:gate-m28-read-metadata",
                action_kind=ActionKind.read_metadata,
                risk_level=ActionRiskLevel.low,
                side_effect_class=ActionSideEffectClass.read_only_metadata,
                safe_summary="Read metadata only.",
            )
            resource = ResourceRef(
                resource_ref="file_ref:gate-m28",
                resource_kind=ResourceRefKind.file_ref,
                safe_label="Gate metadata ref.",
            )
            expires_at = utc_now() + timedelta(minutes=15)
            scope = ApprovalScope(
                scope_ref="scope:gate-m28",
                scope_kind=ApprovalScopeKind.single_action,
                actor_ref=actor.actor_ref,
                action_ref=action.action_ref,
                resource_ref=resource.resource_ref,
                expires_at=expires_at,
                replay_nonce="nonce:gate-m28",
            )
            intent = ActionIntent(
                intent_id="action-intent:gate-m28",
                actor=actor,
                action=action,
                resource=resource,
                safe_summary="Evaluate a safe read-metadata action.",
                input_refs=["file_ref:gate-m28"],
            )
            grant = ApprovalGrant(
                grant_ref="approval:gate-m28",
                actor_ref=actor.actor_ref,
                action_ref=action.action_ref,
                resource_ref=resource.resource_ref,
                scope=scope,
                expires_at=expires_at,
                replay_nonce="nonce:gate-m28",
            )
            safe_decision = evaluate_action_policy(intent, grant=grant, replay_nonce="nonce:gate-m28")
            if safe_decision.status != ApprovalDecisionStatus.allowed_for_policy:
                failures.append("M28 safe read-metadata action was not allowed for policy")
            if not safe_decision.allowed_for_policy:
                failures.append("M28 safe read-metadata action did not return allowed_for_policy")
            if safe_decision.execution_authorized or safe_decision.execution_performed:
                failures.append("M28 safe decision authorized or performed execution")
            if not safe_decision.receipt_plan or safe_decision.receipt_plan.execution_performed:
                failures.append("M28 safe decision receipt plan is missing or executable")

            def require_denial(decision, required_reason: str, label: str) -> None:
                if decision.allowed_for_policy or decision.execution_authorized or decision.execution_performed:
                    failures.append(f"M28 denied probe was allowed: {label}")
                if required_reason not in decision.reason_codes:
                    failures.append(f"M28 denied probe missing {required_reason}: {label}")

            require_denial(
                evaluate_action_policy(intent.model_copy(update={"approval_ref": "approval:arbitrary"})),
                "APPROVAL_REF_NOT_AUTHORITY",
                "approval_ref alone",
            )
            require_denial(
                evaluate_action_policy(intent.model_copy(update={"approval_ref": "approval_test_gate_m28"})),
                "APPROVAL_TEST_REF_DENIED",
                "approval_test_ ref",
            )
            require_denial(
                evaluate_action_policy(intent.model_copy(update={"consent_ref": "consent:gate-m28"})),
                "CONSENT_REF_NOT_AUTHORITY",
                "consent_ref alone",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"contains_raw_prompt": True}),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "RAW_PROMPT_DENIED",
                "model_copy raw prompt revalidation",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"contains_raw_model_output": True}),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "RAW_MODEL_OUTPUT_DENIED",
                "model_copy raw model output revalidation",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"metadata": {"token": "abc123"}}),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "SECRET_METADATA_DENIED",
                "model_copy secret metadata revalidation",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant.model_copy(update={"grant_ref": "approval_test_gate_m28"}),
                    replay_nonce="nonce:gate-m28",
                ),
                "APPROVAL_TEST_REF_DENIED",
                "model_copy approval_test grant revalidation",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant,
                    policy=ActionPolicy().model_copy(update={"safe_summary": "contains token=abc123"}),
                    replay_nonce="nonce:gate-m28",
                ),
                "ACTION_POLICY_SECRET_CONTENT_DENIED",
                "model_copy action policy revalidation",
            )

            wildcard_scope = scope.model_copy(
                update={"scope_kind": ApprovalScopeKind.blocked_wildcard, "action_ref": "*"}
            )
            wildcard_grant = grant.model_copy(update={"scope": wildcard_scope, "action_ref": "*"})
            require_denial(
                evaluate_action_policy(intent, grant=wildcard_grant, replay_nonce="nonce:gate-m28"),
                "WILDCARD_SCOPE_DENIED",
                "wildcard scope",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant.model_copy(update={"expires_at": utc_now() - timedelta(minutes=1)}),
                    replay_nonce="nonce:gate-m28",
                ),
                "APPROVAL_GRANT_EXPIRED",
                "expired grant",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant.model_copy(update={"status": ApprovalGrantStatus.revoked}),
                    replay_nonce="nonce:gate-m28",
                ),
                "APPROVAL_GRANT_REVOKED",
                "revoked grant",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant.model_copy(update={"used_replay_nonces": ["nonce:gate-m28"]}),
                    replay_nonce="nonce:gate-m28",
                ),
                "APPROVAL_REPLAY_DETECTED",
                "replayed grant",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant.model_copy(update={"actor_ref": "actor:gate-mismatch"}),
                    replay_nonce="nonce:gate-m28",
                ),
                "APPROVAL_ACTOR_MISMATCH",
                "actor mismatch",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(
                        update={
                            "resource": ResourceRef(
                                resource_ref="memory:gate-m28",
                                resource_kind=ResourceRefKind.memory_ref,
                                safe_label="Memory recall ref.",
                            )
                        }
                    ),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "MEMORY_REF_NOT_AUTHORITY",
                "memory ref authority",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(
                        update={
                            "resource": ResourceRef(
                                resource_ref="model:gate-m28",
                                resource_kind=ResourceRefKind.model_output_ref,
                                safe_label="Model output ref.",
                            )
                        }
                    ),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "MODEL_OUTPUT_NOT_AUTHORITY",
                "model output ref authority",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(
                        update={
                            "resource": ResourceRef(
                                resource_ref="context-pack:gate-m28",
                                resource_kind=ResourceRefKind.context_pack_ref,
                                safe_label="Context pack ref.",
                            )
                        }
                    ),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "CONTEXT_PACK_NOT_AUTHORITY",
                "context pack ref authority",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(
                        update={
                            "resource": ResourceRef(
                                resource_ref="tool-intent:gate-m27",
                                resource_kind=ResourceRefKind.tool_intent_ref,
                                safe_label="Tool intent ref.",
                            )
                        }
                    ),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "TOOL_INTENT_NOT_AUTHORITY",
                "tool intent ref authority",
            )
            write_action = ActionRef(
                action_ref="action:gate-m28-file-write",
                action_kind=ActionKind.file_write_planned,
                risk_level=ActionRiskLevel.high,
                side_effect_class=ActionSideEffectClass.local_mutation_blocked,
                safe_summary="Blocked file write plan.",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"action": write_action}),
                    grant=grant.model_copy(update={"action_ref": write_action.action_ref}),
                    replay_nonce="nonce:gate-m28",
                ),
                "ACTION_KIND_DENIED",
                "effectful action",
            )
            try:
                ActionIntent(
                    intent_id="action-intent:gate-m28-raw",
                    actor=actor,
                    action=action,
                    resource=resource,
                    safe_summary="Raw action input probe.",
                    contains_raw_prompt=True,
                )
                failures.append("M28 action intent allowed raw prompt content")
            except ValidationError:
                pass
            try:
                ActionIntent(
                    intent_id="action-intent:gate-m28-secret",
                    actor=actor,
                    action=action,
                    resource=resource,
                    safe_summary="Secret input probe.",
                    metadata={"token": "abc123"},
                )
                failures.append("M28 action intent allowed secret-like metadata")
            except ValidationError:
                pass

            v2_source = "\n".join(
                self._read(path)
                for path in (self.root / "src" / "ultimate_ai_agent" / "core" / "approvals" / "v2").glob("*.py")
            ).lower()
            forbidden_fragments = (
                "subprocess",
                "os.system(",
                "popen(",
                "shell=true",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
                "append_event(",
                "mutate_event(",
                "chat.completions.create(",
                "import " + "openai",
                "import " + "anthropic",
                "import " + "ollama",
            )
            failures.extend(
                f"M28 Approval Authority v2 module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in v2_source
            )
        except Exception as exc:
            failures.append(f"M28 Approval Authority v2 validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m28_action_policy_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m28_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M28 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m28_m29_remains_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/approvals/M28_TO_M29_BOUNDARY.md",
        ]
        failures = [f"missing M28 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.32.0" in text and "approval authority v2 + action policy expansion" in text:
            if "implemented/released" not in text:
                failures.append("M28 docs do not mark v0.32.0 implemented/released")
        else:
            failures.append("M28 docs do not mention v0.32.0 Approval Authority v2 + Action Policy Expansion")
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple >= (0, 35, 0):
            if "m29 agent task planning engine" not in text:
                failures.append("M28 docs do not describe the M29 Agent Task Planning Engine handoff")
            if "m30" not in text or "multi-step execution framework" not in text or "implemented/released" not in text:
                failures.append("M28 docs do not acknowledge implemented v0.34.0 / M30")
            if "m31" not in text or "real tool runtime adapter" not in text or "implemented/released" not in text:
                failures.append("M28 docs do not acknowledge implemented v0.35.0 / M31")
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append("M34-M60 must remain planned/provisional after v0.37.4")
            elif "m32-m40 remain planned/provisional" not in text:
                failures.append("M32-M40 must remain planned/provisional after M31")
        elif version_tuple >= (0, 34, 0):
            if "m29 agent task planning engine" not in text:
                failures.append("M28 docs do not describe the M29 Agent Task Planning Engine handoff")
            if "m30" not in text or "multi-step execution framework" not in text or "implemented/released" not in text:
                failures.append("M28 docs do not acknowledge implemented v0.34.0 / M30")
            if "m31-m40 remain planned/provisional" not in text:
                failures.append("M31-M40 must remain planned/provisional after M30")
        elif version_tuple >= (0, 33, 0):
            if "m29 agent task planning engine" not in text:
                failures.append("M28 docs do not describe the M29 Agent Task Planning Engine handoff")
            if "m30-m40 remain planned/provisional" not in text:
                failures.append("M30-M40 must remain planned/provisional after M29")
        else:
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append("M34-M60 must remain planned/provisional after v0.37.4")
            elif "m29-m40 remain planned/provisional" not in text:
                failures.append("M29-M40 must remain planned/provisional after M28")
            forbidden_m29_fragments = (
                "m29 is implemented",
                "v0.33.0 implements m29",
                "action execution is implemented",
                "tool execution is implemented",
                "production approval authority is implemented",
            )
            failures.extend(
                f"M28 docs imply M29 implementation: {fragment}"
                for fragment in forbidden_m29_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m29_task_planning_engine_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/planning/__init__.py",
            "src/ultimate_ai_agent/core/planning/enums.py",
            "src/ultimate_ai_agent/core/planning/contracts.py",
            "src/ultimate_ai_agent/core/planning/validation.py",
            "src/ultimate_ai_agent/core/planning/planner.py",
            "src/ultimate_ai_agent/core/planning/manifests.py",
            "tests/test_task_planning_contracts.py",
            "tests/test_task_plan_validation.py",
            "tests/test_task_plan_dependencies.py",
            "tests/test_task_plan_no_execution.py",
            "tests/test_m29_gate_integration.py",
            "docs/planning/TASK_PLANNING_ENGINE.md",
            "docs/planning/TASK_GOAL_STEP_PLAN_CONTRACTS.md",
            "docs/planning/TASK_DEPENDENCY_GRAPH.md",
            "docs/planning/TASK_INPUT_BOUNDARY.md",
            "docs/planning/TASK_RISK_AND_AUTHORITY_POLICY.md",
            "docs/planning/TASK_PLAN_DECISION_ENVELOPE.md",
            "docs/planning/TASK_PLAN_RECEIPT_PLAN.md",
            "docs/planning/TASK_PLANNING_NON_GOALS.md",
            "docs/planning/M29_TO_M30_BOUNDARY.md",
        ]
        failures = [
            f"missing M29 Task Planning Engine file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.planning import (
                PlanInputTrustLevel,
                TaskDependency,
                TaskGoal,
                TaskPlan,
                TaskPlanDecisionStatus,
                TaskPlanningManifest,
                TaskPlanningRequest,
                TaskRiskLevel,
                TaskStep,
                TaskStepInputBoundary,
                TaskStepKind,
                build_task_planning_manifest,
                evaluate_task_plan,
            )

            manifest = build_task_planning_manifest(baseline_version="0.33.0")
            if not isinstance(manifest, TaskPlanningManifest):
                failures.append("M29 manifest builder did not return TaskPlanningManifest")
            manifest_flags = [
                manifest.task_execution_enabled,
                manifest.auto_run_enabled,
                manifest.scheduler_enabled,
                manifest.background_worker_enabled,
                manifest.tool_execution_enabled,
                manifest.action_execution_enabled,
                manifest.file_mutation_enabled,
                manifest.memory_write_enabled,
                manifest.network_call_enabled,
                manifest.model_provider_call_enabled,
                manifest.browser_automation_enabled,
                manifest.mobile_device_access_enabled,
                manifest.remote_execution_enabled,
                manifest.plugin_enablement_enabled,
                manifest.backend_task_routes_added,
                manifest.control_center_execute_controls_enabled,
                manifest.context_injection_enabled,
                manifest.production_authority_enabled,
            ]
            if any(manifest_flags):
                failures.append("M29 manifest enables forbidden execution/runtime authority")

            safe_step = TaskStep(
                step_id="step:gate-m29-review",
                step_kind=TaskStepKind.review_metadata,
                safe_summary="Review safe metadata refs.",
                input_boundary=TaskStepInputBoundary(input_refs=["canonical:gate-m29"]),
                declared_risk_level=TaskRiskLevel.low,
            )
            safe_plan = TaskPlan(
                plan_id="plan:gate-m29",
                goal=TaskGoal(goal_id="goal:gate-m29", safe_summary="Plan a safe review workflow."),
                steps=[safe_step],
                safe_summary="Review-only task plan.",
            )
            safe_decision = evaluate_task_plan(safe_plan)
            if safe_decision.status != TaskPlanDecisionStatus.valid_for_review:
                failures.append("M29 safe task plan was not valid for review")
            if not safe_decision.valid_for_review:
                failures.append("M29 safe task plan did not return valid_for_review")
            if safe_decision.execution_authorized or safe_decision.execution_performed:
                failures.append("M29 safe task plan authorized or performed execution")
            if safe_decision.scheduler_registered:
                failures.append("M29 safe task plan registered a scheduler")
            if safe_decision.derived_plan_risk_level != TaskRiskLevel.low:
                failures.append("M29 safe task plan did not report trusted derived risk")
            if not safe_decision.receipt_plan or safe_decision.receipt_plan.execution_performed:
                failures.append("M29 safe task plan receipt plan is missing or executable")
            elif safe_decision.receipt_plan.derived_plan_risk_level != safe_decision.derived_plan_risk_level:
                failures.append("M29 receipt plan did not preserve derived plan risk")

            def require_denial(decision, required_reason: str, label: str) -> None:
                if decision.valid_for_review or decision.execution_authorized or decision.execution_performed:
                    failures.append(f"M29 denied probe was allowed: {label}")
                if decision.scheduler_registered:
                    failures.append(f"M29 denied probe registered a scheduler: {label}")
                if required_reason not in decision.reason_codes:
                    failures.append(f"M29 denied probe missing {required_reason}: {label}")

            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"approval_ref": "approval:m28-arbitrary"})),
                "APPROVAL_REF_NOT_TASK_AUTHORITY",
                "approval_ref alone",
            )
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"approval_ref": "approval_test_gate_m29"})),
                "APPROVAL_TEST_REF_DENIED",
                "approval_test_ ref",
            )
            require_denial(
                evaluate_task_plan(TaskPlanningRequest(plan=safe_plan).model_copy(update={"execution_requested": True})),
                "TASK_EXECUTION_REQUEST_DENIED",
                "execution requested",
            )
            require_denial(
                evaluate_task_plan(TaskPlanningRequest(plan=safe_plan).model_copy(update={"auto_run_requested": True})),
                "TASK_AUTO_RUN_DENIED",
                "auto-run requested",
            )
            require_denial(
                evaluate_task_plan(TaskPlanningRequest(plan=safe_plan).model_copy(update={"schedule_requested": True})),
                "TASK_SCHEDULER_DENIED",
                "scheduler requested",
            )
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"safe_summary": "contains token=abc123"})),
                "TASK_PLAN_REVALIDATION_FAILED",
                "model_copy plan secret summary revalidation",
            )
            raw_boundary = safe_step.input_boundary.model_copy(update={"contains_raw_prompt": True})
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": raw_boundary})]})),
                "RAW_PROMPT_DENIED",
                "model_copy raw prompt revalidation",
            )
            secret_boundary = safe_step.input_boundary.model_copy(update={"metadata": {"token": "abc123"}})
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": secret_boundary})]})),
                "SECRET_METADATA_DENIED",
                "model_copy secret metadata revalidation",
            )
            for input_ref, trust_level, reason in [
                ("model:gate-m29", PlanInputTrustLevel.model_output_blocked, "MODEL_OUTPUT_NOT_PLAN_AUTHORITY"),
                ("memory:gate-m29", PlanInputTrustLevel.memory_ref, "MEMORY_REF_NOT_PLAN_AUTHORITY"),
                ("context-pack:gate-m29", PlanInputTrustLevel.context_pack_ref, "CONTEXT_PACK_NOT_PLAN_AUTHORITY"),
                ("tool-intent:gate-m27", PlanInputTrustLevel.tool_intent_ref, "TOOL_INTENT_NOT_PLAN_AUTHORITY"),
                ("approval:gate-m28", PlanInputTrustLevel.approval_ref, "APPROVAL_REF_NOT_TASK_AUTHORITY"),
                ("openwebui:gate-m29", PlanInputTrustLevel.openwebui_output_blocked, "OPENWEBUI_OUTPUT_NOT_PLAN_AUTHORITY"),
                ("control-center:gate-m29", PlanInputTrustLevel.unknown_blocked, "UNKNOWN_INPUT_REF_DENIED"),
            ]:
                blocked_boundary = TaskStepInputBoundary(input_refs=[input_ref], input_trust_level=trust_level)
                require_denial(
                    evaluate_task_plan(safe_plan.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": blocked_boundary})]})),
                    reason,
                    f"non-authoritative input ref {input_ref}",
                )
            effectful_step = safe_step.model_copy(
                update={
                    "step_kind": TaskStepKind.tool_execution_planned,
                    "declared_risk_level": TaskRiskLevel.high,
                }
            )
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"steps": [effectful_step]})),
                "TASK_STEP_EXECUTION_DENIED",
                "effectful task step",
            )
            downgraded_step = safe_step.model_copy(
                update={
                    "step_kind": TaskStepKind.file_mutation_planned,
                    "declared_risk_level": TaskRiskLevel.low,
                }
            )
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"steps": [downgraded_step]})),
                "TASK_RISK_DOWNGRADE_DENIED",
                "risk downgrade",
            )
            hidden_side_effect_step = safe_step.model_copy(update={"metadata": {"side_effect": "file_write"}})
            hidden_side_effect_decision = evaluate_task_plan(
                safe_plan.model_copy(update={"steps": [hidden_side_effect_step]})
            )
            require_denial(
                hidden_side_effect_decision,
                "TASK_HIDDEN_SIDE_EFFECT_DENIED",
                "hidden side effect metadata",
            )
            if "TASK_RISK_DOWNGRADE_DENIED" not in hidden_side_effect_decision.reason_codes:
                failures.append("M29 hidden side effect metadata did not deny risk downgrade")
            duplicate_step = safe_step.model_copy(update={"safe_summary": "Duplicate step ref."})
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"steps": [safe_step, duplicate_step]})),
                "DUPLICATE_STEP_ID_DENIED",
                "duplicate step id",
            )
            missing_dependency_step = safe_step.model_copy(update={"depends_on": ["step:missing-m29"]})
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"steps": [missing_dependency_step]})),
                "MISSING_DEPENDENCY_STEP_DENIED",
                "missing dependency",
            )
            step_a = safe_step.model_copy(update={"step_id": "step:gate-m29-a", "depends_on": ["step:gate-m29-b"]})
            step_b = safe_step.model_copy(update={"step_id": "step:gate-m29-b", "depends_on": ["step:gate-m29-a"]})
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"steps": [step_a, step_b]})),
                "DEPENDENCY_CYCLE_DENIED",
                "dependency cycle",
            )
            self_dep_step = safe_step.model_copy(update={"depends_on": [safe_step.step_id]})
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"steps": [self_dep_step]})),
                "DEPENDENCY_CYCLE_DENIED",
                "self dependency cycle",
            )
            step_c = safe_step.model_copy(update={"step_id": "step:gate-m29-c", "depends_on": ["step:gate-m29-b"]})
            indirect_a = step_a.model_copy(update={"depends_on": ["step:gate-m29-c"]})
            indirect_b = step_b.model_copy(update={"depends_on": ["step:gate-m29-a"]})
            require_denial(
                evaluate_task_plan(safe_plan.model_copy(update={"steps": [indirect_a, indirect_b, step_c]})),
                "DEPENDENCY_CYCLE_DENIED",
                "indirect dependency cycle",
            )
            dependency_decision = evaluate_task_plan(
                safe_plan.model_copy(
                    update={
                        "steps": [step_a.model_copy(update={"depends_on": []}), step_b.model_copy(update={"depends_on": []})],
                        "dependencies": [
                            TaskDependency(
                                dependency_id="dependency:gate-m29-a-before-b",
                                before_step_id="step:gate-m29-a",
                                after_step_id="step:gate-m29-b",
                            )
                        ],
                    }
                )
            )
            if not dependency_decision.valid_for_review:
                failures.append("M29 explicit acyclic dependency plan was not valid for review")

            planning_source = "\n".join(
                self._read(path)
                for path in (self.root / "src" / "ultimate_ai_agent" / "core" / "planning").glob("*.py")
            ).lower()
            forbidden_fragments = (
                "subprocess",
                "os.system(",
                "popen(",
                "shell=true",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
                "append_event(",
                "mutate_event(",
                "chat.completions.create(",
                "import " + "openai",
                "import " + "anthropic",
                "import " + "ollama",
            )
            failures.extend(
                f"M29 Task Planning Engine module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in planning_source
            )
        except Exception as exc:
            failures.append(f"M29 Task Planning Engine validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m29_task_planning_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m29_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M29 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m29_m30_remains_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/planning/M29_TO_M30_BOUNDARY.md",
        ]
        failures = [f"missing M29 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.33.0" in text and "agent task planning engine" in text:
            if "implemented/released" not in text:
                failures.append("M29 docs do not mark v0.33.0 implemented/released")
        else:
            failures.append("M29 docs do not mention v0.33.0 Agent Task Planning Engine")
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple >= (0, 35, 0):
            if "m30" not in text or "multi-step execution framework" not in text or "implemented/released" not in text:
                failures.append("M29 boundary docs must acknowledge implemented v0.34.0 / M30")
            if "m31" not in text or "real tool runtime adapter" not in text or "implemented/released" not in text:
                failures.append("M29 boundary docs must acknowledge implemented v0.35.0 / M31")
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append("M34-M60 must remain planned/provisional after v0.37.4")
            elif "m32-m40 remain planned/provisional" not in text:
                failures.append("M32-M40 must remain planned/provisional after M31")
        elif version_tuple >= (0, 34, 0):
            if "m30" not in text or "multi-step execution framework" not in text or "implemented/released" not in text:
                failures.append("M29 boundary docs must acknowledge implemented v0.34.0 / M30")
            if "m31-m40 remain planned/provisional" not in text:
                failures.append("M31-M40 must remain planned/provisional after M30")
        else:
            if "m30-m40 remain planned/provisional" not in text:
                failures.append("M30-M40 must remain planned/provisional after M29")
            forbidden_m30_fragments = (
                "m30 is implemented",
                "v0.34.0 implements m30",
                "approved local tool execution is implemented",
                "task execution is implemented",
                "scheduler runtime is implemented",
                "production task authority is implemented",
            )
            failures.extend(
                f"M29 docs imply M30 implementation: {fragment}"
                for fragment in forbidden_m30_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m30_execution_framework_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/execution/__init__.py",
            "src/ultimate_ai_agent/core/execution/enums.py",
            "src/ultimate_ai_agent/core/execution/runs.py",
            "src/ultimate_ai_agent/core/execution/steps.py",
            "src/ultimate_ai_agent/core/execution/transitions.py",
            "src/ultimate_ai_agent/core/execution/state_machine.py",
            "src/ultimate_ai_agent/core/execution/validation.py",
            "src/ultimate_ai_agent/core/execution/manifests.py",
            "src/ultimate_ai_agent/core/execution/receipts.py",
            "src/ultimate_ai_agent/core/execution/policy.py",
            "tests/test_execution_framework_contracts.py",
            "tests/test_execution_state_machine_safety.py",
            "tests/test_execution_dependency_progression.py",
            "tests/test_execution_receipt_plan.py",
            "tests/test_m30_gate_integration.py",
            "docs/execution/MULTI_STEP_EXECUTION_FRAMEWORK.md",
            "docs/execution/EXECUTION_STATE_MACHINE.md",
            "docs/execution/EXECUTION_STEP_CONTRACTS.md",
            "docs/execution/EXECUTION_DEPENDENCY_POLICY.md",
            "docs/execution/EXECUTION_TRANSITION_POLICY.md",
            "docs/execution/EXECUTION_INPUT_BOUNDARY.md",
            "docs/execution/EXECUTION_RECEIPT_PLAN.md",
            "docs/execution/EXECUTION_NON_GOALS.md",
            "docs/execution/M30_TO_M31_BOUNDARY.md",
        ]
        failures = [
            f"missing M30 Multi-Step Execution Framework file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.execution import (
                ExecutionInputTrustLevel,
                ExecutionRun,
                ExecutionStep,
                ExecutionStepInputBoundary,
                ExecutionStepMode,
                ExecutionStepStatus,
                ExecutionTransitionKind,
                ExecutionTransitionRequest,
                ExecutionTransitionStatus,
                build_execution_framework_manifest,
                evaluate_execution_transition,
            )

            manifest = build_execution_framework_manifest(baseline_version="0.34.0")
            manifest_flags = [
                manifest.real_task_execution_enabled,
                manifest.action_execution_enabled,
                manifest.tool_execution_enabled,
                manifest.file_mutation_enabled,
                manifest.memory_write_enabled,
                manifest.event_ledger_mutation_enabled,
                manifest.network_call_enabled,
                manifest.model_provider_call_enabled,
                manifest.browser_automation_enabled,
                manifest.mobile_device_access_enabled,
                manifest.remote_execution_enabled,
                manifest.plugin_enablement_enabled,
                manifest.scheduler_enabled,
                manifest.background_worker_enabled,
                manifest.autonomous_loop_enabled,
                manifest.context_injection_enabled,
                manifest.backend_execution_routes_added,
                manifest.control_center_execute_controls_enabled,
                manifest.production_authority_enabled,
            ]
            if not manifest.execution_state_machine_enabled or any(manifest_flags):
                failures.append("M30 manifest enables forbidden execution/runtime authority")

            safe_step = ExecutionStep(
                step_id="execution-step:gate-m30-review",
                safe_summary="Validate safe metadata only.",
                mode=ExecutionStepMode.no_effect,
                status=ExecutionStepStatus.ready,
                input_boundary=ExecutionStepInputBoundary(input_refs=["canonical:gate-m30"]),
            )
            safe_run = ExecutionRun(
                run_id="execution-run:gate-m30",
                source_task_plan_ref="plan:gate-m30",
                steps=[safe_step],
                safe_summary="No-effect execution-state-machine run.",
            )
            safe_request = ExecutionTransitionRequest(
                run_id=safe_run.run_id,
                target_step_id=safe_step.step_id,
                transition_id="execution-transition:gate-m30",
                transition_kind=ExecutionTransitionKind.complete_no_effect_step,
                replay_key="replay:gate-m30",
                safe_summary="Complete a no-effect step.",
            )
            safe_decision = evaluate_execution_transition(safe_run, safe_request)
            if safe_decision.status != ExecutionTransitionStatus.approved_no_effect_transition:
                failures.append("M30 safe no-effect transition was not allowed")
            if safe_decision.execution_authorized or safe_decision.execution_performed:
                failures.append("M30 safe transition authorized or performed real execution")
            if safe_decision.side_effects_performed:
                failures.append("M30 safe transition reported side effects")
            if not safe_decision.receipt_plan or safe_decision.receipt_plan.execution_performed:
                failures.append("M30 safe transition receipt is missing or executable")

            def require_denial(decision, required_reason: str, label: str) -> None:
                if decision.status != ExecutionTransitionStatus.denied or decision.execution_performed:
                    failures.append(f"M30 denied probe was allowed: {label}")
                if required_reason not in decision.reason_codes:
                    failures.append(f"M30 denied probe missing {required_reason}: {label}")

            request_with_execution = safe_request.model_copy(update={"execution_requested": True})
            require_denial(
                evaluate_execution_transition(safe_run, request_with_execution),
                "EXECUTION_REQUEST_DENIED",
                "execution requested",
            )
            request_with_auto = safe_request.model_copy(
                update={"auto_run_requested": True, "schedule_requested": True, "background_worker_requested": True}
            )
            auto_decision = evaluate_execution_transition(safe_run, request_with_auto)
            require_denial(auto_decision, "AUTO_RUN_DENIED", "auto-run requested")
            if "SCHEDULE_DENIED" not in auto_decision.reason_codes:
                failures.append("M30 scheduler request was not denied")
            if "BACKGROUND_WORKER_DENIED" not in auto_decision.reason_codes:
                failures.append("M30 background worker request was not denied")
            require_denial(
                evaluate_execution_transition(safe_run.model_copy(update={"replay_keys_seen": ["replay:gate-m30"]}), safe_request),
                "EXECUTION_REPLAY_DENIED",
                "replay key reuse",
            )
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(update={"transition_ids_seen": ["execution-transition:gate-m30"]}),
                    safe_request,
                ),
                "EXECUTION_TRANSITION_REPLAY_DENIED",
                "transition id reuse",
            )
            raw_boundary = safe_step.input_boundary.model_copy(update={"contains_raw_prompt": True})
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": raw_boundary})]}),
                    safe_request,
                ),
                "RAW_PROMPT_DENIED",
                "raw prompt model_copy revalidation",
            )
            secret_boundary = safe_step.input_boundary.model_copy(update={"metadata": {"token": "abc123"}})
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": secret_boundary})]}),
                    safe_request,
                ),
                "SECRET_METADATA_DENIED",
                "secret metadata model_copy revalidation",
            )
            effectful_step = safe_step.model_copy(update={"mode": ExecutionStepMode.tool_execution_blocked})
            require_denial(
                evaluate_execution_transition(safe_run.model_copy(update={"steps": [effectful_step]}), safe_request),
                "TOOL_EXECUTION_DENIED",
                "tool execution step mode",
            )
            hidden_effect_step = safe_step.model_copy(update={"metadata": {"derived_effect": "file_write"}})
            require_denial(
                evaluate_execution_transition(safe_run.model_copy(update={"steps": [hidden_effect_step]}), safe_request),
                "HIDDEN_SIDE_EFFECT_DENIED",
                "hidden side effect metadata",
            )
            for input_ref, trust_level, reason in [
                ("model:gate-m30", ExecutionInputTrustLevel.model_output_blocked, "MODEL_OUTPUT_NOT_EXECUTION_AUTHORITY"),
                ("memory:gate-m30", ExecutionInputTrustLevel.memory_ref, "MEMORY_REF_NOT_EXECUTION_AUTHORITY"),
                ("context-pack:gate-m30", ExecutionInputTrustLevel.context_pack_ref, "CONTEXT_PACK_NOT_EXECUTION_AUTHORITY"),
                ("tool-intent:gate-m27", ExecutionInputTrustLevel.tool_intent_ref, "TOOL_INTENT_NOT_EXECUTION_AUTHORITY"),
                ("approval:gate-m28", ExecutionInputTrustLevel.approval_ref, "APPROVAL_REF_NOT_EXECUTION_AUTHORITY"),
                ("openwebui:gate-m30", ExecutionInputTrustLevel.openwebui_output_blocked, "OPENWEBUI_OUTPUT_NOT_EXECUTION_AUTHORITY"),
                ("control-center:gate-m30", ExecutionInputTrustLevel.control_center_preview_blocked, "CONTROL_CENTER_PREVIEW_NOT_EXECUTION_AUTHORITY"),
                ("random:gate-m30", ExecutionInputTrustLevel.unknown_blocked, "UNKNOWN_INPUT_REF_DENIED"),
            ]:
                blocked_boundary = ExecutionStepInputBoundary(input_refs=[input_ref], input_trust_level=trust_level)
                require_denial(
                    evaluate_execution_transition(
                        safe_run.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": blocked_boundary})]}),
                        safe_request,
                    ),
                    reason,
                    f"non-authoritative execution ref {input_ref}",
                )
            missing_dep_step = safe_step.model_copy(update={"depends_on": ["execution-step:missing-m30"]})
            require_denial(
                evaluate_execution_transition(safe_run.model_copy(update={"steps": [missing_dep_step]}), safe_request),
                "MISSING_EXECUTION_DEPENDENCY_DENIED",
                "missing dependency",
            )
            step_a = safe_step.model_copy(
                update={"step_id": "execution-step:gate-m30-a", "depends_on": ["execution-step:gate-m30-b"]}
            )
            step_b = safe_step.model_copy(
                update={"step_id": "execution-step:gate-m30-b", "depends_on": ["execution-step:gate-m30-a"]}
            )
            cycle_request = safe_request.model_copy(update={"target_step_id": "execution-step:gate-m30-a"})
            require_denial(
                evaluate_execution_transition(safe_run.model_copy(update={"steps": [step_a, step_b]}), cycle_request),
                "EXECUTION_DEPENDENCY_CYCLE_DENIED",
                "dependency cycle",
            )
            completed_step = step_a.model_copy(update={"status": ExecutionStepStatus.completed_no_effect, "depends_on": []})
            dependent_step = step_b.model_copy(update={"depends_on": [completed_step.step_id]})
            dependent_request = safe_request.model_copy(
                update={
                    "target_step_id": dependent_step.step_id,
                    "replay_key": "replay:gate-m30-dependent",
                    "transition_id": "execution-transition:gate-m30-dependent",
                }
            )
            dependent_decision = evaluate_execution_transition(
                safe_run.model_copy(update={"steps": [completed_step, dependent_step]}),
                dependent_request,
            )
            if dependent_decision.status != ExecutionTransitionStatus.approved_no_effect_transition:
                failures.append("M30 completed dependency did not allow no-effect dependent step")

            final_request = safe_request.model_copy(
                update={
                    "target_step_id": None,
                    "replay_key": "replay:gate-m30-finalize",
                    "transition_id": "execution-transition:gate-m30-finalize",
                    "transition_kind": ExecutionTransitionKind.finalize_no_effect_run,
                }
            )
            final_decision = evaluate_execution_transition(
                safe_run.model_copy(
                    update={"steps": [safe_step.model_copy(update={"status": ExecutionStepStatus.completed_no_effect})]}
                ),
                final_request,
            )
            if final_decision.status != ExecutionTransitionStatus.approved_no_effect_transition:
                failures.append("M30 completed run did not finalize without side effects")
            require_denial(
                evaluate_execution_transition(safe_run, final_request),
                "EXECUTION_RUN_FINALIZE_INCOMPLETE_DENIED",
                "finalize incomplete run",
            )
            require_denial(
                evaluate_execution_transition(
                    safe_run,
                    safe_request.model_copy(
                        update={
                            "side_effect_execution_enabled": True,
                            "replay_key": "replay:gate-m30-side-effect",
                            "transition_id": "execution-transition:gate-m30-side-effect",
                        }
                    ),
                ),
                "SIDE_EFFECT_EXECUTION_DENIED",
                "side-effect execution flag",
            )

            execution_source = "\n".join(
                self._read(path)
                for path in (self.root / "src" / "ultimate_ai_agent" / "core" / "execution").glob("*.py")
            ).lower()
            forbidden_fragments = (
                "os.system(",
                "popen(",
                "shell=true",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
                "append_event(",
                "mutate_event(",
                "chat.completions.create(",
                "import " + "openai",
                "import " + "anthropic",
                "import " + "ollama",
            )
            failures.extend(
                f"M30 Multi-Step Execution Framework module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in execution_source
            )
        except Exception as exc:
            failures.append(f"M30 Multi-Step Execution Framework validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m30_execution_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m30_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M30 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m30_m31_remains_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/execution/M30_TO_M31_BOUNDARY.md",
        ]
        failures = [f"missing M30 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.34.0" in text and "multi-step execution framework" in text:
            if "implemented/released" not in text:
                failures.append("M30 docs do not mark v0.34.0 implemented/released")
        else:
            failures.append("M30 docs do not mention v0.34.0 Multi-Step Execution Framework")
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple >= (0, 35, 0):
            if "m31" not in text or "real tool runtime adapter" not in text or "implemented/released" not in text:
                failures.append("M30 docs do not acknowledge implemented v0.35.0 / M31")
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append("M34-M60 must remain planned/provisional after v0.37.4")
            elif "m32-m40 remain planned/provisional" not in text:
                failures.append("M32-M40 must remain planned/provisional after M31")
        else:
            if "m31-m40 remain planned/provisional" not in text:
                failures.append("M31-M40 must remain planned/provisional after M30")
            forbidden_m31_fragments = (
                "m31 is implemented",
                "v0.35.0 implements m31",
                "native client contract is implemented",
                "ccc ios is implemented",
                "ccc android is implemented",
                "ccc macos is implemented",
            )
            failures.extend(
                f"M30 docs imply M31 implementation: {fragment}"
                for fragment in forbidden_m31_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m31_tool_runtime_noop_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/runtime/__init__.py",
            "src/ultimate_ai_agent/core/tools/runtime/adapters.py",
            "src/ultimate_ai_agent/core/tools/runtime/contracts.py",
            "src/ultimate_ai_agent/core/tools/runtime/enums.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "src/ultimate_ai_agent/core/tools/runtime/manifests.py",
            "src/ultimate_ai_agent/core/tools/runtime/noop.py",
            "src/ultimate_ai_agent/core/tools/runtime/policy.py",
            "src/ultimate_ai_agent/core/tools/runtime/receipts.py",
            "src/ultimate_ai_agent/core/tools/runtime/validation.py",
            "tests/test_tool_runtime_contracts.py",
            "tests/test_tool_runtime_noop_invocation.py",
            "tests/test_tool_runtime_no_side_effects.py",
            "tests/test_tool_runtime_authority_boundaries.py",
            "tests/test_tool_runtime_replay_protection.py",
            "tests/test_tool_runtime_no_dynamic_dispatch.py",
            "tests/test_m31_gate_integration.py",
            "docs/tools/TOOL_RUNTIME_ADAPTER.md",
            "docs/tools/NOOP_TOOL_RUNTIME.md",
            "docs/tools/TOOL_RUNTIME_INVOCATION_CONTRACT.md",
            "docs/tools/TOOL_RUNTIME_AUTHORITY_BOUNDARY.md",
            "docs/tools/TOOL_RUNTIME_REPLAY_POLICY.md",
            "docs/tools/TOOL_RUNTIME_RECEIPT_PLAN.md",
            "docs/tools/TOOL_RUNTIME_NON_GOALS.md",
            "docs/tools/M31_TO_M32_BOUNDARY.md",
        ]
        failures = [f"missing M31 Tool Runtime file: {path}" for path in required_files if not (self.root / path).exists()]
        try:
            from ultimate_ai_agent.core.tools.runtime import (
                NOOP_TOOL_NAME,
                NOOP_TOOL_REF,
                ToolInvocationRequest,
                ToolInvocationStatus,
                ToolRuntimeAdapter,
                build_tool_runtime_manifest,
                evaluate_tool_invocation,
            )

            manifest = build_tool_runtime_manifest(baseline_version="0.35.1")
            policy = manifest.policy
            forbidden_flags = [
                policy.arbitrary_tool_execution_enabled,
                policy.side_effecting_tools_enabled,
                policy.shell_tools_enabled,
                policy.file_tools_enabled,
                policy.memory_write_tools_enabled,
                policy.network_tools_enabled,
                policy.model_tools_enabled,
                policy.browser_tools_enabled,
                policy.mobile_tools_enabled,
                policy.remote_tools_enabled,
                policy.plugin_tools_enabled,
                policy.dynamic_tool_registration_enabled,
                policy.backend_execute_routes_enabled,
                policy.control_center_execute_controls_enabled,
                policy.production_authority_enabled,
            ]
            if not policy.tool_runtime_enabled or not policy.noop_tool_enabled or any(forbidden_flags):
                failures.append("M31 manifest enables forbidden runtime tool authority")
            if NOOP_TOOL_REF not in manifest.allowlisted_tool_refs:
                failures.append("M31 manifest no longer allowlists the no-op tool")

            safe_request = ToolInvocationRequest(
                invocation_id="tool-runtime-invocation:gate-m31",
                tool_ref=NOOP_TOOL_REF,
                tool_name=NOOP_TOOL_NAME,
                replay_key="tool-runtime-replay:gate-m31",
                safe_summary="Run deterministic no-op tool.",
                input_refs=["canonical:gate-m31"],
            )
            safe_decision = ToolRuntimeAdapter().invoke(safe_request)
            if safe_decision.status != ToolInvocationStatus.noop_completed:
                failures.append("M31 no-op runtime invocation did not complete")
            if not safe_decision.execution_performed or not safe_decision.invocation_allowed:
                failures.append("M31 no-op runtime invocation did not report the no-op invocation")
            if safe_decision.side_effects_performed:
                failures.append("M31 no-op runtime reported side effects")
            if not safe_decision.result or safe_decision.result.output.safe_message != "NOOP_TOOL_COMPLETED":
                failures.append("M31 no-op runtime result envelope is missing or non-deterministic")
            if safe_decision.result and (safe_decision.result.output.raw_input_echoed or safe_decision.result.raw_content_stored):
                failures.append("M31 no-op runtime echoed or stored raw content")

            def require_denial(decision, required_reason: str, label: str) -> None:
                if decision.status == ToolInvocationStatus.noop_completed or decision.execution_performed:
                    failures.append(f"M31 denied probe was allowed: {label}")
                if decision.side_effects_performed:
                    failures.append(f"M31 denied probe reported side effects: {label}")
                if required_reason not in decision.reason_codes:
                    failures.append(f"M31 denied probe missing {required_reason}: {label}")

            require_denial(
                evaluate_tool_invocation(safe_request.model_copy(update={"tool_ref": "tool:file_write.v1"})),
                "TOOL_NOT_ALLOWLISTED_DENIED",
                "file tool ref",
            )
            require_denial(
                evaluate_tool_invocation(safe_request.model_copy(update={"tool_name": "module.callable"})),
                "DYNAMIC_DISPATCH_DENIED",
                "dynamic dispatch tool name",
            )
            require_denial(
                evaluate_tool_invocation(safe_request.model_copy(update={"module_path": "tool_plugins.file_writer"})),
                "DYNAMIC_DISPATCH_DENIED",
                "model_copy module path",
            )
            require_denial(
                evaluate_tool_invocation(safe_request.model_copy(update={"metadata": {"callable_name": "run_noop"}})),
                "DYNAMIC_DISPATCH_DENIED",
                "metadata callable name",
            )
            require_denial(
                evaluate_tool_invocation(safe_request.model_copy(update={"side_effects_performed": ["file:write"]})),
                "SIDE_EFFECT_ATTEMPT_DENIED",
                "model_copy side effect field",
            )
            require_denial(
                evaluate_tool_invocation(safe_request.model_copy(update={"metadata": {"file_write_requested": True}})),
                "SIDE_EFFECT_ATTEMPT_DENIED",
                "metadata side effect field",
            )
            require_denial(
                evaluate_tool_invocation(safe_request.model_copy(update={"approval_ref": "approval:gate-m31"})),
                "APPROVAL_REF_NOT_AUTHORITY",
                "approval_ref alone",
            )
            require_denial(
                evaluate_tool_invocation(safe_request.model_copy(update={"approval_ref": "approval_test_gate_m31"})),
                "APPROVAL_TEST_REF_DENIED",
                "approval_test ref",
            )
            for authority_ref in [
                "task-plan:gate-m31",
                "context-pack:gate-m31",
                "memory:gate-m31",
                "tool-intent:gate-m31",
                "approval:gate-m31",
                "model:gate-m31",
            ]:
                require_denial(
                    evaluate_tool_invocation(safe_request.model_copy(update={"authority_refs": [authority_ref]})),
                    "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY",
                    f"authority ref {authority_ref}",
                )
            require_denial(
                evaluate_tool_invocation(safe_request.model_copy(update={"contains_raw_prompt": True})),
                "RAW_PROMPT_DENIED",
                "raw prompt model_copy revalidation",
            )
            require_denial(
                evaluate_tool_invocation(safe_request.model_copy(update={"metadata": {"token": "abc123"}})),
                "SECRET_CONTENT_DENIED",
                "secret metadata model_copy revalidation",
            )
            require_denial(
                evaluate_tool_invocation(safe_request, replay_keys_seen=["tool-runtime-replay:gate-m31"]),
                "TOOL_RUNTIME_REPLAY_DETECTED",
                "replay key reuse",
            )

            runtime_source = "\n".join(
                self._read(path)
                for path in (self.root / "src" / "ultimate_ai_agent" / "core" / "tools" / "runtime").glob("*.py")
            ).lower()
            forbidden_fragments = (
                "os.system(",
                "popen(",
                "shell=true",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
                "append_event(",
                "mutate_event(",
                "importlib",
                "chat.completions.create(",
                "import " + "openai",
                "import " + "anthropic",
                "import " + "ollama",
            )
            failures.extend(
                f"M31 Tool Runtime module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in runtime_source
            )
        except Exception as exc:
            failures.append(f"M31 Tool Runtime validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m31_tool_runtime_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m31_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M31 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m31_m32_remains_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/tools/M31_TO_M32_BOUNDARY.md",
        ]
        failures = [f"missing M31 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.35.0" not in text or "real tool runtime adapter" not in text or "implemented/released" not in text:
            failures.append("M31 docs do not mark v0.35.0 Real Tool Runtime Adapter implemented/released")
        if "v0.35.1" not in text or "hardens m31" not in text:
            failures.append("M31 docs do not mark v0.35.1 no-op tool runtime hardening")
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple >= (0, 36, 0):
            if "m32 is implemented/released" not in text and "m32 safe local filesystem metadata tool" not in text:
                failures.append("M31/M32 docs do not acknowledge implemented M32")
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append("M34-M60 must remain planned/provisional after v0.37.4")
            elif "m33-m40 remain planned/provisional" not in text:
                failures.append("M33-M40 must remain planned/provisional after M32")
        else:
            if "m32-m40 remain planned/provisional" not in text:
                failures.append("M32-M40 must remain planned/provisional after M31")
            forbidden_m32_fragments = (
                "m32 is implemented",
                "v0.36.0 implements m32",
                "file tools are implemented",
                "network tools are implemented",
                "model tools are implemented",
                "arbitrary tool execution is implemented",
            )
            failures.extend(
                f"M31 docs imply M32 implementation: {fragment}"
                for fragment in forbidden_m32_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m32_filesystem_metadata_tool_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/runtime/filesystem_metadata.py",
            "tests/test_filesystem_metadata_tool_contracts.py",
            "tests/test_filesystem_metadata_path_policy.py",
            "tests/test_filesystem_metadata_authority_boundaries.py",
            "tests/test_m32_gate_integration.py",
            "docs/tools/FILESYSTEM_METADATA_TOOL.md",
            "docs/tools/FILESYSTEM_METADATA_PATH_POLICY.md",
            "docs/tools/FILESYSTEM_METADATA_RESULT_CONTRACT.md",
            "docs/tools/FILESYSTEM_METADATA_AUTHORITY_BOUNDARY.md",
            "docs/tools/FILESYSTEM_METADATA_NON_GOALS.md",
            "docs/tools/M32_TO_M33_BOUNDARY.md",
        ]
        failures = [f"missing M32 filesystem metadata file: {path}" for path in required_files if not (self.root / path).exists()]
        try:
            from ultimate_ai_agent.core.tools.runtime import (
                FILESYSTEM_METADATA_TOOL_NAME,
                FILESYSTEM_METADATA_TOOL_REF,
                NOOP_TOOL_REF,
                REDACTED_FILE_PREVIEW_TOOL_REF,
                FilesystemSafeRoot,
                ToolInvocationKind,
                ToolInvocationRequest,
                ToolInvocationStatus,
                build_tool_runtime_manifest,
                evaluate_tool_invocation,
            )

            manifest = build_tool_runtime_manifest(baseline_version="0.37.1")
            policy = manifest.policy
            forbidden_flags = [
                policy.arbitrary_tool_execution_enabled,
                policy.side_effecting_tools_enabled,
                policy.shell_tools_enabled,
                policy.file_tools_enabled,
                policy.file_content_read_enabled,
                policy.file_preview_enabled,
                policy.file_hash_enabled,
                policy.directory_listing_enabled,
                policy.recursive_traversal_enabled,
                policy.symlink_following_enabled,
                policy.caller_selected_root_enabled,
                policy.file_write_enabled,
                policy.file_delete_enabled,
                policy.memory_write_tools_enabled,
                policy.network_tools_enabled,
                policy.model_tools_enabled,
                policy.browser_tools_enabled,
                policy.mobile_tools_enabled,
                policy.remote_tools_enabled,
                policy.plugin_tools_enabled,
                policy.dynamic_tool_registration_enabled,
                policy.backend_execute_routes_enabled,
                policy.control_center_execute_controls_enabled,
                policy.production_authority_enabled,
            ]
            expected_allowlist = [
                NOOP_TOOL_REF,
                FILESYSTEM_METADATA_TOOL_REF,
                REDACTED_FILE_PREVIEW_TOOL_REF,
            ]
            if manifest.allowlisted_tool_refs != expected_allowlist:
                failures.append("M32 manifest allowlist does not preserve no-op and filesystem metadata")
            if not policy.filesystem_metadata_tool_enabled or any(forbidden_flags):
                failures.append("M32 policy enables forbidden filesystem/content/mutation/runtime authority")

            with tempfile.TemporaryDirectory() as tmp:
                safe_root_path = Path(tmp) / "safe-root"
                safe_root_path.mkdir()
                notes = safe_root_path / "notes"
                notes.mkdir()
                target = notes / "report.md"
                target.write_text("gate metadata only", encoding="utf-8")
                safe_root = FilesystemSafeRoot(
                    root_ref="safe-root:gate-m32",
                    root_path=safe_root_path,
                    safe_label="Gate safe root",
                )
                safe_request = ToolInvocationRequest(
                    invocation_id="tool-runtime-invocation:gate-m32",
                    tool_ref=FILESYSTEM_METADATA_TOOL_REF,
                    tool_name=FILESYSTEM_METADATA_TOOL_NAME,
                    invocation_kind=ToolInvocationKind.filesystem_metadata,
                    replay_key="tool-runtime-replay:gate-m32",
                    safe_summary="Inspect safe filesystem metadata.",
                    metadata={"root_ref": "safe-root:gate-m32", "relative_path": "notes/report.md"},
                )
                safe_decision = evaluate_tool_invocation(safe_request, safe_roots=[safe_root])
                if safe_decision.status != ToolInvocationStatus.metadata_completed or not safe_decision.invocation_allowed:
                    failures.append("M32 safe filesystem metadata request did not complete")
                if safe_decision.side_effects_performed or not safe_decision.result:
                    failures.append("M32 safe filesystem metadata request reported side effects or no result")
                if safe_decision.result:
                    dumped = safe_decision.model_dump()
                    output = safe_decision.result.output
                    if getattr(output, "raw_content_returned", True) or getattr(output, "text_preview_returned", True):
                        failures.append("M32 filesystem metadata output returned raw content or text preview")
                    if getattr(output, "content_hash_returned", True) or getattr(output, "directory_listing_returned", True):
                        failures.append("M32 filesystem metadata output returned content hash or directory listing")
                    if getattr(output, "absolute_path_returned", True) or str(safe_root_path) in str(dumped):
                        failures.append("M32 filesystem metadata output leaked an absolute safe-root path")
                    if "gate metadata only" in str(dumped):
                        failures.append("M32 filesystem metadata output leaked file content")

                def require_denial(decision, required_reason: str, label: str) -> None:
                    if decision.status == ToolInvocationStatus.metadata_completed or decision.execution_performed:
                        failures.append(f"M32 denied probe was allowed: {label}")
                    if decision.side_effects_performed:
                        failures.append(f"M32 denied probe reported side effects: {label}")
                    if required_reason not in decision.reason_codes:
                        failures.append(f"M32 denied probe missing {required_reason}: {label}")

                for relative_path, reason in [
                    ("../outside.md", "PATH_TRAVERSAL_DENIED"),
                    ("notes/%2e%2e/outside.md", "PATH_TRAVERSAL_DENIED"),
                    ("~/notes/report.md", "HOME_PATH_DENIED"),
                    ("C:/Users/report.md", "WINDOWS_PATH_DENIED"),
                    ("notes//report.md", "UNSAFE_PATH_SEPARATOR_DENIED"),
                    (".env", "HIDDEN_PATH_DENIED"),
                    (".git/config", "HIDDEN_PATH_DENIED"),
                    ("notes/token.txt", "SECRET_LIKE_PATH_DENIED"),
                    ("keys/id_rsa", "SECRET_LIKE_PATH_DENIED"),
                    ("keys/private.key", "SECRET_LIKE_PATH_DENIED"),
                    ("notes/*.md", "GLOB_PATH_DENIED"),
                    ("notes/%2A.md", "GLOB_PATH_DENIED"),
                ]:
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m32",
                                        "relative_path": relative_path,
                                    }
                                }
                            ),
                            safe_roots=[safe_root],
                        ),
                        reason,
                        f"path {relative_path}",
                    )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={
                                "metadata": {
                                    "root_ref": "safe-root:gate-m32",
                                    "relative_path": "notes/report.md",
                                    "root_path": str(safe_root_path),
                                }
                            }
                        ),
                        safe_roots=[safe_root],
                    ),
                    "CALLER_SELECTED_ROOT_DENIED",
                    "caller-selected root",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={
                                "metadata": {
                                    "root_ref": "safe-root:missing",
                                    "relative_path": "notes/%2e%2e/outside.md",
                                }
                            }
                        ),
                        safe_roots=[safe_root],
                    ),
                    "PATH_TRAVERSAL_DENIED",
                    "model_copy encoded traversal",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(update={"tool_ref": "tool:file_content_read.v1"}),
                        safe_roots=[safe_root],
                    ),
                    "TOOL_NOT_ALLOWLISTED_DENIED",
                    "model_copy file content tool ref",
                )
                for flag_name, reason in [
                    ("raw_content_enabled", "RAW_FILE_CONTENT_DENIED"),
                    ("file_preview_enabled", "TEXT_PREVIEW_DENIED"),
                    ("file_hash_enabled", "CONTENT_HASH_DENIED"),
                    ("directory_listing_enabled", "DIRECTORY_LISTING_DENIED"),
                    ("recursive_traversal_enabled", "RECURSIVE_TRAVERSAL_DENIED"),
                    ("symlink_following_enabled", "SYMLINK_FOLLOWING_DENIED"),
                    ("file_write_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("file_delete_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("caller_selected_root_enabled", "CALLER_SELECTED_ROOT_DENIED"),
                ]:
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m32",
                                        "relative_path": "notes/report.md",
                                        flag_name: True,
                                    }
                                }
                            ),
                            safe_roots=[safe_root],
                        ),
                        reason,
                        f"metadata alias flag {flag_name}",
                    )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(update={"contains_raw_file_content": True}),
                        safe_roots=[safe_root],
                    ),
                    "RAW_FILE_CONTENT_DENIED",
                    "raw file model_copy revalidation",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(update={"authority_refs": ["model:gate-m32"]}),
                        safe_roots=[safe_root],
                    ),
                    "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY",
                    "model authority ref",
                )
                try:
                    link = safe_root_path / "link.md"
                    link.symlink_to(target)
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m32",
                                        "relative_path": "link.md",
                                    }
                                }
                            ),
                            safe_roots=[safe_root],
                        ),
                        "SYMLINK_DENIED",
                        "symlink path",
                    )
                except (OSError, NotImplementedError):
                    pass

            runtime_source = "\n".join(
                self._read(path)
                for path in (self.root / "src" / "ultimate_ai_agent" / "core" / "tools" / "runtime").glob("*.py")
            ).lower()
            forbidden_fragments = (
                "read_text(",
                "read_bytes(",
                "hashlib",
                ".glob(",
                ".rglob(",
                "os.walk(",
                "follow_symlinks=true",
                "shutil",
                ".unlink(",
                ".remove(",
                ".rename(",
                ".replace(",
                ".chmod(",
                ".chown(",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "os.system(",
                "popen(",
            )
            failures.extend(
                f"M32 filesystem metadata module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in runtime_source
            )
        except Exception as exc:
            failures.append(f"M32 filesystem metadata validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m32_filesystem_metadata_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m32_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M32 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m32_m33_remains_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/tools/M32_TO_M33_BOUNDARY.md",
        ]
        failures = [f"missing M32 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple >= (0, 36, 1):
            if "v0.36.1" not in text or "filesystem metadata path safety" not in text:
                failures.append("M32 docs do not mark v0.36.1 filesystem metadata path safety hardening")
        if "safe local filesystem metadata" not in text or "implemented/released" not in text:
            failures.append("M32 docs do not mark safe local filesystem metadata implemented/released")
        if version_tuple >= (0, 37, 0):
            if "m33" not in text or "redacted preview" not in text or "implemented/released" not in text:
                failures.append("M32/M33 docs do not acknowledge implemented M33 redacted preview")
            if version_tuple >= (0, 38, 0):
                if "m34" not in text or "broader file capability review" not in text or "implemented/released" not in text:
                    failures.append("M32/M34 docs do not acknowledge implemented M34 broader file capability review")
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append("M34-M60 must remain planned/provisional after v0.37.4")
        else:
            if "m33-m40 remain planned/provisional" not in text:
                failures.append("M33-M40 must remain planned/provisional after M32")
            forbidden_m33_fragments = (
                "m33 is implemented",
                "v0.37.0 implements m33",
                "mobile approval surface is implemented",
                "mobile sensors are implemented",
            )
            failures.extend(
                f"M32 docs imply M33 implementation: {fragment}"
                for fragment in forbidden_m33_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m33_redacted_file_preview_tool_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/runtime/file_preview.py",
            "tests/test_redacted_file_preview_tool_contracts.py",
            "tests/test_redacted_file_preview_path_policy.py",
            "tests/test_redacted_file_preview_authority_boundaries.py",
            "tests/test_m33_gate_integration.py",
            "docs/tools/REDACTED_FILE_PREVIEW_TOOL.md",
            "docs/tools/REDACTED_FILE_PREVIEW_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md",
            "docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md",
            "docs/tools/M33_TO_M34_BOUNDARY.md",
        ]
        failures = [f"missing M33 redacted file preview file: {path}" for path in required_files if not (self.root / path).exists()]
        try:
            from ultimate_ai_agent.core.tools.runtime import (
                FILESYSTEM_METADATA_TOOL_REF,
                NOOP_TOOL_REF,
                REDACTED_FILE_PREVIEW_TOOL_NAME,
                REDACTED_FILE_PREVIEW_TOOL_REF,
                FilePreviewRedactionSummary,
                FilePreviewSafeRoot,
                RedactedFilePreviewOutput,
                RedactedFilePreviewStatus,
                ToolInvocationKind,
                ToolInvocationRequest,
                ToolInvocationStatus,
                build_tool_runtime_manifest,
                evaluate_tool_invocation,
            )

            manifest = build_tool_runtime_manifest(baseline_version="0.37.1")
            policy = manifest.policy
            if manifest.allowlisted_tool_refs != [NOOP_TOOL_REF, FILESYSTEM_METADATA_TOOL_REF, REDACTED_FILE_PREVIEW_TOOL_REF]:
                failures.append("M33 manifest allowlist is not exactly no-op, filesystem metadata, and redacted preview")
            forbidden_flags = [
                policy.arbitrary_tool_execution_enabled,
                policy.side_effecting_tools_enabled,
                policy.shell_tools_enabled,
                policy.file_tools_enabled,
                policy.file_content_read_enabled,
                policy.file_preview_enabled,
                policy.file_hash_enabled,
                policy.directory_listing_enabled,
                policy.recursive_traversal_enabled,
                policy.symlink_following_enabled,
                policy.caller_selected_root_enabled,
                policy.file_write_enabled,
                policy.file_delete_enabled,
                policy.memory_write_tools_enabled,
                policy.network_tools_enabled,
                policy.model_tools_enabled,
                policy.browser_tools_enabled,
                policy.mobile_tools_enabled,
                policy.remote_tools_enabled,
                policy.plugin_tools_enabled,
                policy.dynamic_tool_registration_enabled,
                policy.backend_execute_routes_enabled,
                policy.control_center_execute_controls_enabled,
                policy.production_authority_enabled,
            ]
            if not policy.redacted_file_preview_tool_enabled or any(forbidden_flags):
                failures.append("M33 policy enables forbidden filesystem/runtime authority")

            with tempfile.TemporaryDirectory() as tmp:
                safe_root_path = Path(tmp) / "safe-root"
                safe_root_path.mkdir()
                notes = safe_root_path / "notes"
                notes.mkdir()
                target = notes / "report.md"
                target.write_text("Title\nAPI_KEY=gate-secret-value\nPublic summary.\n", encoding="utf-8")
                safe_root = FilePreviewSafeRoot(
                    root_ref="safe-root:gate-m33",
                    root_path=safe_root_path,
                    safe_label="Gate safe root",
                )
                safe_request = ToolInvocationRequest(
                    invocation_id="tool-runtime-invocation:gate-m33",
                    tool_ref=REDACTED_FILE_PREVIEW_TOOL_REF,
                    tool_name=REDACTED_FILE_PREVIEW_TOOL_NAME,
                    invocation_kind=ToolInvocationKind.redacted_file_preview,
                    replay_key="tool-runtime-replay:gate-m33",
                    safe_summary="Generate a redacted file preview proposal.",
                    metadata={"root_ref": "safe-root:gate-m33", "relative_path": "notes/report.md"},
                )
                safe_decision = evaluate_tool_invocation(safe_request, safe_roots=[safe_root])
                if safe_decision.status != ToolInvocationStatus.preview_completed or not safe_decision.invocation_allowed:
                    failures.append("M33 safe redacted file preview request did not complete")
                if safe_decision.side_effects_performed or not safe_decision.result:
                    failures.append("M33 safe redacted file preview request reported side effects or no result")
                if safe_decision.result:
                    dumped = safe_decision.model_dump()
                    output = safe_decision.result.output
                    if getattr(output, "status", None) != RedactedFilePreviewStatus.preview_generated:
                        failures.append("M33 redacted preview output status is invalid")
                    if not getattr(output, "redacted_preview_returned", False) or not getattr(output, "redacted_preview", ""):
                        failures.append("M33 redacted preview output did not return a redacted preview")
                    if "gate-secret-value" in str(dumped):
                        failures.append("M33 redacted preview leaked a secret-like value")
                    if str(safe_root_path) in str(dumped):
                        failures.append("M33 redacted preview leaked an absolute safe-root path")
                    unsafe_output_flags = [
                        getattr(output, "raw_content_returned", True),
                        getattr(output, "raw_content_stored", True),
                        getattr(output, "full_file_returned", True),
                        getattr(output, "content_hash_returned", True),
                        getattr(output, "directory_listing_returned", True),
                        getattr(output, "absolute_path_returned", True),
                        getattr(output, "symlink_followed", True),
                        getattr(output, "mutation_performed", True),
                        getattr(output, "context_injection_performed", True),
                    ]
                    if any(unsafe_output_flags):
                        failures.append("M33 redacted preview output returned raw/full/hash/list/mutation/context data")
                    try:
                        RedactedFilePreviewOutput(
                            output_ref="redacted-file-preview-output:gate-unsafe",
                            status=RedactedFilePreviewStatus.preview_generated,
                            root_ref="safe-root:gate-m33",
                            safe_path_ref="filesystem-preview-path:safe-root_gate-m33/notes/report.md",
                            redacted_preview="API_KEY=gate-secret-value",
                            redaction_summary=FilePreviewRedactionSummary(),
                            file_size_bytes=25,
                        )
                        failures.append("M33 redacted preview output accepted unredacted secret-like content")
                    except ValueError as exc:
                        if "REDACTED_FILE_PREVIEW_OUTPUT_CONTAINS_SECRET_LIKE_CONTENT" not in str(exc):
                            failures.append("M33 redacted preview output rejected unsafe content with unexpected reason")

                def require_denial(decision, required_reason: str, label: str) -> None:
                    if decision.status == ToolInvocationStatus.preview_completed or decision.execution_performed:
                        failures.append(f"M33 denied probe was allowed: {label}")
                    if decision.side_effects_performed:
                        failures.append(f"M33 denied probe reported side effects: {label}")
                    if required_reason not in decision.reason_codes:
                        failures.append(f"M33 denied probe missing {required_reason}: {label}")

                for relative_path, reason in [
                    ("/etc/passwd", "ABSOLUTE_PATH_DENIED"),
                    ("../outside.md", "PATH_TRAVERSAL_DENIED"),
                    ("notes/%2e%2e/outside.md", "PATH_TRAVERSAL_DENIED"),
                    (".env", "HIDDEN_PATH_DENIED"),
                    ("notes/token.txt", "SECRET_LIKE_PATH_DENIED"),
                    ("keys/id_rsa", "SECRET_LIKE_PATH_DENIED"),
                    ("notes/*.md", "GLOB_PATH_DENIED"),
                ]:
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={"metadata": {"root_ref": "safe-root:gate-m33", "relative_path": relative_path}}
                            ),
                            safe_roots=[safe_root],
                        ),
                        reason,
                        f"path {relative_path}",
                    )
                directory = safe_root_path / "docs"
                directory.mkdir()
                (directory / "child.md").write_text("child content", encoding="utf-8")
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"metadata": {"root_ref": "safe-root:gate-m33", "relative_path": "docs"}}
                        ),
                        safe_roots=[safe_root],
                    ),
                    "DIRECTORY_PATH_DENIED",
                    "directory path",
                )
                binary = notes / "binary.txt"
                binary.write_bytes(b"hello\x00world")
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"metadata": {"root_ref": "safe-root:gate-m33", "relative_path": "notes/binary.txt"}}
                        ),
                        safe_roots=[safe_root],
                    ),
                    "BINARY_FILE_DENIED",
                    "binary file",
                )
                try:
                    symlink_root_path = Path(tmp) / "safe-root-link"
                    symlink_root_path.symlink_to(safe_root_path, target_is_directory=True)
                    symlink_root = FilePreviewSafeRoot(
                        root_ref="safe-root:gate-m33-link",
                        root_path=symlink_root_path,
                        safe_label="Gate symlink safe root",
                    )
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m33-link",
                                        "relative_path": "notes/report.md",
                                    }
                                }
                            ),
                            safe_roots=[symlink_root],
                        ),
                        "SAFE_ROOT_SYMLINK_DENIED",
                        "symlink safe root",
                    )
                except (OSError, NotImplementedError):
                    pass
                large = notes / "large.md"
                large.write_bytes(b"a" * 70000)
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"metadata": {"root_ref": "safe-root:gate-m33", "relative_path": "notes/large.md"}}
                        ),
                        safe_roots=[safe_root],
                    ),
                    "FILE_TOO_LARGE_DENIED",
                    "oversized file",
                )
                for flag_name, reason in [
                    ("raw_content_enabled", "RAW_FILE_CONTENT_DENIED"),
                    ("full_file_read_enabled", "FULL_FILE_READ_DENIED"),
                    ("content_hash_enabled", "CONTENT_HASH_DENIED"),
                    ("directory_listing_enabled", "DIRECTORY_LISTING_DENIED"),
                    ("recursive_traversal_enabled", "RECURSIVE_TRAVERSAL_DENIED"),
                    ("symlink_following_enabled", "SYMLINK_FOLLOWING_DENIED"),
                    ("file_write_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("file_delete_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("caller_selected_root_enabled", "CALLER_SELECTED_ROOT_DENIED"),
                    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
                ]:
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m33",
                                        "relative_path": "notes/report.md",
                                        flag_name: True,
                                    }
                                }
                            ),
                            safe_roots=[safe_root],
                        ),
                        reason,
                        f"metadata alias flag {flag_name}",
                    )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(update={"contains_raw_file_content": True}),
                        safe_roots=[safe_root],
                    ),
                    "RAW_FILE_CONTENT_DENIED",
                    "raw file model_copy revalidation",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(update={"tool_ref": "tool:filesystem.raw_read.v1"}),
                        safe_roots=[safe_root],
                    ),
                    "TOOL_NOT_ALLOWLISTED_DENIED",
                    "model_copy raw read tool ref",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(update={"authority_refs": ["model:gate-m33"]}),
                        safe_roots=[safe_root],
                    ),
                    "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY",
                    "model authority ref",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(update={"approval_ref": "approval_test_m33"}),
                        safe_roots=[safe_root],
                    ),
                    "APPROVAL_TEST_REF_DENIED",
                    "approval_test ref",
                )
                try:
                    link = safe_root_path / "link.md"
                    link.symlink_to(target)
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={"metadata": {"root_ref": "safe-root:gate-m33", "relative_path": "link.md"}}
                            ),
                            safe_roots=[safe_root],
                        ),
                        "SYMLINK_DENIED",
                        "symlink path",
                    )
                except (OSError, NotImplementedError):
                    pass

            runtime_root = self.root / "src" / "ultimate_ai_agent" / "core" / "tools" / "runtime"
            preview_source = self._read(runtime_root / "file_preview.py").lower()
            forbidden_preview_fragments = (
                "read_text(",
                "read_bytes(",
                "hashlib",
                ".glob(",
                ".rglob(",
                "os.walk(",
                "follow_symlinks=true",
                "shutil",
                ".unlink(",
                ".remove(",
                ".rename(",
                ".replace(",
                ".chmod(",
                ".chown(",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "os.system(",
                "popen(",
                "shell=true",
            )
            failures.extend(
                f"M33 redacted preview module contains forbidden fragment: {fragment}"
                for fragment in forbidden_preview_fragments
                if fragment in preview_source
            )
        except Exception as exc:
            failures.append(f"M33 redacted preview validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m33_redacted_file_preview_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m33_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M33 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m33_m34_remains_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/tools/M33_TO_M34_BOUNDARY.md",
            "docs/files/LOCAL_FILE_REDACTED_PREVIEW_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md",
            "docs/tools/REDACTED_FILE_PREVIEW_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md",
            "docs/tools/REDACTED_FILE_PREVIEW_TOOL.md",
        ]
        failures = [f"missing M33 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "first safe local file read proposal" not in text or "redacted preview" not in text:
            failures.append("M33 docs do not mark redacted file preview proposal implemented/released")
        if "implemented/released" not in text:
            failures.append("M33 docs do not mark M33 implemented/released")
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple >= (0, 38, 0):
            if "m34" not in text or "broader file capability review" not in text or "implemented/released" not in text:
                failures.append("M34 broader file capability review must be implemented/released at v0.38.0+")
            if "m36-m60 remain planned/provisional" not in text:
                failures.append("M36-M60 must remain planned/provisional after M34")
            active_currentness_docs = {
                path: self._read(self.root / path)
                for path in ["README.md", *required_docs]
                if (self.root / path).exists()
            }
            failures.extend(m34_active_currentness_failures(active_currentness_docs))
        elif "m34" not in text or "planned/provisional" not in text:
            failures.append("M34 must remain planned/provisional after M33")
        forbidden_m34_fragments = (
            "full file read is implemented",
            "file write tool is implemented",
            "safe file review workflow is implemented",
            "file review ui is implemented",
            "approval persistence is implemented",
            "context injection is implemented",
        )
        failures.extend(
            f"M33 docs imply M34 implementation: {fragment}"
            for fragment in forbidden_m34_fragments
            if fragment in text
        )
        return self._result(criterion, failures, required_docs)

    def check_m34_broader_file_capability_review_docs_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/files/BROADER_FILE_CAPABILITY_REVIEW.md",
            "docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md",
            "docs/files/FILE_CAPABILITY_RISK_REGISTER.md",
            "docs/files/FILE_CAPABILITY_DECISION_RECORD.md",
            "docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md",
            "docs/files/M34_TO_M35_BOUNDARY.md",
            "docs/control_center/FILE_REVIEW_SURFACE_READINESS.md",
            "docs/tools/FILE_TOOL_CAPABILITY_MATRIX.md",
            "docs/release_notes/v0_38_2.md",
            "docs/archive/releases/v0_38_2/README_IMPORT.md",
            "docs/archive/releases/v0_38_2/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_38_2.md",
            "tests/test_m34_gate_integration.py",
        ]
        failures = [f"missing M34 broader file capability review file: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        current_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in current_version.split(".")[:3])
        required_fragments = {
            "M34 docs must say planning/review only": "planning/review only",
            "M34 docs must say no runtime file capability": "no runtime file capability",
            "M34 docs must say no raw file reads": "no raw file reads",
            "M34 docs must say no file review UI": "no file review ui",
            "M34 docs must say no approval persistence": "no approval persistence",
            "M34 docs must say no context proposal": "no context proposal",
            "M34 docs must say no context injection": "no context injection",
            "M34 docs must say no memory writes": "no memory writes",
            "M34 docs must say no export": "no export",
            "M34 docs must say no execution": "no execution",
            "M34 docs must say no backend routes": "no backend routes",
        }
        if version_tuple < (0, 40, 0):
            required_fragments["M36 must remain planned/provisional"] = "m36 remains planned/provisional"
        if version_tuple >= (0, 39, 0):
            required_fragments["M34 docs must acknowledge M35 implementation"] = "v0.39.0 implements m35"
        else:
            required_fragments["M35 must remain planned/provisional"] = "m35 remains planned/provisional"
        for failure, fragment in required_fragments.items():
            if fragment not in text:
                failures.append(failure)
        forbidden_fragments = (
            "m34 implements safe file review workflow contracts",
            "approval persistence is implemented",
            "review approval capture is implemented",
            "context proposal is implemented",
            "context injection is implemented",
            "memory writes are implemented",
            "raw file export is implemented",
            "execution is implemented",
            "backend file route is implemented",
        )
        if version_tuple < (0, 40, 0):
            forbidden_fragments += (
                "file review ui is implemented",
                "ccc file review surface is implemented",
            )
        failures.extend(
            f"M34 docs imply forbidden implementation: {fragment}"
            for fragment in forbidden_fragments
            if fragment in text
        )
        if version_tuple < (0, 39, 0):
            failures.extend(
                f"M34 docs imply forbidden implementation: {fragment}"
                for fragment in ("safe file review workflow is implemented",)
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m34_file_capability_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m34_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M34 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m34_m35_m36_remain_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/files/M34_TO_M35_BOUNDARY.md",
            "docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md",
            "docs/files/LOCAL_FILE_REDACTED_PREVIEW_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md",
            "docs/tools/REDACTED_FILE_PREVIEW_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md",
            "docs/tools/REDACTED_FILE_PREVIEW_TOOL.md",
        ]
        failures = [f"missing M34/M35 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.38.0" not in text or "m34" not in text or "broader file capability review" not in text:
            failures.append("M34 roadmap docs do not identify v0.38.0 Broader File Capability Review")
        if "m34 is implemented/released" not in text and "m34 is implemented/released by v0.38.0" not in text:
            failures.append("M34 roadmap docs do not mark M34 implemented/released")
        if "planning/docs/verifier" not in text and "planning, architecture review" not in text:
            failures.append("M34 roadmap docs do not constrain M34 to planning/docs/verifier work")
        current_version = self._active_version() or "0.0.0"
        current_tuple = tuple(int(part) for part in current_version.split(".")[:3])
        if current_tuple >= (0, 45, 0):
            if "m41 is implemented/released" not in text and "v0.45.0 implements m41" not in text:
                failures.append("M41 roadmap docs do not mark M41 implemented/released")
            if (
                "m42-m60 remain planned/provisional" not in text
                and "m44-m60 remain planned/provisional" not in text
                and "m45-m60 remain planned/provisional" not in text
                and "m46-m60 remain planned/provisional" not in text
                and "m47-m60 remain planned/provisional" not in text
                and "m48-m60 remain planned/provisional" not in text
                and "m49-m60 remain planned/provisional" not in text
                and "m50-m60 remain planned/provisional" not in text
                and "m51-m60 remain planned/provisional" not in text
                and "m52-m60 remain planned/provisional" not in text
                and "m53-m60 remain planned/provisional" not in text
                and "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M42-M60 through M49-M60 planned/provisional marker missing after M41")
        elif current_tuple >= (0, 44, 0):
            if "m40 is implemented/released" not in text and "v0.44.0 implements m40" not in text:
                failures.append("M40 roadmap docs do not mark M40 implemented/released")
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif current_tuple >= (0, 43, 0):
            if "m39 is implemented/released" not in text and "v0.43.0 implements m39" not in text:
                failures.append("M39 roadmap docs do not mark M39 implemented/released")
            if "m40-m60 remain planned/provisional" not in text:
                failures.append("M40-M60 must remain planned/provisional after M39")
        elif current_tuple >= (0, 42, 0):
            if "m38 is implemented/released" not in text and "v0.42.0 implements m38" not in text:
                failures.append("M38 roadmap docs do not mark M38 implemented/released")
            if "m39-m60 remain planned/provisional" not in text:
                failures.append("M39-M60 must remain planned/provisional after M38")
        elif current_tuple >= (0, 41, 0):
            if "m37 is implemented/released" not in text and "v0.41.0 implements m37" not in text:
                failures.append("M37 roadmap docs do not mark M37 implemented/released")
            if "m38-m60 remain planned/provisional" not in text:
                failures.append("M38-M60 must remain planned/provisional after M37")
        elif current_tuple >= (0, 40, 0):
            if "m36 is implemented/released" not in text and "v0.40.0 implements m36" not in text:
                failures.append("M36 roadmap docs do not mark M36 implemented/released")
            if "m37-m60 remain planned/provisional" not in text:
                failures.append("M37-M60 must remain planned/provisional after M36")
        elif current_tuple >= (0, 39, 0):
            if "m35 is implemented/released" not in text and "v0.39.0 implements m35" not in text:
                failures.append("M35 roadmap docs do not mark M35 implemented/released")
            if "m36-m60 remain planned/provisional" not in text:
                failures.append("M36-M60 must remain planned/provisional after M35")
        elif "m36-m60 remain planned/provisional" not in text:
            failures.append("M36-M60 must remain planned/provisional after M34")
        future_fragments = [
            "approval persistence is implemented",
            "context injection is implemented",
        ]
        if current_tuple < (0, 42, 0):
            future_fragments.append("context proposal is implemented")
        if current_tuple < (0, 40, 0):
            future_fragments.extend(
                [
                    "ccc file review surface is implemented",
                    "m36 is implemented",
                    "v0.40.0 implements m36",
                    "file review ui is implemented",
                ]
            )
        if current_tuple < (0, 41, 0):
            future_fragments.extend(
                [
                    "approval persistence is implemented",
                    "review approval capture is implemented",
                    "m37 is implemented",
                    "v0.41.0 implements m37",
                ]
            )
        if current_tuple < (0, 42, 0):
            future_fragments.extend(
                [
                    "m38 is implemented",
                    "v0.42.0 implements m38",
                ]
            )
        for fragment in future_fragments:
            if fragment in text:
                failures.append(f"M34 docs imply future milestone implementation: {fragment}")
        if current_tuple < (0, 39, 0):
            for fragment in (
                "safe file review workflow is implemented",
                "m35 is implemented",
                "v0.39.0 implements m35",
            ):
                if fragment in text:
                    failures.append(f"M34 docs imply future milestone implementation: {fragment}")
        failures.extend(
            m34_active_currentness_failures(
                {path: self._read(self.root / path) for path in required_docs if (self.root / path).exists()}
            )
        )
        return self._result(criterion, failures, required_docs)

    def check_m35_safe_file_review_workflow_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/file_review/__init__.py",
            "src/ultimate_ai_agent/core/file_review/contracts.py",
            "src/ultimate_ai_agent/core/file_review/enums.py",
            "src/ultimate_ai_agent/core/file_review/workflow.py",
            "docs/files/SAFE_FILE_REVIEW_WORKFLOW.md",
            "docs/files/FILE_REVIEW_PACKET_CONTRACT.md",
            "docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md",
            "docs/files/FILE_REVIEW_AUTHORITY_BOUNDARY.md",
            "docs/files/FILE_REVIEW_RECEIPT_PLAN.md",
            "docs/files/FILE_REVIEW_NON_GOALS.md",
            "docs/files/M35_TO_M36_BOUNDARY.md",
            "docs/release_notes/v0_39_0.md",
            "docs/archive/releases/v0_39_0/README_IMPORT.md",
            "docs/archive/releases/v0_39_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_39_0.md",
            "tests/test_file_review_workflow_contracts.py",
            "tests/test_file_review_packet_validation.py",
            "tests/test_file_review_approval_gate.py",
            "tests/test_file_review_authority_boundaries.py",
            "tests/test_file_review_receipt_plan.py",
            "tests/test_m35_gate_integration.py",
        ]
        failures = [f"missing M35 file review workflow file: {path}" for path in required_files if not (self.root / path).exists()]
        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        current_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in current_version.split(".")[:3])
        required_fragments = {
            "M35 docs must say redacted review packets only": "redacted review packets only",
            "M35 docs must say exact approval binding": "exact approval binding",
            "M35 docs must say review-only": "review-only",
            "M35 docs must say no raw file access": "no raw file access",
            "M35 docs must say no raw content": "no raw content",
            "M35 docs must say no approval capture": "no approval capture",
            "M35 docs must say no approval persistence": "no approval persistence",
            "M35 docs must say no context proposal": "no context proposal",
            "M35 docs must say no context injection": "no context injection",
            "M35 docs must say no memory writes": "no memory writes",
            "M35 docs must say no export": "no export",
            "M35 docs must say no execution": "no execution",
            "M35 docs must say no backend routes": "no backend routes",
        }
        if version_tuple < (0, 40, 0):
            required_fragments["M36 must remain planned/provisional"] = "m36 remains planned/provisional"
        if version_tuple < (0, 41, 0):
            required_fragments["M37 must remain planned/provisional"] = "m37 remains planned/provisional"
        if version_tuple < (0, 42, 0):
            required_fragments["M38 must remain planned/provisional"] = "m38 remains planned/provisional"
        for failure, fragment in required_fragments.items():
            if fragment not in docs_text:
                failures.append(failure)

        try:
            from datetime import timedelta

            from ultimate_ai_agent.core.file_review import (
                FileReviewDecisionStatus,
                UserFileReviewApproval,
                build_file_review_packet,
                evaluate_file_review_gate,
                evaluate_file_review_packet,
            )
            from ultimate_ai_agent.core.time import utc_now
            from ultimate_ai_agent.core.tools.runtime import (
                FilePreviewRedactionSummary,
                RedactedFilePreviewOutput,
                RedactedFilePreviewStatus,
            )

            preview = RedactedFilePreviewOutput(
                output_ref="redacted-file-preview-output:gate",
                status=RedactedFilePreviewStatus.preview_generated,
                root_ref="safe-root:gate",
                safe_path_ref="filesystem-preview-path:safe-root_gate/docs/review.md",
                redacted_preview="Redacted preview only.",
                redaction_summary=FilePreviewRedactionSummary(redaction_count=0, categories=[]),
                file_size_bytes=32,
            )
            packet = build_file_review_packet(
                preview_output=preview,
                actor_ref="user:gate",
                request_ref="file-review-request:gate",
                file_ref="file-ref:gate-review",
                safe_summary="Review a redacted preview packet.",
            )
            packet_decision = evaluate_file_review_packet(packet)
            if packet_decision.status != FileReviewDecisionStatus.packet_valid_for_review:
                failures.append("M35 safe redacted packet was not valid for review")
            if packet_decision.execution_authorized or packet_decision.execution_performed:
                failures.append("M35 packet decision authorized or performed execution")
            raw_packet_decision = evaluate_file_review_packet(packet.model_copy(update={"raw_content": "raw secret"}))
            if "FILE_REVIEW_RAW_CONTENT_DENIED" not in raw_packet_decision.reason_codes:
                failures.append("M35 packet evaluator did not deny model_copy raw_content")
            context_packet_decision = evaluate_file_review_packet(packet.model_copy(update={"context_injection_enabled": True}))
            if "FILE_REVIEW_CONTEXT_INJECTION_DENIED" not in context_packet_decision.reason_codes:
                failures.append("M35 packet evaluator did not deny model_copy context injection flag")

            approval = UserFileReviewApproval(
                approval_ref="file-review-approval:gate",
                actor_ref="user:gate",
                review_packet_ref=packet.review_packet_ref,
                preview_result_ref=packet.source.preview_result_ref,
                redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
                file_ref=packet.source.file_ref,
                safe_path_ref=packet.source.safe_path_ref,
                issued_at=utc_now(),
                expires_at=utc_now() + timedelta(minutes=5),
            )
            allowed_decision = evaluate_file_review_gate(packet, approval=approval, current_time=utc_now())
            if allowed_decision.status != FileReviewDecisionStatus.review_allowed:
                failures.append("M35 exact approval binding did not allow review-only decision")
            if (
                allowed_decision.raw_file_access_authorized
                or allowed_decision.context_injection_authorized
                or allowed_decision.memory_write_authorized
                or allowed_decision.export_authorized
                or allowed_decision.execution_authorized
                or allowed_decision.execution_performed
            ):
                failures.append("M35 exact approval binding granted forbidden authority")
            mismatch_decision = evaluate_file_review_gate(
                packet,
                approval=approval.model_copy(update={"review_packet_ref": "file-review-packet:other"}),
                current_time=utc_now(),
            )
            if "FILE_REVIEW_APPROVAL_PACKET_MISMATCH" not in mismatch_decision.reason_codes:
                failures.append("M35 approval gate did not deny mismatched packet")
            file_ref_mismatch_decision = evaluate_file_review_gate(
                packet.model_copy(update={"source": packet.source.model_copy(update={"file_ref": "file-ref:gate-mutated"})}),
                approval=approval,
                current_time=utc_now(),
            )
            if "FILE_REVIEW_APPROVAL_FILE_REF_MISMATCH" not in file_ref_mismatch_decision.reason_codes:
                failures.append("M35 approval gate did not deny mutated packet file_ref")
            path_ref_mismatch_decision = evaluate_file_review_gate(
                packet.model_copy(
                    update={"source": packet.source.model_copy(update={"safe_path_ref": "filesystem-preview-path:safe-root_gate/docs/mutated.md"})}
                ),
                approval=approval,
                current_time=utc_now(),
            )
            if "FILE_REVIEW_APPROVAL_PATH_REF_MISMATCH" not in path_ref_mismatch_decision.reason_codes:
                failures.append("M35 approval gate did not deny mutated packet safe_path_ref")
            test_ref_decision = evaluate_file_review_gate(
                packet,
                approval=approval.model_copy(update={"approval_ref": "approval_test_gate"}),
                current_time=utc_now(),
            )
            if "FILE_REVIEW_APPROVAL_TEST_REF_DENIED" not in test_ref_decision.reason_codes:
                failures.append("M35 approval gate did not deny approval_test ref")
        except Exception as exc:
            failures.append(f"M35 file review workflow contract probe failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m35_file_review_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            paths = set(app.openapi().get("paths", {}))
            if (self._active_version() or "") >= "0.41.0":
                paths.discard(M37_ALLOWED_CAPTURE_ROUTE)
            failures.extend(m35_openapi_route_failures(paths))
        except Exception as exc:
            failures.append(f"M35 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m35_m36_m37_m38_remain_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        required_docs = [
            "README.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/files/SAFE_FILE_REVIEW_WORKFLOW.md",
            "docs/files/FILE_REVIEW_PACKET_CONTRACT.md",
            "docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md",
            "docs/files/FILE_REVIEW_AUTHORITY_BOUNDARY.md",
            "docs/files/FILE_REVIEW_NON_GOALS.md",
            "docs/files/M35_TO_M36_BOUNDARY.md",
        ]
        failures = [f"missing M35/M36 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.39.0" not in text or "m35" not in text or "safe file review workflow contracts" not in text:
            failures.append("M35 roadmap docs do not identify v0.39.0 Safe File Review Workflow Contracts")
        if "m35 is implemented/released" not in text and "m35 implemented/released" not in text:
            failures.append("M35 roadmap docs do not mark M35 implemented/released")
        if version_tuple < (0, 40, 0) and "m36 remains planned/provisional" not in text:
            failures.append("M36 must remain planned/provisional after M35")
        if version_tuple >= (0, 41, 0):
            if "m37 is implemented/released" not in text and "m37 implemented/released" not in text:
                failures.append("M37 must be implemented/released for active v0.41.0+ docs")
        elif "m37 remains planned/provisional" not in text:
            failures.append("M37 must remain planned/provisional after M35")
        if version_tuple >= (0, 45, 0):
            if "m41 is implemented/released" not in text and "v0.45.0 implements m41" not in text:
                failures.append("M41 must be implemented/released for active v0.45.0+ docs")
            if (
                "m42-m60 remain planned/provisional" not in text
                and "m44-m60 remain planned/provisional" not in text
                and "m45-m60 remain planned/provisional" not in text
                and "m46-m60 remain planned/provisional" not in text
                and "m47-m60 remain planned/provisional" not in text
                and "m48-m60 remain planned/provisional" not in text
                and "m49-m60 remain planned/provisional" not in text
                and "m50-m60 remain planned/provisional" not in text
                and "m51-m60 remain planned/provisional" not in text
                and "m52-m60 remain planned/provisional" not in text
                and "m53-m60 remain planned/provisional" not in text
                and "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M42-M60 through M49-M60 planned/provisional marker missing after M41")
        elif version_tuple >= (0, 44, 0):
            if "m40 is implemented/released" not in text and "v0.44.0 implements m40" not in text:
                failures.append("M40 must be implemented/released for active v0.44.0+ docs")
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif version_tuple >= (0, 43, 0):
            if "m39 is implemented/released" not in text and "v0.43.0 implements m39" not in text:
                failures.append("M39 must be implemented/released for active v0.43.0+ docs")
            if "m40-m60 remain planned/provisional" not in text:
                failures.append("M40-M60 must remain planned/provisional after M39")
        elif version_tuple >= (0, 42, 0):
            if "m38 is implemented/released" not in text and "m38 implemented/released" not in text:
                failures.append("M38 must be implemented/released for active v0.42.0+ docs")
            if "m39-m60 remain planned/provisional" not in text:
                failures.append("M39-M60 must remain planned/provisional after M38")
        elif "m38 remains planned/provisional" not in text:
            failures.append("M38 must remain planned/provisional after M35")
        future_fragments = [
            "ccc file review surface is implemented",
            "m36 is implemented",
            "v0.40.0 implements m36",
        ]
        if version_tuple >= (0, 40, 0):
            future_fragments = []
        future_fragments.extend(["file review ui is implemented"])
        if version_tuple < (0, 41, 0):
            future_fragments.extend(
                [
                    "approval persistence is implemented",
                    "review approval capture is implemented",
                    "m37 is implemented",
                    "v0.41.0 implements m37",
                ]
            )
        if version_tuple < (0, 42, 0):
            future_fragments.extend(
                [
                    "context proposal is implemented",
                    "m38 is implemented",
                    "v0.42.0 implements m38",
                ]
            )
        future_fragments.append("context injection is implemented")
        for fragment in future_fragments:
            if fragment in text:
                failures.append(f"M35 docs imply future milestone implementation: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m36_ccc_file_review_surface_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        if (self._active_version() or "") >= "0.41.0":
            return self._result(criterion, [], ["apps/control-center/src/components/FileReviewSurfacePanel.tsx"])
        required_files = [
            "apps/control-center/src/components/FileReviewSurfacePanel.tsx",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/App.test.tsx",
            "docs/control_center/FILE_REVIEW_SURFACE.md",
            "docs/control_center/FILE_REVIEW_REVIEW_ONLY_POLICY.md",
            "docs/control_center/FILE_REVIEW_MOCK_DATA_POLICY.md",
            "docs/control_center/FILE_REVIEW_BINDING_DISPLAY_POLICY.md",
            "docs/control_center/M36_TO_M37_BOUNDARY.md",
            "tests/test_m36_gate_integration.py",
        ]
        failures = [f"missing M36 file review surface file: {path}" for path in required_files if not (self.root / path).exists()]

        combined = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if (self.root / path).exists()
        )
        required_fragments = {
            "M36 route missing": "/files/review",
            "review-only surface copy missing": "review-only surface",
            "mock non-authoritative copy missing": "mock and non-authoritative",
            "redacted preview display missing": "redacted preview",
            "redaction summary display missing": "redaction summary",
            "review packet ref display missing": "review_packet_ref",
            "safe refs only marker missing": "safe refs only",
            "no mutating request marker missing": "no mutating request is made",
            "preview result ref display missing": "preview_result_ref",
            "redaction summary ref display missing": "redaction_summary_ref",
            "file ref display missing": "file_ref",
            "safe path ref display missing": "safe_path_ref",
            "approval gate contract status missing": "approval gate contract status",
            "receipt plan metadata missing": "receipt plan metadata",
            "no approval capture marker missing": "no_approval_capture",
            "no approval persistence marker missing": "no_approval_persistence",
            "no raw display marker missing": "no_raw_file_display",
            "M37 future marker missing": "m37 remains planned/provisional",
        }
        for message, fragment in required_fragments.items():
            if fragment not in combined:
                failures.append(message)

        component_text = self._read(self.root / "apps/control-center/src/components/FileReviewSurfacePanel.tsx").lower()
        mock_text = self._read(self.root / "apps/control-center/src/mocks/controlCenterData.ts")
        failures.extend(m36_file_review_surface_failures(component_text=component_text, mock_text=mock_text))
        for fragment in (
            "approve",
            "deny",
            "submit",
            "mark reviewed",
            "export",
            "download",
            "copy raw",
            "file picker",
            "root selector",
            "open raw file",
            "context proposal",
            "context injection control",
            "write memory",
            "execute",
            "run tool",
            "call model",
        ):
            if re.search(rf"<button\b[^>]*>\s*{re.escape(fragment)}\s*</button>", component_text, re.IGNORECASE):
                failures.append(f"M36 component exposes forbidden control: {fragment}")

        return self._result(criterion, failures, required_files)

    def check_m36_file_review_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            paths = set(app.openapi().get("paths", {}))
            if (self._active_version() or "") >= "0.41.0":
                paths.discard(M37_ALLOWED_CAPTURE_ROUTE)
            failures.extend(m36_openapi_route_failures(paths))
        except Exception as exc:
            failures.append(f"M36 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m36_m37_m38_remain_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        required_docs = [
            "README.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/control_center/M36_TO_M37_BOUNDARY.md",
            "docs/control_center/FILE_REVIEW_SURFACE.md",
        ]
        failures = [f"missing M36/M37 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.40.0" not in text or "m36" not in text or "ccc file review surface" not in text:
            failures.append("M36 roadmap docs do not identify v0.40.0 CCC File Review Surface")
        if "m36 is implemented/released" not in text and "m36 implemented/released" not in text:
            failures.append("M36 roadmap docs do not mark M36 implemented/released")
        if version_tuple >= (0, 41, 0):
            if "m37 is implemented/released" not in text and "m37 implemented/released" not in text:
                failures.append("M37 must be implemented/released for active v0.41.0+ docs")
        elif "m37 remains planned/provisional" not in text:
            failures.append("M37 must remain planned/provisional after M36")
        if version_tuple >= (0, 45, 0):
            if "m41 is implemented/released" not in text and "v0.45.0 implements m41" not in text:
                failures.append("M41 must be implemented/released for active v0.45.0+ docs")
            if (
                "m42-m60 remain planned/provisional" not in text
                and "m44-m60 remain planned/provisional" not in text
                and "m45-m60 remain planned/provisional" not in text
                and "m46-m60 remain planned/provisional" not in text
                and "m47-m60 remain planned/provisional" not in text
                and "m48-m60 remain planned/provisional" not in text
                and "m49-m60 remain planned/provisional" not in text
                and "m50-m60 remain planned/provisional" not in text
                and "m51-m60 remain planned/provisional" not in text
                and "m52-m60 remain planned/provisional" not in text
                and "m53-m60 remain planned/provisional" not in text
                and "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M42-M60 through M49-M60 planned/provisional marker missing after M41")
        elif version_tuple >= (0, 44, 0):
            if "m40 is implemented/released" not in text and "v0.44.0 implements m40" not in text:
                failures.append("M40 must be implemented/released for active v0.44.0+ docs")
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif version_tuple >= (0, 43, 0):
            if "m39 is implemented/released" not in text and "v0.43.0 implements m39" not in text:
                failures.append("M39 must be implemented/released for active v0.43.0+ docs")
            if "m40-m60 remain planned/provisional" not in text:
                failures.append("M40-M60 must remain planned/provisional after M39")
        elif version_tuple >= (0, 42, 0):
            if "m38 is implemented/released" not in text and "m38 implemented/released" not in text:
                failures.append("M38 must be implemented/released for active v0.42.0+ docs")
            if "m39-m60 remain planned/provisional" not in text:
                failures.append("M39-M60 must remain planned/provisional after M38")
        elif "m38 remains planned/provisional" not in text:
            failures.append("M38 must remain planned/provisional after M36")
        future_fragments = []
        if version_tuple < (0, 41, 0):
            future_fragments.extend(
                [
                    "approval persistence is implemented",
                    "review approval capture is implemented",
                    "m37 is implemented",
                    "v0.41.0 implements m37",
                ]
            )
        if version_tuple < (0, 42, 0):
            future_fragments.extend(
                [
                    "context proposal is implemented",
                    "m38 is implemented",
                    "v0.42.0 implements m38",
                ]
            )
        future_fragments.append("context injection is implemented")
        for fragment in future_fragments:
            if fragment in text:
                failures.append(f"M36 docs imply future milestone implementation: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m37_file_review_approval_capture_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/file_review/approval_capture.py",
            "src/ultimate_ai_agent/core/file_review/__init__.py",
            "tests/test_file_review_approval_capture_contracts.py",
            "tests/test_file_review_approval_store.py",
        ]
        failures = [f"missing M37 approval capture file: {path}" for path in required_files if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_files if (self.root / path).exists())
        required_fragments = {
            "capture request contract missing": "filereviewapprovalcapturerequest",
            "capture record contract missing": "filereviewapprovalrecord",
            "approval store missing": "filereviewapprovalstore",
            "capture evaluator missing": "capture_file_review_approval",
            "safe-ref persistence missing": "safe refs only",
            "raw access denial missing": "raw_file_access_authorized",
            "context proposal denial missing": "context_proposal_authorized",
            "memory write denial missing": "memory_write_authorized",
            "execution denial missing": "execution_authorized",
            "idempotency/replay coverage missing": "idempotent",
        }
        for message, fragment in required_fragments.items():
            if fragment not in text:
                failures.append(message)
        for fragment in (
            "raw_file_access_authorized: bool = true",
            "context_proposal_authorized: bool = true",
            "memory_write_authorized: bool = true",
            "export_authorized: bool = true",
            "execution_authorized: bool = true",
            "execution_performed: bool = true",
        ):
            if fragment in text:
                failures.append(f"M37 contract grants forbidden authority: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m37_file_review_approval_capture_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m37_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M37 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m37_control_center_review_only_approval_capture(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/control-center/src/components/FileReviewSurfacePanel.tsx",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "apps/control-center/src/App.test.tsx",
        ]
        failures = [f"missing M37 Control Center file: {path}" for path in required_files if not (self.root / path).exists()]
        component_text = self._read(self.root / "apps/control-center/src/components/FileReviewSurfacePanel.tsx")
        mock_text = self._read(self.root / "apps/control-center/src/mocks/controlCenterData.ts").lower()
        failures.extend(m37_control_center_surface_failures(component_text))
        normalized_mock_text = mock_text.replace(" ", "").replace("\n", "")
        for fragment in (
            "m37_review_only_capture_surface",
            "safe_ref_persistence_only",
            "no_authority_granted",
            "rawfileaccessauthorized: false",
            "contextproposalauthorized: false",
            "memorywriteauthorized: false",
            "exportauthorized: false",
            "executionauthorized: false",
            "executionperformed: false",
        ):
            if fragment.replace(" ", "") not in normalized_mock_text:
                failures.append(f"M37 mock fixture missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m37_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [f"missing M37 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.41.0" not in text or "m37" not in text or "review approval capture" not in text:
            failures.append("active docs do not identify v0.41.0/M37 Review Approval Capture")
        if "m37 is implemented/released" not in text and "m37 implemented/released" not in text:
            failures.append("active docs do not mark M37 implemented/released")
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split(".")[:3])
        if version_tuple >= (0, 45, 0):
            if "m41 is implemented/released" not in text and "v0.45.0 implements m41" not in text:
                failures.append("active docs do not mark M41 implemented/released")
            if (
                "m42-m60 remain planned/provisional" not in text
                and "m44-m60 remain planned/provisional" not in text
                and "m45-m60 remain planned/provisional" not in text
                and "m46-m60 remain planned/provisional" not in text
                and "m47-m60 remain planned/provisional" not in text
                and "m48-m60 remain planned/provisional" not in text
                and "m49-m60 remain planned/provisional" not in text
                and "m50-m60 remain planned/provisional" not in text
                and "m51-m60 remain planned/provisional" not in text
                and "m52-m60 remain planned/provisional" not in text
                and "m53-m60 remain planned/provisional" not in text
                and "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M42-M60 through M49-M60 planned/provisional marker missing after M41")
        elif version_tuple >= (0, 44, 0):
            if "m40 is implemented/released" not in text and "v0.44.0 implements m40" not in text:
                failures.append("active docs do not mark M40 implemented/released")
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif version_tuple >= (0, 43, 0):
            if "m39 is implemented/released" not in text and "v0.43.0 implements m39" not in text:
                failures.append("active docs do not mark M39 implemented/released")
            if "m40-m60 remain planned/provisional" not in text and "m40 remains planned/provisional" not in text:
                failures.append("M40-M60 must remain planned/provisional after M39")
        elif version_tuple >= (0, 42, 0):
            if "m38 is implemented/released" not in text and "m38 implemented/released" not in text:
                failures.append("active docs do not mark M38 implemented/released")
            if "m39-m60 remain planned/provisional" not in text:
                failures.append("M39-M60 must remain planned/provisional after M38")
        elif "m38 remains planned/provisional" not in text:
            failures.append("M38 must remain planned/provisional after M37")
        future_fragments = [
            "context injection is implemented",
            "raw file reads are implemented",
        ]
        if version_tuple < (0, 42, 0):
            future_fragments.extend(
                [
                    "context proposal is implemented",
                    "m38 is implemented",
                    "v0.42.0 implements m38",
                ]
            )
        elif version_tuple < (0, 43, 0):
            future_fragments.extend(
                [
                    "m39 is implemented",
                    "v0.43.0 implements m39",
                    "m40 is implemented",
                    "v0.44.0 implements m40",
                ]
            )
        for fragment in future_fragments:
            if fragment in text:
                failures.append(f"M37 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m38_safe_context_proposal_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/context_proposal/__init__.py",
            "src/ultimate_ai_agent/core/context_proposal/contracts.py",
            "src/ultimate_ai_agent/core/context_proposal/validation.py",
            "src/ultimate_ai_agent/core/context_proposal/workflow.py",
            "tests/test_safe_context_proposal_contracts.py",
            "tests/test_safe_context_proposal_binding.py",
            "tests/test_safe_context_proposal_no_raw_content.py",
            "tests/test_safe_context_proposal_authority_boundaries.py",
            "tests/test_safe_context_proposal_receipt_plan.py",
        ]
        failures = [f"missing M38 context proposal file: {path}" for path in required_files if not (self.root / path).exists()]
        try:
            from ultimate_ai_agent.core.context_proposal import (
                SafeContextProposalDecisionStatus,
                build_safe_context_proposal_policy,
                evaluate_safe_context_proposal_request,
            )
            from ultimate_ai_agent.core.file_review import (
                FileReviewApprovalCaptureDecisionStatus,
                FileReviewApprovalDecisionKind,
                FileReviewApprovalRecord,
                build_file_review_packet,
            )
            from ultimate_ai_agent.core.tools.runtime import (
                FilePreviewRedactionSummary,
                RedactedFilePreviewOutput,
                RedactedFilePreviewStatus,
            )

            policy = build_safe_context_proposal_policy()
            for field_name in [
                "context_surface_enabled",
                "context_handoff_enabled",
                "context_injection_enabled",
                "openwebui_handoff_enabled",
                "model_call_enabled",
                "memory_write_enabled",
                "export_enabled",
                "execution_enabled",
                "raw_file_access_enabled",
            ]:
                if getattr(policy, field_name):
                    failures.append(f"M38 policy enables forbidden flag: {field_name}")

            preview = RedactedFilePreviewOutput(
                output_ref="redacted-file-preview-output:m38-gate",
                status=RedactedFilePreviewStatus.preview_generated,
                root_ref="safe-root:m38-gate",
                safe_path_ref="filesystem-preview-path:safe-root_m38_gate/docs/review.md",
                redacted_preview="Redacted preview only.",
                redaction_summary=FilePreviewRedactionSummary(redaction_count=0, categories=[]),
                file_size_bytes=32,
            )
            packet = build_file_review_packet(
                preview_output=preview,
                actor_ref="user:m38-gate",
                request_ref="file-review-request:m38-gate",
                file_ref="file-ref:m38-gate-review",
                safe_summary="Review a redacted packet for context proposal.",
            )
            record = FileReviewApprovalRecord(
                approval_ref="file-review-approval-capture:m38-gate",
                actor_ref=packet.source.actor_ref,
                review_packet_ref=packet.review_packet_ref,
                preview_result_ref=packet.source.preview_result_ref,
                redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
                file_ref=packet.source.file_ref,
                safe_path_ref=packet.source.safe_path_ref,
                decision=FileReviewApprovalDecisionKind.approve_review_only,
                status=FileReviewApprovalCaptureDecisionStatus.approved_for_review_only,
                idempotency_key="file-review-approval-idempotency:m38-gate",
                receipt_plan_ref="file-review-approval-capture-receipt:m38-gate",
            )
            allowed = evaluate_safe_context_proposal_request(packet=packet, approval_record=record)
            if allowed.status != SafeContextProposalDecisionStatus.proposal_ready or not allowed.proposal_ready:
                failures.append("M38 safe approved review did not build a proposal")
            if any(
                [
                    allowed.context_injection_authorized,
                    allowed.openwebui_handoff_authorized,
                    allowed.model_call_authorized,
                    allowed.memory_write_authorized,
                    allowed.export_authorized,
                    allowed.execution_authorized,
                    allowed.execution_performed,
                ]
            ):
                failures.append("M38 proposal decision granted forbidden authority")
            denied_ref = evaluate_safe_context_proposal_request(
                packet=packet,
                approval_record=None,
                approval_ref=record.approval_ref,
            )
            if "approval_ref_not_authority" not in denied_ref.reason_codes:
                failures.append("M38 did not deny approval_ref alone")
            denied_test = evaluate_safe_context_proposal_request(
                packet=packet,
                approval_record=record.model_copy(update={"approval_ref": "approval_test_m38"}),
            )
            if "approval_test_ref_denied" not in denied_test.reason_codes:
                failures.append("M38 did not deny approval_test_ ref")
            denied_path = evaluate_safe_context_proposal_request(
                packet=packet,
                approval_record=record.model_copy(
                    update={"safe_path_ref": "filesystem-preview-path:safe-root_m38_gate/docs/mutated.md"}
                ),
            )
            if "path_ref_mismatch" not in denied_path.reason_codes:
                failures.append("M38 did not enforce safe_path_ref binding")
            denied_flag = evaluate_safe_context_proposal_request(
                packet=packet,
                approval_record=record,
                policy_overrides={"context_injection_enabled": True},
            )
            if "context_injection_denied" not in denied_flag.reason_codes:
                failures.append("M38 did not deny model_copy-mutated context injection flag")
        except Exception as exc:
            failures.append(f"M38 context proposal probe failed: {exc}")

        text = "\n".join(self._read(self.root / path).lower() for path in required_files if (self.root / path).exists())
        for fragment in [
            "safecontextproposalpolicy",
            "safecontextproposalrequest",
            "safecontextproposalsource",
            "safecontextproposalbinding",
            "safecontextproposalredactionverification",
            "safecontextproposalsection",
            "safecontextproposaldecision",
            "safecontextproposalreceiptplan",
            "context_injection_enabled: bool = false",
            "openwebui_handoff_enabled: bool = false",
            "memory_write_enabled: bool = false",
            "execution_enabled: bool = false",
        ]:
            if fragment not in text:
                failures.append(f"M38 contracts/tests missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m38_safe_context_proposal_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m38_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M38 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m38_no_control_center_context_surface(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/control-center/src/components/FileReviewSurfacePanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        failures = [f"missing M38 Control Center boundary file: {path}" for path in required_files if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_files if (self.root / path).exists())
        current = tuple(int(part) for part in (self._active_version() or "0.0.0").split(".")[:3])
        forbidden_fragments = [
            "/context/proposals",
            "/context/propose",
            "/context/inject",
            "/openwebui/handoff",
            "context proposal surface",
            "send to openwebui",
            "export context",
        ]
        if current >= (0, 43, 0):
            forbidden_fragments = [
                fragment
                for fragment in forbidden_fragments
                if fragment not in {"/context/proposals", "context proposal surface"}
            ]
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M38 must not add M39/M40 Control Center surface/control: {fragment}")
        for label in [
            "inject context",
            "write memory",
            "export context",
            "execute context",
        ]:
            if re.search(rf"<button\b[^>]*>\s*{re.escape(label)}\s*</button>", text, re.IGNORECASE):
                failures.append(f"M38 must not add M39/M40 Control Center control: {label}")
        return self._result(criterion, failures, required_files)

    def check_m38_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [f"missing M38 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.42.0" not in text or "m38" not in text or "safe context proposal" not in text:
            failures.append("active docs do not identify v0.42.0/M38 Safe Context Proposal")
        if "m38 is implemented/released" not in text and "m38 implemented/released" not in text:
            failures.append("active docs do not mark M38 implemented/released")
        current = tuple(int(part) for part in (self._active_version() or "0.0.0").split(".")[:3])
        if current >= (0, 45, 0):
            if "m41 is implemented/released" not in text and "v0.45.0 implements m41" not in text:
                failures.append("active docs do not mark M41 implemented/released after v0.45.0")
            if (
                "m42-m60 remain planned/provisional" not in text
                and "m44-m60 remain planned/provisional" not in text
                and "m45-m60 remain planned/provisional" not in text
                and "m46-m60 remain planned/provisional" not in text
                and "m47-m60 remain planned/provisional" not in text
                and "m48-m60 remain planned/provisional" not in text
                and "m49-m60 remain planned/provisional" not in text
                and "m50-m60 remain planned/provisional" not in text
                and "m51-m60 remain planned/provisional" not in text
                and "m52-m60 remain planned/provisional" not in text
                and "m53-m60 remain planned/provisional" not in text
                and "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M42-M60 through M49-M60 planned/provisional marker missing after M41")
        elif current >= (0, 44, 0):
            if "m40 is implemented/released" not in text and "v0.44.0 implements m40" not in text:
                failures.append("active docs do not mark M40 implemented/released after v0.44.0")
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif current >= (0, 43, 0):
            if "m39 is implemented/released" not in text and "v0.43.0 implements m39" not in text:
                failures.append("active docs do not mark M39 implemented/released after v0.43.0")
            if "m40 remains planned/provisional" not in text and "m40-m60 remain planned/provisional" not in text:
                failures.append("M40 must remain planned/provisional after M39")
        elif "m39 remains planned/provisional" not in text and "m39-m60 remain planned/provisional" not in text:
            failures.append("M39 must remain planned/provisional after M38")
        forbidden_future = [
            "context injection is implemented",
            "openwebui handoff is implemented",
        ]
        if current < (0, 44, 0):
            forbidden_future.extend(["m40 is implemented", "v0.44.0 implements m40"])
        if current < (0, 43, 0):
            forbidden_future.extend(["m39 is implemented", "v0.43.0 implements m39"])
        for fragment in forbidden_future:
            if fragment in text:
                failures.append(f"M38 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m39_ccc_context_proposal_surface_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/control-center/src/components/ContextProposalSurfacePanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "apps/control-center/src/App.test.tsx",
            "docs/control_center/CONTEXT_PROPOSAL_SURFACE.md",
            "docs/control_center/CONTEXT_PROPOSAL_REVIEW_ONLY_POLICY.md",
            "docs/control_center/CONTEXT_PROPOSAL_MOCK_DATA_POLICY.md",
            "docs/control_center/CONTEXT_PROPOSAL_BINDING_DISPLAY_POLICY.md",
            "docs/control_center/M39_TO_M40_BOUNDARY.md",
        ]
        failures = [f"missing M39 context proposal surface file: {path}" for path in required_files if not (self.root / path).exists()]
        app_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("apps/") and (self.root / path).exists()
        )
        for fragment in [
            "/context/proposals",
            "contextproposalsurfacepanel",
            "m39contextproposals",
            "safe-context-proposal:mock_001",
            "safe proposal sections",
            "exact binding refs",
            "source chain refs",
            "control center output is not authority",
            "openwebui handoff authorized",
            "context injection authorized",
            "memory write authorized",
            "export authorized",
            "execution authorized",
            "rawfileaccessauthorized: false",
            "executionauthorized: false",
        ]:
            normalized = app_text.replace("_", "")
            if fragment not in app_text and fragment not in normalized:
                failures.append(f"M39 Control Center missing safe marker: {fragment}")
        for label in [
            "send to openwebui",
            "inject context",
            "write memory",
            "export context",
            "download context",
            "execute context",
            "call model",
            "open raw file",
        ]:
            if re.search(rf"<button\b[^>]*>\s*{re.escape(label)}\s*</button>", app_text, re.IGNORECASE):
                failures.append(f"M39 Control Center added forbidden control: {label}")
        for forbidden in [
            "/context/propose",
            "/context/inject",
            "/context/handoff",
            "/openwebui/handoff",
            "/memory/write",
            "/tools/execute",
        ]:
            if forbidden in app_text:
                failures.append(f"M39 Control Center references forbidden route/control: {forbidden}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "read-only",
            "proposal-only",
            "mock and non-authoritative",
            "no context handoff",
            "no context injection",
            "no openwebui handoff",
            "no memory writes",
            "no export",
            "no execution",
            "no raw file access",
            "m40 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M39 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m39_context_proposal_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m39_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M39 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m39_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [f"missing M39 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.43.0" not in text or "m39" not in text or "ccc context proposal surface" not in text:
            failures.append("active docs do not identify v0.43.0/M39 CCC Context Proposal Surface")
        if "m39 is implemented/released" not in text and "v0.43.0 implements m39" not in text:
            failures.append("active docs do not mark M39 implemented/released")
        m41_implemented = "v0.45.0 implements m41" in text or "m41 is implemented/released" in text
        m40_implemented = "v0.44.0 implements m40" in text or "m40 is implemented/released" in text
        if m41_implemented:
            if (
                "m42-m60 remain planned/provisional" not in text
                and "m44-m60 remain planned/provisional" not in text
                and "m45-m60 remain planned/provisional" not in text
                and "m46-m60 remain planned/provisional" not in text
                and "m47-m60 remain planned/provisional" not in text
                and "m48-m60 remain planned/provisional" not in text
                and "m49-m60 remain planned/provisional" not in text
                and "m50-m60 remain planned/provisional" not in text
                and "m51-m60 remain planned/provisional" not in text
                and "m52-m60 remain planned/provisional" not in text
                and "m53-m60 remain planned/provisional" not in text
                and "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M42-M60 through M49-M60 planned/provisional marker missing after M41")
        elif m40_implemented:
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif "m40 remains planned/provisional" not in text and "m40-m60 remain planned/provisional" not in text:
            failures.append("M40 must remain planned/provisional after M39")
        for fragment in (
            "context injection is implemented",
            "openwebui handoff is implemented",
        ):
            if fragment in text:
                failures.append(f"M39 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m40_context_handoff_approval_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/context_handoff/__init__.py",
            "src/ultimate_ai_agent/core/context_handoff/contracts.py",
            "src/ultimate_ai_agent/core/context_handoff/validation.py",
            "src/ultimate_ai_agent/core/context_handoff/workflow.py",
            "src/ultimate_ai_agent/core/context_handoff/receipts.py",
            "tests/test_context_handoff_approval_contracts.py",
            "tests/test_context_handoff_approval_binding.py",
            "tests/test_context_handoff_no_injection.py",
            "tests/test_m40_gate_integration.py",
            "docs/context/CONTEXT_HANDOFF_APPROVAL.md",
            "docs/context/CONTEXT_HANDOFF_APPROVAL_BOUNDARY.md",
            "docs/context/CONTEXT_HANDOFF_NO_INJECTION_POLICY.md",
            "docs/context/CONTEXT_HANDOFF_RECEIPT_PLAN.md",
            "docs/context/M40_TO_M41_BOUNDARY.md",
        ]
        failures = [f"missing M40 context handoff approval file: {path}" for path in required_files if not (self.root / path).exists()]
        try:
            from ultimate_ai_agent.core.context_handoff import (
                ContextHandoffApprovalDecisionStatus,
                ContextHandoffApprovalKind,
                ContextHandoffApprovalRequest,
                evaluate_context_handoff_approval,
            )
            from ultimate_ai_agent.core.context_proposal import build_safe_context_proposal
            from ultimate_ai_agent.core.file_review import (
                FileReviewApprovalCaptureDecisionStatus,
                FileReviewApprovalDecisionKind,
                FileReviewApprovalRecord,
                build_file_review_packet,
            )
            from ultimate_ai_agent.core.tools.runtime import (
                FilePreviewRedactionSummary,
                RedactedFilePreviewOutput,
                RedactedFilePreviewStatus,
            )

            preview = RedactedFilePreviewOutput(
                output_ref="redacted-file-preview-output:m40-gate",
                status=RedactedFilePreviewStatus.preview_generated,
                root_ref="safe-root:m40-gate",
                safe_path_ref="filesystem-preview-path:safe-root_m40_gate/docs/review.md",
                redacted_preview="M40 gate redacted preview only.",
                redaction_summary=FilePreviewRedactionSummary(redaction_count=1, categories=["secret_assignment"]),
                file_size_bytes=64,
            )
            packet = build_file_review_packet(
                preview_output=preview,
                actor_ref="user:m40-gate",
                request_ref="file-review-request:m40-gate",
                file_ref="file-ref:m40-gate-review",
                safe_summary="Review a redacted packet for M40 handoff approval.",
            )
            approval_record = FileReviewApprovalRecord(
                approval_ref="file-review-approval-capture:m40-gate",
                actor_ref=packet.source.actor_ref,
                review_packet_ref=packet.review_packet_ref,
                preview_result_ref=packet.source.preview_result_ref,
                redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
                file_ref=packet.source.file_ref,
                safe_path_ref=packet.source.safe_path_ref,
                decision=FileReviewApprovalDecisionKind.approve_review_only,
                status=FileReviewApprovalCaptureDecisionStatus.approved_for_review_only,
                idempotency_key="file-review-approval-idempotency:m40-gate",
                safe_reason="User approved the redacted review packet for review-only follow-up.",
                receipt_plan_ref="file-review-approval-capture-receipt:m40-gate",
            )
            proposal = build_safe_context_proposal(packet=packet, approval_record=approval_record)
            request = ContextHandoffApprovalRequest(
                approval_ref="context-handoff-approval:m40-gate",
                actor_ref=proposal.binding.actor_ref,
                proposal_ref=proposal.proposal_ref,
                approval_record_ref=proposal.source.approval_record_ref,
                review_packet_ref=proposal.binding.review_packet_ref,
                preview_result_ref=proposal.binding.preview_result_ref,
                redaction_summary_ref=proposal.binding.redaction_summary_ref,
                file_ref=proposal.binding.file_ref,
                safe_path_ref=proposal.binding.safe_path_ref,
                decision=ContextHandoffApprovalKind.approve_handoff_review_only,
                idempotency_key="context-handoff-idempotency:m40-gate",
                safe_reason="Approve the safe context proposal for future handoff review only.",
            )
            decision = evaluate_context_handoff_approval(proposal=proposal, request=request)
            if decision.status != ContextHandoffApprovalDecisionStatus.approved_for_handoff_review_only:
                failures.append("M40 safe handoff approval did not produce review-only approval")
            if not decision.handoff_approved_for_review:
                failures.append("M40 safe handoff approval did not preserve review decision")
            for field_name in [
                "handoff_execution_authorized",
                "context_injection_authorized",
                "openwebui_handoff_authorized",
                "model_call_authorized",
                "memory_write_authorized",
                "export_authorized",
                "execution_authorized",
                "context_injection_performed",
                "openwebui_handoff_performed",
                "model_call_performed",
                "memory_write_performed",
                "export_performed",
                "execution_performed",
            ]:
                if getattr(decision, field_name):
                    failures.append(f"M40 decision granted or performed forbidden authority: {field_name}")
            if decision.receipt_plan is None:
                failures.append("M40 approved decision is missing receipt plan")
            elif any(
                getattr(decision.receipt_plan, field_name)
                for field_name in [
                    "receipt_is_authority",
                    "raw_content_stored",
                    "full_file_content_stored",
                    "unredacted_preview_stored",
                    "context_injection_performed",
                    "openwebui_handoff_performed",
                    "model_call_performed",
                    "memory_write_performed",
                    "export_performed",
                    "execution_performed",
                ]
            ):
                failures.append("M40 receipt plan stores raw content or performs authority")
            mutated_proposal = proposal.model_copy(update={"context_injection_enabled": True})
            mutated_decision = evaluate_context_handoff_approval(proposal=mutated_proposal, request=request)
            if "context_injection_denied" not in mutated_decision.reason_codes:
                failures.append("M40 evaluator did not revalidate model_copy-mutated proposal context injection")
            mutated_request = request.model_copy(update={"openwebui_handoff_execution_enabled": True})
            mutated_request_decision = evaluate_context_handoff_approval(proposal=proposal, request=mutated_request)
            if "openwebui_handoff_denied" not in mutated_request_decision.reason_codes:
                failures.append("M40 evaluator did not revalidate model_copy-mutated request OpenWebUI handoff")
            ref_only = evaluate_context_handoff_approval(proposal=None, request_ref="context-handoff-approval:m40-gate")
            if "approval_ref_not_authority" not in ref_only.reason_codes:
                failures.append("M40 approval_ref-alone probe did not fail closed")
            test_ref_request = request.model_copy(update={"approval_ref": "approval_test_m40_gate"})
            test_ref_decision = evaluate_context_handoff_approval(proposal=proposal, request=test_ref_request)
            if "approval_test_ref_denied" not in test_ref_decision.reason_codes:
                failures.append("M40 approval_test_ mutation probe did not fail closed")
            mismatch_request = request.model_copy(update={"proposal_ref": "safe-context-proposal:mismatch"})
            mismatch_decision = evaluate_context_handoff_approval(proposal=proposal, request=mismatch_request)
            if "proposal_ref_mismatch" not in mismatch_decision.reason_codes:
                failures.append("M40 exact proposal binding mismatch probe did not fail closed")
        except Exception as exc:
            failures.append(f"M40 context handoff approval probe failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "exact proposal binding",
            "review-only",
            "no context injection",
            "no openwebui handoff execution",
            "no model calls",
            "no memory writes",
            "no export",
            "no execution",
            "approval_ref alone is not authority",
            "approval_test_ is not runtime authority",
            "evaluator boundaries revalidate",
            "m41 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M40 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m40_context_handoff_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m40_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M40 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m40_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [f"missing M40 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.44.0" not in text or "m40" not in text or "context handoff approval, no injection" not in text:
            failures.append("active docs do not identify v0.44.0/M40 Context Handoff Approval, No Injection")
        if "m40 is implemented/released" not in text and "v0.44.0 implements m40" not in text:
            failures.append("active docs do not mark M40 implemented/released")
        active_version = tuple(int(part) for part in (self._active_version() or "0.0.0").split(".")[:3])
        if active_version >= (0, 45, 0):
            if "m41 is implemented/released" not in text and "v0.45.0 implements m41" not in text:
                failures.append("active docs do not mark M41 implemented/released")
            if (
                "m42-m60 remain planned/provisional" not in text
                and "m44-m60 remain planned/provisional" not in text
                and "m45-m60 remain planned/provisional" not in text
                and "m46-m60 remain planned/provisional" not in text
                and "m47-m60 remain planned/provisional" not in text
                and "m48-m60 remain planned/provisional" not in text
                and "m49-m60 remain planned/provisional" not in text
                and "m50-m60 remain planned/provisional" not in text
                and "m51-m60 remain planned/provisional" not in text
                and "m52-m60 remain planned/provisional" not in text
                and "m53-m60 remain planned/provisional" not in text
                and "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M42-M60 through M49-M60 planned/provisional marker missing after M41")
        elif "m41 remains planned/provisional" not in text and "m41-m60 remain planned/provisional" not in text:
            failures.append("M41-M60 must remain planned/provisional after M40")
        for fragment in (
            "context injection is implemented",
            "openwebui handoff execution is implemented",
        ):
            if fragment in text:
                failures.append(f"M40 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m41_local_prototype_safety_freeze(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "docs/prototype/LOCAL_PROTOTYPE_SAFETY_FREEZE.md",
            "docs/prototype/LOCAL_PROTOTYPE_BROWSER_SMOKE_REVIEW.md",
            "docs/prototype/LOCAL_PROTOTYPE_NO_AUTHORITY_BOUNDARY.md",
            "docs/prototype/M41_TO_M42_BOUNDARY.md",
            "docs/developer/LOCAL_LAUNCHER.md",
            "scripts/dev/uaa_launcher.py",
            "tests/test_m41_gate_integration.py",
            "tests/test_m41_local_prototype_safety_freeze.py",
        ]
        failures = [f"missing M41 local prototype safety freeze file: {path}" for path in required_files if not (self.root / path).exists()]
        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "local prototype safety freeze",
            "localhost-only",
            "review-only",
            "mock/non-authoritative",
            "no raw file browsing",
            "no raw file export",
            "no full-file reads",
            "no arbitrary caller-selected roots",
            "no shell/subprocess",
            "no unrestricted network tools",
            "no provider/model calls as authority",
            "no background workers",
            "no mobile sensors",
            "no plugin enablement",
            "no production authority",
            "no unreviewed memory writes",
            "no automatic context injection",
            "no raw prompt/provider payload exposure",
            "no credentials/cookie handling",
            "no remote execution",
            "no browser automation execution",
            "approval refs are not authority",
            "browser smoke review is local-only",
            "m42 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M41 docs missing safety fragment: {fragment}")

        forbidden_fragments = [
            "raw file browsing is implemented",
            "raw file export is implemented",
            "full-file reads are implemented",
            "shell execution is implemented",
            "network tools are implemented",
            "model calls are authority",
            "background workers are implemented",
            "mobile sensors are implemented",
            "plugin enablement is implemented",
            "production authority is implemented",
            "automatic context injection is implemented",
            "remote execution is implemented",
            "browser automation execution is implemented",
            "approval refs are authority",
        ]
        for fragment in forbidden_fragments:
            if fragment in docs_text:
                failures.append(f"M41 docs imply forbidden capability: {fragment}")

        try:
            launcher_source = self._read(self.root / "scripts/dev/uaa_launcher.py")
            if "SAFE_HOSTS" not in launcher_source or "validate_local_host" not in launcher_source:
                failures.append("M41 launcher safety check cannot prove localhost-only refusal")
            for fragment in ['"127.0.0.1"', '"localhost"', '"::1"']:
                if fragment not in launcher_source:
                    failures.append(f"M41 launcher missing safe host fragment: {fragment}")
            for fragment in ["shell=True", "os." + "system(", "eval(", "ex" + "ec("]:
                if fragment in launcher_source:
                    failures.append(f"M41 launcher contains forbidden shell/dynamic fragment: {fragment}")
        except Exception as exc:
            failures.append(f"M41 launcher safety read failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m41_local_prototype_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m41_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M41 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m41_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [f"missing M41 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.45.0" not in text or "m41" not in text or "local prototype safety freeze" not in text:
            failures.append("active docs do not identify v0.45.0/M41 Local Prototype Safety Freeze")
        if "m41 is implemented/released" not in text and "v0.45.0 implements m41" not in text:
            failures.append("active docs do not mark M41 implemented/released")
        current_tuple = tuple(int(part) for part in (self._active_version() or "0.0.0").split(".")[:3])
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current_tuple >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif current_tuple >= (0, 50, 0):
            if "m47-m60 remain planned/provisional" not in text:
                failures.append("M47-M60 must remain planned/provisional after M46")
        elif current_tuple >= (0, 49, 0):
            if "m46-m60 remain planned/provisional" not in text:
                failures.append("M46-M60 must remain planned/provisional after M45")
        elif current_tuple >= (0, 48, 0):
            if "m45-m60 remain planned/provisional" not in text:
                failures.append("M45-M60 must remain planned/provisional after M44")
        elif current_tuple >= (0, 46, 0):
            if "m44-m60 remain planned/provisional" not in text:
                failures.append("M44-M60 must remain planned/provisional after M43")
        elif "m42-m60 remain planned/provisional" not in text:
            failures.append("M42-M60 must remain planned/provisional after M41")
        forbidden_fragments = ["testflight pipeline is implemented"]
        if current_tuple < (0, 48, 0):
            forbidden_fragments.append("ccc ios skeleton is implemented")
        if current_tuple < (0, 46, 0):
            forbidden_fragments.extend(
                [
                    "m42 is implemented",
                    "v0.46.0 implements m42",
                    "mobile companion product contract refresh is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M41 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m42_mobile_product_contract_refresh(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/MOBILE_COMPANION_PRODUCT_CONTRACT_REFRESH.md",
            "docs/mobile/M42_TO_M43_BOUNDARY.md",
            "docs/release_notes/v0_46_0.md",
            "docs/archive/releases/v0_46_0/README_IMPORT.md",
            "docs/archive/releases/v0_46_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_46_0.md",
            "tests/test_m42_mobile_product_contract_refresh.py",
        ]
        failures = [f"missing M42 mobile product contract refresh file: {path}" for path in required_files if not (self.root / path).exists()]

        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_mobile_product_contract_refresh_only,
                build_default_mobile_product_contract_refresh,
            )

            refresh = build_default_mobile_product_contract_refresh()
            assert_mobile_product_contract_refresh_only(refresh)
            if refresh.milestone != "M42" or refresh.version != "0.46.0":
                failures.append("default M42 mobile product refresh has wrong milestone/version")
            if not refresh.contract_refresh_only:
                failures.append("default M42 mobile product refresh is not contract_refresh_only")
            if not refresh.m43_read_only_api_future or not refresh.m44_ios_skeleton_future:
                failures.append("M42 does not keep M43/M44 future")
            forbidden_flags = [
                refresh.native_app_implemented,
                refresh.mobile_api_implemented,
                refresh.mobile_sensor_access_enabled,
                refresh.os_permission_integration_enabled,
                refresh.background_service_enabled,
                refresh.signing_or_store_workflow_enabled,
                refresh.approval_capture_enabled,
                refresh.approval_execution_enabled,
                refresh.memory_write_enabled,
                refresh.context_injection_enabled,
                refresh.raw_payload_exposure_enabled,
                refresh.production_authority_enabled,
            ]
            if any(forbidden_flags):
                failures.append("default M42 mobile product refresh enables forbidden authority")
        except Exception as exc:
            failures.append(f"M42 mobile product contract validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "mobile companion product contract refresh",
            "planning/docs/contracts/verifier",
            "governance/control",
            "not the agent brain",
            "review-only",
            "read-only",
            "m43 is implemented/released",
            "m44 remains future",
            "no mobile app",
            "no ios app",
            "no android app",
            "no native package",
            "no native build workflow",
            "no signing",
            "no testflight",
            "no backend route",
            "no mobile api route",
            "no approval capture",
            "no approval execution",
            "no mobile sensor access",
            "no os permission integration",
            "no background service",
            "no notification runtime",
            "no raw payload exposure",
            "no memory write",
            "no context injection",
            "no production authority",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M42 docs missing safety fragment: {fragment}")

        forbidden_fragments = [
            "mobile app is implemented",
            "ios app is implemented",
            "android app is implemented",
            "mobile api is implemented",
            "mobile sensors are implemented",
            "approval execution is implemented",
            "production authority is implemented",
        ]
        for fragment in forbidden_fragments:
            if fragment in docs_text:
                failures.append(f"M42 docs imply forbidden/future capability: {fragment}")

        return self._result(criterion, failures, required_files)

    def check_m42_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m42_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M42 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m42_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [f"missing M42 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.46.0" not in text or "m42" not in text or "mobile companion product contract refresh" not in text:
            failures.append("active docs do not identify v0.46.0/M42 Mobile Companion Product Contract Refresh")
        if "m42 is implemented/released" not in text and "v0.46.0 implements m42" not in text:
            failures.append("active docs do not mark M42 implemented/released")
        current_tuple = tuple(int(part) for part in (self._active_version() or "0.0.0").split(".")[:3])
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current_tuple >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif current_tuple >= (0, 50, 0):
            if "m47-m60 remain planned/provisional" not in text:
                failures.append("M47-M60 must remain planned/provisional after M46")
        elif current_tuple >= (0, 49, 0):
            if "m46-m60 remain planned/provisional" not in text:
                failures.append("M46-M60 must remain planned/provisional after M45")
        elif current_tuple >= (0, 48, 0):
            if "m45-m60 remain planned/provisional" not in text:
                failures.append("M45-M60 must remain planned/provisional after M44")
        elif "m44-m60 remain planned/provisional" not in text:
            failures.append("M44-M60 must remain planned/provisional after M43")
        forbidden_fragments = ["testflight pipeline is implemented"]
        if current_tuple < (0, 48, 0):
            forbidden_fragments.append("ccc ios skeleton is implemented")
        if current_tuple < (0, 47, 0):
            forbidden_fragments.extend(
                [
                    "m43 is implemented",
                    "v0.47.0 implements m43",
                    "mobile api boundary is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M42 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m43_mobile_api_boundary_read_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/MOBILE_API_BOUNDARY_READ_ONLY.md",
            "docs/mobile/M43_TO_M44_BOUNDARY.md",
            "docs/release_notes/v0_47_0.md",
            "docs/archive/releases/v0_47_0/README_IMPORT.md",
            "docs/archive/releases/v0_47_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_47_0.md",
            "tests/test_m43_mobile_api_boundary_read_only.py",
        ]
        failures = [
            f"missing M43 mobile API boundary file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_mobile_api_boundary_read_only,
                build_default_mobile_read_only_api_boundary,
            )

            boundary = build_default_mobile_read_only_api_boundary()
            assert_mobile_api_boundary_read_only(boundary)
            if boundary.milestone != "M43" or boundary.version != "0.47.0":
                failures.append("default M43 mobile API boundary has wrong milestone/version")
            if not boundary.boundary_contract_only or not boundary.read_only_boundary:
                failures.append("default M43 mobile API boundary is not contract/read-only")
            if not boundary.redacted_summary_only:
                failures.append("default M43 mobile API boundary is not redacted-summary-only")
            if not boundary.m44_ios_skeleton_future:
                failures.append("M43 does not keep M44 future")
            forbidden_flags = [
                boundary.backend_routes_added,
                boundary.mobile_mutation_enabled,
                boundary.mobile_sensor_access_enabled,
                boundary.approval_capture_enabled,
                boundary.approval_execution_enabled,
                boundary.raw_data_enabled,
                boundary.raw_payload_exposure_enabled,
                boundary.raw_absolute_path_exposure_enabled,
                boundary.context_injection_enabled,
                boundary.memory_write_enabled,
                boundary.export_enabled,
                boundary.execution_enabled,
                boundary.credential_or_cookie_handling_enabled,
                boundary.background_collection_enabled,
                boundary.production_authority_enabled,
            ]
            if any(forbidden_flags):
                failures.append("default M43 mobile API boundary enables forbidden authority")
            if not boundary.endpoints:
                failures.append("default M43 mobile API boundary has no endpoint contracts")
        except Exception as exc:
            failures.append(f"M43 mobile API boundary validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "mobile api boundary, read-only",
            "contract-only",
            "read-only",
            "redacted summary only",
            "planned endpoint refs",
            "no backend route",
            "no mobile mutation",
            "no approval capture",
            "no approval execution",
            "no mobile sensor access",
            "no raw data",
            "no raw payload exposure",
            "no raw absolute path",
            "no credential",
            "no cookie",
            "no context injection",
            "no memory write",
            "no export",
            "no execution",
            "no production authority",
            "m44 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M43 docs missing safety fragment: {fragment}")

        forbidden_fragments = [
            "mobile api route is implemented",
            "mobile mutation is implemented",
            "mobile sensors are implemented",
            "approval execution is implemented",
            "approval capture is implemented",
            "production authority is implemented",
            "m44 is implemented",
        ]
        for fragment in forbidden_fragments:
            if fragment in docs_text:
                failures.append(f"M43 docs imply forbidden/future capability: {fragment}")

        return self._result(criterion, failures, required_files)

    def check_m43_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m43_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M43 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m43_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M43 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.47.0" not in text or "m43" not in text or "mobile api boundary, read-only" not in text:
            failures.append("active docs do not identify v0.47.0/M43 Mobile API Boundary, Read-Only")
        if "m43 is implemented/released" not in text and "v0.47.0 implements m43" not in text:
            failures.append("active docs do not mark M43 implemented/released")
        current_tuple = tuple(int(part) for part in (self._active_version() or "0.0.0").split(".")[:3])
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current_tuple >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif current_tuple >= (0, 50, 0):
            if "m47-m60 remain planned/provisional" not in text:
                failures.append("M47-M60 must remain planned/provisional after M46")
        elif current_tuple >= (0, 49, 0):
            if "m46-m60 remain planned/provisional" not in text:
                failures.append("M46-M60 must remain planned/provisional after M45")
        elif current_tuple >= (0, 48, 0):
            if "m45-m60 remain planned/provisional" not in text:
                failures.append("M45-M60 must remain planned/provisional after M44")
        elif "m44-m60 remain planned/provisional" not in text:
            failures.append("M44-M60 must remain planned/provisional after M43")
        forbidden_fragments = [
            "mobile sensors are implemented",
            "approval execution is implemented",
            "production authority is implemented",
        ]
        if current_tuple < (0, 48, 0):
            forbidden_fragments.extend(
                [
                    "m44 is implemented",
                    "v0.48.0 implements m44",
                    "ccc ios skeleton is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M43 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m44_ccc_ios_skeleton_no_authority(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/ccc-ios/README.md",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/UltimateAIAgentCCCApp.swift",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReadOnlyDashboardView.swift",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/SkeletonFixtures.swift",
            "docs/mobile/CCC_IOS_SKELETON_NO_AUTHORITY.md",
            "docs/mobile/M44_TO_M45_BOUNDARY.md",
            "docs/release_notes/v0_48_0.md",
            "docs/archive/releases/v0_48_0/README_IMPORT.md",
            "docs/archive/releases/v0_48_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_48_0.md",
            "tests/test_m44_ccc_ios_skeleton_no_authority.py",
        ]
        failures = [
            f"missing M44 iOS skeleton file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_ccc_ios_skeleton_no_authority,
                build_default_ccc_ios_skeleton_manifest,
            )

            manifest = build_default_ccc_ios_skeleton_manifest()
            assert_ccc_ios_skeleton_no_authority(manifest)
            if manifest.milestone != "M44" or manifest.version != "0.48.0":
                failures.append("default M44 iOS skeleton manifest has wrong milestone/version")
            if not manifest.source_only_skeleton or not manifest.no_authority:
                failures.append("default M44 iOS skeleton is not source-only/no-authority")
            forbidden_flags = [
                manifest.production_workflow_enabled,
                manifest.signing_or_store_workflow_enabled,
                manifest.native_build_workflow_enabled,
                manifest.network_access_enabled,
                manifest.sensor_access_enabled,
                manifest.os_permission_integration_enabled,
                manifest.approval_capture_enabled,
                manifest.approval_execution_enabled,
                manifest.context_injection_enabled,
                manifest.memory_write_enabled,
                manifest.file_mutation_enabled,
                manifest.execution_enabled,
                manifest.credential_storage_enabled,
                manifest.background_task_enabled,
                manifest.production_authority_enabled,
            ]
            if any(forbidden_flags):
                failures.append("default M44 iOS skeleton enables forbidden authority")
            if not manifest.m45_local_read_only_connection_future:
                failures.append("M44 does not keep M45 future")
        except Exception as exc:
            failures.append(f"M44 iOS skeleton validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "ccc ios skeleton, no authority",
            "source-only",
            "mock-only",
            "read-only",
            "non-authoritative",
            "no xcode project",
            "no swift package",
            "no info.plist",
            "no entitlements",
            "no backend route",
            "no mobile api route runtime",
            "no network",
            "no mobile sensor access",
            "no os permission integration",
            "no approval capture",
            "no approval execution",
            "no context injection",
            "no memory write",
            "no file mutation",
            "no execution",
            "no credential",
            "no background",
            "no production authority",
            "m45 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M44 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m44_ios_skeleton_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        ios_root = self.root / "apps" / "ccc-ios"
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        failures: List[str] = []
        if not swift_root.exists():
            failures.append("M44 Swift source root missing")
            return self._result(criterion, failures, [str(swift_root.relative_to(self.root))])
        for forbidden_path in [
            ios_root / "Package.swift",
            *ios_root.glob("*.xcodeproj"),
            *ios_root.rglob("*.entitlements"),
            *ios_root.rglob("Info.plist"),
        ]:
            if forbidden_path.exists():
                failures.append(f"M44 forbidden native workflow file present: {forbidden_path.relative_to(self.root)}")
        swift_files = sorted(swift_root.rglob("*.swift"))
        if not swift_files:
            failures.append("M44 Swift source files missing")
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M44_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(f"M44 forbidden Swift API fragment present: {fragment}")
        lowered = swift_text.lower()
        for required in ["swiftui", "mock", "non-authoritative", "read-only"]:
            if required not in lowered:
                failures.append(f"M44 Swift source missing required marker: {required}")
        return self._result(
            criterion,
            failures,
            [path.relative_to(self.root).as_posix() for path in swift_files],
        )

    def check_m44_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m44_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M44 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m44_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M44 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.48.0" not in text or "m44" not in text or "ccc ios skeleton, no authority" not in text:
            failures.append("active docs do not identify v0.48.0/M44 CCC iOS Skeleton, No Authority")
        if "m44 is implemented/released" not in text and "v0.48.0 implements m44" not in text:
            failures.append("active docs do not mark M44 implemented/released")
        current_tuple = tuple(int(part) for part in (self._active_version() or "0.0.0").split(".")[:3])
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current_tuple >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif current_tuple >= (0, 50, 0):
            if "m47-m60 remain planned/provisional" not in text:
                failures.append("M47-M60 must remain planned/provisional after M46")
        elif current_tuple >= (0, 49, 0):
            if "m46-m60 remain planned/provisional" not in text:
                failures.append("M46-M60 must remain planned/provisional after M45")
        elif "m45-m60 remain planned/provisional" not in text:
            failures.append("M45-M60 must remain planned/provisional after M44")
        forbidden_fragments = [
            "m45 is implemented",
            "v0.49.0 implements m45",
            "local read-only connection is implemented",
            "testflight pipeline is implemented",
            "mobile sensors are implemented",
            "approval execution is implemented",
            "production authority is implemented",
        ]
        if current_tuple >= (0, 49, 0):
            forbidden_fragments = [
                fragment
                for fragment in forbidden_fragments
                if fragment not in {
                    "m45 is implemented",
                    "v0.49.0 implements m45",
                    "local read-only connection is implemented",
                }
            ]
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M44 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m45_ccc_ios_local_read_only_connection(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/ccc-ios/README.md",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/UltimateAIAgentCCCApp.swift",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReadOnlyDashboardView.swift",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/SkeletonFixtures.swift",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/LocalReadOnlyConnectionModels.swift",
            "docs/mobile/CCC_IOS_LOCAL_READ_ONLY_CONNECTION.md",
            "docs/mobile/M45_TO_M46_BOUNDARY.md",
            "docs/release_notes/v0_49_0.md",
            "docs/archive/releases/v0_49_0/README_IMPORT.md",
            "docs/archive/releases/v0_49_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_49_0.md",
            "tests/test_m45_ccc_ios_local_read_only_connection.py",
            "tests/test_m45_gate_integration.py",
        ]
        failures = [
            f"missing M45 iOS local connection file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_ccc_ios_local_read_only_connection_safe,
                build_default_ccc_ios_local_read_only_connection_manifest,
            )

            manifest = build_default_ccc_ios_local_read_only_connection_manifest()
            assert_ccc_ios_local_read_only_connection_safe(manifest)
            if manifest.milestone != "M45" or manifest.version != "0.49.0":
                failures.append("default M45 local connection manifest has wrong milestone/version")
            if not manifest.local_only or not manifest.read_only:
                failures.append("default M45 local connection is not local-only/read-only")
            forbidden_flags = [
                manifest.connection_runtime_enabled,
                manifest.backend_routes_added,
                manifest.network_runtime_enabled,
                manifest.external_network_enabled,
                manifest.raw_data_enabled,
                manifest.approval_capture_enabled,
                manifest.approval_execution_enabled,
                manifest.context_injection_enabled,
                manifest.memory_write_enabled,
                manifest.file_mutation_enabled,
                manifest.execution_enabled,
                manifest.background_collection_enabled,
                manifest.sensor_access_enabled,
                manifest.credential_or_cookie_handling_enabled,
                manifest.native_build_workflow_enabled,
                manifest.signing_or_store_workflow_enabled,
                manifest.production_authority_enabled,
            ]
            if any(forbidden_flags):
                failures.append("default M45 local connection enables forbidden authority")
            if not manifest.m46_review_receipt_surfaces_future:
                failures.append("M45 does not keep M46 future")
        except Exception as exc:
            failures.append(f"M45 local connection validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "ccc ios local read-only connection",
            "local-only",
            "loopback-only",
            "read-only",
            "redacted summary",
            "non-authoritative",
            "no runtime network call",
            "no backend route",
            "no approval capture",
            "no approval execution",
            "no raw data",
            "no context injection",
            "no memory write",
            "no file mutation",
            "no execution",
            "no background collection",
            "no mobile sensor access",
            "no credential",
            "no production authority",
            "m46 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M45 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m45_ios_local_connection_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        ios_root = self.root / "apps" / "ccc-ios"
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        failures: List[str] = []
        if not swift_root.exists():
            failures.append("M45 Swift source root missing")
            return self._result(criterion, failures, [str(swift_root.relative_to(self.root))])
        for forbidden_path in [
            ios_root / "Package.swift",
            *ios_root.glob("*.xcodeproj"),
            *ios_root.rglob("*.entitlements"),
            *ios_root.rglob("Info.plist"),
            *ios_root.rglob("ExportOptions.plist"),
        ]:
            if forbidden_path.exists():
                failures.append(f"M45 forbidden native workflow file present: {forbidden_path.relative_to(self.root)}")
        swift_files = sorted(swift_root.rglob("*.swift"))
        if not swift_files:
            failures.append("M45 Swift source files missing")
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M45_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(f"M45 forbidden Swift API fragment present: {fragment}")
        lowered = swift_text.lower()
        for required in ["local read-only connection", "loopback-only", "non-authoritative", "no runtime network call"]:
            if required not in lowered:
                failures.append(f"M45 Swift source missing required marker: {required}")
        return self._result(
            criterion,
            failures,
            [path.relative_to(self.root).as_posix() for path in swift_files],
        )

    def check_m45_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m45_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M45 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m45_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M45 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.49.0" not in text or "m45" not in text or "ccc ios local read-only connection" not in text:
            failures.append("active docs do not identify v0.49.0/M45 CCC iOS Local Read-Only Connection")
        if "m45 is implemented/released" not in text and "v0.49.0 implements m45" not in text:
            failures.append("active docs do not mark M45 implemented/released")
        active_version = self._active_version() or "0.0.0"
        current = tuple(int(part) for part in active_version.split(".")[:3])
        if current >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif current >= (0, 50, 0):
            if "m47-m60 remain planned/provisional" not in text:
                failures.append("M47-M60 must remain planned/provisional after M46")
        elif "m46-m60 remain planned/provisional" not in text:
            failures.append("M46-M60 must remain planned/provisional after M45")
        forbidden_fragments: list[str] = []
        if current < (0, 50, 0):
            forbidden_fragments.extend(
                [
                    "m46 is implemented",
                    "v0.50.0 implements m46",
                    "review/receipt read-only surfaces are implemented",
                ]
            )
        forbidden_fragments.extend(
            [
                "testflight pipeline is implemented",
                "mobile sensors are implemented",
                "approval execution is implemented",
                "production authority is implemented",
            ]
        )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M45 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m46_ccc_ios_review_receipt_read_only_surfaces(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReviewReceiptReadOnlyModels.swift",
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/CCC_IOS_REVIEW_RECEIPT_READ_ONLY_SURFACES.md",
            "docs/mobile/M46_TO_M47_BOUNDARY.md",
            "tests/test_m46_ccc_ios_review_receipt_read_only_surfaces.py",
        ]
        failures = [
            f"missing M46 review/receipt file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_ccc_ios_review_receipt_read_only_surfaces_safe,
                build_default_ccc_ios_review_receipt_read_only_surface_manifest,
            )

            manifest = build_default_ccc_ios_review_receipt_read_only_surface_manifest()
            assert_ccc_ios_review_receipt_read_only_surfaces_safe(manifest)
        except Exception as exc:
            failures.append(f"M46 review/receipt surface validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "ios review/receipt read-only surfaces",
            "source-only",
            "read-only",
            "redacted summary",
            "mock",
            "non-authoritative",
            "no runtime network call",
            "no backend route",
            "no approval capture",
            "no approval execution",
            "no raw data",
            "no context injection",
            "no memory write",
            "no file mutation",
            "no export",
            "no execution",
            "no background collection",
            "no mobile sensor access",
            "no credential",
            "no production authority",
            "m47 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M46 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m46_ios_review_receipt_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        ios_root = self.root / "apps" / "ccc-ios"
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        failures: List[str] = []
        if not swift_root.exists():
            failures.append("M46 Swift source root missing")
            return self._result(criterion, failures, [str(swift_root.relative_to(self.root))])
        for forbidden_path in [
            ios_root / "Package.swift",
            *ios_root.glob("*.xcodeproj"),
            *ios_root.rglob("*.entitlements"),
            *ios_root.rglob("Info.plist"),
            *ios_root.rglob("ExportOptions.plist"),
            *ios_root.rglob("*.mobileprovision"),
        ]:
            if forbidden_path.exists():
                failures.append(f"M46 forbidden native workflow file present: {forbidden_path.relative_to(self.root)}")
        swift_files = sorted(swift_root.rglob("*.swift"))
        if not swift_files:
            failures.append("M46 Swift source files missing")
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M46_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(f"M46 forbidden Swift API fragment present: {fragment}")
        lowered = swift_text.lower()
        for required in [
            "review/receipt read-only surfaces",
            "redacted review packet summary",
            "redacted receipt summary",
            "mock non-authoritative",
            "no approval capture",
            "no raw data",
            "no runtime network call",
        ]:
            if required not in lowered:
                failures.append(f"M46 Swift source missing required marker: {required}")
        return self._result(
            criterion,
            failures,
            [path.relative_to(self.root).as_posix() for path in swift_files],
        )

    def check_m46_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m46_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M46 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m46_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M46 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.50.0" not in text or "m46" not in text or "ios review/receipt read-only surfaces" not in text:
            failures.append("active docs do not identify v0.50.0/M46 iOS Review/Receipt Read-Only Surfaces")
        if "m46 is implemented/released" not in text and "v0.50.0 implements m46" not in text:
            failures.append("active docs do not mark M46 implemented/released")
        current_tuple = tuple(int(part) for part in (self._active_version() or "0.0.0").split(".")[:3])
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current_tuple >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif "m47-m60 remain planned/provisional" not in text:
            failures.append("M47-M60 must remain planned/provisional after M46")
        forbidden_fragments = [
            "testflight pipeline is implemented",
            "mobile approval capture is implemented",
            "mobile sensors are implemented",
            "background collection is implemented",
            "production authority is implemented",
        ]
        if current_tuple < (0, 51, 0):
            forbidden_fragments.extend(["m47 is implemented", "v0.51.0 implements m47"])
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M46 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m47_internal_testflight_pipeline_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/TESTFLIGHT_PIPELINE_INTERNAL_ONLY.md",
            "docs/mobile/M47_TO_M48_BOUNDARY.md",
            "tests/test_m47_testflight_pipeline_internal_only.py",
        ]
        failures = [
            f"missing M47 TestFlight pipeline file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_internal_testflight_pipeline_safe,
                build_default_internal_testflight_pipeline_manifest,
            )

            manifest = build_default_internal_testflight_pipeline_manifest()
            assert_internal_testflight_pipeline_safe(manifest)
        except Exception as exc:
            failures.append(f"M47 TestFlight pipeline validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "testflight pipeline, internal only",
            "internal-only",
            "contract",
            "checklist",
            "no build execution",
            "no upload execution",
            "no signing asset storage",
            "no app store connect api",
            "no external beta",
            "no public distribution",
            "no production authority",
            "m48 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M47 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m47_testflight_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        ios_root = self.root / "apps" / "ccc-ios"
        failures: List[str] = []
        forbidden_paths = [
            ios_root / "Package.swift",
            *ios_root.glob("*.xcodeproj"),
            *ios_root.rglob("*.xcworkspace"),
            *ios_root.rglob("*.entitlements"),
            *ios_root.rglob("Info.plist"),
            *ios_root.rglob("ExportOptions.plist"),
            *ios_root.rglob("*.mobileprovision"),
            *ios_root.rglob("*.p8"),
            *ios_root.rglob("*.cer"),
            *ios_root.rglob("*.p12"),
        ]
        if (self.root / ".github").exists():
            forbidden_paths.extend((self.root / ".github").rglob("*testflight*"))
        for forbidden_path in forbidden_paths:
            if forbidden_path.exists():
                failures.append(f"M47 forbidden pipeline artifact present: {forbidden_path.relative_to(self.root)}")
        for forbidden_dir in [
            self.root / "fastlane",
            ios_root / "fastlane",
            ios_root / "DerivedData",
        ]:
            if forbidden_dir.exists():
                failures.append(f"M47 forbidden build/upload directory present: {forbidden_dir.relative_to(self.root)}")
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        swift_files = sorted(swift_root.rglob("*.swift")) if swift_root.exists() else []
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M47_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(f"M47 forbidden Swift pipeline fragment present: {fragment}")
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            ios_root,
        ]
        enabled = "{}=True".format
        forbidden_source_fragments = [
            enabled("build_execution_enabled"),
            enabled("upload_execution_enabled"),
            enabled("signing_asset_storage_enabled"),
            enabled("signing_identity_configured"),
            enabled("provisioning_profile_configured"),
            enabled("app_store_connect_api_enabled"),
            enabled("credentials_or_cookies_handling_enabled"),
            enabled("external_beta_enabled"),
            enabled("public_distribution_enabled"),
            enabled("production_authority_enabled"),
            enabled("mobile_sensor_access_enabled"),
            enabled("background_collection_enabled"),
            enabled("approval_execution_enabled"),
            enabled("context_injection_enabled"),
            enabled("memory_write_enabled"),
            enabled("executes_build"),
            enabled("uploads_build"),
            enabled("calls_app_store_connect"),
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel == "src/ultimate_ai_agent/core/gate/evaluators.py":
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M47 forbidden enabled flag in {rel}: {fragment}")
        return self._result(
            criterion,
            failures,
            [path.relative_to(self.root).as_posix() for path in swift_files],
        )

    def check_m47_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m47_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M47 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m47_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M47 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.51.0" not in text or "m47" not in text or "testflight pipeline, internal only" not in text:
            failures.append("active docs do not identify v0.51.0/M47 TestFlight Pipeline, Internal Only")
        if "m47 is implemented/released" not in text and "v0.51.0 implements m47" not in text:
            failures.append("active docs do not mark M47 implemented/released")
        current_tuple = tuple(int(part) for part in (self._active_version() or "0.0.0").split(".")[:3])
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif "m48-m60 remain planned/provisional" not in text:
            failures.append("M48-M60 must remain planned/provisional after M47")
        forbidden_fragments = [
            "mobile approval capture is implemented",
            "mobile sensors are implemented",
            "production authority is implemented",
        ]
        if current_tuple < (0, 52, 0):
            forbidden_fragments.extend(
                [
                    "m48 is implemented",
                    "v0.52.0 implements m48",
                    "first internal testflight build is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M47 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m48_first_internal_testflight_build_candidate(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/FIRST_INTERNAL_TESTFLIGHT_BUILD.md",
            "docs/mobile/M48_TO_M49_BOUNDARY.md",
            "tests/test_m48_first_internal_testflight_build.py",
        ]
        failures = [
            f"missing M48 first internal TestFlight build file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_first_internal_testflight_build_candidate_safe,
                build_default_first_internal_testflight_build_candidate,
            )

            candidate = build_default_first_internal_testflight_build_candidate()
            assert_first_internal_testflight_build_candidate_safe(candidate)
        except Exception as exc:
            failures.append(f"M48 first internal TestFlight build candidate validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "first internal testflight build",
            "build candidate",
            "review-only",
            "internal-only",
            "no committed build artifact",
            "no ipa",
            "no signing material",
            "no app store connect",
            "no testflight upload",
            "no external beta",
            "no production authority",
            "m49 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M48 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m48_testflight_build_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        ios_root = self.root / "apps" / "ccc-ios"
        failures: List[str] = []
        forbidden_paths = [
            ios_root / "Package.swift",
            *ios_root.glob("*.xcodeproj"),
            *ios_root.rglob("*.xcworkspace"),
            *ios_root.rglob("*.entitlements"),
            *ios_root.rglob("Info.plist"),
            *ios_root.rglob("ExportOptions.plist"),
            *ios_root.rglob("*.xcarchive"),
            *ios_root.rglob("*.ipa"),
            *ios_root.rglob("*.mobileprovision"),
            *ios_root.rglob("*.p8"),
            *ios_root.rglob("*.cer"),
            *ios_root.rglob("*.p12"),
        ]
        if (self.root / ".github").exists():
            forbidden_paths.extend((self.root / ".github").rglob("*testflight*"))
            forbidden_paths.extend((self.root / ".github").rglob("*app-store-connect*"))
        for forbidden_path in forbidden_paths:
            if forbidden_path.exists():
                failures.append(f"M48 forbidden build/signing artifact present: {forbidden_path.relative_to(self.root)}")
        for forbidden_dir in [
            self.root / "fastlane",
            ios_root / "fastlane",
            ios_root / "DerivedData",
            ios_root / "Archives",
            ios_root / "build",
            ios_root / "dist",
        ]:
            if forbidden_dir.exists():
                failures.append(f"M48 forbidden build/upload directory present: {forbidden_dir.relative_to(self.root)}")
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        swift_files = sorted(swift_root.rglob("*.swift")) if swift_root.exists() else []
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M48_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(f"M48 forbidden Swift build fragment present: {fragment}")
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            ios_root,
        ]
        enabled = "{}=True".format
        forbidden_source_fragments = [
            enabled("build_execution_performed"),
            enabled("archive_created_in_repo"),
            enabled("ipa_created_in_repo"),
            enabled("testflight_upload_performed"),
            enabled("app_store_connect_api_called"),
            enabled("signing_asset_storage_enabled"),
            enabled("signing_identity_material_stored"),
            enabled("provisioning_profile_material_stored"),
            enabled("certificate_or_private_key_stored"),
            enabled("fastlane_workflow_enabled"),
            enabled("ci_upload_workflow_enabled"),
            enabled("external_beta_enabled"),
            enabled("public_distribution_enabled"),
            enabled("production_authority_enabled"),
            enabled("mobile_sensor_access_enabled"),
            enabled("background_collection_enabled"),
            enabled("approval_execution_enabled"),
            enabled("context_injection_enabled"),
            enabled("memory_write_enabled"),
            enabled("raw_data_export_enabled"),
            enabled("export_enabled"),
            enabled("execution_enabled"),
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in {
                    "src/ultimate_ai_agent/core/gate/evaluators.py",
                    "tests/test_m48_first_internal_testflight_build.py",
                    "tests/test_m48_gate_integration.py",
                }:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M48 forbidden enabled flag in {rel}: {fragment}")
        return self._result(
            criterion,
            failures,
            [path.relative_to(self.root).as_posix() for path in swift_files],
        )

    def check_m48_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m48_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M48 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m48_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M48 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.52.0" not in text or "m48" not in text or "first internal testflight build" not in text:
            failures.append("active docs do not identify v0.52.0/M48 First Internal TestFlight Build")
        if "m48 is implemented/released" not in text and "v0.52.0 implements m48" not in text:
            failures.append("active docs do not mark M48 implemented/released")
        self._append_post_m48_mobile_status_failures(text, failures)
        forbidden_fragments = [
            "mobile approval execution is implemented",
            "mobile sensors are implemented",
            "external beta is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 53, 0):
            forbidden_fragments.extend(
                [
                    "m49 is implemented",
                    "v0.53.0 implements m49",
                    "mobile review approval capture is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M48 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m49_mobile_review_approval_capture(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/MOBILE_REVIEW_APPROVAL_CAPTURE.md",
            "docs/mobile/M49_TO_M50_BOUNDARY.md",
            "tests/test_m49_mobile_review_approval_capture.py",
        ]
        failures = [
            f"missing M49 mobile review approval capture file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from datetime import timedelta

            from ultimate_ai_agent.core.mobile_companion import (
                MobileReviewApprovalCaptureDecisionStatus,
                MobileReviewApprovalDecisionKind,
                MobileReviewApprovalCaptureRequest,
                capture_mobile_review_approval,
            )
            from ultimate_ai_agent.core.time import utc_now

            now = utc_now()
            request = MobileReviewApprovalCaptureRequest(
                approval_ref="mobile-review-approval-capture:gate",
                actor_ref="user:foundation-gate-mobile-reviewer",
                mobile_surface_ref="ccc-ios-review-surface:gate",
                review_packet_ref="file-review-packet:gate-mobile-review",
                preview_result_ref="redacted-file-preview-output:gate-mobile-review",
                redaction_summary_ref="file-review-redaction-summary:gate-mobile-review",
                file_ref="file-ref:gate-mobile-review",
                safe_path_ref="filesystem-preview-path:safe-root_mobile/gate/review.md",
                receipt_plan_ref="mobile-review-receipt-plan:gate-mobile-review",
                decision=MobileReviewApprovalDecisionKind.approve_review_only,
                idempotency_key="mobile-review-approval-idempotency:gate-mobile-review",
                expected_actor_ref="user:foundation-gate-mobile-reviewer",
                expected_mobile_surface_ref="ccc-ios-review-surface:gate",
                expected_review_packet_ref="file-review-packet:gate-mobile-review",
                expected_preview_result_ref="redacted-file-preview-output:gate-mobile-review",
                expected_redaction_summary_ref="file-review-redaction-summary:gate-mobile-review",
                expected_file_ref="file-ref:gate-mobile-review",
                expected_safe_path_ref="filesystem-preview-path:safe-root_mobile/gate/review.md",
                expires_at=now + timedelta(minutes=5),
            )
            decision = capture_mobile_review_approval(request, current_time=now)
            if decision.status != MobileReviewApprovalCaptureDecisionStatus.approved_for_mobile_review_only:
                failures.append("M49 safe mobile review approval capture did not produce review-only approval")
            if not decision.captured or not decision.persisted or not decision.review_only:
                failures.append("M49 safe mobile review approval capture was not captured/persisted as review-only")
            for field_name in [
                "raw_file_access_authorized",
                "context_proposal_authorized",
                "context_injection_authorized",
                "memory_write_authorized",
                "export_authorized",
                "execution_authorized",
                "execution_performed",
            ]:
                if getattr(decision, field_name):
                    failures.append(f"M49 decision granted forbidden authority: {field_name}")

            unsafe = capture_mobile_review_approval(
                request.model_copy(update={"raw_content_enabled": True}),
                current_time=now,
            )
            if unsafe.status != MobileReviewApprovalCaptureDecisionStatus.rejected:
                failures.append("M49 model_copy raw-content mutation was not rejected")
            if "MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED" not in unsafe.reason_codes:
                failures.append("M49 model_copy raw-content rejection reason missing")

            test_ref = capture_mobile_review_approval(
                request.model_copy(update={"approval_ref": "approval_test_m49_gate"}),
                current_time=now,
            )
            if test_ref.status != MobileReviewApprovalCaptureDecisionStatus.rejected:
                failures.append("M49 approval_test_ ref was not rejected")
        except Exception as exc:
            failures.append(f"M49 mobile review approval capture validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile review approval capture",
            "review-only",
            "exact-scope",
            "actor-bound",
            "resource-bound",
            "replay-safe",
            "revocable",
            "safe refs only",
            "no raw file access",
            "no context proposal",
            "no context injection",
            "no memory write",
            "no export",
            "no execution",
            "no mobile sensor access",
            "no background collection",
            "m50 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M49 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m49_mobile_approval_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        ios_root = self.root / "apps" / "ccc-ios"
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        swift_files = sorted(swift_root.rglob("*.swift")) if swift_root.exists() else []
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M49_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(f"M49 forbidden Swift approval/sensor fragment present: {fragment}")

        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            ios_root,
        ]
        enabled = "{}=True".format
        forbidden_source_fragments = [
            enabled("raw_file_access_enabled"),
            enabled("raw_content_enabled"),
            enabled("full_file_content_enabled"),
            enabled("unredacted_preview_enabled"),
            enabled("context_proposal_enabled"),
            enabled("context_injection_enabled"),
            enabled("memory_write_enabled"),
            enabled("export_enabled"),
            enabled("execution_enabled"),
            enabled("approval_execution_enabled"),
            enabled("mobile_sensor_access_enabled"),
            enabled("background_collection_enabled"),
            "/mobile/review/approvals/capture",
            "/mobile/review/approvals/execute",
            "/mobile/context/inject",
            "/mobile/memory/write",
            "/mobile/tools/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
            "tests/test_m49_mobile_review_approval_capture.py",
            "tests/test_m49_gate_integration.py",
        }
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M49 forbidden authority/route fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [path.relative_to(self.root).as_posix() for path in swift_files])

    def check_m49_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m49_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M49 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m49_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M49 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.53.0" not in text or "m49" not in text or "mobile review approval capture" not in text:
            failures.append("active docs do not identify v0.53.0/M49 Mobile Review Approval Capture")
        if "m49 is implemented/released" not in text and "v0.53.0 implements m49" not in text:
            failures.append("active docs do not mark M49 implemented/released")
        if self._active_version_tuple() >= (0, 57, 0):
            if "m50 is implemented/released" not in text and "v0.54.0 implements m50" not in text:
                failures.append("M50 must be implemented/released after v0.54.0")
            if "m51 is implemented/released" not in text and "v0.55.0 implements m51" not in text:
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52 is implemented/released" not in text and "v0.56.0 implements m52" not in text:
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53 is implemented/released" not in text and "v0.57.0 implements m53" not in text:
                failures.append("M53 must be implemented/released after v0.57.0")
            if (
                "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M54-M60 must remain planned/provisional after M53")
        elif self._active_version_tuple() >= (0, 56, 0):
            if "m50 is implemented/released" not in text and "v0.54.0 implements m50" not in text:
                failures.append("M50 must be implemented/released after v0.54.0")
            if "m51 is implemented/released" not in text and "v0.55.0 implements m51" not in text:
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52 is implemented/released" not in text and "v0.56.0 implements m52" not in text:
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53-m60 remain planned/provisional" not in text:
                failures.append("M53-M60 must remain planned/provisional after M52")
        elif self._active_version_tuple() >= (0, 55, 0):
            if "m50 is implemented/released" not in text and "v0.54.0 implements m50" not in text:
                failures.append("M50 must be implemented/released after v0.54.0")
            if "m51 is implemented/released" not in text and "v0.55.0 implements m51" not in text:
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52-m60 remain planned/provisional" not in text:
                failures.append("M52-M60 must remain planned/provisional after M51")
        elif self._active_version_tuple() >= (0, 54, 0):
            if "m50 is implemented/released" not in text and "v0.54.0 implements m50" not in text:
                failures.append("M50 must be implemented/released after v0.54.0")
            if "m51-m60 remain planned/provisional" not in text:
                failures.append("M51-M60 must remain planned/provisional after M50")
        elif "m50-m60 remain planned/provisional" not in text:
            failures.append("M50-M60 must remain planned/provisional after M49")
        forbidden_fragments = [
            "mobile approval execution is implemented",
            "mobile sensors are implemented",
            "context injection is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 54, 0):
            forbidden_fragments.extend(
                [
                    "m50 is implemented",
                    "v0.54.0 implements m50",
                    "mobile approval audit hardening is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M49 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m50_mobile_approval_audit_hardening(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/MOBILE_APPROVAL_AUDIT_HARDENING.md",
            "docs/mobile/M50_TO_M51_BOUNDARY.md",
            "tests/test_m50_mobile_approval_audit_hardening.py",
        ]
        failures = [
            f"missing M50 mobile approval audit file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from datetime import timedelta

            from ultimate_ai_agent.core.mobile_companion import (
                MobileApprovalAuditStatus,
                MobileReviewApprovalDecisionKind,
                MobileReviewApprovalCaptureRequest,
                MobileReviewApprovalStore,
                audit_mobile_review_approval_records,
                audit_mobile_review_approval_store,
                capture_mobile_review_approval,
            )
            from ultimate_ai_agent.core.time import utc_now

            now = utc_now()
            request = MobileReviewApprovalCaptureRequest(
                approval_ref="mobile-review-approval-capture:m50-gate",
                actor_ref="user:m50-mobile-reviewer",
                mobile_surface_ref="ccc-ios-review-surface:m50-gate",
                review_packet_ref="file-review-packet:m50-mobile-review",
                preview_result_ref="redacted-file-preview-output:m50-mobile-review",
                redaction_summary_ref="file-review-redaction-summary:m50-mobile-review",
                file_ref="file-ref:m50-mobile-review",
                safe_path_ref="filesystem-preview-path:safe-root_mobile/m50/review.md",
                receipt_plan_ref="mobile-review-receipt-plan:m50-mobile-review",
                decision=MobileReviewApprovalDecisionKind.approve_review_only,
                idempotency_key="mobile-review-approval-idempotency:m50-mobile-review",
                expected_actor_ref="user:m50-mobile-reviewer",
                expected_mobile_surface_ref="ccc-ios-review-surface:m50-gate",
                expected_review_packet_ref="file-review-packet:m50-mobile-review",
                expected_preview_result_ref="redacted-file-preview-output:m50-mobile-review",
                expected_redaction_summary_ref="file-review-redaction-summary:m50-mobile-review",
                expected_file_ref="file-ref:m50-mobile-review",
                expected_safe_path_ref="filesystem-preview-path:safe-root_mobile/m50/review.md",
                expires_at=now + timedelta(minutes=5),
            )
            store = MobileReviewApprovalStore()
            decision = capture_mobile_review_approval(request, store=store, current_time=now)
            if decision.record is None:
                failures.append("M50 setup capture did not produce a safe record")
            safe_report = audit_mobile_review_approval_store(store)
            if safe_report.status != MobileApprovalAuditStatus.passed:
                failures.append(f"M50 safe audit report did not pass: {safe_report.reason_codes}")
            if safe_report.record_count != 1 or not safe_report.review_only:
                failures.append("M50 safe audit report did not remain review-only over one record")
            for field_name in ["memory_write_performed", "export_performed", "execution_performed"]:
                if getattr(safe_report, field_name):
                    failures.append(f"M50 audit report performed forbidden effect: {field_name}")
            if decision.record is not None:
                raw_report = audit_mobile_review_approval_records(
                    [decision.record.model_copy(update={"raw_content": "secret raw mobile audit"})]
                )
                if raw_report.status != MobileApprovalAuditStatus.failed:
                    failures.append("M50 model_copy raw record was not rejected by audit")
                if "MOBILE_APPROVAL_AUDIT_RAW_CONTENT_DENIED" not in raw_report.reason_codes:
                    failures.append("M50 raw audit rejection reason missing")
                unsafe_report = audit_mobile_review_approval_records(
                    [decision.record.model_copy(update={"execution_enabled": True})]
                )
                if unsafe_report.status != MobileApprovalAuditStatus.failed:
                    failures.append("M50 model_copy execution record was not rejected by audit")
                if "MOBILE_APPROVAL_AUDIT_EXECUTION_DENIED" not in unsafe_report.reason_codes:
                    failures.append("M50 execution audit rejection reason missing")
        except Exception as exc:
            failures.append(f"M50 mobile approval audit validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile approval audit hardening",
            "review-only",
            "safe-ref-only",
            "model_copy",
            "no raw content",
            "no context injection",
            "no memory write",
            "no export",
            "no execution",
            "no mobile sensor access",
            "no backend route",
            "m51 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M50 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m50_mobile_audit_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        ios_root = self.root / "apps" / "ccc-ios"
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        swift_files = sorted(swift_root.rglob("*.swift")) if swift_root.exists() else []
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M50_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(f"M50 forbidden Swift audit/authority fragment present: {fragment}")

        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            ios_root,
        ]
        enabled = "{}=True".format
        forbidden_source_fragments = [
            enabled("raw_file_access_enabled"),
            enabled("raw_content_enabled"),
            enabled("full_file_content_enabled"),
            enabled("unredacted_preview_enabled"),
            enabled("context_proposal_enabled"),
            enabled("context_injection_enabled"),
            enabled("memory_write_enabled"),
            enabled("export_enabled"),
            enabled("execution_enabled"),
            enabled("approval_execution_enabled"),
            enabled("mobile_sensor_access_enabled"),
            enabled("background_collection_enabled"),
            "/mobile/review/audit",
            "/mobile/review/audit/export",
            "/mobile/review/audit/raw",
            "/mobile/approvals/audit/write",
            "/mobile/context/inject",
            "/mobile/memory/write",
            "/mobile/tools/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
            "tests/test_m49_mobile_review_approval_capture.py",
            "tests/test_m49_gate_integration.py",
            "tests/test_m50_mobile_approval_audit_hardening.py",
            "tests/test_m50_gate_integration.py",
        }
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M50 forbidden authority/route fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [path.relative_to(self.root).as_posix() for path in swift_files])

    def check_m50_mobile_audit_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m50_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M50 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m50_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M50 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.54.0" not in text or "m50" not in text or "mobile approval audit hardening" not in text:
            failures.append("active docs do not identify v0.54.0/M50 Mobile Approval Audit Hardening")
        if "m50 is implemented/released" not in text and "v0.54.0 implements m50" not in text:
            failures.append("active docs do not mark M50 implemented/released")
        if self._active_version_tuple() >= (0, 57, 0):
            if "m51 is implemented/released" not in text and "v0.55.0 implements m51" not in text:
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52 is implemented/released" not in text and "v0.56.0 implements m52" not in text:
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53 is implemented/released" not in text and "v0.57.0 implements m53" not in text:
                failures.append("M53 must be implemented/released after v0.57.0")
            if (
                "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M54-M60 must remain planned/provisional after M53")
        elif self._active_version_tuple() >= (0, 56, 0):
            if "m51 is implemented/released" not in text and "v0.55.0 implements m51" not in text:
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52 is implemented/released" not in text and "v0.56.0 implements m52" not in text:
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53-m60 remain planned/provisional" not in text:
                failures.append("M53-M60 must remain planned/provisional after M52")
        elif self._active_version_tuple() >= (0, 55, 0):
            if "m51 is implemented/released" not in text and "v0.55.0 implements m51" not in text:
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52-m60 remain planned/provisional" not in text:
                failures.append("M52-M60 must remain planned/provisional after M51")
        elif "m51-m60 remain planned/provisional" not in text:
            failures.append("M51-M60 must remain planned/provisional after M50")
        forbidden_fragments = [
            "mobile sensors are implemented",
            "context injection is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 55, 0):
            forbidden_fragments.extend(
                [
                    "m51 is implemented",
                    "v0.55.0 implements m51",
                    "openwebui bridge adapter pilot is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M50 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m51_openwebui_bridge_adapter_pilot(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/openwebui_bridge/adapter.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_PILOT.md",
            "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_POLICY.md",
            "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_AUTHORITY_BOUNDARY.md",
            "docs/openwebui/M51_TO_M52_BOUNDARY.md",
            "tests/test_m51_openwebui_bridge_adapter_pilot.py",
        ]
        failures = [
            f"missing M51 OpenWebUI adapter file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.openwebui_bridge import (
                OpenWebUIBridgeAdapterRequest,
                OpenWebUIBridgeAdapterStatus,
                adapt_openwebui_bridge_request,
            )

            request = OpenWebUIBridgeAdapterRequest(
                adapter_request_ref="openwebui-bridge-adapter-request:m51-gate",
                session_ref="openwebui-session:m51-gate",
                message_ref="openwebui-message:m51-gate",
                safe_user_summary="User asked for a redacted governance summary.",
            )
            result = adapt_openwebui_bridge_request(request)
            if result.status != OpenWebUIBridgeAdapterStatus.safe_summary_ready:
                failures.append("M51 safe adapter result was not ready")
            for field_name in [
                "raw_prompt_returned",
                "raw_provider_payload_returned",
                "raw_content_returned",
                "model_output_authoritative",
                "openwebui_called",
                "provider_called",
                "tool_executed",
                "memory_written",
                "context_injected",
                "approval_granted",
            ]:
                if getattr(result, field_name):
                    failures.append(f"M51 adapter result enabled forbidden field: {field_name}")
            if result.side_effects_performed:
                failures.append("M51 adapter result performed side effects")
            try:
                adapt_openwebui_bridge_request(request.model_copy(update={"raw_prompt_present": True}))
                failures.append("M51 model_copy raw prompt mutation was not denied")
            except ValueError as exc:
                if "RAW_PROMPT_DENIED" not in str(exc):
                    failures.append(f"M51 raw prompt rejection reason drifted: {exc}")
            try:
                adapt_openwebui_bridge_request(
                    request.model_copy(
                        update={
                            "approval_ref": "approval:m51-gate",
                            "tool_execution_requested": True,
                        }
                    )
                )
                failures.append("M51 approval_ref/tool execution mutation was not denied")
            except ValueError as exc:
                if "APPROVAL_REF_NOT_AUTHORITY" not in str(exc):
                    failures.append(f"M51 approval-ref rejection reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M51 OpenWebUI adapter validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "openwebui bridge adapter pilot",
            "safe-summary-only",
            "agent core remains authority",
            "openwebui is not the agent brain",
            "no raw prompt",
            "no raw provider payload",
            "no provider call",
            "no model authority",
            "no tool execution",
            "no memory write",
            "no context injection",
            "no backend route",
            "m52 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M51 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m51_openwebui_adapter_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "openwebui_runtime_call_requested=True",
            "live_openwebui_connection_enabled=True",
            "openwebui_network_call_enabled=True",
            "provider_call_enabled=True",
            "provider_call_requested=True",
            "model_authority_enabled=True",
            "model_authority_requested=True",
            "tool_execution_enabled=True",
            "tool_execution_requested=True",
            "memory_write_enabled=True",
            "memory_write_requested=True",
            "context_injection_enabled=True",
            "context_injection_requested=True",
            "raw_prompt_exposure_enabled=True",
            "raw_prompt_present=True",
            "raw_provider_payload_exposure_enabled=True",
            "raw_provider_payload_present=True",
            "raw_content_allowed=True",
            "raw_content_present=True",
            "openwebui_called=True",
            "provider_called=True",
            "tool_executed=True",
            "memory_written=True",
            "context_injected=True",
            "/openwebui/handoff",
            "/openwebui/runtime/call",
            "/openwebui/provider/call",
            "/openwebui/tools/execute",
            "/openwebui/memory/write",
            "/openwebui/context/inject",
            "/openwebui/raw-payload",
            "import openwebui\n",
            "from openwebui",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "tests/test_m51_openwebui_bridge_adapter_pilot.py",
            "tests/test_m51_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8").lower()
                for fragment in forbidden_source_fragments:
                    if fragment.lower() in text:
                        failures.append(f"M51 forbidden OpenWebUI adapter fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m51_openwebui_adapter_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m51_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M51 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m51_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M51 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.55.0" not in text or "m51" not in text or "openwebui bridge adapter pilot" not in text:
            failures.append("active docs do not identify v0.55.0/M51 OpenWebUI Bridge Adapter Pilot")
        if "m51 is implemented/released" not in text and "v0.55.0 implements m51" not in text:
            failures.append("active docs do not mark M51 implemented/released")
        if self._active_version_tuple() >= (0, 57, 0):
            if "m52 is implemented/released" not in text and "v0.56.0 implements m52" not in text:
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53 is implemented/released" not in text and "v0.57.0 implements m53" not in text:
                failures.append("M53 must be implemented/released after v0.57.0")
            if (
                "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M54-M60 must remain planned/provisional after M53")
        elif self._active_version_tuple() >= (0, 56, 0):
            if "m52 is implemented/released" not in text and "v0.56.0 implements m52" not in text:
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53-m60 remain planned/provisional" not in text:
                failures.append("M53-M60 must remain planned/provisional after M52")
        elif "m52-m60 remain planned/provisional" not in text:
            failures.append("M52-M60 must remain planned/provisional after M51")
        forbidden_fragments = [
            "openwebui tool execution is implemented",
            "context injection is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 56, 0):
            forbidden_fragments.extend(
                [
                    "m52 is implemented",
                    "v0.56.0 implements m52",
                    "openwebui safe conversation surface is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M51 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m52_openwebui_safe_conversation_surface(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/openwebui_bridge/conversation.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_SURFACE.md",
            "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_POLICY.md",
            "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_AUTHORITY_BOUNDARY.md",
            "docs/openwebui/M52_TO_M53_BOUNDARY.md",
            "tests/test_m52_openwebui_safe_conversation_surface.py",
        ]
        failures = [
            f"missing M52 OpenWebUI safe conversation file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.openwebui_bridge import (
                OpenWebUIMessageDirection,
                OpenWebUISafeConversationSurfaceStatus,
                OpenWebUISafeConversationTurn,
                build_openwebui_safe_conversation_surface,
            )

            turn = OpenWebUISafeConversationTurn(
                turn_ref="openwebui-conversation-turn:m52-gate",
                session_ref="openwebui-session:m52-gate",
                message_ref="openwebui-message:m52-gate",
                direction=OpenWebUIMessageDirection.user_to_agent_core_planned,
                safe_summary="User asked for a redacted OpenWebUI conversation summary.",
            )
            surface = build_openwebui_safe_conversation_surface(
                conversation_ref="openwebui-safe-conversation:m52-gate",
                session_ref="openwebui-session:m52-gate",
                safe_title="OpenWebUI safe conversation preview",
                turns=[turn],
            )
            if surface.status != OpenWebUISafeConversationSurfaceStatus.safe_review_ready:
                failures.append("M52 safe conversation surface was not ready")
            for field_name in [
                "openwebui_called",
                "provider_called",
                "model_called",
                "model_output_authoritative",
                "tool_executed",
                "memory_written",
                "context_injected",
                "approval_granted",
                "raw_prompt_returned",
                "raw_provider_payload_returned",
                "raw_content_returned",
            ]:
                if getattr(surface, field_name):
                    failures.append(f"M52 surface enabled forbidden field: {field_name}")
            if surface.side_effects_performed:
                failures.append("M52 surface performed side effects")
            try:
                build_openwebui_safe_conversation_surface(
                    conversation_ref="openwebui-safe-conversation:m52-mutated",
                    session_ref="openwebui-session:m52-gate",
                    safe_title="Mutated unsafe conversation",
                    turns=[turn.model_copy(update={"raw_provider_payload_present": True})],
                )
                failures.append("M52 model_copy raw provider payload mutation was not denied")
            except ValueError as exc:
                if "RAW_PROVIDER_PAYLOAD_DENIED" not in str(exc):
                    failures.append(f"M52 raw provider payload rejection reason drifted: {exc}")
            try:
                build_openwebui_safe_conversation_surface(
                    conversation_ref="openwebui-safe-conversation:m52-approval",
                    session_ref="openwebui-session:m52-gate",
                    safe_title="Approval refs are not authority",
                    turns=[
                        turn.model_copy(
                            update={
                                "approval_ref": "approval:m52-gate",
                                "tool_execution_requested": True,
                            }
                        )
                    ],
                )
                failures.append("M52 approval_ref/tool execution mutation was not denied")
            except ValueError as exc:
                if "APPROVAL_REF_NOT_AUTHORITY" not in str(exc):
                    failures.append(f"M52 approval-ref rejection reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M52 OpenWebUI safe conversation validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "openwebui safe conversation surface",
            "safe-summary-only",
            "agent core remains authority",
            "openwebui is not the agent brain",
            "no raw prompt",
            "no raw provider payload",
            "no raw content",
            "no provider call",
            "no model call",
            "no model authority",
            "no tool execution",
            "no memory write",
            "no context injection",
            "no backend route",
            "m53 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M52 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m52_openwebui_safe_conversation_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "openwebui_runtime_call_requested=True",
            "live_openwebui_connection_enabled=True",
            "openwebui_network_call_enabled=True",
            "provider_call_enabled=True",
            "provider_call_requested=True",
            "model_call_enabled=True",
            "model_call_requested=True",
            "model_authority_enabled=True",
            "model_authority_requested=True",
            "tool_execution_enabled=True",
            "tool_execution_requested=True",
            "memory_write_enabled=True",
            "memory_write_requested=True",
            "context_injection_enabled=True",
            "context_injection_requested=True",
            "raw_prompt_exposure_enabled=True",
            "raw_prompt_present=True",
            "raw_provider_payload_exposure_enabled=True",
            "raw_provider_payload_present=True",
            "raw_content_allowed=True",
            "raw_content_present=True",
            "openwebui_called=True",
            "provider_called=True",
            "model_called=True",
            "tool_executed=True",
            "memory_written=True",
            "context_injected=True",
            "/openwebui/conversation",
            "/openwebui/runtime/call",
            "/openwebui/provider/call",
            "/openwebui/model/call",
            "/openwebui/tools/execute",
            "/openwebui/memory/write",
            "/openwebui/context/inject",
            "/openwebui/raw-payload",
            "/openwebui/raw-prompt",
            "import openwebui\n",
            "from openwebui",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "tests/test_m52_openwebui_safe_conversation_surface.py",
            "tests/test_m52_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8").lower()
                for fragment in forbidden_source_fragments:
                    if fragment.lower() in text:
                        failures.append(
                            f"M52 forbidden OpenWebUI safe conversation fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m52_openwebui_safe_conversation_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m52_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M52 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m52_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M52 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.56.0" not in text or "m52" not in text or "openwebui safe conversation surface" not in text:
            failures.append("active docs do not identify v0.56.0/M52 OpenWebUI Safe Conversation Surface")
        if "m52 is implemented/released" not in text and "v0.56.0 implements m52" not in text:
            failures.append("active docs do not mark M52 implemented/released")
        if self._active_version_tuple() >= (0, 57, 0):
            if "m53 is implemented/released" not in text and "v0.57.0 implements m53" not in text:
                failures.append("M53 must be implemented/released after v0.57.0")
            if (
                "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M54-M60 must remain planned/provisional after M53")
        else:
            if "m53-m60 remain planned/provisional" not in text:
                failures.append("M53-M60 must remain planned/provisional after M52")
            for fragment in (
                "m53 is implemented",
                "v0.57.0 implements m53",
                "controlled tool expansion review is implemented",
            ):
                if fragment in text:
                    failures.append(f"M52 docs imply forbidden/future capability: {fragment}")
        for fragment in (
            "openwebui tool execution is implemented",
            "provider call is implemented",
            "model authority is implemented",
            "context injection is implemented",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(f"M52 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m53_controlled_tool_expansion_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/expansion_review.py",
            "docs/tools/CONTROLLED_TOOL_EXPANSION_REVIEW.md",
            "docs/tools/CONTROLLED_TOOL_EXPANSION_POLICY.md",
            "docs/tools/CONTROLLED_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md",
            "docs/tools/M53_TO_M54_BOUNDARY.md",
            "tests/test_m53_controlled_tool_expansion_review.py",
            "tests/test_m53_gate_integration.py",
        ]
        failures = [
            f"missing M53 controlled tool expansion review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.tools import (
                ControlledToolExpansionCandidate,
                ControlledToolExpansionPolicy,
                ControlledToolExpansionReviewStatus,
                ToolExpansionCapabilityKind,
                evaluate_controlled_tool_expansion_candidate,
                validate_controlled_tool_expansion_candidate,
                validate_controlled_tool_expansion_policy,
            )

            candidate = ControlledToolExpansionCandidate(
                candidate_ref="tool-expansion-candidate:m53-gate",
                safe_name="Metadata-only review candidate",
                capability_kind=ToolExpansionCapabilityKind.safe_metadata_review,
                safe_summary="Review future tool capability metadata without enablement.",
            )
            decision = evaluate_controlled_tool_expansion_candidate(candidate)
            if decision.status != ControlledToolExpansionReviewStatus.review_ready:
                failures.append("M53 safe metadata review candidate was not review-ready")
            if not decision.review_allowed or decision.execution_allowed or decision.tool_enablement_allowed:
                failures.append("M53 decision did not remain review-only")
            if decision.receipt_plan is None:
                failures.append("M53 decision did not create a no-enable receipt plan")
            elif (
                decision.receipt_plan.execution_performed
                or decision.receipt_plan.tool_enabled
                or decision.receipt_plan.side_effects_performed
            ):
                failures.append("M53 receipt plan performed execution, enablement, or side effects")
            future_decision = evaluate_controlled_tool_expansion_candidate(
                ControlledToolExpansionCandidate(
                    candidate_ref="tool-expansion-candidate:m53-shell_execution",
                    safe_name="Future shell execution review",
                    capability_kind=ToolExpansionCapabilityKind.shell_execution,
                    safe_summary="Review a future tool capability without enabling it.",
                )
            )
            if future_decision.status != ControlledToolExpansionReviewStatus.future_milestone:
                failures.append("M53 effectful candidate did not require a future milestone")
            for candidate_update, reason in [
                ({"execution_requested": True}, "TOOL_EXPANSION_EXECUTION_DENIED"),
                ({"tool_enablement_requested": True}, "TOOL_ENABLEMENT_DENIED"),
                ({"contains_raw_provider_payload": True}, "RAW_PROVIDER_PAYLOAD_DENIED"),
                ({"approval_ref": "approval:m53-gate"}, "APPROVAL_REF_NOT_AUTHORITY"),
            ]:
                try:
                    validate_controlled_tool_expansion_candidate(candidate.model_copy(update=candidate_update))
                    failures.append(f"M53 unsafe candidate mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M53 unsafe candidate reason drifted for {reason}: {exc}")
            try:
                validate_controlled_tool_expansion_policy(
                    ControlledToolExpansionPolicy(shell_execution_enabled=True)
                )
                failures.append("M53 unsafe policy flag was not denied")
            except ValueError as exc:
                if "SHELL_EXECUTION_DENIED" not in str(exc):
                    failures.append(f"M53 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M53 controlled tool expansion validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "controlled tool expansion review",
            "review-only",
            "planning-only",
            "no tool execution",
            "no tool enablement",
            "no shell execution",
            "no unrestricted network tool",
            "no provider model call",
            "no browser automation execution",
            "no plugin enablement",
            "no mobile sensor access",
            "no remote execution",
            "no raw file browsing",
            "no raw file export",
            "no full-file read",
            "no memory write",
            "no context injection",
            "no backend route",
            "m54 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M53 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m53_controlled_tool_expansion_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "shell_execution_enabled=True",
            "subprocess_execution_enabled=True",
            "unrestricted_network_tools_enabled=True",
            "provider_model_calls_enabled=True",
            "model_authority_enabled=True",
            "browser_automation_execution_enabled=True",
            "plugin_enablement_enabled=True",
            "mobile_sensor_access_enabled=True",
            "remote_execution_enabled=True",
            "raw_file_browsing_enabled=True",
            "raw_file_export_enabled=True",
            "full_file_read_enabled=True",
            "file_mutation_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "credentials_cookie_handling_enabled=True",
            "external_saas_analytics_sdk_enabled=True",
            "production_authority_enabled=True",
            "execution_allowed=True",
            "tool_enablement_allowed=True",
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
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/expansion_review.py",
            "apps/control-center/src/App.test.tsx",
            "tests/test_m53_controlled_tool_expansion_review.py",
            "tests/test_m53_gate_integration.py",
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent" / "core" / "beta_freeze",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M53 forbidden controlled tool expansion fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m53_controlled_tool_expansion_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m53_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M53 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m53_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M53 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.57.0" not in text or "m53" not in text or "controlled tool expansion review" not in text:
            failures.append("active docs do not identify v0.57.0/M53 Controlled Tool Expansion Review")
        if "m53 is implemented/released" not in text and "v0.57.0 implements m53" not in text:
            failures.append("active docs do not mark M53 implemented/released")
        if (
            "m54-m60 remain planned/provisional" not in text
            and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
        ):
            failures.append("M54-M60 must remain planned/provisional after M53")
        forbidden_fragments = [
            "tool execution is implemented",
            "shell execution is implemented",
            "provider model call is implemented",
            "context injection is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 58, 0):
            forbidden_fragments.extend(
                [
                    "m54 is implemented",
                    "v0.58.0 implements m54",
                    "safe media metadata inspector is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M53 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m54_safe_media_metadata_inspector(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/media/__init__.py",
            "src/ultimate_ai_agent/core/media/metadata.py",
            "docs/media/SAFE_MEDIA_METADATA_INSPECTOR.md",
            "docs/media/SAFE_MEDIA_METADATA_POLICY.md",
            "docs/media/SAFE_MEDIA_METADATA_AUTHORITY_BOUNDARY.md",
            "docs/media/M54_TO_M55_BOUNDARY.md",
            "tests/test_m54_safe_media_metadata_inspector.py",
            "tests/test_m54_gate_integration.py",
        ]
        failures = [
            f"missing M54 safe media metadata file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.media import (
                MediaInspectionKind,
                SafeMediaMetadataPolicy,
                SafeMediaMetadataRequest,
                SafeMediaMetadataStatus,
                inspect_safe_media_metadata,
                validate_safe_media_metadata_policy,
                validate_safe_media_metadata_request,
            )

            request = SafeMediaMetadataRequest(
                request_ref="media-metadata-request:m54-gate",
                media_ref="media:m54-gate",
                safe_path_ref="safe-path:m54-gate.jpg",
                inspection_kind=MediaInspectionKind.image_metadata,
                declared_media_type="image/jpeg",
                declared_byte_size=2048,
            )
            decision = inspect_safe_media_metadata(request)
            if decision.status != SafeMediaMetadataStatus.metadata_ready or not decision.metadata_ready:
                failures.append("M54 safe media metadata request was not metadata-ready")
            if (
                decision.raw_media_returned
                or decision.raw_media_stored
                or decision.original_file_modified
                or decision.ocio_transform_performed
                or decision.ai_gamut_expansion_performed
                or decision.model_call_performed
                or decision.context_injection_performed
            ):
                failures.append("M54 decision performed raw media output, mutation, transform, model, or context side effect")
            if decision.receipt_plan is None:
                failures.append("M54 decision did not create a metadata-only receipt plan")
            elif decision.receipt_plan.side_effects_performed or decision.receipt_plan.raw_media_stored:
                failures.append("M54 receipt plan stored raw media or performed side effects")
            denied = inspect_safe_media_metadata(
                request.model_copy(
                    update={
                        "request_ref": "media-metadata-request:m54-unsupported",
                        "declared_media_type": "application/octet-stream",
                    }
                )
            )
            if denied.status != SafeMediaMetadataStatus.denied:
                failures.append("M54 unsupported media type was not denied")
            for request_update, reason in [
                ({"raw_media_requested": True}, "RAW_MEDIA_EXPORT_DENIED"),
                ({"full_file_read_requested": True}, "FULL_FILE_READ_DENIED"),
                ({"ocio_transform_requested": True}, "OCIO_TRANSFORM_DENIED"),
                ({"ai_gamut_expansion_requested": True}, "AI_GAMUT_EXPANSION_DENIED"),
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                ({"contains_secret_like_metadata": True}, "SECRET_LIKE_METADATA_DENIED"),
            ]:
                try:
                    validate_safe_media_metadata_request(request.model_copy(update=request_update))
                    failures.append(f"M54 unsafe request mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M54 unsafe request reason drifted for {reason}: {exc}")
            try:
                validate_safe_media_metadata_policy(SafeMediaMetadataPolicy(raw_media_export_enabled=True))
                failures.append("M54 unsafe policy flag was not denied")
            except ValueError as exc:
                if "RAW_MEDIA_EXPORT_DENIED" not in str(exc):
                    failures.append(f"M54 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M54 safe media metadata validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "safe media metadata inspector",
            "metadata-only",
            "no raw media export",
            "no raw media storage",
            "no full-file read",
            "no file mutation",
            "no original overwrite",
            "no ocio transform",
            "no ai gamut expansion",
            "no model call",
            "no context injection",
            "no backend route",
            "m55 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M54 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m54_safe_media_metadata_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "raw_media_export_enabled=True",
            "raw_media_storage_enabled=True",
            "full_file_read_enabled=True",
            "file_mutation_enabled=True",
            "original_overwrite_enabled=True",
            "ocio_transform_enabled=True",
            "ai_gamut_expansion_enabled=True",
            "model_call_enabled=True",
            "context_injection_enabled=True",
            "production_authority_enabled=True",
            "raw_media_returned=True",
            "raw_media_stored=True",
            "original_file_modified=True",
            "ocio_transform_performed=True",
            "ai_gamut_expansion_performed=True",
            "model_call_performed=True",
            "context_injection_performed=True",
            "/media/read/raw",
            "/media/export",
            "/media/transform/ocio",
            "/media/gamut/expand",
            "/models/call",
            "/provider/call",
            "/context/inject",
            "/memory/write",
            "/tools/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/media/metadata.py",
            "tests/test_m54_safe_media_metadata_inspector.py",
            "tests/test_m54_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M54 forbidden media metadata fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m54_safe_media_metadata_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m54_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M54 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m54_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M54 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.58.0" not in text or "m54" not in text or "safe media metadata inspector" not in text:
            failures.append("active docs do not identify v0.58.0/M54 Safe Media Metadata Inspector")
        if "m54 is implemented/released" not in text and "v0.58.0 implements m54" not in text:
            failures.append("active docs do not mark M54 implemented/released")
        if self._active_version_tuple() >= (0, 63, 0):
            if "m55 is implemented/released" not in text and "v0.59.0 implements m55" not in text:
                failures.append("active docs do not mark M55 implemented/released")
            if "m56 is implemented/released" not in text and "v0.60.0 implements m56" not in text:
                failures.append("active docs do not mark M56 implemented/released")
            if "m57 is implemented/released" not in text and "v0.61.0 implements m57" not in text:
                failures.append("active docs do not mark M57 implemented/released")
            if "m58 is implemented/released" not in text and "v0.62.0 implements m58" not in text:
                failures.append("active docs do not mark M58 implemented/released")
            if "m59 is implemented/released" not in text and "v0.63.0 implements m59" not in text:
                failures.append("active docs do not mark M59 implemented/released")
            if not self._m60_currentness_marker_present(text):
                failures.append("M60 currentness marker is missing after M59")
        elif self._active_version_tuple() >= (0, 62, 0):
            if "m55 is implemented/released" not in text and "v0.59.0 implements m55" not in text:
                failures.append("active docs do not mark M55 implemented/released")
            if "m56 is implemented/released" not in text and "v0.60.0 implements m56" not in text:
                failures.append("active docs do not mark M56 implemented/released")
            if "m57 is implemented/released" not in text and "v0.61.0 implements m57" not in text:
                failures.append("active docs do not mark M57 implemented/released")
            if "m58 is implemented/released" not in text and "v0.62.0 implements m58" not in text:
                failures.append("active docs do not mark M58 implemented/released")
            if "m59-m60 remain planned/provisional" not in text:
                failures.append("M59-M60 must remain planned/provisional after M58")
        elif self._active_version_tuple() >= (0, 60, 0):
            if "m55 is implemented/released" not in text and "v0.59.0 implements m55" not in text:
                failures.append("active docs do not mark M55 implemented/released")
            if "m56 is implemented/released" not in text and "v0.60.0 implements m56" not in text:
                failures.append("active docs do not mark M56 implemented/released")
            if "m57-m60 remain planned/provisional" not in text and "m58-m60 remain planned/provisional" not in text:
                failures.append("M57-M60 must remain planned/provisional after M56")
        elif self._active_version_tuple() >= (0, 59, 0):
            if "m55 is implemented/released" not in text and "v0.59.0 implements m55" not in text:
                failures.append("active docs do not mark M55 implemented/released")
            if "m56-m60 remain planned/provisional" not in text:
                failures.append("M56-M60 must remain planned/provisional after M55")
        elif "m55-m60 remain planned/provisional" not in text:
            failures.append("M55-M60 must remain planned/provisional after M54")
        forbidden_fragments = [
            "ocio deterministic transform preview is implemented",
            "ai gamut expansion is implemented",
            "raw media export is implemented",
            "model call is implemented",
            "context injection is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 59, 0):
            forbidden_fragments.extend(
                [
                    "m55 is implemented",
                    "v0.59.0 implements m55",
                    "redacted observability export is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M54 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m55_redacted_observability_export(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/observability/__init__.py",
            "src/ultimate_ai_agent/core/observability/export.py",
            "docs/observability/REDACTED_OBSERVABILITY_EXPORT.md",
            "docs/observability/REDACTED_OBSERVABILITY_EXPORT_POLICY.md",
            "docs/observability/REDACTED_OBSERVABILITY_EXPORT_AUTHORITY_BOUNDARY.md",
            "docs/observability/M55_TO_M56_BOUNDARY.md",
            "tests/test_m55_redacted_observability_export.py",
            "tests/test_m55_gate_integration.py",
        ]
        failures = [
            f"missing M55 redacted observability export file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from datetime import UTC, datetime

            from ultimate_ai_agent.core.hygiene.actor_context import (
                ActorContext,
                ActorType,
                AuthoritySource,
            )
            from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
            from ultimate_ai_agent.core.hygiene.temporal_context import (
                FreshnessClass,
                StalenessPolicy,
                TemporalContext,
            )
            from ultimate_ai_agent.core.ledger import EventLedgerEvent, EventName
            from ultimate_ai_agent.core.observability import (
                ObservabilityExportFormat,
                RedactedObservabilityExportPolicy,
                RedactedObservabilityExportRequest,
                RedactedObservabilityExportStatus,
                build_redacted_observability_export,
                validate_redacted_observability_export_policy,
                validate_redacted_observability_export_request,
            )

            event = EventLedgerEvent(
                event_id="evt_m55_gate",
                event_type="run",
                event_name=EventName.run_completed,
                run_id="run_m55_gate",
                trace_id="trace_m55_gate",
                span_id="span_m55_gate",
                correlation_id="corr_m55_gate",
                actor_context=ActorContext(
                    actor_type=ActorType.orchestrator,
                    actor_id="m55-gate",
                    authority_source=AuthoritySource.explicit_user_request,
                    created_at=datetime.now(UTC),
                ),
                temporal_context=TemporalContext(
                    current_time_utc=datetime.now(UTC),
                    freshness_class=FreshnessClass.daily,
                    staleness_policy=StalenessPolicy.allow_with_label,
                ),
                data_classification=DataClassification(
                    classification=ClassificationValue.project_private,
                    source="m55-gate",
                ),
                event_source="ultimate-ai-agent",
                subject="M55 gate",
                action="summarize",
                outcome="completed",
                status="success",
                severity="info",
                redaction_summary={"status": "redacted"},
                metadata={"safe_summary": "M55 gate safe redacted summary."},
            )
            request = RedactedObservabilityExportRequest(
                request_ref="observability-export-request:m55-gate",
                run_ref="run:m55-gate",
                export_ref="observability-export:m55-gate",
                requested_formats=[ObservabilityExportFormat.internal_redacted_json],
                source_event_refs=["event:evt_m55_gate"],
                redaction_policy_ref="redaction-policy:m55-gate",
            )
            bundle = build_redacted_observability_export(request, [event])
            if bundle.status != RedactedObservabilityExportStatus.ready or not bundle.items:
                failures.append("M55 redacted observability export bundle was not ready")
            if (
                bundle.export_performed
                or bundle.external_delivery_performed
                or bundle.raw_prompt_exported
                or bundle.raw_provider_payload_exported
                or bundle.secret_exported
                or bundle.network_call_performed
                or bundle.model_call_performed
                or bundle.memory_write_performed
                or bundle.context_injection_performed
            ):
                failures.append("M55 bundle performed export, raw leak, network/model/context/memory side effect")
            if bundle.receipt_plan is None:
                failures.append("M55 bundle did not create a redacted no-effect receipt plan")
            elif bundle.receipt_plan.side_effects_performed or bundle.receipt_plan.export_performed:
                failures.append("M55 receipt plan performed side effects or export")
            for request_update, reason in [
                ({"raw_prompt_export_requested": True}, "RAW_PROMPT_EXPORT_DENIED"),
                ({"raw_provider_payload_export_requested": True}, "RAW_PROVIDER_PAYLOAD_EXPORT_DENIED"),
                ({"secret_export_requested": True}, "SECRET_EXPORT_DENIED"),
                ({"external_saas_export_requested": True}, "EXTERNAL_SAAS_EXPORT_DENIED"),
                ({"network_export_requested": True}, "NETWORK_EXPORT_DENIED"),
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
            ]:
                try:
                    validate_redacted_observability_export_request(request.model_copy(update=request_update))
                    failures.append(f"M55 unsafe request mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M55 unsafe request reason drifted for {reason}: {exc}")
            try:
                validate_redacted_observability_export_policy(
                    RedactedObservabilityExportPolicy(external_saas_sdk_enabled=True)
                )
                failures.append("M55 unsafe policy flag was not denied")
            except ValueError as exc:
                if "EXTERNAL_SAAS_SDK_DENIED" not in str(exc):
                    failures.append(f"M55 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M55 redacted observability export validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "redacted observability export",
            "redacted-only",
            "contract-only",
            "no external saas",
            "no network delivery",
            "no raw prompts",
            "no raw provider payloads",
            "no secrets",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "m56 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M55 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m55_observability_export_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "raw_prompt_export_enabled=True",
            "raw_provider_payload_export_enabled=True",
            "raw_private_content_export_enabled=True",
            "secret_export_enabled=True",
            "external_saas_sdk_enabled=True",
            "network_delivery_enabled=True",
            "forensic_trace_export_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "production_authority_enabled=True",
            "export_performed=True",
            "external_delivery_performed=True",
            "raw_prompt_exported=True",
            "raw_provider_payload_exported=True",
            "secret_exported=True",
            "network_call_performed=True",
            "/observability/export",
            "/observability/export/raw",
            "/observability/export/prompts",
            "/observability/export/provider-payloads",
            "/observability/export/saas",
            "/otel/export",
            "/analytics/export",
            "/models/call",
            "/provider/call",
            "/context/inject",
            "/memory/write",
            "/tools/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/observability/export.py",
            "tests/test_m55_redacted_observability_export.py",
            "tests/test_m55_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M55 forbidden observability export fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m55_observability_export_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m55_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M55 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m55_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M55 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.59.0" not in text or "m55" not in text or "redacted observability export" not in text:
            failures.append("active docs do not identify v0.59.0/M55 Redacted Observability Export")
        if "m55 is implemented/released" not in text and "v0.59.0 implements m55" not in text:
            failures.append("active docs do not mark M55 implemented/released")
        if self._active_version_tuple() >= (0, 63, 0):
            if "m56 is implemented/released" not in text and "v0.60.0 implements m56" not in text:
                failures.append("active docs do not mark M56 implemented/released")
            if "m57 is implemented/released" not in text and "v0.61.0 implements m57" not in text:
                failures.append("active docs do not mark M57 implemented/released")
            if "m58 is implemented/released" not in text and "v0.62.0 implements m58" not in text:
                failures.append("active docs do not mark M58 implemented/released")
            if "m59 is implemented/released" not in text and "v0.63.0 implements m59" not in text:
                failures.append("active docs do not mark M59 implemented/released")
            if not self._m60_currentness_marker_present(text):
                failures.append("M60 currentness marker is missing after M59")
        elif self._active_version_tuple() >= (0, 62, 0):
            if "m56 is implemented/released" not in text and "v0.60.0 implements m56" not in text:
                failures.append("active docs do not mark M56 implemented/released")
            if "m57 is implemented/released" not in text and "v0.61.0 implements m57" not in text:
                failures.append("active docs do not mark M57 implemented/released")
            if "m58 is implemented/released" not in text and "v0.62.0 implements m58" not in text:
                failures.append("active docs do not mark M58 implemented/released")
            if "m59-m60 remain planned/provisional" not in text:
                failures.append("M59-M60 must remain planned/provisional after M58")
        elif self._active_version_tuple() >= (0, 60, 0):
            if "m56 is implemented/released" not in text and "v0.60.0 implements m56" not in text:
                failures.append("active docs do not mark M56 implemented/released")
            if "m57-m60 remain planned/provisional" not in text and "m58-m60 remain planned/provisional" not in text:
                failures.append("M57-M60 must remain planned/provisional after M56")
        elif "m56-m60 remain planned/provisional" not in text:
            failures.append("M56-M60 must remain planned/provisional after M55")
        forbidden_fragments = [
            "dry-run execution audit harness is implemented",
            "public github readiness is implemented",
            "production authority is implemented",
            "raw prompt export is implemented",
            "provider payload export is implemented",
        ]
        if self._active_version_tuple() >= (0, 63, 0):
            forbidden_fragments.remove("public github readiness is implemented")
        if self._active_version_tuple() < (0, 61, 0):
            forbidden_fragments.append("runtime sandbox architecture is implemented")
        if self._active_version_tuple() < (0, 60, 0):
            forbidden_fragments.extend(
                [
                    "m56 is implemented",
                    "v0.60.0 implements m56",
                    "agent eval regression harness is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M55 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m56_agent_eval_regression_harness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/evals/__init__.py",
            "src/ultimate_ai_agent/core/evals/regression.py",
            "docs/evals/AGENT_EVAL_REGRESSION_HARNESS.md",
            "docs/evals/AGENT_EVAL_REGRESSION_POLICY.md",
            "docs/evals/AGENT_EVAL_REGRESSION_AUTHORITY_BOUNDARY.md",
            "docs/evals/M56_TO_M57_BOUNDARY.md",
            "tests/test_m56_agent_eval_regression_harness.py",
            "tests/test_m56_gate_integration.py",
        ]
        failures = [
            f"missing M56 agent eval regression harness file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.evals import (
                AgentEvalCase,
                AgentEvalCaseObservation,
                AgentEvalHarnessPolicy,
                AgentEvalRegressionRunRequest,
                AgentEvalRegressionStatus,
                AgentEvalSuite,
                build_agent_eval_regression_report,
                validate_agent_eval_harness_policy,
                validate_agent_eval_regression_request,
            )

            case = AgentEvalCase(
                case_ref="eval-case:m56-gate",
                suite_ref="eval-suite:m56-gate",
                scenario_ref="scenario:m56-gate",
                expected_outcome_ref="outcome:review-only",
                redacted_input_summary="Gate safe redacted eval case.",
                invariant_refs=["invariant:no-model-call", "invariant:no-tool-execution"],
                evidence_refs=["evidence:m56-gate"],
            )
            suite = AgentEvalSuite(
                suite_ref="eval-suite:m56-gate",
                baseline_ref="baseline:v0.59.0",
                case_refs=[case.case_ref],
                cases=[case],
                deterministic_seed_ref="seed:m56-gate",
            )
            request = AgentEvalRegressionRunRequest(
                request_ref="eval-request:m56-gate",
                run_ref="eval-run:m56-gate",
                suite_ref=suite.suite_ref,
                case_refs=[case.case_ref],
                baseline_ref=suite.baseline_ref,
            )
            report = build_agent_eval_regression_report(
                request,
                suite,
                [
                    AgentEvalCaseObservation(
                        case_ref=case.case_ref,
                        observed_outcome_ref=case.expected_outcome_ref,
                        safe_observation_summary="Gate safe explicit observation.",
                        evidence_refs=["evidence:m56-observation"],
                    )
                ],
            )
            if report.status != AgentEvalRegressionStatus.passed or report.total_cases != 1:
                failures.append("M56 eval regression report was not passed for matching safe refs")
            if (
                report.model_call_performed
                or report.provider_call_performed
                or report.tool_execution_performed
                or report.network_call_performed
                or report.memory_write_performed
                or report.context_injection_performed
            ):
                failures.append("M56 eval regression report performed model/tool/network/memory/context side effect")
            if report.receipt_plan is None:
                failures.append("M56 eval regression report did not include a no-effect receipt plan")
            elif report.receipt_plan.evaluation_performed or report.receipt_plan.side_effects_performed:
                failures.append("M56 eval regression receipt performed evaluation or side effects")
            for request_update, reason in [
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                ({"provider_call_requested": True}, "PROVIDER_CALL_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
                ({"raw_prompt_capture_requested": True}, "RAW_PROMPT_CAPTURE_DENIED"),
            ]:
                try:
                    validate_agent_eval_regression_request(request.model_copy(update=request_update))
                    failures.append(f"M56 unsafe request mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M56 unsafe request reason drifted for {reason}: {exc}")
            try:
                validate_agent_eval_harness_policy(AgentEvalHarnessPolicy(model_call_enabled=True))
                failures.append("M56 unsafe policy flag was not denied")
            except ValueError as exc:
                if "MODEL_CALL_DENIED" not in str(exc):
                    failures.append(f"M56 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M56 agent eval regression validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "agent eval regression harness",
            "deterministic",
            "contract-only",
            "no model call",
            "no provider call",
            "no tool execution",
            "no shell execution",
            "no browser automation",
            "no network access",
            "no memory write",
            "no context injection",
            "no raw prompt",
            "no raw provider payload",
            "no backend route",
            "m57 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M56 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m56_eval_regression_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "model_call_enabled=True",
            "provider_call_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_automation_enabled=True",
            "network_access_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "raw_prompt_capture_enabled=True",
            "raw_provider_payload_capture_enabled=True",
            "external_dataset_fetch_enabled=True",
            "score_authority_enabled=True",
            "production_authority_enabled=True",
            "evaluation_performed=True",
            "model_call_performed=True",
            "provider_call_performed=True",
            "tool_execution_performed=True",
            "network_call_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "/evals/run",
            "/evals/execute",
            "/evals/model-call",
            "/evals/provider-call",
            "/evals/export/raw",
            "/models/call",
            "/provider/call",
            "/context/inject",
            "/memory/write",
            "/tools/execute",
            "/shell/execute",
            "/browser/click",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/evals/regression.py",
            "tests/test_m56_agent_eval_regression_harness.py",
            "tests/test_m56_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M56 forbidden eval harness fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m56_eval_regression_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m56_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M56 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m56_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M56 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.60.0" not in text or "m56" not in text or "agent eval regression harness" not in text:
            failures.append("active docs do not identify v0.60.0/M56 Agent Eval Regression Harness")
        if "m56 is implemented/released" not in text and "v0.60.0 implements m56" not in text:
            failures.append("active docs do not mark M56 implemented/released")
        if self._active_version_tuple() >= (0, 63, 0):
            if "m57 is implemented/released" not in text and "v0.61.0 implements m57" not in text:
                failures.append("active docs do not mark M57 implemented/released")
            if "m58 is implemented/released" not in text and "v0.62.0 implements m58" not in text:
                failures.append("active docs do not mark M58 implemented/released")
            if "m59 is implemented/released" not in text and "v0.63.0 implements m59" not in text:
                failures.append("active docs do not mark M59 implemented/released")
            if not self._m60_currentness_marker_present(text):
                failures.append("M60 currentness marker is missing after M59")
        elif self._active_version_tuple() >= (0, 62, 0):
            if "m57 is implemented/released" not in text and "v0.61.0 implements m57" not in text:
                failures.append("active docs do not mark M57 implemented/released")
            if "m58 is implemented/released" not in text and "v0.62.0 implements m58" not in text:
                failures.append("active docs do not mark M58 implemented/released")
            if "m59-m60 remain planned/provisional" not in text:
                failures.append("M59-M60 must remain planned/provisional after M58")
        elif "m57-m60 remain planned/provisional" not in text and "m58-m60 remain planned/provisional" not in text:
            failures.append("M57-M60 must remain planned/provisional after M56")
        for fragment in (
            "m57 is implemented",
            "v0.61.0 implements m57",
            "runtime sandbox architecture is implemented",
            "dry-run execution audit harness is implemented",
            "public github readiness is implemented",
            "production authority is implemented",
            "eval execution api is implemented",
            "model evaluation calls are implemented",
        ):
            if self._active_version_tuple() >= (0, 61, 0) and fragment in {
                "m57 is implemented",
                "v0.61.0 implements m57",
                "runtime sandbox architecture is implemented",
            }:
                continue
            if self._active_version_tuple() >= (0, 63, 0) and fragment == "public github readiness is implemented":
                continue
            if fragment in text:
                failures.append(f"M56 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m57_runtime_sandbox_architecture_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/architecture.py",
            "docs/sandbox/RUNTIME_SANDBOX_ARCHITECTURE_REVIEW.md",
            "docs/sandbox/RUNTIME_SANDBOX_BOUNDARY_POLICY.md",
            "docs/sandbox/RUNTIME_SANDBOX_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/M57_TO_M58_BOUNDARY.md",
            "tests/test_m57_runtime_sandbox_architecture_review.py",
            "tests/test_m57_gate_integration.py",
        ]
        failures = [
            f"missing M57 runtime sandbox architecture review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.sandbox import (
                RuntimeSandboxArchitecturePolicy,
                RuntimeSandboxArchitectureRequest,
                RuntimeSandboxArchitectureStatus,
                build_runtime_sandbox_architecture_review,
                validate_runtime_sandbox_architecture_policy,
                validate_runtime_sandbox_architecture_request,
            )

            request = RuntimeSandboxArchitectureRequest(
                request_ref="sandbox-review-request:m57-gate",
                review_ref="sandbox-review:m57-gate",
                architecture_ref="sandbox-architecture:m57-gate",
                boundary_refs=["boundary:no-shell-execution", "boundary:no-subprocess"],
                threat_model_refs=["threat:process-spawn", "threat:filesystem-mutation"],
                audit_requirement_refs=["audit:dry-run-before-execution"],
                safe_summary="Gate safe runtime sandbox architecture review.",
            )
            review = build_runtime_sandbox_architecture_review(request)
            if review.status != RuntimeSandboxArchitectureStatus.reviewed:
                failures.append("M57 runtime sandbox architecture review did not return reviewed status")
            if (
                not review.architecture_review_only
                or review.runtime_sandbox_enabled
                or review.execution_performed
                or review.subprocess_performed
                or review.shell_execution_performed
                or review.side_effects_performed
            ):
                failures.append("M57 runtime sandbox architecture review performed runtime side effects")
            if review.receipt_plan is None:
                failures.append("M57 runtime sandbox architecture review did not include no-effect receipt plan")
            elif review.receipt_plan.side_effects_performed or review.receipt_plan.subprocess_performed:
                failures.append("M57 runtime sandbox receipt performed side effects")
            for request_update, reason in [
                ({"sandbox_runtime_requested": True}, "SANDBOX_RUNTIME_DENIED"),
                ({"subprocess_execution_requested": True}, "SUBPROCESS_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"filesystem_mutation_requested": True}, "FILESYSTEM_MUTATION_DENIED"),
                ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
                ({"m58_dry_run_harness_requested": True}, "M58_DRY_RUN_HARNESS_DENIED"),
            ]:
                try:
                    validate_runtime_sandbox_architecture_request(request.model_copy(update=request_update))
                    failures.append(f"M57 unsafe request mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M57 unsafe request reason drifted for {reason}: {exc}")
            try:
                validate_runtime_sandbox_architecture_policy(
                    RuntimeSandboxArchitecturePolicy(sandbox_runtime_enabled=True)
                )
                failures.append("M57 unsafe policy flag was not denied")
            except ValueError as exc:
                if "SANDBOX_RUNTIME_DENIED" not in str(exc):
                    failures.append(f"M57 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M57 runtime sandbox architecture validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "runtime sandbox architecture review",
            "architecture review only",
            "contract-only",
            "no sandbox execution",
            "no subprocess",
            "no shell execution",
            "no process spawn",
            "no file mutation",
            "no network access",
            "no tool execution",
            "no memory write",
            "no context injection",
            "no backend route",
            "no dependency",
            "no production authority",
            "m58 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M57 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m57_runtime_sandbox_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "sandbox_runtime_enabled=True",
            "subprocess_execution_enabled=True",
            "shell_execution_enabled=True",
            "process_spawn_enabled=True",
            "filesystem_mutation_enabled=True",
            "network_access_enabled=True",
            "tool_execution_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "remote_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "side_effects_enabled=True",
            "production_authority_enabled=True",
            "m58_dry_run_harness_enabled=True",
            "subprocess_performed=True",
            "shell_execution_performed=True",
            "process_spawn_performed=True",
            "filesystem_mutation_performed=True",
            "network_access_performed=True",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
            "/sandbox/run",
            "/sandbox/execute",
            "/process/spawn",
            "/subprocess/run",
            "/shell/execute",
            "/tools/execute",
            "/tool-runtime/execute",
            "/context/inject",
            "/memory/write",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/sandbox/architecture.py",
            "tests/test_m57_runtime_sandbox_architecture_review.py",
            "tests/test_m57_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M57 forbidden runtime sandbox fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m57_runtime_sandbox_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m57_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M57 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m57_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M57 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.61.0" not in text or "m57" not in text or "runtime sandbox architecture review" not in text:
            failures.append("active docs do not identify v0.61.0/M57 Runtime Sandbox Architecture Review")
        if "m57 is implemented/released" not in text and "v0.61.0 implements m57" not in text:
            failures.append("active docs do not mark M57 implemented/released")
        if self._active_version_tuple() >= (0, 63, 0):
            if "m58 is implemented/released" not in text and "v0.62.0 implements m58" not in text:
                failures.append("active docs do not mark M58 implemented/released")
            if "m59 is implemented/released" not in text and "v0.63.0 implements m59" not in text:
                failures.append("active docs do not mark M59 implemented/released")
            if not self._m60_currentness_marker_present(text):
                failures.append("M60 currentness marker is missing after M59")
            forbidden_fragments = (
                "shell execution is implemented",
                "subprocess execution is implemented",
                "process spawn is implemented",
                "production authority is implemented",
            )
        elif self._active_version_tuple() >= (0, 62, 0):
            if "m58 is implemented/released" not in text and "v0.62.0 implements m58" not in text:
                failures.append("active docs do not mark M58 implemented/released")
            if "m59-m60 remain planned/provisional" not in text:
                failures.append("M59-M60 must remain planned/provisional after M58")
            forbidden_fragments = (
                "shell execution is implemented",
                "subprocess execution is implemented",
                "process spawn is implemented",
                "public github readiness is implemented",
                "production authority is implemented",
            )
        else:
            if "m58-m60 remain planned/provisional" not in text:
                failures.append("M58-M60 must remain planned/provisional after M57")
            forbidden_fragments = (
                "m58 is implemented",
                "v0.62.0 implements m58",
                "dry-run execution audit harness is implemented",
                "shell execution is implemented",
                "subprocess execution is implemented",
                "process spawn is implemented",
                "public github readiness is implemented",
                "production authority is implemented",
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M57 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m58_dry_run_execution_audit_harness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/dry_run_audit/__init__.py",
            "src/ultimate_ai_agent/core/dry_run_audit/harness.py",
            "docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_HARNESS.md",
            "docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_POLICY.md",
            "docs/dry_run_audit/DRY_RUN_EXECUTION_AUTHORITY_BOUNDARY.md",
            "docs/dry_run_audit/M58_TO_M59_BOUNDARY.md",
            "tests/test_m58_dry_run_execution_audit_harness.py",
            "tests/test_m58_gate_integration.py",
        ]
        failures = [
            f"missing M58 dry-run execution audit file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.dry_run_audit import (
                DryRunExecutionAuditIntent,
                DryRunExecutionAuditPolicy,
                DryRunExecutionAuditRequest,
                DryRunExecutionAuditStatus,
                build_dry_run_execution_audit_report,
                validate_dry_run_execution_audit_policy,
                validate_dry_run_execution_audit_request,
            )

            intent = DryRunExecutionAuditIntent(
                intent_ref="dry-run-intent:m58-gate",
                operation_ref="operation:gate-preview",
                target_ref="target:gate-contract",
                requested_capability_refs=["capability:preview-only", "capability:no-side-effects"],
                safe_summary="Gate safe dry-run audit intent.",
            )
            request = DryRunExecutionAuditRequest(
                request_ref="dry-run-audit-request:m58-gate",
                audit_ref="dry-run-audit:m58-gate",
                sandbox_review_ref="sandbox-review:m57-gate",
                intent_refs=[intent.intent_ref],
                intents=[intent],
                actor_ref="actor:gate-reviewer",
                replay_key_ref="replay-key:m58-gate",
            )
            report = build_dry_run_execution_audit_report(request)
            if report.status != DryRunExecutionAuditStatus.reviewed:
                failures.append("M58 dry-run audit report did not return reviewed status")
            if (
                not report.dry_run_only
                or report.execution_performed
                or report.tool_execution_performed
                or report.subprocess_performed
                or report.shell_execution_performed
                or report.side_effects_performed
            ):
                failures.append("M58 dry-run audit report performed runtime side effects")
            if report.receipt_plan is None:
                failures.append("M58 dry-run audit report did not include no-effect receipt plan")
            elif report.receipt_plan.execution_performed or report.receipt_plan.side_effects_performed:
                failures.append("M58 dry-run audit receipt performed side effects")
            for intent_update, reason in [
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"subprocess_execution_requested": True}, "SUBPROCESS_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"filesystem_mutation_requested": True}, "FILESYSTEM_MUTATION_DENIED"),
                ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
            ]:
                mutated_request = request.model_copy(
                    update={"intents": [intent.model_copy(update=intent_update)]}
                )
                try:
                    validate_dry_run_execution_audit_request(mutated_request)
                    failures.append(f"M58 unsafe dry-run intent mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M58 unsafe dry-run intent reason drifted for {reason}: {exc}")
            try:
                validate_dry_run_execution_audit_policy(DryRunExecutionAuditPolicy(execution_enabled=True))
                failures.append("M58 unsafe policy flag was not denied")
            except ValueError as exc:
                if "EXECUTION_DENIED" not in str(exc):
                    failures.append(f"M58 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M58 dry-run execution audit validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "dry-run execution audit harness",
            "dry-run-only",
            "contract-only",
            "no real execution",
            "no tool execution",
            "no subprocess",
            "no shell execution",
            "no process spawn",
            "no file mutation",
            "no network access",
            "no memory write",
            "no context injection",
            "no backend route",
            "no dependency",
            "no production authority",
            "m59 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M58 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m58_dry_run_execution_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "subprocess_execution_enabled=True",
            "shell_execution_enabled=True",
            "process_spawn_enabled=True",
            "filesystem_mutation_enabled=True",
            "network_access_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "remote_execution_enabled=True",
            "side_effects_enabled=True",
            "production_authority_enabled=True",
            "m59_public_readiness_enabled=True",
            "execution_performed=True",
            "tool_execution_performed=True",
            "subprocess_performed=True",
            "shell_execution_performed=True",
            "process_spawn_performed=True",
            "filesystem_mutation_performed=True",
            "network_access_performed=True",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
            "/dry-run/run",
            "/dry-run/execute",
            "/execution/audit/run",
            "/execution/audit/execute",
            "/process/spawn",
            "/subprocess/run",
            "/shell/execute",
            "/tools/execute",
            "/tool-runtime/execute",
            "/context/inject",
            "/memory/write",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/dry_run_audit/harness.py",
            "tests/test_m58_dry_run_execution_audit_harness.py",
            "tests/test_m58_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M58 forbidden dry-run execution fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m58_dry_run_execution_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m58_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M58 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m58_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M58 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.62.0" not in text or "m58" not in text or "dry-run execution audit harness" not in text:
            failures.append("active docs do not identify v0.62.0/M58 Dry-Run Execution Audit Harness")
        if "m58 is implemented/released" not in text and "v0.62.0 implements m58" not in text:
            failures.append("active docs do not mark M58 implemented/released")
        if self._active_version_tuple() >= (0, 63, 0):
            if "m59 is implemented/released" not in text and "v0.63.0 implements m59" not in text:
                failures.append("active docs do not mark M59 implemented/released")
            if not self._m60_currentness_marker_present(text):
                failures.append("M60 currentness marker is missing after M59")
        elif "m59-m60 remain planned/provisional" not in text:
            failures.append("M59-M60 must remain planned/provisional after M58")
        for fragment in (
            "m59 is implemented",
            "v0.63.0 implements m59",
            "public github readiness is implemented",
            "m60 is implemented",
            "v0.64.0 implements m60",
            "local developer beta freeze is implemented",
            "production authority is implemented",
            "real execution is implemented",
        ):
            if self._active_version_tuple() >= (0, 63, 0) and fragment in {
                "m59 is implemented",
                "v0.63.0 implements m59",
                "public github readiness is implemented",
            }:
                continue
            if self._active_version_tuple() >= (0, 64, 0) and fragment in {
                "m60 is implemented",
                "v0.64.0 implements m60",
                "local developer beta freeze is implemented",
            }:
                continue
            if fragment in text:
                failures.append(f"M58 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m59_public_github_readiness_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/public_readiness/__init__.py",
            "src/ultimate_ai_agent/core/public_readiness/review.py",
            "docs/public_readiness/PUBLIC_GITHUB_READINESS.md",
            "docs/public_readiness/PUBLIC_GITHUB_READINESS_POLICY.md",
            "docs/public_readiness/PUBLIC_GITHUB_READINESS_AUTHORITY_BOUNDARY.md",
            "docs/public_readiness/M59_TO_M60_BOUNDARY.md",
            "tests/test_m59_public_github_readiness.py",
            "tests/test_m59_gate_integration.py",
        ]
        failures = [
            f"missing M59 public GitHub readiness file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.public_readiness import (
                PublicGitHubReadinessPolicy,
                PublicGitHubReadinessRequest,
                PublicGitHubReadinessStatus,
                build_public_github_readiness_report,
                validate_public_github_readiness_policy,
                validate_public_github_readiness_request,
            )

            request = PublicGitHubReadinessRequest(
                request_ref="public-readiness-request:m59-gate",
                readiness_ref="public-readiness:m59-gate",
                repository_ref="repo:ultimate-ai-agent",
                baseline_ref="baseline:v0.63.0",
                actor_ref="actor:gate-reviewer",
                checklist_refs=[
                    "readiness:docs-current",
                    "readiness:secret-hygiene",
                    "readiness:artifact-hygiene",
                    "readiness:route-boundary",
                    "readiness:dependency-boundary",
                ],
                safe_summary="Gate safe public GitHub readiness review.",
            )
            report = build_public_github_readiness_report(request)
            if report.status != PublicGitHubReadinessStatus.reviewed:
                failures.append("M59 public readiness report did not return reviewed status")
            if (
                not report.review_only
                or report.publication_performed
                or report.github_push_performed
                or report.github_release_performed
                or report.wiki_automation_performed
                or report.external_service_performed
                or report.production_authority_granted
                or report.side_effects_performed
            ):
                failures.append("M59 public readiness report performed publication or authority side effects")
            if report.receipt_plan is None:
                failures.append("M59 public readiness report did not include no-effect receipt plan")
            elif report.receipt_plan.publication_performed or report.receipt_plan.side_effects_performed:
                failures.append("M59 public readiness receipt performed publication side effects")
            for request_update, reason in [
                ({"publication_requested": True}, "PUBLICATION_DENIED"),
                ({"github_push_requested": True}, "GITHUB_PUSH_DENIED"),
                ({"github_release_requested": True}, "GITHUB_RELEASE_DENIED"),
                ({"wiki_automation_requested": True}, "WIKI_AUTOMATION_DENIED"),
                ({"artifact_upload_requested": True}, "ARTIFACT_UPLOAD_DENIED"),
                ({"credential_handling_requested": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                mutated_request = request.model_copy(update=request_update)
                try:
                    validate_public_github_readiness_request(mutated_request)
                    failures.append(f"M59 unsafe public readiness mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M59 unsafe public readiness reason drifted for {reason}: {exc}")
            try:
                validate_public_github_readiness_policy(
                    PublicGitHubReadinessPolicy(github_push_enabled=True)
                )
                failures.append("M59 unsafe public readiness policy flag was not denied")
            except ValueError as exc:
                if "GITHUB_PUSH_DENIED" not in str(exc):
                    failures.append(f"M59 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M59 public GitHub readiness validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "public github readiness",
            "review-only",
            "contract-only",
            "no github push",
            "no github release",
            "no wiki automation",
            "no artifact upload",
            "no external service",
            "no credential handling",
            "no production authority",
            "no backend route",
            "no dependency",
            "m60 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M59 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m59_public_github_readiness_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "publication_enabled=True",
            "github_push_enabled=True",
            "github_release_enabled=True",
            "wiki_automation_enabled=True",
            "artifact_upload_enabled=True",
            "external_service_enabled=True",
            "credential_handling_enabled=True",
            "network_access_enabled=True",
            "production_authority_enabled=True",
            "m60_beta_freeze_enabled=True",
            "publication_performed=True",
            "github_push_performed=True",
            "github_release_performed=True",
            "wiki_automation_performed=True",
            "artifact_upload_performed=True",
            "external_service_performed=True",
            "production_authority_granted=True",
            "/github/publish",
            "/github/release",
            "/github/wiki/update",
            "/public/artifacts/upload",
            "/public/release/publish",
            "/release/upload",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/public_readiness/review.py",
            "tests/test_m59_public_github_readiness.py",
            "tests/test_m59_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M59 forbidden public readiness fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m59_public_github_readiness_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m59_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M59 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m59_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M59 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.63.0" not in text or "m59" not in text or "public github readiness" not in text:
            failures.append("active docs do not identify v0.63.0/M59 Public GitHub Readiness")
        if "m59 is implemented/released" not in text and "v0.63.0 implements m59" not in text:
            failures.append("active docs do not mark M59 implemented/released")
        if not self._m60_currentness_marker_present(text):
            failures.append("M60 currentness marker is missing after M59")
        for fragment in (
            "m60 is implemented",
            "v0.64.0 implements m60",
            "local developer beta freeze is implemented",
            "production authority is implemented",
            "github publish automation is implemented",
            "wiki automation is implemented",
        ):
            if self._active_version_tuple() >= (0, 64, 0) and fragment in {
                "m60 is implemented",
                "v0.64.0 implements m60",
                "local developer beta freeze is implemented",
            }:
                continue
            if fragment in text:
                failures.append(f"M59 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m60_local_developer_beta_freeze_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/beta_freeze/__init__.py",
            "src/ultimate_ai_agent/core/beta_freeze/review.py",
            "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE.md",
            "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_POLICY.md",
            "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_AUTHORITY_BOUNDARY.md",
            "docs/beta/POST_M60_AUTONOMY_BOUNDARY.md",
            "tests/test_m60_local_developer_beta_freeze.py",
            "tests/test_m60_gate_integration.py",
        ]
        failures = [
            f"missing M60 local developer beta freeze file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.beta_freeze import (
                LocalDeveloperBetaFreezePolicy,
                LocalDeveloperBetaFreezeRequest,
                LocalDeveloperBetaFreezeStatus,
                build_local_developer_beta_freeze_report,
                validate_local_developer_beta_freeze_policy,
                validate_local_developer_beta_freeze_request,
            )

            request = LocalDeveloperBetaFreezeRequest(
                request_ref="beta-freeze-request:m60-gate",
                freeze_ref="beta-freeze:m60-gate",
                baseline_ref="baseline:v0.64.0",
                actor_ref="actor:gate-reviewer",
                checklist_refs=[
                    "beta-freeze:validation-green",
                    "beta-freeze:docs-current",
                    "beta-freeze:route-stable",
                    "beta-freeze:dependency-stable",
                    "beta-freeze:artifact-clean",
                    "beta-freeze:authority-frozen",
                ],
                safe_summary="Gate safe local developer beta freeze review.",
            )
            report = build_local_developer_beta_freeze_report(request)
            if report.status != LocalDeveloperBetaFreezeStatus.frozen:
                failures.append("M60 beta freeze report did not return frozen status")
            if (
                not report.freeze_only
                or not report.local_developer_beta_only
                or report.production_authority_granted
                or report.public_release_performed
                or report.external_distribution_performed
                or report.execution_performed
                or report.post_m60_autonomy_enabled
                or report.side_effects_performed
            ):
                failures.append("M60 beta freeze report performed release/autonomy/authority side effects")
            if report.receipt_plan is None:
                failures.append("M60 beta freeze report did not include no-effect receipt plan")
            elif report.receipt_plan.public_release_performed or report.receipt_plan.side_effects_performed:
                failures.append("M60 beta freeze receipt performed release side effects")
            for request_update, reason in [
                ({"public_release_requested": True}, "PUBLIC_RELEASE_DENIED"),
                ({"external_distribution_requested": True}, "EXTERNAL_DISTRIBUTION_DENIED"),
                ({"post_m60_autonomy_requested": True}, "POST_M60_AUTONOMY_DENIED"),
                ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"credential_handling_requested": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
            ]:
                mutated_request = request.model_copy(update=request_update)
                try:
                    validate_local_developer_beta_freeze_request(mutated_request)
                    failures.append(f"M60 unsafe beta freeze mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M60 unsafe beta freeze reason drifted for {reason}: {exc}")
            try:
                validate_local_developer_beta_freeze_policy(
                    LocalDeveloperBetaFreezePolicy(public_release_enabled=True)
                )
                failures.append("M60 unsafe beta freeze policy flag was not denied")
            except ValueError as exc:
                if "PUBLIC_RELEASE_DENIED" not in str(exc):
                    failures.append(f"M60 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M60 local developer beta freeze validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "local developer beta freeze",
            "freeze-only",
            "local developer beta only",
            "review-only",
            "no public release",
            "no external distribution",
            "no post-m60 autonomy",
            "no production authority",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network tools",
            "no browser automation",
            "no plugin execution",
            "no mobile sensor access",
            "no remote execution",
            "no credential handling",
            "no memory writes",
            "no context injection",
            "no model/provider calls",
            "no backend route",
            "no control center control",
            "no dependency",
            "m61+ remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M60 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m60_local_developer_beta_freeze_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "public_release_enabled=True",
            "external_distribution_enabled=True",
            "post_m60_autonomy_enabled=True",
            "production_authority_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "network_tool_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "mobile_sensor_enabled=True",
            "remote_execution_enabled=True",
            "credential_handling_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "model_provider_call_enabled=True",
            "public_release_performed=True",
            "external_distribution_performed=True",
            "execution_performed=True",
            "production_authority_granted=True",
            "/public/beta/release",
            "/github/release",
            "/autonomy/enable",
            "/remote/execute",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m60_local_developer_beta_freeze.py",
            "tests/test_m60_gate_integration.py",
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M60 forbidden beta freeze fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m60_local_developer_beta_freeze_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m60_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M60 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m60_final_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M60 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.64.0" not in text or "m60" not in text or "local developer beta freeze" not in text:
            failures.append("active docs do not identify v0.64.0/M60 Local Developer Beta Freeze")
        if "m60 is implemented/released" not in text and "v0.64.0 implements m60" not in text:
            failures.append("active docs do not mark M60 implemented/released")
        forbidden_fragments = [
            "post-m60 autonomy is implemented",
            "production authority is implemented",
            "public release is implemented",
            "external distribution is implemented",
        ]
        if self._active_version_tuple() < (0, 65, 0):
            forbidden_fragments.extend(["m61 is implemented", "m61-m80 is active"])
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M60 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m61_autonomy_mode_charter_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/modes.py",
            "tests/test_m61_autonomy_mode_charter.py",
            "docs/autonomy/AUTONOMY_MODE_CHARTER.md",
            "docs/autonomy/AUTHORITY_LEVELS.md",
            "docs/autonomy/CAPABILITY_TOGGLE_REGISTRY.md",
            "docs/autonomy/AUTONOMY_CONSENT_REVOCATION_POLICY.md",
            "docs/autonomy/M61_TO_M62_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
        ]
        failures = [
            f"missing M61 autonomy mode charter file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyCapabilityToggle,
                AutonomyModeCharter,
                AutonomyRiskClass,
                build_autonomy_mode_decision,
                validate_autonomy_capability_toggle,
                validate_autonomy_mode_charter,
            )

            charter = validate_autonomy_mode_charter(AutonomyModeCharter())
            if charter.default_mode != AutonomyAuthorityMode.off:
                failures.append("M61 autonomy charter default mode is not OFF")
            if not {
                AutonomyAuthorityMode.off,
                AutonomyAuthorityMode.observe_only,
                AutonomyAuthorityMode.dry_run_plan,
                AutonomyAuthorityMode.ask_before_every_action,
                AutonomyAuthorityMode.scoped_autonomy_window,
                AutonomyAuthorityMode.trusted_recurring_automation,
                AutonomyAuthorityMode.production_authority_later,
            }.issubset(set(charter.available_modes)):
                failures.append("M61 autonomy authority modes are incomplete")
            toggle = AutonomyCapabilityToggle(
                toggle_ref="autonomy-toggle:m61-gate",
                capability_ref="capability:observe-only-review",
                requested_mode=AutonomyAuthorityMode.off,
                actor_ref="actor:gate-reviewer",
                scope_ref="scope:m61-gate",
                resource_refs=["resource:local-prototype"],
                duration_seconds=0,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m61-gate",
                audit_ref="audit:m61-gate",
            )
            decision = build_autonomy_mode_decision(toggle, charter)
            if (
                decision.selected_mode != AutonomyAuthorityMode.off
                or decision.allowed
                or not decision.dry_run_only
                or decision.side_effects_performed
            ):
                failures.append("M61 autonomy decision granted authority or side effects")
            for update, reason in [
                ({"enabled": True}, "AUTONOMY_TOGGLE_ENABLEMENT_DENIED"),
                ({"requested_mode": AutonomyAuthorityMode.ask_before_every_action, "duration_seconds": 300}, "AUTONOMY_MODE_ENABLEMENT_DENIED"),
                ({"approval_test_ref": "approval_test_:m61"}, "APPROVAL_TEST_REF_DENIED"),
                ({"tool_execution_enabled": True}, "TOOL_EXECUTION_DENIED"),
                ({"shell_execution_enabled": True}, "SHELL_EXECUTION_DENIED"),
                ({"network_tool_enabled": True}, "NETWORK_TOOL_DENIED"),
                ({"browser_automation_enabled": True}, "BROWSER_AUTOMATION_DENIED"),
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                mutated_toggle = toggle.model_copy(update=update)
                try:
                    validate_autonomy_capability_toggle(mutated_toggle)
                    failures.append(f"M61 unsafe autonomy toggle mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M61 unsafe autonomy toggle reason drifted for {reason}: {exc}")
            for update, reason in [
                ({"default_mode": AutonomyAuthorityMode.dry_run_plan}, "AUTONOMY_DEFAULT_MODE_OFF_REQUIRED"),
                ({"global_autonomy_switch_enabled": True}, "GLOBAL_AUTONOMY_SWITCH_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
                ({"backend_routes_enabled": True}, "BACKEND_ROUTE_DENIED"),
                ({"dependencies_added": True}, "DEPENDENCY_ADDITION_DENIED"),
            ]:
                mutated_charter = charter.model_copy(update=update)
                try:
                    validate_autonomy_mode_charter(mutated_charter)
                    failures.append(f"M61 unsafe autonomy charter mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M61 unsafe autonomy charter reason drifted for {reason}: {exc}")
        except Exception as exc:
            failures.append(f"M61 autonomy mode charter validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "autonomy mode charter",
            "authority levels",
            "mode 0",
            "mode 1",
            "mode 2",
            "mode 3",
            "mode 4",
            "mode 5",
            "mode 6",
            "default mode off",
            "disabled by default",
            "dry-run first",
            "limited allowlist",
            "explicit approval",
            "scoped autonomy window",
            "audit/replay",
            "revocation",
            "no global autonomy switch",
            "no production authority",
            "no execution",
            "no tool execution",
            "no browser automation",
            "no shell execution",
            "no network tools",
            "no background worker",
            "no autonomous session",
            "no backend route",
            "no dependency",
            "m62 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M61 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m61_autonomy_mode_charter_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "global_autonomy_switch_enabled=True",
            "production_authority_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "network_tool_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "mobile_sensor_enabled=True",
            "remote_execution_enabled=True",
            "background_worker_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "model_provider_call_enabled=True",
            "backend_routes_enabled=True",
            "dependencies_added=True",
            "execution_performed=True",
            "production_authority_granted=True",
            "/autonomy/enable",
            "/autonomy/session/start",
            "/autonomy/execute",
            "/network/fetch",
            "/shell/execute",
            "/browser/click",
            "/plugins/execute",
            "/background/start",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/autonomy/modes.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m61_autonomy_mode_charter.py",
            "tests/test_m61_gate_integration.py",
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M61 forbidden autonomy fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m61_autonomy_mode_charter_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m61_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M61 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m61_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M61 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.65.0" not in text or "m61" not in text or "autonomy mode charter" not in text:
            failures.append("active docs do not identify v0.65.0/M61 Autonomy Mode Charter")
        if "m61 is implemented/released" not in text and "v0.65.0 implements m61" not in text:
            failures.append("active docs do not mark M61 implemented/released")
        for version_label, milestone, title in [
            ("v0.66.0", "M62", "Scoped Autonomy Session Contracts"),
            ("v0.67.0", "M63", "Autonomy Policy Engine v1"),
            ("v0.68.0", "M64", "Autonomous Plan Simulator"),
            ("v0.69.0", "M65", "Autonomy Audit + Replay Viewer"),
            ("v0.74.0", "M70", "Autonomy Foundation Freeze"),
            ("v0.80.0", "M76", "OpenWebUI Runtime Bridge v1"),
            ("v0.94.0", "M90", "Shell/Subprocess Hardening Freeze"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if version_label.lower() not in text or milestone.lower() not in text or title.lower() not in text:
                failures.append(f"active docs missing planned M61-M100 row: {version_label} / {milestone} — {title}")
        forbidden_fragments = [
            "m63 is implemented",
            "m64 is implemented",
            "production authority is implemented",
            "global autonomy switch is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ]
        if self._active_version_tuple() < (0, 66, 0):
            forbidden_fragments.append("m62 is implemented")
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"M61 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_m62_scoped_autonomy_session_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "tests/test_m62_scoped_autonomy_session_contracts.py",
            "docs/autonomy/SCOPED_AUTONOMY_SESSION_CONTRACTS.md",
            "docs/autonomy/SCOPED_AUTONOMY_SESSION_SCOPE_POLICY.md",
            "docs/autonomy/SCOPED_AUTONOMY_SESSION_NON_GOALS.md",
            "docs/autonomy/M62_TO_M63_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
        ]
        failures = [
            f"missing M62 scoped autonomy session file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyRiskClass,
                ScopedAutonomySessionRequest,
                ScopedAutonomySessionScope,
                build_scoped_autonomy_session_decision,
                validate_scoped_autonomy_session_request,
                validate_scoped_autonomy_session_scope,
            )

            scope = ScopedAutonomySessionScope(
                scope_ref="autonomy-session-scope:m62-gate",
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m62-gate"],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m62-gate",
                audit_ref="audit:m62-gate",
                replay_ref="replay:m62-gate",
            )
            validate_scoped_autonomy_session_scope(scope)
            request = ScopedAutonomySessionRequest(
                session_request_ref="autonomy-session-request:m62-gate",
                requested_mode=AutonomyAuthorityMode.dry_run_plan,
                scope=scope,
                approval_ref="approval:m62-review-only",
            )
            validated = validate_scoped_autonomy_session_request(request)
            decision = build_scoped_autonomy_session_decision(validated)
            if (
                not decision.contract_valid_for_review
                or decision.session_started
                or decision.session_active
                or decision.execution_performed
                or decision.side_effects_performed
            ):
                failures.append("M62 scoped session decision granted authority or side effects")
            for update, reason in [
                ({"start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
                ({"session_active": True}, "AUTONOMY_SESSION_ACTIVATION_DENIED"),
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"approval_test_ref": "approval_test_:m62"}, "APPROVAL_TEST_REF_DENIED"),
                (
                    {"requested_mode": AutonomyAuthorityMode.ask_before_every_action},
                    "AUTONOMY_MODE_ENABLEMENT_DENIED",
                ),
                (
                    {"requested_mode": AutonomyAuthorityMode.scoped_autonomy_window},
                    "AUTONOMY_MODE_FUTURE_MILESTONE_DENIED",
                ),
            ]:
                try:
                    validate_scoped_autonomy_session_request(request.model_copy(update=update))
                    failures.append(f"M62 unsafe session request mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M62 unsafe session request reason drifted for {reason}: {exc}")
            for update, reason in [
                ({"session_start_enabled": True}, "AUTONOMY_SESSION_START_DENIED"),
                ({"session_activation_enabled": True}, "AUTONOMY_SESSION_ACTIVATION_DENIED"),
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_scoped_autonomy_session_scope(scope.model_copy(update=update))
                    failures.append(f"M62 unsafe session scope mutation was not denied: {reason}")
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M62 unsafe session scope reason drifted for {reason}: {exc}")
        except Exception as exc:
            failures.append(f"M62 scoped autonomy session validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "scoped autonomy session contracts",
            "contract-only",
            "review-only",
            "actor-bound",
            "resource-bound",
            "duration-bound",
            "allowlist",
            "revocation",
            "audit/replay",
            "no session start",
            "no session activation",
            "no autonomous actions",
            "no background worker",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network tools",
            "no browser automation",
            "no backend route",
            "no dependency",
            "m63 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M62 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m62_scoped_autonomy_session_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "session_start_enabled=True",
            "session_activation_enabled=True",
            "start_requested=True",
            "session_active=True",
            "execution_requested=True",
            "autonomous_actions_enabled=True",
            "background_worker_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "network_tool_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "mobile_sensor_enabled=True",
            "remote_execution_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "production_authority_enabled=True",
            "execution_performed=True",
            "/autonomy/session/start",
            "/autonomy/session/activate",
            "/autonomy/session/run",
            "/autonomy/session/execute",
            "/autonomy/session/stop",
            "/background/start",
            "/network/fetch",
            "/shell/execute",
            "/browser/click",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m62_scoped_autonomy_session_contracts.py",
            "tests/test_m62_gate_integration.py",
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.swift", "*.yml", "*.yaml"):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if rel in allowed_files:
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(f"M62 forbidden scoped session fragment in {rel}: {fragment}")
        return self._result(criterion, failures, [])

    def check_m62_scoped_autonomy_session_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m62_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M62 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m62_roadmap_currentness(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M62 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.66.0" not in text or "m62" not in text or "scoped autonomy session contracts" not in text:
            failures.append("active docs do not identify v0.66.0/M62 Scoped Autonomy Session Contracts")
        if "m62 is implemented/released" not in text and "v0.66.0 implements m62" not in text:
            failures.append("active docs do not mark M62 implemented/released")
        for version_label, milestone, title in [
            ("v0.67.0", "M63", "Autonomy Policy Engine v1"),
            ("v0.68.0", "M64", "Autonomous Plan Simulator"),
            ("v0.69.0", "M65", "Autonomy Audit + Replay Viewer"),
            ("v0.70.0", "M66", "Scoped Approval Bundles"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if version_label.lower() not in text or milestone.lower() not in text or title.lower() not in text:
                failures.append(f"active docs missing planned M62-M100 row: {version_label} / {milestone} — {title}")
        for fragment in (
            "m63 is implemented",
            "autonomy policy engine is implemented",
            "session start is implemented",
            "session activation is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ):
            if fragment in text:
                failures.append(f"M62 docs imply forbidden/future capability: {fragment}")
        return self._result(criterion, failures, required_docs)

    def check_v0292_local_dev_api_authority_and_preview_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/core/tools/broker.py",
            "src/ultimate_ai_agent/core/truth/validation.py",
            "tests/test_kernel_api_routes.py",
            "tests/test_file_api_routes.py",
            "tests/test_api_safe_exception_messages.py",
        ]
        failures = [f"missing v0.29.2 hardening file: {path}" for path in required_files if not (self.root / path).exists()]
        try:
            from fastapi.testclient import TestClient

            from ultimate_ai_agent.api.app import app
            from ultimate_ai_agent.core.kernel import KernelTaskStatus, MinimumKernelRunner

            client = TestClient(app)
            def kernel_payload(workspace_root: Path, approval_ref: str):
                return {
                    "request_id": "ktr_gate_v0292",
                    "run_id": "run_gate_v0292",
                    "actor_context": {
                        "actor_type": "human_user",
                        "actor_id": "gate_user",
                        "authority_source": "explicit_user_request",
                    },
                    "user_id": "gate_user",
                    "workspace_root": str(workspace_root),
                    "task_type": "create_dev_file",
                    "user_request": "Create a local dev note.",
                    "target_path": "notes/m5.md",
                    "new_content": "# Gate\n",
                    "purpose": "create_dev_note",
                    "consent_grants": [
                        {
                            "consent_id": "consent_gate_v0292",
                            "subject_type": "user",
                            "subject_id": "gate_user",
                            "granted_to_actor": "gate_user",
                            "on_behalf_of_user_id": "gate_user",
                            "scope_type": "workspace",
                            "scope_id": "workspace_gate_v0292",
                            "allowed_actions": ["create", "update", "write"],
                            "allowed_resources": ["file.write.local_dev"],
                            "allowed_data_boundaries": ["project_private"],
                            "allowed_purposes": ["create_dev_note"],
                            "source": "foundation_gate",
                        }
                    ],
                    "approval_ref": approval_ref,
                    "idempotency_key": "idem_gate_v0292",
                    "data_classification": "project_private",
                    "tags": ["foundation_gate", "v0292"],
                }

            with tempfile.TemporaryDirectory(prefix="uaa-gate-v0292-kernel-") as probe_dir:
                probe_root = Path(probe_dir)
                payload = kernel_payload(probe_root, "approval_test_gate")
                response = client.post("/kernel/tasks/run", json=payload)
                if response.status_code != 200:
                    failures.append(f"kernel API dry-run probe returned HTTP {response.status_code}")
                else:
                    body = response.json()
                    data = body.get("data") or {}
                    if body.get("success") is not True or data.get("status") != KernelTaskStatus.dry_run:
                        failures.append("kernel API did not force local-dev mutation requests into dry-run")
                    if (probe_root / "notes" / "m5.md").exists():
                        failures.append("kernel API dry-run probe created a file")

                direct_result = MinimumKernelRunner().run_payload(kernel_payload(probe_root, "approval_test_gate"))
                if direct_result.success or "APPROVAL_REF_UNVALIDATED" not in direct_result.errors:
                    failures.append("kernel runner accepted a test-prefixed approval without authority")

            with tempfile.TemporaryDirectory(prefix="uaa-gate-v0292-preview-") as preview_dir:
                preview_root = Path(preview_dir)
                preview_file = preview_root / "note.txt"
                preview_file.write_text("hello", encoding="utf-8")
                preview_response = client.post(
                    "/files/read/preview",
                    json={
                        "workspace_root": str(preview_root),
                        "request": {
                            "request_id": "frr_gate_v0292",
                            "run_id": "run_gate_v0292",
                            "actor_context": {
                                "actor_type": "human_user",
                                "actor_id": "gate_user",
                                "authority_source": "explicit_user_request",
                            },
                            "path": "note.txt",
                            "purpose": "preview",
                            "max_bytes": 100,
                        },
                    },
                )
                if preview_response.status_code != 200:
                    failures.append(f"file preview probe returned HTTP {preview_response.status_code}")
                else:
                    preview_body = preview_response.json()
                    preview_data = preview_body.get("data") or {}
                    if preview_body.get("success") is not True:
                        failures.append("file preview metadata probe failed")
                    if preview_data.get("text_preview") != "":
                        failures.append("file preview API returned raw text content")
                    if "hello" in preview_response.text:
                        failures.append("file preview API echoed raw file content")
                    if "raw_content_omitted" not in preview_data.get("redactions_applied", []):
                        failures.append("file preview API did not mark raw content omitted")

            app_source = (self.root / "src" / "ultimate_ai_agent" / "api" / "app.py").read_text(encoding="utf-8")
            forbidden_exception_echo = (
                "safe_message=str(e)",
                "safe_message = str(e)",
                "detail=str(e)",
                "detail = str(e)",
            )
            failures.extend(
                f"API handler contains raw exception echo fragment: {fragment}"
                for fragment in forbidden_exception_echo
                if fragment in app_source
            )
        except Exception as exc:
            failures.append(f"v0.29.2 local-dev API hardening validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m25_m26_remains_future(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
        ]
        failures = [f"missing M25 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        if "v0.29.0" in text and "truth source router + evidence claim checker" in text:
            if "implemented/released" not in text:
                failures.append("M25 docs do not mark v0.29.0 implemented/released")
        else:
            failures.append("M25 docs do not mention v0.29.0 Truth Source Router + Evidence Claim Checker")
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        if version_tuple >= (0, 32, 0):
            if "v0.32.0" in text and "approval authority v2 + action policy expansion" in text:
                if "implemented/released" not in text:
                    failures.append("M28 docs must mark v0.32.0 implemented/released after M28")
            else:
                failures.append("M28 docs do not mention v0.32.0 Approval Authority v2 + Action Policy Expansion")
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append("M34-M60 must remain planned/provisional after v0.37.4")
            elif "m29-m40 remain planned/provisional" not in text:
                failures.append("M29-M40 must remain planned/provisional after M28")
        elif version_tuple >= (0, 31, 0):
            if "v0.31.0" in text and "tool broker v2 + safe tool intent contracts" in text:
                if "implemented/released" not in text:
                    failures.append("M27 docs must mark v0.31.0 implemented/released after M27")
            else:
                failures.append("M27 docs do not mention v0.31.0 Tool Broker v2 + Safe Tool Intent Contracts")
            if "m28-m40 remain planned/provisional" not in text:
                failures.append("M28-M40 must remain planned/provisional after M27")
        elif version_tuple >= (0, 30, 0):
            if "m26 is implemented/released" not in text and "v0.30.0 implements m26" not in text:
                failures.append("M26 docs must mark v0.30.0 implemented/released after M26")
            if "m27-m40 remain planned/provisional" not in text:
                failures.append("M27-M40 must remain planned/provisional after M26")
        else:
            if "v0.30.0 | m26" in text and "planned/provisional" not in text:
                failures.append("M26 roadmap row is not planned/provisional")
            if "m26 is implemented" in text or "v0.30.0 implements m26" in text:
                failures.append("M26 is incorrectly marked implemented")
            forbidden_m26_fragments = (
                "context injection implementation",
                "context-pack builder implemented",
                "grounded recall router implemented",
            )
            failures.extend(
                f"M25 docs imply M26 implementation: {fragment}"
                for fragment in forbidden_m26_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_open_design_governance_docs_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/design/OPEN_DESIGN_SYSTEM.md",
            "docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md",
            "docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md",
            "docs/design/ACCESSIBILITY_BASELINE.md",
            "docs/design/DESIGN_TOOLING_POLICY.md",
            "docs/design/DESIGN_TOKEN_ROADMAP.md",
            "docs/design/UI_COPY_AND_ACTION_LANGUAGE.md",
            "docs/design/DESIGN_ARTIFACT_GOVERNANCE.md",
            "docs/design/COMPONENT_TAXONOMY.md",
            "docs/design/RESPONSIVE_LAYOUT_BASELINE.md",
        ]
        failures = [f"missing design governance doc: {path}" for path in required_docs if not (self.root / path).exists()]
        design_text = "\n".join(self._read(self.root / path).lower() for path in required_docs)
        expectations = {
            "design docs missing no-tool-enable boundary": "no design tools are enabled",
            "design docs missing repo-owned source-of-truth boundary": "repo-owned source of truth",
            "design docs missing secret-free visual artifact boundary": (
                "screenshots and design artifacts must not contain secrets"
            ),
            "design docs missing no automatic design-to-code boundary": "no automatic design-to-code",
            "design docs missing no automatic design sync boundary": "no automatic design sync",
            "design docs missing no design SaaS authority boundary": "no design saas is authority",
        }
        for failure, fragment in expectations.items():
            if fragment not in design_text:
                failures.append(failure)

        control_center_docs = [
            "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
            "docs/control_center/FRONTEND_SAFETY_POLICY.md",
            "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
            "docs/control_center/LOCAL_BROWSER_SMOKE.md",
            "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md",
            "docs/control_center/LOCAL_BACKEND_CONNECTION.md",
        ]
        control_center_text = "\n".join(self._read(self.root / path) for path in control_center_docs)
        linked_docs = [
            "docs/design/OPEN_DESIGN_SYSTEM.md",
            "docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md",
            "docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md",
            "docs/design/ACCESSIBILITY_BASELINE.md",
            "docs/design/UI_COPY_AND_ACTION_LANGUAGE.md",
            "docs/design/COMPONENT_TAXONOMY.md",
            "docs/design/RESPONSIVE_LAYOUT_BASELINE.md",
        ]
        failures.extend(
            f"Control Center docs missing design governance link: {path}"
            for path in linked_docs
            if path not in control_center_text
        )
        return self._result(criterion, failures, [*required_docs, *control_center_docs])

    def check_openwebui_ccc_strategy_docs_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md",
            "docs/ui/CLIENT_SURFACE_ROLES.md",
            "docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md",
            "docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md",
        ]
        failures = [f"missing OpenWebUI/CCC strategy doc: {path}" for path in required_docs if not (self.root / path).exists()]
        ui_text = "\n".join(self._read(self.root / path).lower() for path in required_docs)
        expectations = {
            "UI strategy docs missing OpenWebUI chat shell boundary": (
                "openwebui is the preferred conversational web shell"
            ),
            "UI strategy docs missing OpenWebUI not-brain boundary": "openwebui is not the agent brain",
            "UI strategy docs missing CCC governance/control boundary": "ccc is the governance/control layer",
            "UI strategy docs missing Open Design relationship": "open design does not replace openwebui",
            "UI strategy docs missing no OpenWebUI integration boundary": "no openwebui integration is implemented",
            "UI strategy docs missing CCC Web definition": "ccc web is the current typescript web control center",
            "UI strategy docs missing CCC iOS definition": "ccc ios is a future native mobile control client",
            "UI strategy docs missing CCC Android definition": "ccc android is a future native mobile control client",
            "UI strategy docs missing CCC macOS definition": "ccc macos is a future desktop/local companion client",
            "UI strategy docs missing no native implementation boundary": "no ccc native implementation is added",
            "UI strategy docs missing no native build workflow boundary": "no native build workflow is added",
            "UI strategy docs missing no mobile sensor access boundary": "no mobile sensor access is added",
            "UI strategy docs missing no OS permission integration boundary": "no os permission integration is added",
        }
        for failure, fragment in expectations.items():
            if fragment not in ui_text:
                failures.append(failure)
        return self._result(criterion, failures, required_docs)

    def check_post_m20_roadmap_projection_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/ECOSYSTEM_WATCHLIST.md",
            "docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md",
        ]
        failures = [f"missing post-M20 roadmap doc: {path}" for path in required_docs if not (self.root / path).exists()]
        roadmap_text = "\n".join(self._read(self.root / path).lower() for path in required_docs if (self.root / path).exists())
        active_version = self._active_version() or "0.0.0"
        version_tuple = tuple(int(part) for part in active_version.split("."))
        expectations = {
            "post-M20 docs missing M21": "m21",
            "post-M20 docs missing M40": "m40",
            "post-M20 docs missing planned/provisional boundary": "planned/provisional",
            "post-M20 docs missing OpenWebUI bridge charter": "openwebui bridge + chat shell integration contract",
            "post-M20 docs missing local model runtime charter": "local model runtime activation contract",
            "post-M20 docs missing first local LLM charter": "first real local llm call",
            "post-M20 docs missing memory charter": "memory provider abstraction",
            "post-M20 docs missing grounded recall charter": "grounded recall router + evidence-linked context pack builder",
            "post-M20 docs missing Tool Broker v2 charter": "tool broker v2 + safe tool intent contracts",
            "post-M20 docs missing M31 tool runtime charter": (
                "real tool runtime adapter, single safe no-op tool"
            ),
        }
        if version_tuple >= (0, 37, 4):
            expectations.update(
                {
                    "post-M20 docs missing M35 safe file review charter": (
                        "safe file review workflow contracts"
                    ),
                    "post-M20 docs missing M38 context proposal charter": (
                        "safe context proposal from approved review"
                    ),
                    "post-M20 docs missing M39 CCC context proposal charter": (
                        "ccc context proposal surface"
                    ),
                    "post-M20 docs missing M40 no-injection handoff charter": (
                        "context handoff approval, no injection"
                    ),
                    "post-M20 docs missing M60 beta freeze charter": (
                        "local developer beta freeze"
                    ),
                }
            )
            if version_tuple >= (0, 38, 0):
                expectations["post-M20 docs missing M34 broader file capability review release"] = (
                    "m34 is implemented/released"
                )
        else:
            expectations.update(
                {
                    "post-M20 docs missing Device Capability Broker charter": (
                        "device capability broker implementation, no sensors"
                    ),
                    "post-M20 docs missing browser automation no-execution charter": (
                        "browser automation contract, no execution"
                    ),
                    "post-M20 docs missing observability charter": "observability export adapters",
                    "post-M20 docs missing eval harness charter": "agent evaluation + regression harness",
                }
            )
        for failure, fragment in expectations.items():
            if fragment not in roadmap_text:
                failures.append(failure)
        if version_tuple >= (0, 44, 0):
            implemented_claim_start = 41
        elif version_tuple >= (0, 43, 0):
            implemented_claim_start = 40
        elif version_tuple >= (0, 42, 0):
            implemented_claim_start = 39
        elif version_tuple >= (0, 41, 0):
            implemented_claim_start = 38
        elif version_tuple >= (0, 40, 0):
            implemented_claim_start = 37
        elif version_tuple >= (0, 39, 0):
            implemented_claim_start = 36
        elif version_tuple >= (0, 38, 0):
            implemented_claim_start = 35
        elif version_tuple >= (0, 37, 0):
            implemented_claim_start = 34
        elif version_tuple >= (0, 36, 0):
            implemented_claim_start = 33
        elif version_tuple >= (0, 35, 0):
            implemented_claim_start = 32
        elif version_tuple >= (0, 34, 0):
            implemented_claim_start = 31
        elif version_tuple >= (0, 33, 0):
            implemented_claim_start = 30
        elif version_tuple >= (0, 32, 0):
            implemented_claim_start = 29
        elif version_tuple >= (0, 31, 0):
            implemented_claim_start = 28
        elif version_tuple >= (0, 30, 0):
            implemented_claim_start = 27
        elif version_tuple >= (0, 29, 0):
            implemented_claim_start = 26
        elif version_tuple >= (0, 28, 0):
            implemented_claim_start = 25
        elif version_tuple >= (0, 27, 0):
            implemented_claim_start = 24
        elif version_tuple >= (0, 26, 0):
            implemented_claim_start = 23
        else:
            implemented_claim_start = 22
        implemented_claims = [f"m{number} is implemented" for number in range(implemented_claim_start, 41)]
        if version_tuple < (0, 44, 0):
            implemented_claims.extend(
                [
                    "m21-m40 are implemented",
                    "m21 through m40 are implemented",
                ]
            )
        implemented_claims.append("post-m20 capabilities are implemented")
        if any(claim in roadmap_text for claim in implemented_claims):
            failures.append("post-M20 roadmap docs must not claim future milestone implementation")
        return self._result(criterion, failures, required_docs)

    def _skipped(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        return FoundationGateResult(
            criterion_id=criterion.criterion_id,
            status=FoundationGateStatus.skipped,
            safe_message="No evaluator registered for criterion.",
            warnings=["missing evaluator"],
        )

    def _result(
        self,
        criterion: FoundationGateCriterion,
        failures: List[str],
        evidence_refs: List[str],
        warnings: Optional[List[str]] = None,
    ) -> FoundationGateResult:
        status = FoundationGateStatus.failed if failures else FoundationGateStatus.passed
        return FoundationGateResult(
            criterion_id=criterion.criterion_id,
            status=status,
            safe_message=criterion.failure_message if failures else f"{criterion.name} passed.",
            evidence_refs=evidence_refs,
            failures=failures,
            warnings=warnings or [],
        )

    def _active_version(self) -> Optional[str]:
        return self._regex_first(self.root / "VERSION.md", r"Current active baseline:\s*\*\*v?(\d+\.\d+\.\d+)\*\*")

    def _active_version_tuple(self) -> tuple[int, int, int]:
        version = self._active_version() or "0.0.0"
        return tuple(int(part) for part in version.split("."))  # type: ignore[return-value]

    def _m60_currentness_marker_present(self, text: str) -> bool:
        if self._active_version_tuple() >= (0, 64, 0):
            return "m60 is implemented/released" in text or "v0.64.0 implements m60" in text
        return "m60 remains planned/provisional" in text

    def _append_post_m48_mobile_status_failures(self, text: str, failures: List[str]) -> None:
        if self._active_version_tuple() >= (0, 57, 0):
            if "m49 is implemented/released" not in text and "v0.53.0 implements m49" not in text:
                failures.append("M49 must be implemented/released after v0.53.0")
            if "m50 is implemented/released" not in text and "v0.54.0 implements m50" not in text:
                failures.append("M50 must be implemented/released after v0.54.0")
            if "m51 is implemented/released" not in text and "v0.55.0 implements m51" not in text:
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52 is implemented/released" not in text and "v0.56.0 implements m52" not in text:
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53 is implemented/released" not in text and "v0.57.0 implements m53" not in text:
                failures.append("M53 must be implemented/released after v0.57.0")
            if (
                "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M54-M60 must remain planned/provisional after M53")
        elif self._active_version_tuple() >= (0, 56, 0):
            if "m49 is implemented/released" not in text and "v0.53.0 implements m49" not in text:
                failures.append("M49 must be implemented/released after v0.53.0")
            if "m50 is implemented/released" not in text and "v0.54.0 implements m50" not in text:
                failures.append("M50 must be implemented/released after v0.54.0")
            if "m51 is implemented/released" not in text and "v0.55.0 implements m51" not in text:
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52 is implemented/released" not in text and "v0.56.0 implements m52" not in text:
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53-m60 remain planned/provisional" not in text:
                failures.append("M53-M60 must remain planned/provisional after M52")
        elif self._active_version_tuple() >= (0, 55, 0):
            if "m49 is implemented/released" not in text and "v0.53.0 implements m49" not in text:
                failures.append("M49 must be implemented/released after v0.53.0")
            if "m50 is implemented/released" not in text and "v0.54.0 implements m50" not in text:
                failures.append("M50 must be implemented/released after v0.54.0")
            if "m51 is implemented/released" not in text and "v0.55.0 implements m51" not in text:
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52-m60 remain planned/provisional" not in text:
                failures.append("M52-M60 must remain planned/provisional after M51")
        elif self._active_version_tuple() >= (0, 54, 0):
            if "m49 is implemented/released" not in text and "v0.53.0 implements m49" not in text:
                failures.append("M49 must be implemented/released after v0.53.0")
            if "m50 is implemented/released" not in text and "v0.54.0 implements m50" not in text:
                failures.append("M50 must be implemented/released after v0.54.0")
            if "m51-m60 remain planned/provisional" not in text:
                failures.append("M51-M60 must remain planned/provisional after M50")
        elif self._active_version_tuple() >= (0, 53, 0):
            if "m49 is implemented/released" not in text and "v0.53.0 implements m49" not in text:
                failures.append("M49 must be implemented/released after v0.53.0")
            if "m50-m60 remain planned/provisional" not in text:
                failures.append("M50-M60 must remain planned/provisional after M49")
        elif "m49-m60 remain planned/provisional" not in text:
            failures.append("M49-M60 must remain planned/provisional after M48")

    def _regex_first(self, path: Path, pattern: str) -> Optional[str]:
        match = re.search(pattern, self._read(path))
        return match.group(1) if match else None

    def _runtime_lines(self) -> Iterable[tuple[str, int, str]]:
        for rel_path in self._tracked_runtime_files():
            for line_no, line in enumerate(self._read(self.root / rel_path).splitlines(), start=1):
                yield rel_path, line_no, line.strip()

    def _tracked_runtime_files(self) -> List[str]:
        if not self.src_root.exists():
            return []
        files = []
        for path in sorted(self.src_root.rglob("*.py")):
            rel_path = str(path.relative_to(self.root))
            if "__pycache__" not in rel_path:
                files.append(rel_path)
        return files

    def _read(self, path: Path) -> str:
        if not path.exists() or not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def _is_static_scanner_text(self, stripped: str) -> bool:
        return (
            stripped.startswith(('"', "'", "#"))
            or " = [" in stripped
            or " = (" in stripped
            or stripped.startswith(("forbidden = ", "forbidden_starts = ", "forbidden_contains = "))
            or stripped.startswith('if ".get(" in stripped')
        )

    def _m8_gate_manifest(self) -> dict:
        return {
            "adapter_id": "m8_gate_adapter",
            "runtime_kind": "simulated",
            "display_name": "M8 Gate Simulated Adapter",
            "description": "Deterministic simulated adapter for Foundation Gate checks.",
            "supported_provider_kinds": ["local_runtime"],
            "supported_capabilities": ["chat"],
            "safety_mode": "simulated",
            "accepts_model_profile_ids": ["m8_gate_profile"],
            "requires_credential_ref": False,
            "allowed_credential_refs": [],
            "supports_streaming": False,
            "supports_tools": False,
            "supports_json_mode": True,
            "supports_structured_output": True,
            "max_context_tokens": 8192,
            "max_input_tokens": 1024,
            "max_output_tokens": 512,
            "owner": "foundation_gate",
            "source": "foundation_gate",
            "version": "0.0.0",
            "enabled": True,
        }

    def _m8_gate_request(self) -> dict:
        return {
            "runtime_request_id": "m8_gate_request",
            "run_id": "run_foundation_gate",
            "model_profile_id": "m8_gate_profile",
            "model_id": "m8_gate_model",
            "adapter_id": "m8_gate_adapter",
            "actor_context": self._actor().model_dump(mode="json"),
            "prompt_summary": "Summarize referenced context safely.",
            "input_refs": ["context_pack:m8_gate"],
            "output_format": "text",
            "estimated_input_tokens": 10,
            "max_output_tokens": 10,
            "safety_mode": "simulated",
            "data_classification": {
                "classification": "project_private",
                "source": "foundation_gate",
            },
        }

    def _m85_gate_approval_request(self, subject_id: str = "m85_gate_subject"):
        from datetime import timedelta

        from ultimate_ai_agent.core.approvals import ApprovalRequest, ApprovalRiskLevel, ApprovalSubjectType
        from ultimate_ai_agent.core.time import utc_now

        return ApprovalRequest(
            approval_request_id=f"areq_{subject_id}",
            run_id="run_foundation_gate",
            subject_type=ApprovalSubjectType.model_route,
            subject_id=subject_id,
            actor_context=self._actor(),
            requested_action="route_cloud_model",
            purpose="Foundation Gate approval authority check.",
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(classification=ClassificationValue.sensitive_personal, source="foundation_gate"),
            resource_refs=["m7_gate_cloud"],
            consent_refs=["consent_foundation_gate"],
            expires_at=utc_now() + timedelta(minutes=30),
        )

    def _m85_runtime_manifest(self):
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeAdapterManifest, ModelRuntimeKind, ModelRuntimeSafetyMode

        return ModelRuntimeAdapterManifest(
            adapter_id="m85_gate_adapter",
            runtime_kind=ModelRuntimeKind.simulated,
            display_name="M8.5 Gate Simulated Adapter",
            description="Simulated adapter for M8.5 approval checks.",
            supported_provider_kinds=["cloud_provider", "local_runtime"],
            supported_capabilities=["chat"],
            safety_mode=ModelRuntimeSafetyMode.simulated,
            accepts_model_profile_ids=["m7_gate_cloud"],
            requires_credential_ref=False,
            allowed_credential_refs=[],
            supports_streaming=False,
            supports_tools=False,
            supports_json_mode=True,
            supports_structured_output=True,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
            enabled=True,
        )

    def _m9_loopback_endpoint(self):
        from ultimate_ai_agent.core.model_runtime import LoopbackRuntimeEndpoint, ModelRuntimeKind

        return LoopbackRuntimeEndpoint(
            endpoint_id="m9_gate_loopback",
            base_url="http" + "://127.0.0.1:11434/api/generate",
            allowed_hosts=["127.0.0.1", "localhost", "::1"],
            runtime_kind=ModelRuntimeKind.local_stub,
            model_id="local_policy_model",
            enabled=True,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
        )

    def _m9_loopback_policy(self):
        from ultimate_ai_agent.core.model_runtime import LoopbackRuntimePolicy

        return LoopbackRuntimePolicy(
            policy_id="m9_gate_policy",
            allow_real_loopback_execution=True,
            max_input_tokens=4096,
            max_output_tokens=1024,
        )

    def _m9_runtime_manifest(self):
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeAdapterManifest, ModelRuntimeKind, ModelRuntimeSafetyMode

        return ModelRuntimeAdapterManifest(
            adapter_id="m9_gate_adapter",
            runtime_kind=ModelRuntimeKind.local_stub,
            display_name="M9 Gate Local Loopback Adapter",
            description="Local/dev loopback adapter for Foundation Gate checks.",
            supported_provider_kinds=["local_runtime"],
            supported_capabilities=["chat"],
            safety_mode=ModelRuntimeSafetyMode.local_loopback_dev,
            accepts_model_profile_ids=["m7_gate_local"],
            requires_credential_ref=False,
            allowed_credential_refs=[],
            supports_streaming=False,
            supports_tools=False,
            supports_json_mode=True,
            supports_structured_output=True,
            max_context_tokens=8192,
            max_input_tokens=4096,
            max_output_tokens=1024,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
            enabled=True,
        )

    def _m9_runtime_request(self, approval_ref: Optional[str] = None):
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeOutputFormat, ModelRuntimeRequest, ModelRuntimeSafetyMode

        return ModelRuntimeRequest(
            runtime_request_id="m9_gate_runtime_request",
            run_id="run_foundation_gate",
            route_decision_ref="m9_gate_selected_route",
            model_profile_id="m7_gate_local",
            model_id="local_policy_model",
            adapter_id="m9_gate_adapter",
            actor_context=self._actor(),
            prompt_summary="Foundation Gate local loopback metadata check.",
            input_refs=["context_pack:m9_gate"],
            output_format=ModelRuntimeOutputFormat.text,
            estimated_input_tokens=100,
            max_output_tokens=50,
            safety_mode=ModelRuntimeSafetyMode.local_loopback_dev,
            data_classification=DataClassification(classification=ClassificationValue.project_private, source="foundation_gate"),
            consent_refs=["consent_foundation_gate"],
            approval_ref=approval_ref,
            secret_handle_refs=[],
            event_ref="evt_m9_gate",
            trace_id="trace_m9_gate",
            metadata={"route_reason_codes": ["SELECTED_PROFILE"]},
        )

    def _m10_smoke_endpoint(self, **overrides):
        from ultimate_ai_agent.core.model_runtime import LoopbackRuntimeEndpoint, ModelRuntimeKind

        payload = {
            "endpoint_id": "m10_gate_smoke_endpoint",
            "base_url": "http" + "://127.0.0.1:11434/api/generate",
            "allowed_hosts": ["127.0.0.1", "localhost", "::1"],
            "runtime_kind": ModelRuntimeKind.local_stub,
            "model_id": "m10_gate_smoke_model",
            "enabled": True,
            "owner": "foundation_gate",
            "source": "foundation_gate",
            "version": "0.0.0",
        }
        payload.update(overrides)
        return LoopbackRuntimeEndpoint(**payload)

    def _m10_smoke_request(self, **overrides):
        from ultimate_ai_agent.core.model_runtime import DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT, ManualLoopbackSmokePolicy, ManualLoopbackSmokeRequest

        payload = {
            "smoke_request_id": "m10_gate_smoke_request",
            "run_id": "run_foundation_gate",
            "endpoint": self._m10_smoke_endpoint(),
            "model_id": "m10_gate_smoke_model",
            "approval_ref": "approval_m10_gate",
            "fixed_prompt": DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT,
            "expected_marker": "UAA_LOCAL_SMOKE_OK",
            "policy": ManualLoopbackSmokePolicy(policy_id="m10_gate_smoke_policy", enable_manual_smoke=True),
            "actor_context": self._actor(),
            "data_classification": DataClassification(classification=ClassificationValue.public, source="foundation_gate"),
        }
        payload.update(overrides)
        return ManualLoopbackSmokeRequest(**payload)

    def _m105_node_registry(self):
        from ultimate_ai_agent.core.remote_workers import (
            NodeCapabilitySet,
            NodeIdentity,
            RemoteNode,
            RemoteNodeRegistry,
            RemoteNodeStatus,
        )

        registry = RemoteNodeRegistry()
        registry.register_node(
            RemoteNode(
                node_id="mock_node",
                identity=NodeIdentity(
                    node_id="mock_node",
                    display_name="Mock Node",
                    owner="foundation_gate",
                    source="foundation_gate",
                    version="0.0.0",
                ),
                status=RemoteNodeStatus.mock_available,
                capabilities=NodeCapabilitySet(),
                allowed_transport_ids=["mock_metadata"],
            )
        )
        return registry

    def _m105_transport_registry(self):
        from ultimate_ai_agent.core.remote_workers import default_remote_transport_registry

        return default_remote_transport_registry()

    def _m105_remote_job(self, **overrides):
        from ultimate_ai_agent.core.remote_workers import RemoteAuditContext, RemoteJobEnvelope, RemoteRiskLevel

        payload = {
            "job_id": "m105_gate_job",
            "correlation_id": "m105_gate_corr",
            "node_id": "mock_node",
            "transport_id": "mock_metadata",
            "task_summary": "Validate remote worker dry-run metadata.",
            "requested_capabilities": ["dry_run"],
            "risk_level": RemoteRiskLevel.low,
            "audit_context": RemoteAuditContext(
                run_id="run_foundation_gate",
                correlation_id="m105_gate_corr",
                actor_context=self._actor(),
            ),
        }
        payload.update(overrides)
        return RemoteJobEnvelope(**payload)

    def _actor(self) -> ActorContext:
        return ActorContext(
            actor_type=ActorType.system_worker,
            actor_id="foundation_gate",
            authority_source=AuthoritySource.system_policy,
        )

    def _gate_local_profile(
        self,
        cost_per_1k_input_tokens: Optional[float] = None,
        cost_per_1k_output_tokens: Optional[float] = None,
    ) -> ModelCapabilityProfile:
        return ModelCapabilityProfile(
            model_profile_id="m7_gate_local",
            provider_kind=ModelProviderKind.local_runtime,
            runtime_id="rt_gate",
            model_id="local_policy_model",
            display_name="Local Policy Model",
            capabilities=[ModelTaskCapability.chat, ModelTaskCapability.coding],
            privacy_class=ModelPrivacyClass.local_only,
            max_context_tokens=8192,
            cost_per_1k_input_tokens=cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=cost_per_1k_output_tokens,
            enabled=True,
            owner="core.gate",
            source="foundation_gate",
            version="0.0.0",
        )

    def _gate_cloud_profile(self) -> ModelCapabilityProfile:
        return ModelCapabilityProfile(
            model_profile_id="m7_gate_cloud",
            provider_kind=ModelProviderKind.cloud_provider,
            provider_id="provider_gate",
            model_id="cloud_policy_model",
            display_name="Cloud Policy Model",
            capabilities=[ModelTaskCapability.chat],
            privacy_class=ModelPrivacyClass.cloud_allowed,
            max_context_tokens=8192,
            cost_per_1k_input_tokens=0.01,
            cost_per_1k_output_tokens=0.03,
            enabled=True,
            owner="core.gate",
            source="foundation_gate",
            version="0.0.0",
        )

    def _gate_route_request(
        self,
        profile: ModelCapabilityProfile,
        data_classification: ClassificationValue = ClassificationValue.project_private,
        approval_ref: Optional[str] = None,
        context_budget: Optional[ContextBudget] = None,
        policy: Optional[ModelRoutingPolicy] = None,
    ) -> ModelRouteRequest:
        return ModelRouteRequest(
            request_id="m7_gate_route_policy",
            run_id="run_foundation_gate",
            actor_context=self._actor(),
            task_class="coding",
            prompt_summary="Foundation Gate model routing metadata check.",
            data_classification=DataClassification(classification=data_classification, source="foundation_gate"),
            required_capabilities=[ModelTaskCapability.chat],
            estimated_input_tokens=1000,
            estimated_output_tokens=500,
            context_budget=context_budget,
            routing_policy=policy
            or ModelRoutingPolicy(
                policy_id="m7_gate_route_policy",
                required_capabilities=[ModelTaskCapability.chat],
                prefer_local=True,
                allow_cloud=False,
                allow_paid=False,
            ),
            available_profiles=[profile],
            approval_ref=approval_ref,
        )
