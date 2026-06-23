# Local Backend Connection

Status: Active under v0.104.0 plus UAA-P1-082 loopback CORS hardening.
Local backend connection behavior remains local-only; UAA-P1-082 adds an
explicit server-side CORS allowlist for local Control Center dev/preview
origins only.

The Web Control Center may connect only to the local backend API boundary. The connection layer is frontend-only and does not add backend routes or backend authority.

Default local development uses the relative API base. `apps/control-center/vite.config.ts` proxies `/control-center/*` and `/runtime/*` to `http://127.0.0.1:8000` for the Vite dev server only, with origin rewriting disabled. This avoids browser CORS issues without adding backend API paths or external hosts.

The backend CORS allowlist is intentionally narrower than the frontend API base
URL parser. It allows only these local Control Center browser origins:
`http://localhost:5173`, `http://127.0.0.1:5173`, `http://[::1]:5173`,
`http://localhost:4173`, `http://127.0.0.1:4173`, and
`http://[::1]:4173`. Wildcard CORS, CORS credentials, external hosts, LAN
hosts, `0.0.0.0`, wrong local ports, and `null` origins remain denied. CORS is
browser hardening, not authentication or route authority.

Allowed API base URL forms:

- relative path, including the default empty base.
- `localhost`.
- `127.0.0.1`.
- loopback IPv6 `::1` when represented safely by the browser URL parser.

Blocked API base URL forms:

- external absolute API URLs.
- protocol-relative external URLs.
- public IPs.
- private LAN IPs.
- non-loopback hostnames.
- API bases with credentials.
- API bases containing secret-like query strings, tokens, API keys, passwords, cookies, authorization markers, credential markers, generic key markers, private-key markers, or similar sensitive values.

Connection states:

- `unknown`: reserved for explicitly unknown connection state summaries.
- `checking`: local backend connection checks are pending.
- `online`: all read-only local backend summary requests succeeded.
- `degraded`: at least one local backend summary succeeded, but one or more panels use non-authoritative mock fallback data.
- `mock_fallback`: no local backend summary was available, or the API base URL policy rejected the configured base.
- `offline`: reserved for offline-safe display states; it must not imply production authority.

Safety requirements:

- mock fallback must be visibly mock and non-authoritative.
- partial mock fallback must be called out as degraded.
- errors must be sanitized before display.
- frontend requests must not add Authorization headers, cookies, API keys, credential APIs, analytics, SaaS SDKs, or external API hosts.
- frontend POST targets remain bounded to `/control-center/actions/preview` and
  the disabled-by-default local chat shell endpoint `/v1/chat/completions`.
  Neither target adds frontend auth headers, cookies, credentials, analytics,
  SaaS SDKs, external hosts, connector writes, or provider/model authority.
- M14 adds no backend API path.
- the Vite dev proxy, when used, must stay pinned to `http://127.0.0.1:8000`.
- Vite proxy configuration and env examples must not include external targets, URL credentials, or secret-like API base strings.

M14 is not M15, M16, or M17. v0.19.0 implements M15 as frontend-only Approval Queue + Receipt/Event Viewer UI while preserving the M14 local backend connection boundary. v0.19.1 hardens M15 UI safety without changing local backend connection behavior. v0.21.0 implements M17 as frontend-only evidence/file/memory summary viewers and adds no backend connection power.

Design governance references for connection-state UI:

- `docs/design/OPEN_DESIGN_SYSTEM.md`
- `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`
- `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`
- `docs/design/ACCESSIBILITY_BASELINE.md`
- `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`
- `docs/design/COMPONENT_TAXONOMY.md`
- `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`
