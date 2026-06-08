# M113 Secrets Boundary + Credential Vault Contract

Checkpoint M113 adds a contract-only and review-only secrets boundary plus
credential vault contract. It records safe refs only: source M112
User/Workspace Identity Model refs, user refs, workspace refs, secret boundary
refs, credential scope refs, a redaction policy ref, audit refs, replay refs,
accepted checkpoint refs, and a no-effect receipt plan.

The credential vault contract is not a vault runtime. It is a reviewed
boundary record that says future credential work must be exact-scope,
actor-bound, user-bound, workspace-bound, redacted, replay-safe, revocable where
applicable, and separately reviewed before any runtime exists.

M113 adds no production authority, no production runtime, no auth runtime, no
login, no session cookie handling, no credential handling, no credential
storage, no credential read, no credential write, no secret material access, no
secret export, no vault runtime, no account connector, no network access, no
model call, no memory write, no context injection, no execution, no tool
execution, no shell execution, no browser automation, no plugin execution, no
mobile sensor, no background worker, no remote execution, no backend route, no
Control Center control, no dependency, and no beta release.

M114 remains future. M150 remains the v1.0.0-alpha target.
