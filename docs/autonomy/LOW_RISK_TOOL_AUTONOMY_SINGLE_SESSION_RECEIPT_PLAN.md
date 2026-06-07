# Low-Risk Tool Autonomy Single-Session Receipt Plan

M92 receipt plans are safe summary only and safe refs only. A receipt plan may
store the single_session_ref, M91 decision ref, low-risk dry-run record ref,
tool intent ref, tool runtime ref, capability ref, and safe tool ref.

Receipt plans must not store raw tool payload, raw provider payload, raw prompt,
secret-like content, execution output, tool output, command output, shell output,
network output, browser output, plugin output, model output, memory writes, or
context injection payloads.

The receipt plan records no side effects:

- no execution performed
- no tool execution performed
- no autonomous execution performed
- no session start performed
- no background worker started

Evaluator boundaries revalidate receipt fields before a decision is valid for
review. M93 remains future.
