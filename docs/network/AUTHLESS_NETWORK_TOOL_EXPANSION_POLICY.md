# Authless Network Tool Expansion Policy

M95 Network Tool Expansion, Authless Only is read-only and disabled as runtime authority. A valid request must bind an actor, scope, scoped session, exact scope approval, audit ref, revocation ref, M72 read-only fetch tool ref, allowlisted domain policy ref, target host, and safe target path.

The policy requires authless access, an allowlisted domain, HTTPS, GET only, redirect controls, bounded output, redaction, exact scope, audit, revocation, transport injection, safe refs only, and redacted preview only. Redirects must remain allowlist-bound and count-limited.

The policy denies unrestricted network access, authenticated network access, credentials, cookies, credential headers, request body, POST, PUT, PATCH, DELETE, account action, private network, download, export, browser form, provider model call, shell execution, plugin execution, memory write, context injection, backend route, Control Center control, dependency, production authority, and side effects. M96 remains future.
