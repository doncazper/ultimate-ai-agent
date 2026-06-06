# README Import - v0.68.0

v0.68.0 implements M64 Autonomous Plan Simulator.

This release adds contract-only and review-only autonomous plan simulation
contracts. Simulation requests bind actor refs, resource refs, capability refs,
allowlist refs, audit refs, replay refs, and M63 policy decisions. The simulator
validates a deterministic dependency graph and returns safe review-only
simulation result records.

Approval refs are identifiers and do not grant authority. v0.68.0 adds no
policy activation, no session start, no autonomous actions, no background
worker, no execution, no tool execution, no shell execution, no network tools,
no browser automation, no context injection, no memory write, no backend route,
no dependency, and no production authority. M65 remains future.
