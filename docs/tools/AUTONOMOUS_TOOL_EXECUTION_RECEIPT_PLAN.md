# Autonomous Tool Execution Receipt Plan

M91 receipt plans store safe summary only and safe refs only. They may reference
the autonomous tool execution contract ref, exact M90 hardening freeze decision
ref, tool intent ref, tool runtime ref, capability ref, safe execution scope ref,
and safe tool ref.

M91 receipts store no raw tool payload, no raw provider payload, no raw prompt,
and no secret-like content. Receipt plans record no real tool execution, no
autonomous execution, no session start, no background worker, and no side
effects.

Receipt plans are not authority. Evaluator boundaries revalidate receipt fields.
M92 remains future.
