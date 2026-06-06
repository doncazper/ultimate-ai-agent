# Read-Only HTTP Fetch Receipt Plan

M72 read-only HTTP fetch receipt plans record safe metadata only.

Receipt plans may record:

- tool invocation ref
- tool ref
- safe URL ref
- host ref
- status code
- safe content type
- response byte count
- preview truncation status
- redaction summary
- stable reason codes

Receipt plans must not store:

- raw response body
- raw headers
- raw absolute URL
- query string
- credentials or cookies
- request body
- download or export payload
- context injection payload
- memory write payload
- model/provider payload
- browser automation payload
- tool execution payload
- production authority

Redaction before return is required, and receipt metadata must remain
non-authoritative. The receipt plan is not an approval, not context injection,
not a memory write, not model authority, not tool execution authority, and not
production authority.

M73 remains future.
