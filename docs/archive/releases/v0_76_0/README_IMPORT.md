# v0.76.0 README Import

v0.76.0 implements M72 Read-Only HTTP Fetch Tool, Allowlisted.

It adds a bounded, allowlisted, read-only HTTP fetch tool through the governed
tool runtime adapter. The tool validates explicit allowlisted hosts, HTTPS,
GET-only requests, no credentials or cookies, no request body, no request
headers, no query strings, redaction before return, bounded redacted previews,
safe output contracts, and safe receipt metadata.

It adds no unrestricted network tool, authenticated network action, credentials
or cookies, request body, non-GET method, raw response body, raw headers,
download or export, context injection, memory write, model call, browser
automation, backend route, Control Center control, dependency, production
authority, or M73 work.

M73 remains future.
