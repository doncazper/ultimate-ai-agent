# Shell Dry-Run Classifier Receipt Plan

M83 receipt plans are safe summary only.

Receipt plans must not store:

- raw command content
- shell string content
- raw prompt content
- raw provider payloads
- secrets
- process output
- filesystem output
- network output

Receipt plans must record no side effects and no dry-run execution. They must
also preserve that there is no command execution, no subprocess execution, no
shell execution, no process spawn, no filesystem mutation, no network access,
no tool execution, no browser automation, no plugin execution, no remote
execution, no model call, no memory write, no context injection, no background
worker, no backend route, no Control Center control, no dependency, and no
production authority.

Evaluator boundaries revalidate receipt plan fields.

M84 remains future.
