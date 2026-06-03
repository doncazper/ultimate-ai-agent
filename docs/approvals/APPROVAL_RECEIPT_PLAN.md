# Approval Receipt Plan

Status: active
Current through: v0.32.0
Purpose: Define non-authoritative M28 approval receipt planning.

M28 approval receipt plans are safe summaries and refs only. They are not proof
of execution and do not authorize or perform execution.

Receipt plans must keep:

- `execution_authorized=False`.
- `execution_performed=False`.
- `raw_content_stored=False`.
- `memory_write_performed=False`.
- `file_mutation_performed=False`.
- `network_call_performed=False`.

Receipt plans must not store raw prompts, model output, file content,
transcripts, credentials, tokens, or secret-like data. They must not mutate
memory or the Event Ledger.

M29 remains planned/provisional.
