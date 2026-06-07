# Shell/Subprocess Hardening Freeze Non-Goals

M90 does not implement command execution, shell execution, subprocess
execution, process spawn, emergency stop execution, process kill, process
signal, filesystem mutation, network access, tool execution, browser
automation, plugin execution, remote execution, model call, memory write,
context injection, background worker, backend route, Control Center control,
dependency, production authority, or M91 work.

M90 does not store a shell string, raw command, raw output, raw PID, raw signal,
raw prompt, raw provider payload, or secret-like content.

M90 is a contract-only, review-only, freeze-only, deterministic, local-only,
safe refs only hardening milestone. It keeps the M89 Emergency Stop + Process
Kill Safety boundary exact and revalidated. M91 remains future.
