# Mutating Command Proposal Receipt Plan

M88 receipt plans store safe summary only, safe refs only, and mutation scope
refs only.

Receipt plans must not store raw command, shell string, raw output, raw prompt,
raw provider payload, secrets, command execution evidence, subprocess execution
evidence, shell execution evidence, process spawn evidence, filesystem mutation
evidence, side effects, backend route evidence, Control Center control evidence,
dependency evidence, or production authority evidence.

Receipt plans bind exactly to the mutating command proposal ref, M87 sandboxed
command audit replay decision ref, M86 shell approval gate decision ref,
approval bundle ref, approval ref, command ref, sandbox spec ref, mutation
intent ref, and mutation scope ref.

M89 remains future.
