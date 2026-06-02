# Ultimate AI Agent Canonical Bundle v0.23.1

This is the active project baseline after v0.23.1 / M19 Roadmap Status + Mobile Contract Safety Hardening.

Start here:

```text
README_IMPORT_v0_23_1.md
ultimate_ai_agent_master_plan_v0_23_1.md
docs/DOCUMENTATION_INDEX.md
docs/canonical/09_roadmap.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/roadmap/MILESTONE_CHARTERS.md
docs/roadmap/NEXT_SEQUENCE_v0_17_5.md
docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md
docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md
docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md
docs/roadmap/ECOSYSTEM_WATCHLIST.md
docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md
docs/canonical/21_consent_and_permissions_ledger.md
docs/canonical/37_tool_broker.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/63_observability_standards_mapping.md
docs/canonical/64_mobile_companion_and_device_capability_broker.md
docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md
docs/canonical/66_external_tooling_and_codex_plugin_governance.md
docs/mobile/MOBILE_COMPANION_CONTRACT.md
docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md
docs/mobile/MOBILE_API_PLANNING.md
docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md
docs/mobile/MOBILE_SENSOR_BOUNDARY.md
docs/mobile/MOBILE_SECURITY_MODEL.md
docs/mobile/MOBILE_CAPTURE_POLICY.md
docs/mobile/CCC_IOS_ANDROID_STRATEGY.md
docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md
docs/mobile/MOBILE_COMPANION_NON_GOALS.md
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
docs/control_center/CONTROL_CENTER_CONTRACT.md
docs/control_center/DASHBOARD_SNAPSHOT.md
docs/control_center/ACTION_PREVIEW_POLICY.md
docs/control_center/WEB_CONTROL_CENTER_SHELL.md
docs/control_center/FRONTEND_SAFETY_POLICY.md
docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md
docs/control_center/LOCAL_BACKEND_CONNECTION.md
docs/control_center/LOCAL_BROWSER_SMOKE.md
docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md
docs/control_center/APPROVAL_QUEUE_UI.md
docs/control_center/RECEIPT_EVENT_VIEWER.md
docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md
docs/control_center/EVENT_TIMELINE_UI.md
docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md
docs/control_center/TRACE_REDACTION_POLICY.md
docs/control_center/EVIDENCE_VIEWER.md
docs/control_center/FILE_REFERENCE_VIEWER.md
docs/control_center/MEMORY_VIEWER.md
docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md
docs/control_center/LOCAL_RUNTIME_STATUS_UI.md
docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md
docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md
docs/design/OPEN_DESIGN_SYSTEM.md
docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md
docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md
docs/design/ACCESSIBILITY_BASELINE.md
docs/design/DESIGN_TOOLING_POLICY.md
docs/design/DESIGN_TOKEN_ROADMAP.md
docs/design/UI_COPY_AND_ACTION_LANGUAGE.md
docs/design/DESIGN_ARTIFACT_GOVERNANCE.md
docs/design/COMPONENT_TAXONOMY.md
docs/design/RESPONSIVE_LAYOUT_BASELINE.md
docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md
docs/ui/CLIENT_SURFACE_ROLES.md
docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md
docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md
docs/runtime/model_runtime_adapter_harness.md
docs/runtime/local_loopback_model_runtime.md
docs/runtime/RUNTIME_READINESS.md
docs/runtime/MANUAL_SMOKE_REPORTS.md
docs/runtime/RUNTIME_CAPABILITY_MATRIX.md
docs/security/approval_authority.md
docs/implementation/foundation_gate_implementation_plan_v0_23_1.md
docs/maintenance/documentation_integrity_checklist.md
docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md
docs/tooling/CODEX_PLUGIN_RISK_POLICY.md
docs/testing/test_strategy_v0.md
```

Core rule:

> Do not build scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, provider-specific integrations, or external high-autonomy execution before the kernel, memory/files, event ledger, permission model, Tool Broker, Model Router, Cost Governor, Secret Broker, Provider Registry, Truth Source Router, Evidence Manifest, API boundary, rollback primitives, runtime hygiene contracts, context survival contracts, local runtime profiles, SDK/A2A adapter boundaries, observability standards mapping, and contract tests work.

Stack rule:

> Python Agent Core is the brain. OpenWebUI is the preferred conversational web shell, not the agent brain. CCC means Control Center Clients: CCC Web, CCC iOS, CCC Android, and CCC macOS. CCC is the governance/control client family and must use Python Agent Core authority.

Truth-source rule:

