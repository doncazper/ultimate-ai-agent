# Local Backend Connection

Status: Active for v0.18.0 / M14 Web Control Center Local Backend Connection Stabilization.

The Web Control Center may connect only to the local backend API boundary. The connection layer is frontend-only and does not add backend routes or backend authority.

Default local development uses the relative API base. `apps/control-center/vite.config.ts` proxies `/control-center/*` and `/runtime/*` to `http://127.0.0.1:8000` for the Vite dev server only, with origin rewriting disabled. This avoids browser CORS issues without adding backend API paths or external hosts.

Allowed API base URL forms:

- relative path, including the default empty base.
- `localhost`.
- `127.0.0.1`.
- loopback IPv6 `::1` when represented safely by the browser URL parser.

Blocked API base URL forms:

- external absolute API URLs.
- protocol-relative external URLs.
- API bases with credentials.
- API bases containing secret-like query strings, tokens, API keys, passwords, cookies, authorization markers, private-key markers, or similar sensitive values.

Connection states:

- `online`: all read-only local backend summary requests succeeded.
- `degraded`: at least one local backend summary succeeded, but one or more panels use non-authoritative mock fallback data.
- `mock_fallback`: no local backend summary was available, or the API base URL policy rejected the configured base.
- `offline`: reserved for offline-safe display states; it must not imply production authority.

Safety requirements:

- mock fallback must be visibly mock and non-authoritative.
- partial mock fallback must be called out as degraded.
- errors must be sanitized before display.
- frontend requests must not add Authorization headers, cookies, API keys, credential APIs, analytics, SaaS SDKs, or external API hosts.
- the only frontend POST target remains `/control-center/actions/preview`.
- OpenAPI path count remains `74`; M14 adds no backend API path.
- the Vite dev proxy, when used, must stay pinned to `http://127.0.0.1:8000`.

M14 is not M15. Approval Queue + Receipt/Event Viewer UI remains future work and must not be added by local backend connection stabilization.
