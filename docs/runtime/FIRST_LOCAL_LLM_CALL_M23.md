# First Local LLM Call M23

Status: Active M23 documentation for v0.27.0. Manual/CLI-only,
loopback-only, fixed-prompt-only, non-tool, and non-authoritative.

M23 adds the first bounded local model call path. It is not a general runtime
activation layer and it is not production model authority.

Allowed surface:

- `scripts/manual_local_model_call.py` only.
- dry-run by default.
- explicit `--execute-local-call` for an actual manual local call attempt.
- validated local approval required before execution.
- fixed prompt id `m23_fixed_local_model_smoke_v1`.
- loopback-only HTTP endpoint.
- fake transport for tests and Foundation Gate.
- safe, capped, redacted response summary.
- non-authoritative receipt.

Disallowed surface:

- no backend API route.
- no Control Center execution control.
- no OpenWebUI runtime bridge.
- no runtime activation.
- no endpoint probe.
- no arbitrary prompt.
- no stdin prompt.
- no file prompt.
- no clipboard prompt.
- no memory prompt.
- no OpenWebUI transcript prompt.
- no user content.
- no raw prompt display.
- no raw response storage.
- no raw file, memory, credential, provider payload, or secret display.
- no tool execution.
- no memory write.
- no file write.
- no remote execution.
- no provider SDK.
- no runtime package.
- no dependency.
- no production authority.

The fixed prompt is intentionally non-sensitive and used only to verify the
manual local call path. Model output is never truth authority, never approval
authority, and never trusted control input.

Release validation does not require a real endpoint call. Tests and Foundation
Gate use fake transport only. A real manual local call was not run for v0.27.0
release validation.

OpenAPI path count remains `74`.
