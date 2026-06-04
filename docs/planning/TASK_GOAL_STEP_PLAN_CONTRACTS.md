# Task Goal, Step, and Plan Contracts

Status: active M29 contract. Current active baseline: **v0.33.0**.

M29 adds typed contracts for:

- `TaskGoal`: a safe summary of the user-reviewed objective.
- `TaskStep`: a safe, deterministic planning unit.
- `TaskPlan`: a review-only collection of goals, steps, dependencies, constraints, and safe metadata.
- `TaskPlanningRequest`: a wrapper that may request evaluation but cannot request execution, auto-run, or scheduling.

All summaries and metadata must be safe. Raw prompts, raw model output, raw file content, raw transcripts, secret-like metadata, and private local paths are denied.

Task plans are non-authoritative. They do not override the approval authority, Tool Broker, memory source priority, truth/evidence contracts, or Foundation Gate.

M30-M40 remain planned/provisional.
