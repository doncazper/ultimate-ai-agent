# M94 Low-Risk Browser Click Non-Goals

M94 does not implement general browser automation. It introduces autonomous
browser clicks, low-risk only, under scoped session and allowlist constraints.

Non-goals:

- no form submission
- no typing
- no purchase
- no download
- no upload
- no authentication
- no account change
- no destructive action
- no credential or cookie access
- no raw DOM
- no screenshot
- no broad navigation
- no external network
- no shell execution
- no plugin execution
- no model call
- no memory write
- no context injection
- no backend route
- no Control Center control
- no dependency
- no production authority

The contract still requires exact M93 binding, exact click approval,
allowlisted page, allowlisted action, scoped session, audit, revocation,
injected transport, safe refs only, safe summary only, and evaluator boundaries
revalidate safety-critical fields.

M95 remains future.
