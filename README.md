# Ultimate AI Agent Canonical Bundle v0.5.4

This is the active pre-coding foundation bundle after the Runtime Hygiene Micro-Foundation patch.

Start here:

```text
README_IMPORT_v0_5_4.md
ultimate_ai_agent_master_plan_v0_5_4.md
docs/canonical/09_roadmap.md
docs/canonical/39_verified_task_completion_framework.md
docs/canonical/40_credentials_secret_broker_and_provider_registry.md
docs/canonical/43_minimum_lovable_kernel.md
docs/canonical/46_result_and_error_envelope.md
docs/canonical/47_idempotency_and_retry_policy.md
docs/canonical/48_actor_authority_and_identity.md
docs/canonical/49_temporal_context_and_freshness.md
docs/canonical/50_data_classification_policy.md
docs/canonical/51_redaction_and_safe_debugging.md
docs/canonical/52_service_boundaries_and_dependency_injection.md
docs/implementation/foundation_gate_implementation_plan_v0_5_4.md
docs/implementation/pre_coding_readiness_v0_5_4.md
docs/testing/test_strategy_v0.md
```

Core rule:

> Do not build scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, provider-specific integrations, or external high-autonomy execution before the kernel, memory/files, event ledger, permission model, Tool Broker, Model Router, Cost Governor, Secret Broker, Provider Registry, API boundary, rollback primitives, runtime hygiene contracts, and contract tests work.

Stack rule:

> Python Agent Core is the brain. TypeScript Control Center is the user control layer. OpenWebUI is an optional early chat shell, not the agent brain.

Truth-source rule:

> The canonical roadmap lives in `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. When a master plan and canonical file disagree, the active canonical file wins.

Runtime hygiene rule:

> Every meaningful operation should be traceable through a result envelope, actor context, temporal context, data classification, redaction policy, idempotency policy, and service boundary contract.
