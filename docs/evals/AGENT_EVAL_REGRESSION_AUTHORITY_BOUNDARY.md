# Agent Eval Regression Authority Boundary

M56 eval regression reports are non-authoritative review artifacts.

M56 adds no production authority.

An eval report may show that an explicit safe observation matched an expected
safe outcome ref. That result does not authorize routing, context injection,
memory writes, tool execution, provider calls, shell execution, browser
automation, network access, export, production rollout, or approval decisions.

Model output is never truth. Runtime output is never truth. Memory is recall,
not authority. Context packs are not authority. Tool intents are not execution
authority. Task plans are not execution authority. Approval refs are identifiers,
not authority. `approval_test_*` is never runtime authority.

The M56 harness must not contain raw prompts, raw provider payloads, secrets, or
private payload dumps in cases, observations, reports, receipt plans, metadata,
logs, docs, or safe messages.

M56 has no backend route, no Control Center control, no dependency, no production
authority, and no M57 implementation. M57 remains future.
