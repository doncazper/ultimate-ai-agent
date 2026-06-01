# Ultimate AI Agent Canonical Bundle v0.12.2

This is the active project baseline after M8.5 Approval Authority + Runtime Authorization Bridge.

Start here:

```text
README_IMPORT_v0_12_2.md
ultimate_ai_agent_master_plan_v0_12_2.md
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
docs/security/approval_authority.md
docs/implementation/foundation_gate_implementation_plan_v0_12_2.md
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

> v0.12.2 adds a local/dev approval authority bridge so arbitrary approval strings are not authority. Approval requests, grants, validations, and receipts are typed and can be checked by Model Router, Model Runtime, Tool Broker, and Kernel paths. M8 remains simulated-only. M8.5 does not add scanners, companion proactivity, Skill Factory, self-improving code, autopilot, browser automation, real providers/models/web calls, tokenizers, billing APIs, network calls, runtime agent config loading, SDK/A2A runtime delegation, production auth/OAuth, production databases, pgvector, embeddings, production secrets, production truth connectors, or high-autonomy execution.
