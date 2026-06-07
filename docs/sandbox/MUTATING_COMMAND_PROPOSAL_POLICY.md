# Mutating Command Proposal Policy

M88 policy allows mutating command proposal review only. The policy is
contract-only, proposal-only, review-only, deterministic, local-only, and safe
refs only.

Required policy boundaries:

- exact M87 sandboxed command audit replay binding.
- safe mutation scope.
- safe argument refs.
- safe summary only output.
- evaluator boundaries revalidate safety-critical fields.

Denied policy boundaries:

- no command execution.
- no subprocess execution.
- no shell execution.
- no process spawn.
- no filesystem mutation.
- no network access.
- no tool execution.
- no browser automation.
- no plugin execution.
- no remote execution.
- no model call.
- no memory write.
- no context injection.
- no background worker.
- no backend route.
- no Control Center control.
- no dependency.
- no production authority.

M89 remains future.
