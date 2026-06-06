# OpenWebUI Safe Handoff Result Contract

The M77 safe handoff result is a safe handoff result over safe refs only. It
contains exact approval binding refs, a redacted safe summary, stable reason
codes, and a receipt plan.

The result may set `safe_handoff_executed=True` only for the Agent Core local
handoff record. It must keep `openwebui_called=False`, `provider_called=False`,
`model_called=False`, `model_output_authoritative=False`,
`tool_executed=False`, `memory_written=False`, `context_injected=False`,
`network_called=False`, `credential_cookie_accessed=False`,
`raw_prompt_returned=False`, `raw_provider_payload_returned=False`,
`raw_content_returned=False`, and `production_authority_granted=False`.

Exact approval binding is required for `bridge_envelope_ref`, `session_ref`,
`safe_conversation_ref`, `actor_ref`, and `approval_ref`. Evaluator boundaries
revalidate model_copy-mutated result and receipt fields.

OpenWebUI is a shell/bridge, not the brain. Agent Core remains authority. M78
remains future.
