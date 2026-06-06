# v0.76.0 Master Plan

Milestone: M72 Read-Only HTTP Fetch Tool, Allowlisted.

Plan:

- Add a bounded allowlisted read-only HTTP fetch tool.
- Integrate the tool into the governed tool runtime adapter allowlist.
- Require explicit allowlisted hosts.
- Require HTTPS and GET.
- Deny credentials or cookies, request bodies, request headers, query strings,
  redirects, raw responses, downloads, exports, context injection, memory writes,
  model calls, browser automation, tool execution, backend routes, Control
  Center controls, dependencies, and production authority.
- Return bounded redacted previews only.
- Require redaction before return.
- Revalidate safety-critical fields at evaluator boundaries.
- Add tests, docs, documentation integrity checks, static verification, and
  Foundation Gate coverage.

Non-goals:

- no unrestricted network tool
- no authenticated network action
- no credentials or cookies
- no request body
- no non-GET method
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

M73 remains future.
