# Execution Receipt Plan

Status: active M30 source-of-truth documentation.

M30 receipt plans are non-authoritative, summary/ref-only records for the
state-machine decision. They do not prove that real execution happened.

Receipt plans must keep these fields false:

- `execution_authorized`
- `execution_performed`
- `raw_content_stored`
- `memory_write_performed`
- `file_mutation_performed`
- `network_call_performed`
- `model_call_performed`
- `tool_execution_performed`
- `action_execution_performed`
- `event_ledger_mutation_performed`
- `scheduler_registered`
- `background_worker_registered`

Receipt plans store no raw prompts, files, transcripts, model outputs, runtime
outputs, tool outputs, or secrets.

M31-M40 remain planned/provisional.
