# Read-Only HTTP Fetch Policy

The M72 read-only HTTP fetch policy is allowlisted, bounded, redacted, and
non-authoritative.

Policy invariants:

- read-only HTTP fetch must be allowlisted
- host allowlist is required
- wildcard hosts are denied
- local, private, and IP-literal hosts are denied
- HTTPS is required
- GET is required
- redirects are denied
- credentials or cookies are denied
- request body is denied
- request headers are denied
- non-GET method is denied
- query strings are denied
- raw response body is denied
- raw headers are denied
- download or export is denied
- context injection is denied
- memory write is denied
- model call is denied
- browser automation is denied
- tool execution is denied
- backend route is denied
- Control Center control is denied
- dependency change is denied
- production authority is denied

All request, output, decision, and receipt boundaries revalidate current object
fields. Model-copy mutations that request raw response body, raw headers,
credentials, cookies, request body, non-GET method, download or export, context
injection, memory write, model call, browser automation, tool execution, backend
route, Control Center control, dependency, or production authority are denied.

Redaction before return is required. The output is a bounded redacted preview,
not a truth source, context pack, memory write, execution approval, or production
authority.

M73 remains future.
