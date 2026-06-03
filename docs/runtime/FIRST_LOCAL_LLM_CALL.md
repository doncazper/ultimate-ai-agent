# First Local LLM Call

Status: Active M23 documentation for v0.27.1.

M23 is the first bounded local LLM call path. It is manual/CLI-only,
loopback-only, fixed-prompt-only, non-tool, and non-authoritative. It is not
general model execution, not runtime activation, not an endpoint probe, and not
production authority.

Allowed surface:

- `scripts/manual_local_model_call.py` only.
- dry-run by default.
- `--execute-local-call` for an actual manual local call attempt.
- validated local approval before execution.
- fixed prompt id `m23_fixed_local_model_smoke_v1`.
- loopback-only HTTP endpoint.
- fake transport in tests and Foundation Gate.
- capped and redacted safe response summary.
- non-authoritative receipt.

Disallowed surface:

- no arbitrary prompt.
- no user content.
- no raw responses are stored.
- no backend API route.
- no Control Center execution.
- no OpenWebUI runtime bridge.
- no tool execution.
- no memory write.
- no file write.
- no provider SDK, tokenizer, billing API, dependency, remote execution, or
  production authority.

M24 remains future.
