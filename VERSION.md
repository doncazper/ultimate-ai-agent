# Ultimate AI Agent Version

Current active baseline: **v0.76.0**

v0.76.0 implements M72 Read-Only HTTP Fetch Tool, Allowlisted. It adds a
bounded allowlisted read-only HTTP fetch tool through the governed tool runtime
adapter, with explicit host allowlists, HTTPS-only and GET-only validation, no
credentials or cookies, no request body, no request headers, no query strings,
bounded response bytes, redaction before return, bounded redacted preview
outputs, safe receipt metadata, evaluator revalidation, documentation-integrity
checks, static verification, and Foundation Gate coverage.

It adds no unrestricted network tool, authenticated network action, credentials
or cookies, request body, non-GET method, raw response body, raw headers,
download or export, context injection, memory write, model call, browser
automation, backend routes, Control Center controls, dependencies, M73 work, or
production authority.
