# Recall Source Priority

Status: active
Current through: v0.30.0
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

Unknown or arbitrary source refs are excluded. Model output, runtime output, and
OpenWebUI output are excluded from grounded recall and cannot become truth or
authority through a context pack.
