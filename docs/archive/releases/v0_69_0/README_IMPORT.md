# README Import - v0.69.0

v0.69.0 implements M65 Autonomy Audit + Replay Viewer.

This release adds contract-only, review-only, replay-view-only autonomy audit
and replay viewer contracts. Audit replay views bind exact simulation result
refs, exact simulation request refs, exact policy decision refs, exact replay
step refs, actor refs, audit refs, and replay refs from M64 simulation results.

Approval refs are identifiers and do not grant authority. v0.69.0 adds no
policy activation, no session start, no autonomous actions, no background
worker, no execution, no tool execution, no shell execution, no network tools,
no browser automation, no context injection, no memory write, no backend route,
no dependency, and no production authority. M66 remains future.
