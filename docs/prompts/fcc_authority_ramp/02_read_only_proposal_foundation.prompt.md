# FCC-AUTH-RAMP-001a First Implementation: Read-Only Real-World Web Fetch

Role: You are a Principal Software Engineer implementing the first Authority
Graduation Program lane:
`read_only_real_world_web_fetch` through `WebAccessGateway`.

Mode: implementation only for this exact read-only lane. If prerequisites are
missing, produce a blocked/no-go hardening patch instead of adding authority.

Read first:
- `AGENTS.md`
- `docs/prompts/fcc_authority_ramp/01_fcc_auth_ramp_charter.prompt.md`
- `docs/network/WEB_ACCESS_GATEWAY.md`
- `docs/network/WEB_RUNTIME_AUTHORITY_HARDENING.md`
- `docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md`
- `docs/network/M72_TO_M73_BOUNDARY.md`
- `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`
- `docs/kanban/founder_command_center_board.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `ultimate_ai_agent.core.web_access`
- `ultimate_ai_agent.core.tools.runtime.http_fetch`
- existing Python core/API/CLI contracts for WebAccessGateway, read-only fetch,
  source metadata, audit, redaction, route side-effect metadata, and product
  language

Goal:
Graduate only this first implementation lane:

```text
read_only_real_world_web_fetch
```

The lane must route through `WebAccessGateway`, not around it.

Authority boundary:
Allowed behavior is limited to HTTPS GET against an explicit public allowlist,
through `WebAccessGateway`, returning bounded redacted previews and safe refs.

This task must not add connector reads/writes, account auth, source polling,
send/archive/delete, shell/subprocess execution, provider/model calls, browser
observe, browser action dry-run, clicks/forms, cookies/auth sessions,
downloads/uploads, POST/PUT/PATCH/DELETE, memory writes, context injection,
generic execution, or production authority.

Implementation requirements:
1. Reuse existing `WebAccessGateway` contracts and policy before adding any new
   abstraction.
2. If real-world transport is introduced, place it behind an approved
   WebAccessGateway adapter/transport. Do not add direct `requests`, `httpx`,
   `urllib`, Playwright, Selenium, Firecrawl, Browserbase, browser-provider,
   search-provider, or scrape-provider calls outside the approved adapter
   boundary.
3. Require explicit operator-provided allowlist/scope refs; no wildcard hosts,
   no private/local hosts, no credential-bearing URLs, no query strings, and no
   redirects unless a later verifier-backed scope explicitly allows them.
4. Return only safe URL refs, host refs, status/content-type refs, bounded
   redacted preview, redaction summary, audit refs, and blocked authority refs.
5. Store no raw response body, raw headers, raw URL, raw local path, raw logs,
   prompt/response content, provider payload, username, hostname, environment,
   credential, or secret-like values.
6. Add CLI/repo-local inspection over the same Python core read model or result
   path.
7. Add API/OpenAPI route metadata only if a route is necessary; keep operation
   IDs stable and side-effect classification honest.
8. Do not add Control Center controls unless the backend/core result says the
   exact read-only fetch is eligible and every disallowed capability is labeled
   blocked.
9. Preserve blocked labels for every disallowed authority class.
10. If any prerequisite is missing, update blockers and verifier coverage
   instead of selecting another lane.

Tests to add or update:
- WebAccessGateway/read-only fetch tests proving HTTPS GET, allowlist,
  redaction-before-return, no raw body/header persistence, private/local network
  denial, and fail-closed missing transport behavior
- CLI tests for any new inspection/fetch command
- API/OpenAPI tests if any route is added
- frontend tests only if UI changes
- documentation/product-language checks when docs change

Required verification:
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_m72_read_only_http_fetch_tool.py tests/test_web_access_gateway.py tests/test_web_access_static_guards.py -q`
- `.venv/bin/python scripts/verify_web_runtime_authority.py`
- focused backend/API tests for changed routes or storage helpers
- focused frontend tests if Control Center surfaces change
- `make frontend-check` if frontend files changed
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py` if API contracts change
- `.venv/bin/python scripts/verify_operational_maturity.py`

Definition of done:
- `read_only_real_world_web_fetch` is either implemented through
  `WebAccessGateway` with verifier-backed safety, or explicitly blocked with
  smallest next safe action.
- No broader runtime authority is added.
- Tests/verifiers fail if future UI copy implies unsupported authority.
