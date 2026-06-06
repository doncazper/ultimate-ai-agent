# Agent Eval Regression Policy

M56 eval regression policy is deterministic, contract-only, local-only, and
safe-ref-only.

The policy adds no production authority.

Allowed:

- eval case contracts with redacted input summaries.
- eval suite contracts with deterministic seed refs.
- explicit safe observation contracts.
- comparison of expected outcome refs to observed outcome refs.
- regression reports and no-effect receipt plans.
- documentation, tests, static verification, and Foundation Gate coverage.

Denied:

- model call.
- provider call.
- tool execution.
- shell execution.
- browser automation.
- network access.
- memory write.
- context injection.
- raw prompt capture.
- raw provider payload capture.
- external dataset fetch.
- score authority.
- backend route.
- Control Center control.
- dependency.
- production authority.

M56 does not execute eval cases. It only validates and summarizes already
provided safe observations. Any future runtime sandbox architecture belongs to a
later reviewed milestone, and M57 remains future.
