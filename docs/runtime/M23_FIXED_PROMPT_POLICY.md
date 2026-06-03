# M23 Fixed Prompt Policy

Status: Active M23 policy documentation for v0.27.1.

M23 is fixed-prompt-only. The only allowed prompt id is
`m23_fixed_local_model_smoke_v1`, and the prompt text must exactly match the
repo-defined fixed prompt.

The CLI must not accept arbitrary prompt input, prompt files, stdin prompt
input, clipboard input, memory input, OpenWebUI transcript input, raw files,
raw memory contents, credentials, or user task content. M23 has no arbitrary
prompt path and no user content path.

The fixed prompt is non-sensitive and exists only for local smoke validation.
It cannot request tool execution, memory write, file write, approval bypass, or
Control Center execution. Model output from this prompt is non-authoritative.

Tests and Foundation Gate use fake transport. M24 remains future.
