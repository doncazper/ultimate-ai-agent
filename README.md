# Ultimate AI Agent Canonical Bundle v0.6.1

This is the active project baseline after implementing Milestone M2.5 (Structured World State, Context Budget, Local Runtime Profiles, and SDK/A2A Adapter Boundaries).

Start here:

```text
README_IMPORT_v0_6_1.md
ultimate_ai_agent_master_plan_v0_6_1.md
docs/canonical/09_roadmap.md
docs/canonical/22_observability_and_event_ledger.md
docs/canonical/63_observability_standards_mapping.md
docs/implementation/foundation_gate_implementation_plan_v0_6_1.md
docs/implementation/pre_coding_readiness_v0_5_8.md
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
