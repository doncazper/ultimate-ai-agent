# 25 — Cost and Resource Governor

Status: Foundation cost-control spec, v0.5.3
Owner: Platform / Runtime

## Purpose

The Cost Governor prevents runaway LLM, provider, scanner, execution, storage, and notification costs.

## Cost attribution

Costs must be attributed below the run level. Event Ledger events must support:

```text
run_id
project_id
workspace_id
user_id
task_id
event_id
model_class
model_provider
tool_id
provider_id
scanner_id
skill_id
capability_id
cost_center
estimated_cost_usd
actual_cost_usd
input_tokens
output_tokens
embedding_tokens
api_calls
execution_ms
storage_bytes
```

## Budget scopes

```text
Global user budget
Workspace budget
Project budget
Provider budget
Model budget
Tool budget
Scanner budget
Skill budget
Workflow budget
```

## Modes

```text
cheap: minimal research, no ensembles, cheap classifiers preferred
balanced: strong models for architecture/security/coding review only
premium: deeper research and stronger verification allowed
critical: high-reliability model + independent verification + approval
local_private: prefer local/private models and avoid cloud routing
```

## Blocking rules

```text
High-cost actions require estimate before execution.
Budget overruns block or downgrade actions unless approved.
High-volume scanners require per-scanner budgets and cooldowns.
Provider APIs with paid keys require budget policy and event-level attribution.
```

## Required evals

```text
model_cost_efficiency_eval
provider_fallback_eval
scanner_budget_eval
cost_attribution_eval
```
