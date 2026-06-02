# Local Runtime M22 To M23 Boundary

Status: Active M22-to-M23 boundary documentation for v0.27.0.

M22 is the Local Model Runtime Activation Contract. It defines metadata-only profiles, endpoint policy, activation policy, activation request/decision validation, health probe planning, tests, verifiers, docs, and Foundation Gate criteria.

M22 stops before runtime behavior:

- no model was called.
- no runtime was activated.
- no endpoint was contacted.
- no prompt was processed.
- no tool call was executed.
- no memory write occurred.

M23 is implemented/released by v0.27.0 as a separate manual/CLI-only,
loopback-only, fixed-prompt-only, non-tool, non-authoritative local model call
path. M23 does not authorize runtime activation, endpoint probes, provider SDKs,
runtime packages, arbitrary prompts, user-content model calls, OpenWebUI runtime
behavior, Control Center execution controls, tool execution, memory writes, file
writes, dependencies, or production authority.

M23 must not inherit authority from M22 metadata. The M23 path has its own fixed
prompt, approval validation, redaction policy, receipt policy, timeout cap,
local-only guard, tests, verifier coverage, and Foundation Gate criteria.
