# Ultimate AI Agent Canonical Bundle v0.11.0

This is the active project baseline after Milestone M7 (Model Router and Cost/Resource Governor policy foundation).

Start here:

```text
README_IMPORT_v0_11_0.md
ultimate_ai_agent_master_plan_v0_11_0.md
docs/canonical/09_roadmap.md
docs/canonical/21_consent_and_permissions_ledger.md
docs/canonical/37_tool_broker.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/63_observability_standards_mapping.md
docs/implementation/foundation_gate_implementation_plan_v0_11_0.md
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

> v0.11.0 adds the M7 policy foundation for deterministic model routing and cost/resource governance. It adds metadata-only model profiles, privacy-aware route decisions, budget estimates, budget decisions, and non-executing API preview endpoints. It does not add scanners, companion proactivity, Skill Factory, self-improving code, autopilot, browser automation, real providers/models/web calls, SDK/A2A runtime delegation, production databases, pgvector, embeddings, production secrets, production truth connectors, or high-autonomy execution.
