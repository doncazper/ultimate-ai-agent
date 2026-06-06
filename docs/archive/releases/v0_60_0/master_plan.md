# v0.60.0 Master Plan

Milestone: M56 Agent Eval Regression Harness.

Scope:

- Add deterministic local eval regression harness contracts.
- Add policy validation for safe eval regression reporting.
- Add eval case, suite, observation, result, report, and receipt-plan models.
- Deny model calls, provider calls, tool execution, shell execution, browser
  automation, network access, memory writes, context injection, raw prompt
  capture, raw provider payload capture, external dataset fetch, score
  authority, backend routes, dependencies, and production authority.
- Add tests, docs, verifiers, and Foundation Gate coverage.

Non-goals:

- No live eval execution.
- No model/provider call.
- No tool, shell, or browser execution.
- No network access.
- No raw prompt or provider payload capture.
- No memory write or context injection.
- No backend routes or Control Center controls.
- No M57 implementation.
