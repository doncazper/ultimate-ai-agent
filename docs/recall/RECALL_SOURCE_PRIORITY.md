# Recall Source Priority

Status: active
Current through: v0.32.1
Purpose: Define deterministic M26 recall source ordering.

M26 source priority is:

1. canonical documents.
2. evidence manifests.
3. receipts.
4. Event Ledger records.
5. user-reviewed sources.
6. source-linked memory.
7. reviewed memory.
8. unreviewed memory.
9. blocked output classes and unknown refs.

Memory may help the agent remember context, but it cannot outrank canonical
files, evidence manifests, receipts, Event Ledger records, or user-reviewed
sources. Trust/confidence metadata cannot invert this order.

The router derives trusted source identity from the structured source_ref prefix.
For recognized prefixes, the inferred source kind must match the declared
source_kind before a candidate can be selected. Caller-declared source_kind
cannot upgrade a memory ref into canonical/evidence/receipt/event/user-reviewed
priority, and cannot disguise model, runtime, or OpenWebUI output as a trusted
source.

Unknown or arbitrary source refs are excluded. Model output, runtime output, and
OpenWebUI output are excluded from grounded recall and cannot become truth or
authority through a context pack.
