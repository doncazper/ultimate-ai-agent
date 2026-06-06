# Agent Eval Regression Harness

v0.60.0 / M56 implements Agent Eval Regression Harness as deterministic local
contract-only regression reporting over explicit safe observations.

M56 can define eval cases, eval suites, explicit safe observations, deterministic
case-result comparisons, regression reports, and no-effect receipt plans. The
harness compares expected outcome refs with observed outcome refs that were
already provided as safe refs. It does not run an agent.

The harness adds no production authority.

M56 has no model call, no provider call, no tool execution, no shell execution,
no browser automation, no network access, no memory write, no context injection,
no raw prompt capture, no raw provider payload capture, no external dataset
fetch, no backend route, no Control Center control, no dependency, no production
authority, and no M57 implementation.

Eval results are non-authoritative. They are regression evidence for review,
not truth authority, not routing authority, not approval authority, not execution
authority, not memory authority, and not context authority.

M57 remains future.
