# M113 Secrets Boundary Receipt Plan

M113 receipt plans store safe refs only. They may record the source M112
User/Workspace Identity Model ref, user ref, workspace ref, secret boundary
refs, credential scope refs, redaction policy ref, audit ref, replay ref,
accepted checkpoint refs, and no-effect receipt plan ref.

Receipts store no credential values, no secret material, no raw prompt, no raw
provider payload, no private file content, no auth material, no session cookie,
no credential read output, no credential write output, no vault runtime output,
and no side-effect evidence.

The receipt plan is a no-effect plan. It performs no production runtime, no
auth runtime, no login, no network access, no memory write, no context
injection, no execution, no backend route, no Control Center control, and no
dependency change.
