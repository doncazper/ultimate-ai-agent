# Ultimate AI Agent Canonical Bundle v0.15.1

This is the active project baseline after the v0.15.1 M11 runtime readiness taxonomy clarification patch.

Start here:

```text
README_IMPORT_v0_15_1.md
ultimate_ai_agent_master_plan_v0_15_1.md
docs/DOCUMENTATION_INDEX.md
docs/canonical/09_roadmap.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/canonical/21_consent_and_permissions_ledger.md
docs/canonical/37_tool_broker.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/63_observability_standards_mapping.md
docs/canonical/64_mobile_companion_and_device_capability_broker.md
docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md
docs/canonical/66_external_tooling_and_codex_plugin_governance.md
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
docs/runtime/model_runtime_adapter_harness.md
docs/runtime/local_loopback_model_runtime.md
docs/runtime/RUNTIME_READINESS.md
docs/runtime/MANUAL_SMOKE_REPORTS.md
docs/runtime/RUNTIME_CAPABILITY_MATRIX.md
docs/security/approval_authority.md
docs/implementation/foundation_gate_implementation_plan_v0_15_1.md
docs/maintenance/documentation_integrity_checklist.md
docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md
docs/tooling/CODEX_PLUGIN_RISK_POLICY.md
docs/testing/test_strategy_v0.md
```

Core rule:

> Do not build scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, provider-specific integrations, or external high-autonomy execution before the kernel, memory/files, event ledger, permission model, Tool Broker, Model Router, Cost Governor, Secret Broker, Provider Registry, Truth Source Router, Evidence Manifest, API boundary, rollback primitives, runtime hygiene contracts, context survival contracts, local runtime profiles, SDK/A2A adapter boundaries, observability standards mapping, and contract tests work.

Stack rule:

> Python Agent Core is the brain. TypeScript Control Center is the user control layer. OpenWebUI is an optional early chat shell, not the agent brain.

Truth-source rule:

> The model is never the source of truth. Governed source systems, canonical files, approved APIs, databases, source documents, Event Ledger records, World State snapshots, and evidence manifests define truth. Memory helps recall; it does not outrank canonical truth.

Observability standards rule:

> The Event Ledger remains the source of truth for agent actions, but M2 events must be mappable to OpenTelemetry GenAI semantic conventions and W3C Trace Context. Future event exports should be compatible with CloudEvents and, where message-driven APIs are introduced, documented with AsyncAPI.

Foundation Gate rule:

> v0.14.3 keeps REMOTE-01 / M10.5 foundation-only and adds open-source-first private mesh taxonomy. Headscale, generic WireGuard, Tailscale, private mesh, tailnet, and LAN transports are planned/disabled metadata only. Headscale is the first planned self-hosted/open-source control-plane option to evaluate; Tailscale remains planned metadata, not the default assumption. It adds no live mesh networking, Headscale integration, Tailscale integration, WireGuard command execution, listener, network call, job dispatch, remote subagent launch, remote Tool Broker execution, sandbox execution, personal-data access, write/send action, remote approval, background service, production persistence, provider SDK, tokenizer, billing API, credentials, node keys, hostnames, private IPs, or safety bypass.

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
