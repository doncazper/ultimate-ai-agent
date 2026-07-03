# Web Evidence Level 1 Dogfood Evidence

Status: safe-ref dogfood evidence, not broader web authority
Lane: Web Evidence
Date: 2026-07-03

## Command

```bash
.venv/bin/python scripts/inspect_read_only_web_fetch.py \
  --url https://example.com/ \
  --allowed-host example.com \
  --request-ref http-fetch-request:dogfood-web-evidence-example-com
```

## Result

- status: `http_fetch_completed`
- invocation_allowed: `true`
- network_call_performed: `true`
- request_ref: `http-fetch-request:dogfood-web-evidence-example-com`
- safe_url_ref: `http-fetch-url:example-com/root`
- host_ref: `http-fetch-host:example-com`
- status_code: `200`
- content_type: `text/html`
- transport_ref: `http-fetch-transport:web-access-gateway-real-world-v1`
- web_access_request_ref: `web-access-request:857150c1d2bd40d3a2e96db0b5c1d3d9`
- web_access_audit_ref: `web-access-audit:857150c1d2bd40d3a2e96db0b5c1d3d9`
- redaction_count: `0`
- sensitive_values_returned: `false`

## Boundaries Verified

- HTTPS GET only.
- Explicit host allowlist was required.
- Raw URL was accepted as operator input but not echoed in the CLI output.
- Raw headers were not returned or stored.
- Raw response body was not returned or stored.
- No browser automation was performed.
- No provider SDK call was performed.
- No connector write was performed.
- No memory write was performed.
- No context injection was performed.
- No action execution was performed.
- No production authority was granted.

The fetched preview text is intentionally omitted from this evidence note. The
CLI output contained a bounded redacted preview for operator inspection only.
