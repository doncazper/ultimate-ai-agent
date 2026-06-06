# Autonomy Consent And Revocation Policy

Status: M61 / v0.65.0 implemented-released contract.

M61 documents consent and revocation requirements for future autonomy work. It
does not capture consent, persist approvals, start autonomous sessions, execute
tools, or grant production authority.

## Required Future Properties

Any future risky toggle must be:

- exact-scope
- actor-bound
- resource-bound
- duration-bound
- risk-classed
- revocable
- auditable through audit/replay
- disabled by default
- dry-run first
- covered by tests, docs, static verifier checks, Foundation Gate checks, and
  pushed-release review

No approval ref, consent ref, memory ref, context ref, model output, runtime
output, task plan, or tool intent can authorize autonomy by itself.

## M61 Boundary

M61 has no global autonomy switch, no production authority, no execution, no
tool execution, no browser automation, no shell execution, no network tools, no
background worker, no autonomous session, no backend route, and no dependency.

M62 remains future.
