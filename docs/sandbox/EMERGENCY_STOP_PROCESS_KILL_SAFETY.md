# Emergency Stop + Process Kill Safety

v0.93.0 / M89 implements Emergency Stop + Process Kill Safety as
contract-only, review-only, deterministic, and local-only safety metadata over
an exact M88 Mutating Command Proposal decision.

M89 records safe target process ref, safe emergency scope ref, safe reason refs,
safe refs only receipt plans, stable reason codes, and safe summary only review
metadata. It does not record raw PID values or raw signal values.

M89 adds no emergency stop execution, no process kill, no process signal, no
command execution, no subprocess execution, no shell execution, no process
spawn, no filesystem mutation, no network access, no tool execution, no browser
automation, no plugin execution, no remote execution, no model call, no memory
write, no context injection, no background worker, no backend route, no Control
Center control, no dependency, and no production authority.

Evaluator boundaries revalidate the exact M88 decision and all safety-critical
M89 fields. M90 remains future.
