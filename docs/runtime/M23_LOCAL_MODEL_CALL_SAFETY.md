# M23 Local Model Call Safety

Status: Active M23 safety documentation for v0.27.1.

M23 is manual/CLI-only, loopback-only, fixed-prompt-only, approval-gated,
non-tool, and non-authoritative. It is not general model execution.

Safety requirements:

- CLI defaults dry-run.
- execution requires `--execute-local-call`.
- execution requires validated local approval.
- endpoints must be loopback-only HTTP.
- URL credentials, secret-like query keys, and secret-like query values are
  denied.
- safe endpoint labels must not echo raw URL details.
- responses are capped and redacted.
- raw responses are not stored.
- secret-like responses are blocked.
- model output is not truth, not authority, and not control input.

M23 adds no backend API route, no Control Center execution, no OpenWebUI runtime
bridge, no tool execution, no memory write, no file write, no dependency, and
no production authority. M24 remains future.
