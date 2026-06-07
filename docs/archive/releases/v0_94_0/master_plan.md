# v0.94.0 Master Plan

M90 Shell/Subprocess Hardening Freeze is a contract-only, review-only,
freeze-only milestone.

The release hardens the command safety conveyor by freezing shell,
subprocess, command, process spawn, emergency stop, process kill, and process
signal boundaries as safe metadata over exact M89 Emergency Stop + Process Kill
Safety decisions. It does not implement command execution, shell execution,
subprocess execution, process spawn, emergency stop execution, process kill,
process signal, filesystem mutation, network access, tool execution, browser
automation, plugin execution, remote execution, model call, memory write,
context injection, background worker, backend route, Control Center control,
dependency, M91 work, or production authority.

Foundation Gate, static verification, documentation integrity, and tests must
all preserve exact M89 binding, safe hardening refs, no shell string, no raw
command, no raw PID, no raw signal, safe summary only, and evaluator
boundaries revalidate safety-critical fields.
