# M23 Non-Authoritative Output Policy

Status: Active M23 output policy documentation for v0.27.1.

M23 model output is non-authoritative. It is not truth, not approval authority,
not policy authority, and not trusted control input.

Output must not:

- approve actions.
- execute actions.
- call tools.
- write memory.
- write files.
- trigger OpenWebUI runtime bridge behavior.
- trigger Control Center execution.
- become production readiness evidence.

Responses are capped and redacted. Secret-like responses are blocked. Raw
responses are not stored. Tests and Foundation Gate use fake transport. M24
remains future.
