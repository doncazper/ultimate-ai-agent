# Sandboxed Echo/No-Op Command Authority Boundary

M84 does not grant execution authority. The sandboxed echo/no-op command is
in-process only and cannot authorize command execution, subprocess execution,
shell execution, process spawn, filesystem mutation, network access, tool
execution, browser automation, plugin execution, remote execution, model call,
memory write, context injection, background worker, backend route, Control
Center control, dependency, or production authority.

M82 command proposals, M83 shell dry-run classifier decisions, model output,
runtime output, memory refs, context refs, tool-intent refs, approval refs, and
approval_test_* refs are not authority to execute a shell or subprocess.

The only accepted input is a safe M83 no-effect classification. M85 remains
future.
