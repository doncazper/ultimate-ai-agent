# Mutating Command Proposal Authority Boundary

M88 mutating command proposal decisions are review metadata only. They are not
authority to execute a command, start a shell, spawn a process, mutate the
filesystem, access the network, execute tools, automate browsers, enable
plugins, call models, write memory, inject context, add backend routes, add
Control Center controls, add dependencies, or grant production authority.

Approval refs, audit refs, replay refs, safe argument refs, and mutation scope
refs are identifiers only. They do not grant command execution authority,
filesystem mutation authority, shell execution authority, subprocess execution
authority, process spawn authority, tool execution authority, or production
authority.

M88 must not store a shell string, raw command, raw output, raw prompt, raw
provider payload, secret-like content, or side-effect evidence. Receipt plans
store safe refs only and safe summary only.

Evaluator boundaries revalidate exact M87 sandboxed command audit replay
binding, safe mutation scope, safe argument refs, raw-content flags, execution
flags, mutation flags, route flags, dependency flags, and production authority
flags.

M89 remains future.