> The model is never the source of truth. Governed source systems, canonical files, approved APIs, databases, source documents, Event Ledger records, World State snapshots, and evidence manifests define truth. Memory helps recall; it does not outrank canonical truth.

Observability standards rule:

> The Event Ledger remains the source of truth for agent actions, but M2 events must be mappable to OpenTelemetry GenAI semantic conventions and W3C Trace Context. Future event exports should be compatible with CloudEvents and, where message-driven APIs are introduced, documented with AsyncAPI.

Foundation Gate rule:

> v0.14.3 keeps REMOTE-01 / M10.5 foundation-only and adds open-source-first private mesh taxonomy. Headscale, generic WireGuard, Tailscale, private mesh, tailnet, and LAN transports are planned/disabled metadata only. Headscale is the first planned self-hosted/open-source control-plane option to evaluate; Tailscale remains planned metadata, not the default assumption. It adds no live mesh networking, Headscale integration, Tailscale integration, WireGuard command execution, listener, network call, job dispatch, remote subagent launch, remote Tool Broker execution, sandbox execution, personal-data access, write/send action, remote approval, background service, production persistence, provider SDK, tokenizer, billing API, credentials, node keys, hostnames, private IPs, or safety bypass.

Developer command rule:

```text
make doctor
make test
make verify
make frontend-check
```

Use `.venv/bin/python`, not bare `python`, for repo verification commands. Shell aliases are not reliable in Codex and other non-interactive shells, and no global Python alias is required.

Local runtime status rule:

> v0.22.0 implements M18 Local Runtime Status + Manual Smoke Control Surface in CCC Web only. `/runtime/local` is read-only local runtime status, and `/runtime/manual-smoke` is validation-only manual smoke report summary display. OpenAPI path count remains `74` and no backend route is added. Manual smoke execution remains CLI-only, fixed-prompt-only, approval-gated, and non-authoritative. This release adds no runtime execution, manual smoke execution, model/provider call, local runtime provider integration, remote execution, mobile sensor access, plugin enablement, OpenWebUI integration, dependency, production persistence, raw smoke report display, raw prompts, raw response bodies, credentials, provider payloads, or production Control Center authority.

Roadmap status label cleanup rule:

> v0.23.1 hardens M19 Mobile Companion Contract/API Planning and cleans up roadmap currentness after v0.23.0. v0.23.0 / M19 is implemented/released as contract/API planning only, while M20 and M21-M40 remain planned/provisional. v0.23.1 deepens tests and verifier coverage for contacts/calendar capability denial, secret-like metadata refs, external-send blocking, OS-permission integration blocking, and background-service blocking. OpenAPI path count remains `74`. This release adds no M20 Device Capability Broker, backend API route, frontend feature, Android app, iOS app, macOS app, native build workflow, OS permission integration, mobile sensor access, push notification runtime, background service, mobile approval execution, runtime execution, manual smoke execution, model/provider call, remote execution, plugin enablement, OpenWebUI integration, dependency, architecture behavior change, or production Control Center authority.

Mobile planning rule:

> v0.14.4 adds Mobile Companion and Device Capability Broker roadmap planning only. A future phone app may become a control, approval, capture, receipt, and status surface, but the phone is not the agent brain and mobile sensors are disabled by default. This patch adds no mobile app, iOS code, Android code, React Native, Expo, Flutter, Swift, Kotlin, native mobile package, sensor access, OS permission integration, pairing flow, background service, notification runtime, network call, autonomous mobile action, or runtime device capability execution.

Documentation integrity rule:

> v0.14.5 keeps active docs synchronized with the accepted baseline. Active docs must distinguish implemented, validation-only, dry-run-only, simulated-only, manual-only, planned/disabled, future/backlog, historical, and blocked capabilities. This patch adds no real model/provider/network/remote/mobile sensor execution and no new runtime power.

Codex plugin governance rule:

> v0.14.6 records Codex plugin and external build tool capability classes as governance documentation only. Browser + Build Web Apps may be considered for future Web Control Center work with approval. Chrome authenticated profile control, Computer Use, iOS/macOS build plugins, Hugging Face Jobs/uploads/training, and plugin/skill installers remain disabled unless a future milestone explicitly approves them. This patch adds no plugin enablement, native build workflow, dependency, network call, or runtime capability.

Runtime readiness rule:

> v0.15.0 adds M11 runtime readiness reports, a deterministic capability matrix, manual smoke report validation, three runtime status/validation API routes, and Foundation Gate coverage. It does not add runtime execution, cloud/provider calls, remote execution, live private mesh/tailnet support, Headscale/Tailscale/WireGuard calls, mobile sensor access, plugin/tool enablement, native builds, browser automation, production persistence, or production readiness claims. Model output remains non-authoritative.

