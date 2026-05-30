# Ultimate AI Agent Canonical Bundle v0.5.5

This is the active pre-coding foundation bundle after adding Local Runtime, Context Survival, Structured World State, and Agent Runtime Adapter strategy.

Start here:

```text
README_IMPORT_v0_5_5.md
ultimate_ai_agent_master_plan_v0_5_5.md
docs/canonical/09_roadmap.md
docs/canonical/53_structured_world_state.md
docs/canonical/54_context_budget_and_session_survival.md
docs/canonical/55_tool_result_retention_and_context_trimming.md
docs/canonical/56_prompt_tool_prefix_cache_policy.md
docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md
docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md
docs/implementation/foundation_gate_implementation_plan_v0_5_5.md
docs/implementation/pre_coding_readiness_v0_5_5.md
docs/testing/test_strategy_v0.md
```

Core rule:

> Do not build scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, provider-specific integrations, or external high-autonomy execution before the kernel, memory/files, event ledger, permission model, Tool Broker, Model Router, Cost Governor, Secret Broker, Provider Registry, API boundary, rollback primitives, runtime hygiene contracts, context survival contracts, local runtime profiles, SDK/A2A adapter boundaries, and contract tests work.

Stack rule:

> Python Agent Core is the brain. TypeScript Control Center is the user control layer. OpenWebUI is an optional early chat shell, not the agent brain.

Truth-source rule:

> The canonical roadmap lives in `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. When a master plan and canonical file disagree, the active canonical file wins.

Context-survival rule:

> The conversation transcript is useful context, not durable truth. Long-running runs must preserve exact step parameters and outcomes in Structured World State and Event Ledger records outside the transcript.

SDK/A2A rule:

> External agent SDKs and protocols are adapter layers, not the core brain. OpenAI Agents SDK, Claude Agent SDK, MCP, and A2A can be supported through explicit boundary adapters only when they preserve our Execution Contract, Consent Ledger, Tool Broker, Event Ledger, Model Router, redaction, and rollback policies.
