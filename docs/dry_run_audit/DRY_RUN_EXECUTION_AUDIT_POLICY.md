# Dry-Run Execution Audit Policy

M58 dry-run execution audit policy is dry-run-only, contract-only, local-only,
and no-effect.

Allowed:
- validate structured safe refs.
- bind audit requests to exact intent refs.
- bind audit requests to an actor ref and replay-key ref.
- produce deterministic dry-run audit entries and no-effect receipt plans.

Denied:
- real execution.
- tool execution.
- subprocess.
- shell execution.
- process spawn.
- file mutation.
- network access.
- model/provider calls.
- memory write.
- context injection.
- browser automation.
- plugin execution.
- remote execution.
- backend routes.
- Control Center controls.
- dependencies.
- production authority.

The harness must revalidate current fields at evaluator boundaries. Constructor
validation alone is not trusted.

M59 remains future.
