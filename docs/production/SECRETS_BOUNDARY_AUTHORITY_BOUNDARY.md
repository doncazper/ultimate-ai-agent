# M113 Secrets Boundary Authority Boundary

M113 records safe refs for a future secrets boundary. It does not grant
authority to read, store, write, export, unlock, rotate, copy, send, or handle
credential values or secret material.

The following are explicitly out of authority: production authority, production
runtime, auth runtime, login, session cookie handling, credential handling,
credential storage, credential read, credential write, secret material access,
secret export, vault runtime, account connector, network access, model call,
memory write, context injection, execution, tool execution, shell execution,
browser automation, plugin execution, mobile sensor, background worker, remote
execution, backend route, Control Center control, dependency, and beta release.

User refs, workspace refs, credential vault contract refs, secret boundary refs,
credential scope refs, audit refs, replay refs, and receipt-plan refs are not
authority. They are reviewed identifiers for future governed work.
