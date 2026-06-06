# Command Proposal Contracts

v0.86.0 / M82 implements Command Proposal Contracts as deterministic local
proposal-only and review-only contracts.

M82 may build a structured argv preview for human review. The preview is safe
metadata, not a shell string, not a subprocess request, and not execution
authority. It is local-only and non-authoritative.

The contracts require:

- prior milestone refs for M57, M58, M80, and M81
- a sandbox spec ref
- a command ref
- safe purpose text
- a safe command label
- structured argv preview with no shell string
- no raw absolute path
- safe summary only receipt metadata

The contracts enforce no command execution, no subprocess execution, no shell
execution, no process spawn, no filesystem mutation, no network access, no tool
execution, no browser automation, no plugin execution, no remote execution, no
model call, no memory write, no context injection, no background worker, no
backend route, no Control Center control, no dependency, and no production
authority.

Evaluator boundaries revalidate model-copy mutated fields. Constructor
validation alone is not authority.

M83 remains future.
