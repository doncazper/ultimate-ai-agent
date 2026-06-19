# M114 Account Connector Policy

The M114 policy is contract-only and review-only. It requires safe refs,
connector contract refs, connector scope refs, credential boundary ref, auth
boundary ref, data access boundary refs, audit, replay, and a no-effect receipt
plan.

The policy requires actor-bound, baseline-bound, source-secrets-boundary-bound,
user-bound, workspace-bound, credential-boundary-bound, and auth-boundary-bound
records.

The policy denies no production authority, no production runtime, no auth
runtime, no login, no session cookie, no OAuth flow, no token exchange, no
credential handling, no credential storage, no credential read, no credential
write, no secret material access, no secret export, no vault runtime, no account
connector runtime, no account connector, no network access, no account action,
no model call, no memory write, no context injection, no execution, no tool
execution, no shell execution, no browser automation, no plugin execution, no
mobile sensor, no background worker, no remote execution, no backend route, no
Control Center control, and no dependency.

M115 remains future. M150 remains the planned v1.2.0-alpha target.
