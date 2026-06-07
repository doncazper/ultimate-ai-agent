# Sandboxed Command Audit Replay

M87 adds Sandboxed Command Audit Replay as a contract-only, review-only,
replay-view-only, deterministic, local-only contract over an exact M86 Shell
Approval Gate v1 decision.

The replay view records safe refs only and safe summary only for a reviewed
sandboxed command approval chain. It binds the exact M86 shell approval gate
decision ref, M85 read-only command allowlist decision ref, approval bundle ref,
approval ref, command ref, sandbox spec ref, actor ref, audit ref, replay ref,
and exact replay step refs.

M87 does not start a replay runner, retry a command, run a command, execute a
shell, execute a subprocess, spawn a process, mutate files, access the network,
execute tools, automate a browser, execute plugins, run remotely, call a model,
write memory, inject context, start a background worker, add backend routes, add
Control Center controls, add dependencies, or grant production authority.

M87 stores no shell string, no raw command, no raw output, no raw prompt, no raw
provider payload, and no secret-like content. Evaluator boundaries revalidate
safety-critical fields, including model-copy-mutated M86 shell approval gate
decisions, replay steps, execution flags, raw-content flags, and receipt plans.

M88 remains future.
