# WebAccessGateway Review Checklist

Use this checklist before merging any WebAccessGateway PR.

## Boundary

- [ ] Agent/tool/API code uses `ultimate_ai_agent.core.web_access` for public web access.
- [ ] Direct public-web client imports are limited to approved adapters or documented temporary exceptions.
- [ ] Browser-provider imports are limited to approved adapters or documented temporary exceptions.
- [ ] Temporary exceptions include a lane and future migration target.
- [ ] The exception list did not grow without review.

## Policy

- [ ] Deny-by-default remains intact.
- [ ] All non-GET methods are denied in phase 1.
- [ ] Private/local network access is denied for the public-web lane.
- [ ] Auth, cookies, session state, request bodies, downloads, and uploads are denied.
- [ ] Browser observe/action/click remain disabled unless a later milestone explicitly enables them.

## Audit and source metadata

- [ ] Allowed calls emit audit records.
- [ ] Denied calls emit audit records.
- [ ] Audit records include policy reasons, adapter kind, and network lane.
- [ ] Audit previews are bounded/redacted.
- [ ] Source metadata marks content as untrusted.

## Web content handling

- [ ] Fetched content is evidence/context only.
- [ ] Fetched content cannot become tool, shell, browser, connector, memory, or policy instructions.
- [ ] Raw DOM is not retained by default.
- [ ] Sensitive values are not logged.
- [ ] Redirects/final URLs are represented or denied if ambiguous.

## Browser checks

- [ ] No browser click execution.
- [ ] No form submission.
- [ ] No authenticated browser session.
- [ ] No file download/upload.
- [ ] No persistent browser session.
- [ ] No screenshot capture unless explicitly approved by later policy.
- [ ] Dry-run planning does not secretly create/control a browser session.

## Provider checks

- [ ] No Firecrawl, Browserbase, search, or scrape provider dependency is added in PR 1.
- [ ] Provider objects do not escape adapters.
- [ ] Provider-specific behavior is normalized into WebAccessResult.

## Stop conditions

Do not merge if direct public-web access can route around WebAccessGateway, browser execution was enabled accidentally, static guards were relaxed to hide violations, audit is optional, `content_untrusted` is missing, exceptions are vague/broad, or provider capability was added before the boundary is stable.
