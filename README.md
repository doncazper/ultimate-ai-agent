# Ultimate AI Agent Canonical Bundle v0.14.2

This is the active project baseline after the v0.14.2 M10.5 remote worker policy contract hardening patch.

Start here:

```text
README_IMPORT_v0_14_2.md
ultimate_ai_agent_master_plan_v0_14_2.md
docs/canonical/09_roadmap.md
docs/canonical/21_consent_and_permissions_ledger.md
docs/canonical/37_tool_broker.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/63_observability_standards_mapping.md
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
docs/runtime/model_runtime_adapter_harness.md
docs/runtime/local_loopback_model_runtime.md
docs/security/approval_authority.md
docs/implementation/foundation_gate_implementation_plan_v0_14_2.md
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

> v0.14.2 hardens REMOTE-01 / M10.5 remote worker foundation contracts. Remote worker support remains foundation-only, disabled by default, mock/local metadata only, and dry-run only. `remote_tailnet_enabled=true` and `remote_personal_data_enabled=true` are rejected as unsupported in M10.5, remote-worker API wrappers reject unexpected top-level fields, and the Foundation Gate covers those checks. It adds no live mesh networking, tailnet execution, listener, network call, job dispatch, remote subagent launch, remote Tool Broker execution, sandbox execution, personal-data access, write/send action, remote approval, background service, production persistence, provider SDK, tokenizer, billing API, or safety bypass.
