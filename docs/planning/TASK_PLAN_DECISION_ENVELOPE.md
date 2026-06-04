# Task Plan Decision Envelope

Status: active M29 contract. Current active baseline: **v0.34.1**.

The M29 evaluator returns a decision envelope with stable reason codes and safe messages.

Allowed review status:

- `TASK_PLAN_VALID_FOR_REVIEW`

Denied conditions include:

- `TASK_EXECUTION_REQUEST_DENIED`
- `TASK_AUTO_RUN_DENIED`
- `TASK_SCHEDULER_DENIED`
- `RAW_PROMPT_DENIED`
- `RAW_MODEL_OUTPUT_DENIED`
- `RAW_FILE_CONTENT_DENIED`
- `RAW_TRANSCRIPT_DENIED`
- `SECRET_METADATA_DENIED`
- `MODEL_OUTPUT_NOT_PLAN_AUTHORITY`
- `MEMORY_REF_NOT_PLAN_AUTHORITY`
- `CONTEXT_PACK_NOT_PLAN_AUTHORITY`
- `TOOL_INTENT_NOT_PLAN_AUTHORITY`
- `APPROVAL_REF_NOT_TASK_AUTHORITY`
- `APPROVAL_TEST_REF_DENIED`
- `DUPLICATE_STEP_ID_DENIED`
- `MISSING_DEPENDENCY_STEP_DENIED`
- `DEPENDENCY_CYCLE_DENIED`
- `TASK_STEP_EXECUTION_DENIED`
- `TASK_RISK_DOWNGRADE_DENIED`
- `TASK_HIDDEN_SIDE_EFFECT_DENIED`
- `UNKNOWN_INPUT_REF_DENIED`

Safe messages must not echo raw prompts, secrets, invalid raw values, or private local paths.

Decision envelopes include trusted derived plan risk. They remain
non-authoritative review metadata and always keep `execution_authorized=False`,
`execution_performed=False`, and scheduler/background behavior disabled.

M31-M40 remain planned/provisional.