Runtime taxonomy clarification rule:

> v0.15.1 clarifies M11 terminology only. `local_loopback_policy` is a supported validation-only contract; real smoke execution remains manual-only, approval-gated, fixed-prompt-only, and non-authoritative. `fake_manual_loopback_smoke` is an allowed fake/test manual smoke report origin, not production evidence and not a live runtime origin. This patch adds no runtime execution, route, dependency, provider call, remote execution, mobile sensor access, plugin enablement, or production readiness claim.

Control Center contract rule:

> v0.16.0 adds M12 backend Control Center contracts, read-only dashboard snapshots, preview-only action decisions, and read-only/preview-only API endpoints. It does not add a frontend app, TypeScript UI, React, Next.js, Vite, shadcn, Tailwind, Build Web Apps, Browser, Chrome, Computer Use, iOS/macOS build workflow, runtime execution, model/provider calls, network calls, remote execution, mobile sensor access, plugin enablement, or production Control Center. The Control Center is not the agent brain and cannot bypass Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, or Foundation Gate.

Web Control Center shell rule:

> v0.17.0 adds M13 local React/Vite/TypeScript Web Control Center shell files under `apps/control-center/`. The shell reads existing backend status/manifest/dashboard/readiness routes, renders safe mock fallback data when the backend is unavailable, and submits only preview-only requests to `/control-center/actions/preview`. It adds no backend API path, production Control Center authority, public execution API, runtime/model/provider call, remote dispatch, mobile/native app, sensor access, plugin enablement, Chrome authenticated profile control, Computer Use automation, iOS/macOS build workflow, analytics/auth/payment/SaaS SDK, production persistence, or external action.

Web Control Center safety polish rule:

> v0.17.1 hardens the M13 shell without starting M14. The action preview UI is explicitly preview-only, endpoint allowlists are typed, blocked preview decisions remain visible as safe non-execution results, mock fixtures remain non-authoritative, and `scripts/verify_control_center_frontend.py` plus Foundation Gate checks reject forbidden execution/plugin/mobile/remote endpoints, dangerous action labels, sensitive browser storage, browser credential APIs, camera/microphone/location/notification/push APIs, native build references, and secret-like fixture values. It adds no runtime/model/provider/network/remote/mobile/plugin execution, no production Control Center authority, no Chrome authenticated profile control, no Computer Use automation, and no iOS/macOS build workflow.

Web Control Center verification hardening rule:

> v0.17.2 hardens the M13 shell verification path without starting M14. CI now runs frontend dependency install, typecheck, lint, tests, and build inside `apps/control-center`; browser smoke readiness is documented as manual local-only and non-authoritative; and static verifiers plus Foundation Gate checks reject unsafe frontend CI, browser, plugin, mobile, native, remote, execution, analytics/SaaS SDK, generated artifact, and secret fixture drift. It adds no backend API path, runtime/model/provider/network/remote/mobile/plugin execution, production Control Center authority, Chrome authenticated profile control, Computer Use automation, or iOS/macOS build workflow.

Documentation current-release label rule:

> v0.17.3 cleans up active documentation labels without starting M14. The documentation index points to the active v0.17.3 release notes, older v0.17.x release notes are historical, and the documentation integrity verifier rejects stale current-release note labels. It adds no backend API path, frontend capability, runtime/model/provider/network/remote/mobile/plugin execution, production Control Center authority, Chrome authenticated profile control, Computer Use automation, or iOS/macOS build workflow.

Web Control Center local smoke polish rule:

> v0.17.4 polishes the existing read-only Web Control Center shell and adds safe local browser smoke reporting documentation without starting M14. The shell keeps the same frontend route set and posts only to `/control-center/actions/preview`; OpenAPI path count remains `74`. Local Browser smoke may be run only against localhost, `127.0.0.1`, or `::1`, and reports are non-authoritative and must not include secrets or generated artifacts. This patch adds no backend API path, dependency, production Control Center authority, runtime/model/provider/network/remote/mobile/plugin execution, Chrome authenticated profile control, Computer Use automation, or iOS/macOS build workflow.

Roadmap projection rule:

> v0.17.5 freezes the next canonical sequence without starting M14. M14 is Web Control Center Local Backend Connection Stabilization. M15 is Approval Queue + Receipt/Event Viewer UI. Local browser smoke / UX polish was v0.17.4, not M14. This patch adds no frontend feature, backend API route, runtime/model/provider/network execution, remote dispatch, mobile/native/sensor code, plugin enablement, dependency, architecture change, Chrome authenticated profile control, Computer Use automation, iOS/macOS build workflow, generated artifact, or production Control Center authority.

