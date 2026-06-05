# OpenWebUI Bridge Adapter Authority Boundary

M51 keeps OpenWebUI as a shell and bridge. OpenWebUI is not the agent brain.
Agent Core remains authority for policy, approval, memory, tools, routing,
truth, receipts, and safety decisions.

The adapter result is non-authoritative. It cannot approve, execute, write
memory, inject context, call a provider, call OpenWebUI, expose raw prompt data,
or expose raw provider payloads. approval_ref values are identifiers only and
cannot authorize tool execution, provider calls, model authority, memory write,
or context injection.

Evaluator boundaries revalidate model_copy-mutated request and policy fields.
Unsafe flags are denied before any safe summary is returned.

