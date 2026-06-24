# WebAccessGateway Definition of Done

PR 1 is complete only when every item below is true.

## Boundary

- [ ] `ultimate_ai_agent.core.web_access` package exists.
- [ ] `WebAccessGateway` is the documented central boundary for agent-facing public web access.
- [ ] Contracts exist for request, result, policy decision, audit record, source metadata, authority mode, adapter kind, risk class, request kind, and network lane.
- [ ] The gateway evaluates policy before invoking any adapter.
- [ ] Denied requests do not call adapters.

## Policy

- [ ] Policy is deny-by-default.
- [ ] Phase 1 allows only governed web evidence and/or explicitly enabled read-only HTTPS GET.
- [ ] Non-GET methods are denied.
- [ ] Browser observe is not enabled.
- [ ] Browser dry-run is not enabled.
- [ ] Browser click execution is not enabled.
- [ ] Form fill, auth, cookies, downloads, uploads, and request bodies are denied.
- [ ] Private/local network access is denied for agent public-web lane.
- [ ] Non-gateway lanes are explicitly classified or denied.

## Audit

- [ ] Every allowed request returns `WebAccessAuditRecord`.
- [ ] Every denied request returns `WebAccessAuditRecord`.
- [ ] Audit includes request ID, timestamp, request kind, URL/ref, adapter kind, network lane, authority mode, risk class, policy status, reasons, and source metadata where available.
- [ ] Audit stores bounded/redacted previews only.
- [ ] Audit does not store secrets or unbounded raw page content.

## Source metadata

- [ ] Source metadata includes URL/final URL/host where available.
- [ ] Source metadata marks content as untrusted.
- [ ] Results mark content as untrusted.
- [ ] Fetched content is never treated as instructions.

## Static guardrails

- [ ] Static tests fail on new direct public-web/browser imports outside approved adapters or explicit temporary exceptions.
- [ ] Temporary exceptions are documented and narrow.
- [ ] Existing local-model loopback/model acquisition paths are temporary exceptions, not agent web-browsing authority.
- [ ] M94 low-risk click module remains future/blocked and is not activated.

## Documentation

- [ ] `WEB_ACCESS_GATEWAY.md` explains the boundary, lanes, authority ladder, non-goals, and future milestones.
- [ ] `WEB_ACCESS_GATEWAY_PR_SEQUENCE.md` documents PR 1-5 and later scoped execution.
- [ ] `WEB_ACCESS_GATEWAY_CODEX_PROMPTS.md` includes implementation and review prompts.
- [ ] Root `AGENTS.md` contains WebAccessGateway guidance.
- [ ] Manifest wording is identified as follow-up if not changed in this PR.

## Tests

- [ ] Policy denies POST before adapter call.
- [ ] Policy denies browser click before adapter call.
- [ ] Policy denies private/local network fetches.
- [ ] Policy denies cookies/auth/body/download/upload metadata.
- [ ] Allowed read-only path emits audit and source metadata.
- [ ] Static guard test runs and has explicit baseline exceptions.

## Explicit non-goals confirmed

- [ ] No Firecrawl integration.
- [ ] No Browserbase integration.
- [ ] No new Playwright execution.
- [ ] No browser clicks.
- [ ] No form filling.
- [ ] No downloads/uploads.
- [ ] No auth/cookies.
- [ ] No POST/PUT/PATCH/DELETE.
- [ ] No new broad network provider.
- [ ] No global autonomy toggle.

## Merge blockers

Do not merge if any of these are true:

```text
- Any agent/tool/API path can perform public-web access without WebAccessGateway.
- Browser observe/action/click behavior was accidentally enabled.
- Existing local-model direct HTTP exceptions were made broader.
- Static guardrails were weakened to make tests pass.
- Fetched web content can become tool instructions.
- Audit records are optional.
- The PR adds provider dependencies before the boundary is stable.
```
