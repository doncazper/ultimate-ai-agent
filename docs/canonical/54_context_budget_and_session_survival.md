# 54 — Context Budget and Session Survival

Status: Active foundation contract in v0.5.5.

## Purpose

Long-running agent sessions need explicit context accounting. The full model context window is not available for transcript history.

## Budget formula

```text
available_history_tokens =
  effective_context_limit_tokens
  - system_prompt_tokens
  - tool_schema_tokens
  - prompt_bundle_overhead_tokens
  - world_state_tokens
  - context_pack_tokens
  - completion_reserve_tokens
  - safety_margin_tokens
```

If the effective context limit is unknown, long-running mode is disabled unless a conservative configured limit is explicitly approved.

## Required behavior

- Discover or configure the effective context limit for every model/runtime.
- Track estimated and actual tokens for each call.
- Calibrate token estimates using actual usage when providers return it.
- Treat underestimation as worse than overestimation; calibration may move conservative.
- Reserve completion and safety-margin budget before adding history.
- Emit `context_trim_event` records whenever messages/tool outputs are removed from live context.
- Never trim current user instruction, active Execution Contract, World State, consent/approval constraints, or active safety constraints.

## Session survival target

Foundation testing should include a simulated 50-step workflow with large tool outputs. The workflow must finish without context overflow while preserving exact step state through World State and Event Ledger records.
