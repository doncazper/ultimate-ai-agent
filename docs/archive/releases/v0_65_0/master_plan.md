# v0.65.0 Master Plan

## Scope

Implement M61 Autonomy Mode Charter + Authority Levels as contract-only
planning and validation work.

## Included

- autonomy authority modes from Mode 0 through Mode 6
- default mode off requirement
- capability-toggle registry contracts
- consent, revocation, resource binding, duration, risk, and audit/replay
  documentation
- M61-M100 roadmap promotion
- documentation-integrity checks
- static verifier coverage
- Foundation Gate criteria and evaluator coverage
- tests for unsafe model_copy-mutated fields and approval-ref non-authority

## Excluded

- global autonomy switch
- production authority
- execution
- tool execution
- shell execution
- network tools
- browser automation
- plugin execution
- mobile sensor access
- remote execution
- background worker
- autonomous session
- memory writes
- context injection
- model/provider authority
- backend routes
- Control Center controls
- dependencies
- M62 implementation
