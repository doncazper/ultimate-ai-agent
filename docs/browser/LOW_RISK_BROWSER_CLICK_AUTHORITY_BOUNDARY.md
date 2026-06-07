# M94 Low-Risk Browser Click Authority Boundary

M94 is a scoped browser click authority boundary, not broad browser automation.
The only permitted action is a low-risk click in a scoped session on an
allowlisted page and allowlisted action, after exact M93 binding and exact click
approval have been validated.

Approval refs are identifiers only. approval_test_* refs are not runtime
authority. A promotion approval from M93 is not enough by itself; M94 requires
exact click approval and evaluator boundaries revalidate every safety-critical
field before a decision or result is accepted.

M94 grants no form submission, no typing, no purchase, no download, no upload,
no authentication, no account change, no destructive action, no credential or
cookie access, no raw DOM, no screenshot, no broad navigation, no external
network, no shell execution, no plugin execution, no model call, no memory
write, no context injection, no backend route, no Control Center control, no
dependency, and no production authority.

M95 remains future.
