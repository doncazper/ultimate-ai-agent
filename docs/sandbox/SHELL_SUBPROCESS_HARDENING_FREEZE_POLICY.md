# Shell/Subprocess Hardening Freeze Policy

M90 policy enables Shell/Subprocess Hardening Freeze for review only. The
policy requires contract-only, review-only, freeze-only, deterministic,
local-only, safe refs only handling with exact M89 Emergency Stop + Process
Kill Safety binding.

The policy freezes shell, subprocess, command, process spawn, emergency stop,
process kill, and process signal boundaries. It denies command execution,
shell execution, subprocess execution, process spawn, emergency stop execution,
process kill, process signal, filesystem mutation, network access, tool
execution, browser automation, plugin execution, remote execution, model call,
memory write, context injection, background worker, backend route, Control
Center control, dependency, and production authority.

The policy rejects shell string, raw command, raw output, raw PID, raw signal,
raw prompt, raw provider payload, and secret-like metadata. Evaluator
boundaries revalidate policy, request, decision, and receipt fields. M91
remains future.