Web Control Center local backend connection rule:

> v0.18.0 implements M14 local backend connection stabilization in the existing Web Control Center shell only. API base URLs are local-only: relative path, localhost, 127.0.0.1, and loopback IPv6 are allowed; external absolute API URLs and secret-like query strings are blocked or rejected. The shell displays backend online, degraded, offline-safe, and mock fallback states, and any mock fallback remains visibly non-authoritative. OpenAPI path count remains `74`. This release adds no M15 approval queue, receipt/event viewer UI, backend API route, runtime/model/provider call, remote dispatch, mobile sensor access, plugin enablement, auth, credentials, cookies, Authorization headers, API keys, analytics/SaaS SDK, dependency, native build workflow, external API host, or production Control Center authority.

Web Control Center local backend connection hardening rule:

> v0.18.1 hardens M14 local backend connection safety in the existing Web Control Center shell only. API base URLs remain local-only: relative path, localhost, 127.0.0.1, and loopback IPv6 are allowed; public IPs, private LAN IPs, non-loopback hostnames, URL credentials, external absolute API URLs, and broad secret-like query parameters are blocked or rejected. The shell makes unknown/checking, backend online, degraded, offline-safe, and mock fallback states explicit, and any mock fallback remains visibly non-authoritative. OpenAPI path count remains `74`. This release adds no M15 approval queue, receipt/event viewer UI, backend API route, runtime/model/provider call, remote dispatch, mobile sensor access, plugin enablement, auth, credentials, cookies, Authorization headers, API keys, analytics/SaaS SDK, dependency, native build workflow, external API host, or production Control Center authority.

Open Design System and UI Design Governance rule:

> v0.18.2 adds repo-owned Open Design System and Control Center UI Design Governance documentation before M15. Design docs, reviewed components, and future repo-owned tokens are the design source of truth; design tools, design SaaS, UI generators, screenshot-to-code, and design-to-code systems are not authority and are not enabled. At v0.18.2, M15 Approval Queue + Receipt/Event Viewer UI was still future work; v0.19.0 implements it under the same read-only/preview-only design governance boundary. v0.18.2 adds no frontend behavior, backend API route, runtime/model/provider call, remote dispatch, mobile sensor access, plugin enablement, dependency, design tool integration, Chrome authenticated profile control, Computer Use automation, iOS/macOS build workflow, analytics/SaaS SDK, automatic design sync, automatic design-to-code, or production Control Center authority.

OpenWebUI and CCC Client Strategy rule:

> v0.18.3 clarifies OpenWebUI and CCC Client Strategy before M15. OpenWebUI is the preferred conversational web shell and is not the agent brain. CCC means Control Center Clients: CCC Web, CCC iOS, CCC Android, and CCC macOS. CCC Web is the current TypeScript web Control Center; CCC iOS, CCC Android, and CCC macOS are future native clients only. Open Design governs custom CCC surfaces and does not replace OpenWebUI. This release adds no OpenWebUI integration, OpenWebUI deployment config, backend API route, frontend feature, native CCC implementation, Android app, iOS app, macOS app, native build workflow, mobile sensor access, OS permission integration, signing, keystore, provisioning, App Store workflow, Play Store workflow, dependency, plugin enablement, runtime execution, model/provider call, network call, remote execution, or production authority.

Post-M20 roadmap projection rule:

> v0.18.4 adds post-M20 roadmap projection and M21-M40 capability-layer charters only. M14-M20 remain frozen and unchanged. M21-M40 are planned/provisional charters for OpenWebUI bridge contracts, local model runtime activation, first bounded local LLM calls, memory provider abstraction, truth/evidence governance, sandbox/tool lifecycle, MCP/Agent Skills/AGENTS.md trust registry, CCC native client contracts for iOS/Android/macOS, device pairing, Device Capability Broker implementation, selected mobile capture, one governed sensor capability, browser automation contracts, observability exports, and agent evaluation/regression harnesses. This release adds no implementation of those capabilities, backend API route, frontend behavior, runtime execution, model/provider call, network call, remote execution, mobile sensor access, plugin enablement, dependency, native build workflow, or external action.

Approval queue receipt event viewer rule:

