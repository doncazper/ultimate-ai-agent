# Emergency Stop + Process Kill Safety Authority Boundary

M89 is an authority boundary, not an authority grant.

The Emergency Stop + Process Kill Safety decision is contract-only and
review-only. It can explain that a proposed emergency stop or process kill
needs safety review, but it cannot authorize or perform emergency stop
execution, process kill, process signal, command execution, subprocess
execution, shell execution, process spawn, filesystem mutation, network access,
tool execution, browser automation, plugin execution, remote execution, model
call, memory write, context injection, background worker, backend route, Control
Center control, dependency, or production authority.

Approval refs, model output, runtime output, memory, context packs, tool
intents, task plans, and audit refs are identifiers or evidence inputs only;
they are not process kill authority. `approval_test_*` is never runtime
authority.

Evaluator boundaries revalidate exact M88 binding, safe target process ref,
safe emergency scope ref, safe refs only receipt plans, no raw PID, no raw
signal, safe summary only, and all no-authority flags. M90 remains future.
