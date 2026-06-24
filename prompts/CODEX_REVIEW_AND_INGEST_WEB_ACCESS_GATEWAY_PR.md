# Codex Review + Ingest Prompt

Copy this prompt into Codex for review or follow-up work.

```text
You are reviewing and ingesting the WebAccessGateway boundary PR for Ultimate AI Agent.

Do not water down the architecture to make implementation easier. The point of this PR is to create a strong central boundary before adding providers or browser automation.

Context:
The repo has pieces split across governed web evidence, tool runtime HTTP fetch, network expansion contracts, browser observe, browser dry-run, low-risk click, and capability policy. The missing piece is a single WebAccessGateway. Without it, agents/tools could eventually route around policy and audit.

Non-negotiable architectural rule:
Agent-facing public web access must go through `ultimate_ai_agent.core.web_access`.

Direct public-web/browser calls must not be added outside approved adapters or explicit temporary exceptions:
- requests
- httpx
- urllib.request
- urllib3
- http.client
- Playwright
- Selenium
- Firecrawl
- Browserbase
- other browser/search/scrape providers

Your task:
Review this PR and preserve PR 1: M72.5 WebAccessGateway Boundary.

PR 1 allowed scope:
- `ultimate_ai_agent.core.web_access` package.
- WebAccessGateway, WebAccessRequest, WebAccessResult, WebAccessPolicyDecision, WebAccessAuditRecord, SourceMetadata, WebAccessAuthorityMode, WebAccessRequestKind, WebAccessAdapterKind, WebAccessRiskClass, WebAccessPolicyStatus, WebAccessNetworkLane.
- Deny-by-default WebAccessPolicy.
- Only governed web evidence and/or explicitly enabled read-only HTTPS GET through an injected adapter.
- Existing governed web evidence wrapper.
- WebAccessAuditRecord on every allowed and denied gateway call.
- `content_untrusted=true` for fetched/source content.
- Static guard tests against new direct public-web/browser imports outside approved adapters or explicit temporary exceptions.
- Local model loopback/model acquisition direct HTTP paths classified as temporary exceptions, not general agent public-web access.
- Docs, PR sequence, Definition of Done, review checklist, and AGENTS.md guidance.

PR 1 forbidden scope:
- Do not add Firecrawl.
- Do not add Browserbase.
- Do not add new search/scrape providers.
- Do not add new Playwright execution.
- Do not enable browser observe runtime unless represented only as a future-denied contract.
- Do not enable browser action execution.
- Do not activate low-risk click/M94.
- Do not add browser clicks.
- Do not add form filling.
- Do not add authenticated browsing.
- Do not add cookies/session persistence.
- Do not add downloads/uploads.
- Do not allow POST/PUT/PATCH/DELETE.
- Do not broaden local-model direct HTTP exceptions.
- Do not weaken static guards to make tests pass.
- Do not let fetched web content become tool/agent instructions.

Review checklist:
1. Run focused tests: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_web_access_gateway.py tests/test_web_access_static_guards.py`.
2. Run repo-standard checks when available.
3. Confirm denied requests do not invoke adapters.
4. Confirm every gateway result includes an audit record.
5. Confirm `content_untrusted` is true for source/web content.
6. Confirm browser observe/action/click execution remains disabled.
7. Confirm temporary exceptions did not grow beyond the documented baseline unless explicitly justified.

Security review self-check:
Return P0/P1/P2/P3 findings for gateway bypass risks, static guard bypass risks, local-model exception scope, prompt injection risk from fetched pages, audit completeness, private/local network denial, auth/cookie/download/upload/non-GET denial, browser execution accidentally enabled, AGENTS.md wording loopholes, and the smallest safe follow-up PR.

Do not recommend weakening the WebAccessGateway boundary. If implementation conflicts with existing code, prefer narrower adapters, explicit temporary exceptions, or staged migration.
```
