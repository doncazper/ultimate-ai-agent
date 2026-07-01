# Codex Prompts — WebAccessGateway

Use these prompts to keep Codex aligned with the boundary. They are intentionally strict.

## Prompt 1 — Review before editing

```text
Review this WebAccessGateway boundary PR. Do not modify files yet.

Goal:
Create one central, policy-controlled WebAccessGateway for agent-facing public web access. The repo already has governed web evidence, tool runtime HTTP fetch, browser observe, browser dry-run, low-risk click, and capability policy pieces. The missing piece is a central boundary future agents/tools cannot route around.

Future provider and dangerous-authority sequencing is governed by `docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md`. Preserve its core rule: add providers earlier, add dangerous authority much later.

Non-negotiable rule:
Agent-facing public web access must go through ultimate_ai_agent.core.web_access.

Do not weaken this by allowing direct requests/httpx/urllib.request/urllib3/http.client/Playwright/Selenium/Firecrawl/Browserbase calls from agent/tool/API logic outside approved adapters or explicit temporary exceptions.

First-slice scope:
- WebAccess contracts.
- Deny-by-default policy.
- Normalized audit records.
- Source metadata with content_untrusted=true.
- Wrapper around existing governed web evidence.
- Static guard tests against new direct public-web/browser imports.
- Docs, PR sequence, Definition of Done, review checklist, and AGENTS.md guidance.

Do not add providers, browser execution, browser clicks, form filling, auth, cookies, downloads/uploads, POST/PUT/PATCH/DELETE, or new external dependencies.

Before editing, report exact file list, wrapped functions, static-guard exceptions, naming/signature conflicts, and confirmation that no browser execution/provider behavior is enabled.
```

## Prompt 2 — Security review

```text
Review the WebAccessGateway boundary PR as a hostile security reviewer. Do not modify files.

Return findings as P0/P1/P2/P3.

Check:
1. Can any agent/tool/API path perform public web access without WebAccessGateway?
2. Are direct HTTP/browser static guards enforceable?
3. Are local-model/model-acquisition exceptions narrow and documented?
4. Does every gateway result, including denied results, include WebAccessAuditRecord?
5. Are source contents always marked untrusted?
6. Can fetched web content become tool/agent instructions?
7. Are private/local networks, cookies, auth, request bodies, downloads, uploads, and non-GET methods denied?
8. Did this PR accidentally enable browser observe, browser dry-run execution, browser click, form fill, auth, or downloads?
9. Does this keep M94 low-risk clicks future/blocked?
10. Does AGENTS.md create any loopholes?
11. Does any provider/browser proposal follow `WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md` without blending provider integration into execution authority?
12. What is the smallest safe follow-up PR?

Do not recommend weakening the gateway boundary to make tests easier. Prefer narrower adapters, explicit temporary exceptions, or staged migration.
```

## Prompt 3 — Follow-up PR 2 planning

```text
Plan PR 2 only: WebAccess API/Manifest Wording Integration.

Do not implement browser behavior or add providers.
Do not add or change API routes.

Goals:
- Update manifest wording to distinguish unrestricted web fetching from governed web access.
- Preserve side-effect classification as governed/read-only.
- Keep this as wording/contract alignment only.
- Keep status/preview routes as future work, not PR 2.

Return file list, manifest wording changes, tests, non-goals, and security concerns.
```

## Prompt 4 — Provider authority review

```text
Review `docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md` before any provider, browser, search, scrape, or web-authority implementation.

Do not water it down.

Preserve the core recommendation:
Add providers earlier. Add dangerous authority much later.

Return P0/P1/P2/P3 findings if an implementation blurs disabled/read-only provider integration with browser clicks, form filling, auth/cookies, downloads/uploads, POST-style mutations, or any other execution authority.
```
