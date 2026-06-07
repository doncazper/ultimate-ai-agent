# Shell/Subprocess Hardening Freeze

v0.94.0 / M90 implements Shell/Subprocess Hardening Freeze as contract-only,
review-only, freeze-only, deterministic, and local-only safety metadata over an
exact M89 Emergency Stop + Process Kill Safety decision.

M90 records safe hardening refs, exact M89 binding refs, stable reason codes,
safe refs only receipt plans, and safe summary only review metadata. It records
no shell string, no raw command, no raw output, no raw PID, no raw signal, no
raw prompt, no raw provider payload, or secret-like content.

M90 adds no command execution, no shell execution, no subprocess execution, no
process spawn, no emergency stop execution, no process kill, no process signal,
no filesystem mutation, no network access, no tool execution, no browser
automation, no plugin execution, no remote execution, no model call, no memory
write, no context injection, no background worker, no backend route, no Control
Center control, no dependency, and no production authority.

Evaluator boundaries revalidate the exact M89 decision and all safety-critical
M90 fields. M91 remains future.
