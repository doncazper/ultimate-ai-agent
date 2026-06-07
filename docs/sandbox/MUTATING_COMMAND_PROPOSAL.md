# Mutating Command Proposal

M88 implements Mutating Command Proposal, No Execution as contract-only,
proposal-only, review-only validation over exact M87 Sandboxed Command Audit
Replay decisions.

The proposal may describe a mutating command intent for human review using safe
metadata, safe mutation scope refs, safe argument refs, stable reason codes, and
safe summary only receipt plans.

M88 is deterministic and local-only. It uses exact M87 sandboxed command audit
replay binding and evaluator boundaries revalidate safety-critical fields.

M88 adds no command execution, no subprocess execution, no shell execution, no
process spawn, no filesystem mutation, no network access, no tool execution, no
browser automation, no plugin execution, no remote execution, no model call, no
memory write, no context injection, no background worker, no backend route, no
Control Center control, no dependency, and no production authority.

M89 remains future.
