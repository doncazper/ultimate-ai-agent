# Sandboxed Command Audit Replay Receipt Plan

M87 receipt plans store safe refs only, replay step refs only, and safe summary
only. Receipts may include the replay view ref, exact M86 shell approval gate
decision ref, approval bundle ref, approval ref, command ref, sandbox spec ref,
audit ref, replay ref, and replay step refs.

M87 receipts store no shell string, no raw command, no raw output, no raw
prompt, no raw provider payload, and no secret-like content.

Receipt plans record that no replay runner was started and no replay execution,
command execution, subprocess execution, shell execution, process spawn,
filesystem mutation, network access, tool execution, browser automation, plugin
execution, remote execution, model call, memory write, context injection,
background worker, backend route, Control Center control, dependency, or
production authority occurred.

M88 remains future.
