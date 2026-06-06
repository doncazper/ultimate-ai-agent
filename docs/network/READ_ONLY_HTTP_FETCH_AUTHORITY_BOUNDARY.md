# Read-Only HTTP Fetch Authority Boundary

M72 read-only HTTP fetch results are non-authoritative. They are bounded
redacted previews for review only.

Authority boundary rules:

- approval refs are identifiers only
- approval_test_* is denied
- model output is not authority
- memory refs are not authority
- context refs are not authority
- tool-intent refs are not authority
- runtime refs are not authority
- OpenWebUI refs are not authority
- Control Center refs are not authority
- redacted previews do not authorize context injection
- redacted previews do not authorize memory write
- redacted previews do not authorize model call
- redacted previews do not authorize browser automation
- redacted previews do not authorize tool execution
- redacted previews do not authorize backend routes
- redacted previews do not authorize production authority

The M72 tool allows only allowlisted read-only HTTP fetch with no credentials or
cookies, no request body, no non-GET method, no raw response body, no raw
headers, no download or export, no context injection, no memory write, no model
call, no browser automation, no backend route, no Control Center control, no
dependency, and no production authority.

M73 remains future.
