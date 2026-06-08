# Production Threat Model Policy

Status: Checkpoint M111 policy.

The Production Threat Model policy is contract-only and review-only. It
requires safe refs, actor-bound records, baseline-bound records,
source-freeze-bound records, threat surface refs, mitigation plan refs, audit
refs, replay refs, accepted checkpoint refs, and a no-effect receipt plan.

The default policy keeps every runtime authority disabled: no production
authority, no production runtime, no external distribution, no deployment, no
credential handling, no network access, no model call, no memory write, no
context injection, no execution, no tool execution, no shell execution, no
browser automation, no plugin execution, no mobile sensor, no background
worker, no remote execution, no backend route, no Control Center control, and
no dependency.

Any model_copy mutation or constructor input that tries to enable those fields
must be denied during evaluator revalidation. M111 remains a safe checkpoint
over M110, and M112 remains future.
