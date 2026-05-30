# Import Guide v0.5.4

Status: Active pre-coding baseline after Runtime Hygiene Micro-Foundation.

## What changed from v0.5.3

v0.5.4 keeps the v0.5.3 Claude remediation intact and adds small-but-foundational runtime hygiene contracts that are cheaper to define before coding than retrofit later.

It adds:

- Universal result and error envelopes.
- Idempotency, correlation, causation, retry, and dedupe policy.
- Actor, authority, and identity context.
- Temporal context and freshness policy.
- Data classification policy.
- Redaction and safe debugging policy.
- Service boundaries and dependency injection rules.
- Capability flag schema.
- Test strategy conventions.

## Active documents

```text
ultimate_ai_agent_master_plan_v0_5_4.md
docs/canonical/09_roadmap.md
docs/canonical/39_verified_task_completion_framework.md
docs/canonical/40_credentials_secret_broker_and_provider_registry.md
docs/canonical/41_memory_retrieval_v1.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/43_minimum_lovable_kernel.md
docs/canonical/44_contract_versioning_and_provisional_policy.md
docs/canonical/45_trusted_computing_base.md
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

## Historical documents

Versioned v0.1 through v0.5.3 master plans remain for history. They are no longer the active roadmap source.

The active roadmap is always:

```text
docs/canonical/09_roadmap.md
```

## Pre-coding posture

Start M0 only after v0.5.4 is committed, tagged, and the consistency audit passes. M0 should create validation scripts and stack skeleton only. It should not implement agent features.
