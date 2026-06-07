# Shell/Subprocess Hardening Freeze Receipt Plan

M90 receipt plans are safe summary only and safe refs only. They may store the
hardening freeze ref, exact M89 Emergency Stop + Process Kill Safety decision
ref, command ref, sandbox spec ref, safe target process ref, safe emergency
scope ref, and safe hardening refs.

M90 receipt plans store no shell string, no raw command, no raw output, no raw
PID, no raw signal, no raw prompt, and no secret-like content.

M90 receipt plans record no command execution, no shell execution, no
subprocess execution, no process spawn, no emergency stop execution, no process
kill, no process signal, no filesystem mutation, no network access, no tool
execution, no browser automation, no plugin execution, no remote execution, no
model call, no memory write, no context injection, no background worker, no
backend route, no Control Center control, no dependency, and no production
authority. Evaluator boundaries revalidate receipt fields. M91 remains future.
