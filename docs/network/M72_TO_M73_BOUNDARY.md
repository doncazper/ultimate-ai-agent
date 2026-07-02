# M72 to M73 Boundary

M72 implements Read-Only HTTP Fetch Tool, Allowlisted. It introduces a bounded
allowlisted read-only HTTP fetch tool through the governed tool runtime adapter.
The Authority Graduation Program Prompt 02 lane adds an explicit real-world
HTTPS GET transport through `WebAccessGateway` plus CLI inspection, while
keeping the default tool runtime fail-closed unless that transport is supplied.

M72 allows only:

- explicit allowlisted host
- HTTPS
- GET
- bounded response bytes
- bounded redacted preview
- redaction before return
- safe result metadata
- fake transport in tests and Foundation Gate
- explicit real-world transport through `WebAccessGateway`
- CLI inspection via `scripts/inspect_read_only_web_fetch.py`

M72 does not add:

- unrestricted network tool
- authenticated network action
- credentials or cookies
- request body
- non-GET method
- request headers
- query string
- redirects
- raw response body
- raw headers
- download or export
- context injection
- memory write
- model call
- browser automation
- tool execution
- backend route
- Control Center control
- dependency
- unrestricted web fetching
- browser/provider/connector authority
- production authority

M73 is the future Browser Automation Contract Review milestone. M73 may add
contract-only review for future browser automation categories, but M73 must not
be implemented by M72.

M73 remains future.
