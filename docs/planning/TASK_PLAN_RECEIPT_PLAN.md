# Task Plan Receipt Plan

Status: active M29 contract. Current active baseline: **v0.34.1**.

M29 receipt plans are non-authoritative metadata plans. They may summarize the planning decision but must not store raw content or claim performed side effects.

Receipt plans require:

- `execution_authorized=False`
- `execution_performed=False`
- `scheduler_registered=False`
- `raw_content_stored=False`
- `memory_write_performed=False`
- `file_mutation_performed=False`
- `network_call_performed=False`
- `tool_execution_performed=False`
- `action_execution_performed=False`

Receipt plans do not write the Event Ledger, write memory, schedule tasks, execute tools/actions, or create production audit authority.

Receipt plans may include trusted derived plan risk. They are not authority, do
not prove execution, and must keep `execution_performed=False`.

M31-M40 remain planned/provisional.
