# Runtime Sandbox Spec Contracts

M81 Runtime Sandbox Spec contracts are spec-only, review-only, deterministic,
and local-only.

The contracts require:

- prior milestone refs for M57, M58, and M80
- unique boundary refs
- unique threat model refs
- optional unique audit requirement refs
- safe summary text with no raw prompt, no raw provider payload, and no
  secret-like metadata

The contracts deny runtime sandbox execution, command proposal, command
execution, subprocess execution, shell execution, process spawn, filesystem
mutation, network access, tool execution, browser automation, plugin execution,
remote execution, model call, memory write, context injection, background
worker, backend route, Control Center control, dependency, and production
authority.

Evaluator boundaries revalidate model-copy mutated fields. Constructor
validation alone is not authority.

M82 remains future.
