# Emergency Stop + Process Kill Safety Policy

M89 policy enables Emergency Stop + Process Kill Safety for review only. The
policy requires contract-only, review-only, deterministic, local-only, safe refs
only handling with exact M88 Mutating Command Proposal binding.

The policy requires a safe target process ref and safe emergency scope ref. It
denies emergency stop execution, process kill, process signal, command
execution, subprocess execution, shell execution, process spawn, filesystem
mutation, network access, tool execution, browser automation, plugin execution,
remote execution, model call, memory write, context injection, background
worker, backend route, Control Center control, dependency, and production
authority.

The policy rejects raw PID, raw signal, raw command, shell string, raw output,
raw prompt, raw provider payload, and secret-like metadata. Evaluator
boundaries revalidate policy, request, decision, and receipt fields. M90 remains
future.
