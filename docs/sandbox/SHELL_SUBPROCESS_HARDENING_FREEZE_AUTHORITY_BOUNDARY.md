# Shell/Subprocess Hardening Freeze Authority Boundary

M90 is a shell/subprocess hardening freeze, not an authority grant. The freeze
decision is contract-only, review-only, freeze-only, deterministic,
local-only, and safe refs only.

The exact M89 Emergency Stop + Process Kill Safety decision must be rebound and
revalidated at evaluator boundaries. Approval refs, command refs, sandbox refs,
audit refs, replay refs, safe target process refs, and safe emergency scope
refs are identifiers only. They do not authorize command execution, shell
execution, subprocess execution, process spawn, emergency stop execution,
process kill, process signal, filesystem mutation, network access, tool
execution, browser automation, plugin execution, remote execution, model call,
memory write, context injection, background worker, backend route, Control
Center control, dependency, or production authority.

The authority boundary denies shell string, raw command, raw output, raw PID,
raw signal, raw prompt, raw provider payload, and secret-like content. M91
remains future.
