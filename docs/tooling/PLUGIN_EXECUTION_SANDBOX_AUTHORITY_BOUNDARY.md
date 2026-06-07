# M96 Plugin Execution Sandbox Authority Boundary

M96 is not a general plugin runtime. It is a narrow sandbox contract for one built-in test plugin.

Approval refs are identifiers, not plugin execution authority. `approval_test_*` refs are denied. Model refs, memory refs, context refs, task-plan refs, tool-intent refs, runtime refs, and OpenWebUI refs cannot authorize plugin execution.

The sandbox decision does not grant external plugin loading, marketplace plugin use, arbitrary plugin code, runtime import, networked plugin fetch, plugin secret access, raw plugin payload, shell execution, network access, browser automation, filesystem mutation, model provider call, memory write, context injection, backend route, Control Center control, dependency, production authority, or M97 work.

M97 remains future.
