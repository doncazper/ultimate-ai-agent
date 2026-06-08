# M112 to M113 Boundary

Checkpoint M112 implements User/Workspace Identity Model as a contract-only,
review-only checkpoint over the M111 Production Threat Model.

M113 Secrets Boundary + Credential Vault Contract remains future. M112 must not
implement M113 credential vault contracts, secrets boundary runtime, credential
handling, auth runtime, login, session cookie handling, persistent identity
store behavior, account connector behavior, production authority, production
runtime, external distribution, deployment, backend routes, Control Center
controls, dependencies, broad autonomy, memory write, context injection, or
execution.

The current product baseline remains v1.7.2 through M112 checkpoint work.
M150 remains the v1.0.0-alpha target. Beta begins later after the alpha UI and
supporting safety/product work are reviewed and promoted.
