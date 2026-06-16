# Connector Write Execution Low-Risk Non-Goals

M128 does not introduce a general connector runtime. It is only the first
low-risk connector write execution contract over exact M127 dry-run refs and an
injected safe transport.

Non-goals:

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
- no mailbox, calendar, contacts, or messages account connection
- no backend route
- no Control Center control
- no dependency
- no model call
- no memory write
- no context injection
- no broad autonomy
- no beta release
- no production authority
- no M129 work

Any transport response that reports hidden network access, credentials, raw
content, send/delete/export behavior, attachment download, memory write, context
injection, or production authority is rejected.
