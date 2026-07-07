# Governed Web Evidence v1

Program task: UAA-P1-063

Governed Web Evidence v1 is a narrow evidence-gathering lane for UAA-backed
chat. It is not unrestricted browsing, browser automation, source crawling, a
search engine, a downloader, or a hidden network tool.

The capability builds on the M72 read-only HTTP fetch boundary and keeps UAA as
the guardrail owner. OpenWebUI remains a shell into UAA-managed behavior.

## Current Boundary

UAA-P1-063 adds:

- `GET /web-evidence/status` for operator-visible capability status and chatbot
  capability disclosure.
- `POST /web-evidence/request` for a governed evidence request envelope.
- `POST /control-center/web-evidence/attach` for the Control Center product
  slice, gated by active Browser/read AuthorityLease scope before any transport
  opens.
- HTTPS GET only.
- Explicit operator allowlist through `UAA_GOVERNED_WEB_EVIDENCE_ALLOWED_HOSTS`.
- Enablement through `UAA_GOVERNED_WEB_EVIDENCE_ENABLED=1`.
- Bounded response and preview limits.
- Redaction before returning any preview.
- Receipt refs, preview refs, host refs, path refs, and URL refs.
- No raw page/body storage and no raw header storage.

The current API route fails closed unless governed web evidence is enabled,
required Browser/read authority is active where the Control Center product slice
is used, and a reviewed transport is available. Core tests use an injected fake
transport plus explicit test AuthorityLease scope. This keeps the route contract
testable without adding hidden network access.

## Denied Capabilities

The milestone does not add:

- unrestricted browsing
- browser automation
- POST, PUT, PATCH, DELETE, or other mutation methods
- request bodies
- caller-supplied request headers
- cookies or session state
- credential material
- redirects
- downloads or exports
- raw response bodies
- raw response headers
- provider/model calls
- context injection
- memory writes
- shell/subprocess execution
- plugin execution
- production authority

## Chatbot Disclosure

Local model shells must receive the capability disclosure from
`/web-evidence/status` before claiming web evidence support. If the disclosure
says unavailable, models must not claim current web access.

When evidence is available, models must treat returned previews as untrusted web
content and cite `receipt_ref` or `preview_ref` rather than raw URLs or raw page
content.

## Verification

Required verification lanes:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_m72_gate_integration.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_governed_web_evidence.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/verify_documentation_integrity.py
```
