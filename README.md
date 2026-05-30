# Ultimate AI Agent Canonical Bundle v0.5.6

This is the active pre-coding foundation bundle after adding Truth, Grounding, and Evidence Governance.

Start here:

```text
README_IMPORT_v0_5_6.md
ultimate_ai_agent_master_plan_v0_5_6.md
docs/canonical/09_roadmap.md
docs/canonical/53_structured_world_state.md
docs/canonical/54_context_budget_and_session_survival.md
docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md
docs/canonical/59_truth_grounding_and_evidence_governance.md
docs/canonical/60_truth_source_router.md
docs/canonical/61_evidence_manifest_and_claim_verification.md
docs/canonical/62_hybrid_retrieval_and_reranking_policy.md
docs/implementation/foundation_gate_implementation_plan_v0_5_6.md
docs/implementation/pre_coding_readiness_v0_5_6.md
docs/testing/test_strategy_v0.md
```

Core rule:

> Do not build scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, provider-specific integrations, or external high-autonomy execution before the kernel, memory/files, event ledger, permission model, Tool Broker, Model Router, Cost Governor, Secret Broker, Provider Registry, Truth Source Router, Evidence Manifest, API boundary, rollback primitives, runtime hygiene contracts, context survival contracts, local runtime profiles, SDK/A2A adapter boundaries, and contract tests work.

Stack rule:

> Python Agent Core is the brain. TypeScript Control Center is the user control layer. OpenWebUI is an optional early chat shell, not the agent brain.

Truth-source rule:

> The model is never the source of truth. Governed source systems, canonical files, approved APIs, databases, source documents, Event Ledger records, and evidence manifests define truth. Memory helps recall; it does not outrank canonical truth.

Grounding rule:

> Factual answers must use the correct grounding path for the task: canonical files for project truth, APIs/databases for hard/live structured facts, hybrid RAG for approved documents, live retrieval for fast-changing information, and human review for high-stakes truth.

Context-survival rule:

> The conversation transcript is useful context, not durable truth. Long-running runs must preserve exact step parameters and outcomes in Structured World State and Event Ledger records outside the transcript.

SDK/A2A rule:

> External agent SDKs and protocols are adapter layers, not the core brain. OpenAI Agents SDK, Claude Agent SDK, MCP, and A2A can be supported through explicit boundary adapters only when they preserve our Execution Contract, Consent Ledger, Tool Broker, Event Ledger, Model Router, redaction, rollback, and evidence-governance policies.
