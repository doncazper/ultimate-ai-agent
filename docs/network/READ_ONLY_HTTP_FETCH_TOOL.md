# Read-Only HTTP Fetch Tool

v0.76.0 implements M72 Read-Only HTTP Fetch Tool, Allowlisted.

The M72 tool is a bounded, allowlisted, read-only HTTP fetch capability exposed
through the governed tool runtime adapter. It returns a bounded redacted preview
only. Redaction before return is required, and result contracts must not expose
raw response bodies, raw headers, raw absolute URLs, query strings, credentials,
cookies, downloads, exports, context injection, memory writes, model calls,
browser automation, tool execution, backend routes, Control Center controls,
dependencies, or production authority.

M72 requires:

- explicit host allowlist
- HTTPS only
- GET only
- no credentials or cookies
- no request body
- no non-GET method
- no request headers
- no query string
- no redirects
- bounded response bytes
- bounded redacted preview
- redaction before return
- no raw response body
- no raw headers
- no download or export
- no context injection
- no memory write
- no model call
- no browser automation
- no backend route
- no Control Center control
- no dependency
- no production authority

The runtime path requires an explicit reviewed transport object. Tests and
Foundation Gate coverage use fake transport only. The core tool contracts add no
embedded broad HTTP client and do not make hidden network calls.

M73 remains future.
