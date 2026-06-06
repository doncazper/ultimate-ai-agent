# OpenWebUI Safe Handoff Receipt Plan

M77 receipt plans store only safe refs and redacted summaries for OpenWebUI safe
handoff execution. The receipt plan records the exact-bound
`handoff_request_ref`, `safe_handoff_result_ref`, `bridge_envelope_ref`,
`approval_ref`, `session_ref`, `safe_conversation_ref`, and `actor_ref`.

Receipt plans store no raw prompt, no raw provider payload, no raw content, no
credentials or cookies, and no production authority. They record no live
OpenWebUI connection, no OpenWebUI runtime call, no provider call, no model
call, no tool execution, no memory write, no context injection, and no network
call.

OpenWebUI is a shell/bridge, not the brain. Agent Core remains authority.
Evaluator boundaries revalidate receipt fields. M78 remains future.