> v0.19.0 implements M15 Approval Queue + Receipt/Event Viewer UI in CCC Web. The UI adds read-only/preview-only approval request, receipt, and event summary views with selected detail panels, visibly mock non-authoritative fallback data, redacted display rules, frontend tests, static frontend safety verification, and Foundation Gate coverage. This release adds no backend API route, approval execution, approval grant/reject mutation, send/write/run/deploy/enable controls, raw secret/prompt/file/memory display, runtime execution, model/provider call, remote execution, mobile sensor access, plugin enablement, native build workflow, or production Control Center authority.

Approval receipt UI safety hardening rule:

> v0.19.1 hardens M15 Approval Queue + Receipt/Event Viewer UI safety only. The UI now states that it cannot grant, deny, execute, or bypass approvals; approval refs are identifiers only and never authority; Python Agent Core remains the only approval authority; and receipt/event detail views are redacted summary metadata only. Static frontend verification and Foundation Gate checks reject active approve/deny/execute/send/write/run/deploy/enable controls, mutation endpoints, authority-bypass copy, raw M15 review fields, credential-like review fields, and raw secret/prompt/file/memory/event/receipt/provider payload display. This patch adds no M16 Event Timeline + Run/Receipt Trace Viewer, approval execution, approve/deny mutation, backend API route, OpenAPI path count change, runtime execution, model/provider call, remote execution, mobile sensor access, plugin enablement, dependency, native build workflow, or production Control Center authority.

Event timeline trace viewer rule:

> v0.20.0 implements M16 Event Timeline + Run/Receipt Trace Viewer in CCC Web only. The UI adds `/events/timeline` with read-only redacted timeline summaries, selected run/receipt trace summaries, relation refs, and Foundation Gate evidence summaries. It uses safe refs and visibly mock non-authoritative fallback data. This release adds no backend API route, OpenAPI path count change, approval execution, tool execution, model/provider call, remote execution, mobile sensor access, plugin enablement, raw secret/prompt/file/memory/credential/provider payload display, raw event payload dump, production telemetry export, external observability integration, OpenTelemetry export, cloud traces, dependency, native build workflow, or production Control Center authority.

Event timeline trace safety hardening rule:

> v0.20.1 hardens M16 Event Timeline + Run/Receipt Trace Viewer safety. It adds interaction coverage for selecting alternate trace summaries while remaining read-only, strengthens M16 OpenAPI path-count and no-backend-timeline-route Foundation Gate checks, documents temporary build-output review hygiene, and records a whole-code bug/safety audit. It does not start M17 Evidence/File/Memory Viewer and adds no backend API route, runtime execution, model/provider call, remote execution, mobile sensor access, plugin enablement, telemetry export, external observability integration, raw secret/prompt/file/memory/credential/provider payload display, dependency, native build workflow, or production Control Center authority.

M17 Evidence/File/Memory Viewer rule:

> v0.21.0 implements M17 Evidence/File/Memory Viewer in CCC Web only. It adds `/evidence`, `/files`, and `/memory` frontend routes with read-only, summary-only, redacted mock evidence refs, file refs, and memory refs. Memory is recall, not authority; canonical files and governed source systems outrank memory. This release adds no backend API route, OpenAPI path count change, file mutation, memory mutation, filesystem browsing, runtime execution, model/provider call, remote execution, mobile sensor access, plugin enablement, raw secret/prompt/file/memory/evidence/credential/provider payload display, dependency, native build workflow, or production Control Center authority.

M17 Evidence/File/Memory Viewer safety hardening rule:

> v0.21.1 hardens the existing M17 Evidence/File/Memory Viewer only. `/evidence`, `/files`, and `/memory` remain frontend-only, read-only, summary-only, visibly mock, non-authoritative, and redacted. This patch adds alternate safe mock refs, accessible selected-card reviewability, stronger frontend tests, static verifier checks, docs, and Foundation Gate criteria. OpenAPI path count remains `74`. This patch adds no M18 Local Runtime Status + Manual Smoke Control Surface, backend API route, file mutation, memory mutation, filesystem browsing, raw secret/prompt/file/memory/evidence/credential/provider payload display, embedding/vector DB/memory provider implementation, runtime execution, model/provider call, remote execution, mobile sensor access, plugin enablement, dependency, native build workflow, auth, cookies, analytics, SaaS SDK, or production Control Center authority.

Developer environment command normalization rule:

> v0.21.2 normalizes developer verification commands only. Repo-local commands should use `.venv/bin/python` or Makefile targets such as `make doctor`, `make test`, `make verify`, and `make frontend-check`; shell aliases and a bare `python` binary are not reliable in Codex or other non-interactive shells. This patch adds no runtime feature, frontend feature, backend API route, dependency, global tool install, application behavior change, runtime/model/provider call, network call, mobile/native/browser/computer-use functionality, plugin enablement, or production capability.
