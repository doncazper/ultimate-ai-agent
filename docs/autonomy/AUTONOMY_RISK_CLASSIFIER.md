# M68 Autonomy Risk Classifier

M68 adds Autonomy Risk Classifier contracts as contract-only, review-only,
deterministic validation over M66 scoped approval bundles and M67 Revocation +
Kill Switch records.

The classifier derives the highest risk from caller-declared risk, scoped
approval bundle risk, and explicit risk signals. The derived risk always wins;
risk downgrade is denied at evaluator boundaries. Risk downgrade denied is a
stable M68 safety invariant.

## Boundary

- Autonomy Risk Classifier contracts are contract-only.
- Autonomy Risk Classifier contracts are review-only.
- Risk classification is deterministic.
- Risk classification binds exact scoped approval bundle refs.
- Risk classification binds exact Revocation + Kill Switch refs.
- Risk classification binds actor, resource, capability, allowlist, audit, and
  replay refs.
- Declared risk is an input, not authority.
- Risk signals are explanatory inputs, not authority.
- Approval refs are identifiers and never authority.
- `approval_test_` refs are denied.
- Evaluator boundaries revalidate scoped approval bundles, Revocation + Kill
  Switch records, risk signals, and derived risk.

## Non-Authority Boundary

M68 grants no authority and performs no side effects:

- no policy activation
- no session start
- no autonomous actions
- no background worker
- no execution
- no tool execution
- no shell execution
- no network tools
- no browser automation
- no plugin execution
- no mobile sensor access
- no remote execution
- no memory write
- no context injection
- no model/provider authority
- no backend route
- no Control Center control
- no dependency
- no production authority

M69 remains future.
