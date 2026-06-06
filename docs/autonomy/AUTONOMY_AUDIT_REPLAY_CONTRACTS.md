# Autonomy Audit Replay Contracts

M65 introduces safe contract shapes for autonomy audit and replay review:

- `AutonomyReplayStepView`
- `AutonomyAuditReplayView`
- `build_autonomy_audit_replay_view`
- `validate_autonomy_audit_replay_view`

These contracts are contract-only, review-only, replay-view-only, and
deterministic. They bind to M64 simulation results and expose only safe refs,
safe summaries, reason codes, and replay step references.

## Required Bindings

Each audit replay view must bind:

- exact simulation result ref
- exact simulation request ref
- exact policy decision ref
- exact replay step refs
- actor ref
- audit ref
- replay ref

Replay steps are display records only. A replay step view may show a simulated
step ref and replay outcome ref, but it must not run, retry, execute, mutate,
export, or activate anything.

## Validation Requirements

Validation denies:

- mismatched exact simulation result refs
- mismatched exact replay step refs
- forged replay step refs
- missing reason codes
- `approval_test_` refs
- secret-like metadata or unsafe payloads
- policy activation requests
- session start requests
- autonomous action flags
- background worker flags
- execution flags
- tool execution, shell execution, network tools, browser automation, plugin
  execution, mobile sensor, and remote execution flags
- memory write and context injection flags
- model/provider call authority
- production authority

Approval refs are identifiers and cannot authorize execution or replay running.
M66 remains future.
