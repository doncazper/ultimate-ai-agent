# Emergency Stop + Process Kill Safety Receipt Plan

M89 receipt plans store safe summary only and safe refs only.

Receipt plans may include emergency stop safety ref, process kill safety ref,
exact M88 Mutating Command Proposal decision ref, command ref, sandbox spec ref,
safe target process ref, and safe emergency scope ref.

Receipt plans store no raw PID, no raw signal, no raw command, no shell string,
no raw output, no raw prompt, no secrets, and no side effects. Receipt plans do
not claim emergency stop execution, process kill, process signal, command
execution, subprocess execution, shell execution, process spawn, filesystem
mutation, backend route, Control Center control, dependency, or production
authority.

Evaluator boundaries revalidate receipt bindings and safety-critical receipt
fields. M90 remains future.
