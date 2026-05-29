# ADR-0025: Use Model Routing

Status: Accepted for foundation implementation in v0.4.5
Date: 2026-05-29

## Context

The Ultimate AI Agent will need many forms of intelligence: fast classification, normal conversation, deep reasoning, coding, research, vision, embeddings, reranking, local/private processing, and high-reliability verification.

Using one model for all tasks would be expensive, slow, brittle, and privacy-limited. High-volume modules such as scanners and proactive intelligence would become impractical without cheaper batch routing. High-risk modules such as self-improving code and external execution require independent verification rather than one model judging itself.

## Decision

Use a dedicated Model Router as a foundation service. The Orchestrator decomposes work into tasks; the Model Router selects the best model class/runtime for each task based on task type, risk, privacy, cost, latency, modality, context length, output format, tool needs, and historical eval performance.

The system will route by model class first, then choose a provider/runtime from the capability registry.

Required model classes include:

```text
fast_classifier
standard_assistant
strong_reasoner
coding_model
research_synthesizer
vision_model
audio_model
embedding_model
reranker
local_private_model
structured_output_model
small_batch_worker
long_context_model
high_reliability_critical_model
```

## New foundation rule

> No high-volume scanners, proactive alerts, skill acquisition, self-improving code, or autopilot workflows until the Model Router, Cost Governor, Event Ledger, privacy routing policy, fallback behavior, and routing evals work.

## Consequences

Positive:

```text
Lower cost
Lower latency
Better task-specific quality
Better privacy control
Better resiliency through fallbacks
Better eval-driven improvement
Cleaner separation between orchestration and model choice
Safer self-improving code through independent verification
```

Tradeoffs:

```text
More infrastructure is required before advanced modules.
Routing policy must be tested and maintained.
Model providers must be tracked in the Capability Registry.
Event Ledger volume increases.
Cost and privacy policies must be explicit.
```

## Required implementation artifacts

```text
docs/canonical/26_model_routing_strategy.md
docs/schemas/model_capability.schema.json
docs/schemas/model_route.schema.json
docs/schemas/model_routing_policy.schema.json
docs/schemas/model_eval_result.schema.json
docs/evals/model_routing_eval.md
docs/evals/model_cost_efficiency_eval.md
docs/evals/model_privacy_routing_eval.md
docs/evals/model_critical_verification_eval.md
```

## Related decisions

```text
ADR-0021-use-agent-event-ledger.md
ADR-0024-use-cost-and-resource-governor.md
ADR-0031-use-capability-registry-and-dependency-graph.md
ADR-0033-use-foundation-change-management-and-contract-testing.md
```
