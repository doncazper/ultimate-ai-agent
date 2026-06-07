# M94 Low-Risk Browser Click Policy

The M94 policy allows only autonomous browser clicks, low-risk only. Each
low-risk click must be bound to a scoped session, an allowlisted page, an
allowlisted action, exact M93 promotion evidence, exact click approval, audit,
and revocation. The implementation uses injected transport so tests and local
contracts can verify the boundary without adding a browser runtime route.

The policy requires safe refs only and safe summary only receipt plans. It is
deterministic, local-only, and evaluator boundaries revalidate policy, request,
decision, transport response, and result fields.

The policy permits no form submission, no typing, no purchase, no download, no
upload, no authentication, no account change, no destructive action, no
credential or cookie access, no raw DOM, no screenshot, no broad navigation, no
external network, no shell execution, no plugin execution, no model call, no
memory write, no context injection, no backend route, no Control Center control,
no dependency, and no production authority.

M95 remains future.
