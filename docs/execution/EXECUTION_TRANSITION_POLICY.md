# Execution Transition Policy

Status: active M30 source-of-truth documentation.

M30 transition decisions are non-authoritative and no-effect only.

The evaluator denies:

- `execution_requested=True`.
- `auto_run_requested=True`.
- `schedule_requested=True`.
- `background_worker_requested=True`.
- `side_effect_execution_enabled=True`.
- replay key reuse.
- transition ID reuse.
- missing transition IDs.
- target step mismatch or unknown target step.
- unmet dependencies.
- completing a step before it is `ready`.
- completing blocked, paused, denied, skipped, or already-completed steps.
- finalizing a run while pending, blocked, or future-real-execution steps remain.
- hidden side-effect metadata.
- raw prompt/model/file/transcript flags.
- secret-like metadata or summaries.
- non-authoritative refs that attempt to authorize execution.

Allowed transitions do not authorize or perform execution. They return
`approved_no_effect_transition` only for deterministic state advancement with
`execution_authorized=False` and `execution_performed=False`.

Evaluator boundaries revalidate safety-critical fields, including
`model_copy(update=...)` mutated objects, before any policy allow decision.

M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32-M40 remain planned/provisional.
