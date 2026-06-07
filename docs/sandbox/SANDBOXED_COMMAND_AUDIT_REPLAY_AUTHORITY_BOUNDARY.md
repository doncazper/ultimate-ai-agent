# Sandboxed Command Audit Replay Authority Boundary

M87 audit replay views are non-authoritative. They may explain a reviewed
sandboxed command approval chain with safe refs only, but they cannot authorize
or perform any command, shell, subprocess, process, filesystem, network, tool,
browser, plugin, remote, model, memory, context, backend route, Control Center,
dependency, or production action.

Approval refs are identifiers only. Audit refs and replay refs are identifiers
only. Replay step refs are identifiers only. None of them can become command
execution authority, shell execution authority, subprocess execution authority,
process spawn authority, filesystem mutation authority, context injection
authority, memory write authority, backend route authority, Control Center
control authority, or production authority.

M87 denies `approval_test_` refs and secret-like metadata. It stores no shell
string, no raw command, no raw output, no raw prompt, no raw provider payload,
and no secret-like content.

M88 remains future.
