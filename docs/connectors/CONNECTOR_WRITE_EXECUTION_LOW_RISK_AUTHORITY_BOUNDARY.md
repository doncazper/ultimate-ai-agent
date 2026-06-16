# Connector Write Execution Low-Risk Authority Boundary

M128 is low-risk-only, local-only, safe-ref-only, and exact-bound. It permits a
single reviewed connector write only through an injected safe transport with an
exact connector write approval ref and exact M127 dry-run plan binding.

Allowed authority:

- build a low-risk connector write execution decision from an already-reviewed
  M127 dry-run decision
- require exact connector write approval refs, scoped execution refs, low-risk
  classification refs, audit refs, replay refs, revocation refs, and kill-switch
  refs
- perform the low-risk write only through an injected safe transport
- record a safe result ref and safe summary in a receipt

Denied authority:

- no live connector runtime
- no account auth
- no network access
- no credential handling
- no raw connector content
- no full content read
- no connector send execution
- no connector delete execution
- no connector export
- no connector bulk export
- no attachment download
- no model call
- no memory write
- no context injection
- no backend route
- no Control Center control
- no dependency
- no production authority

The M128 transport boundary is intentionally boring: it is injected, explicit,
bounded, and revalidated before a result can be recorded.
