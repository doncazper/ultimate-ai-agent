# WebAccess Provider and Authority Sequence

Status: future sequencing reference, not active implementation authority  
Branch context: `web-access-gateway-boundary` / PR #39  
Audience: Codex, maintainers, security review

The end-to-end SearXNG discovery plus self-hosted/Firecrawl Cloud extraction
child plan is `docs/network/SEARXNG_FIRECRAWL_HYBRID_IMPLEMENTATION_PLAN.md`.
It remains planning-only and subordinate to this provider/authority sequence
and the active `WEB-RUNTIME-AUTH-001` WIP lane.

## Primary recommendation

Add providers earlier. Add dangerous authority much later.

Firecrawl and Browserbase can appear as disabled/read-only adapters fairly soon after the `WebAccessGateway` boundary is stable. Browser clicks, form filling, auth/cookies, downloads/uploads, and POST-style mutations should wait until the autonomy, audit, approval, and connector/write layers are mature.

This preserves the hybrid-agent advantage without turning web access into a global autonomy switch.

## Core sequencing rule

```text
Capability exists
-> disabled by default
-> read-only or observe-only first
-> dry-run before real actions
-> limited allowlist
-> explicit approval
-> scoped autonomy window
-> audit/replay
-> revocation
-> broader authority only after hardening
```

No implementation should jump from `OFF` to broad browsing, login, form submission, downloads, uploads, or web mutations.

## Provider vs authority distinction

A provider is an integration mechanism. Authority is permission to perform side effects.

Examples:

```text
Firecrawl read-only scrape adapter: provider, low authority
Firecrawl interact/click/form use: provider plus browser/action authority
Browserbase observe-only session: provider, low authority
Browserbase full browser automation: provider plus browser/action/auth/form authority
Playwright observe-only adapter: local browser provider, low authority
Playwright click/form/download/upload: browser execution authority
```

The project should allow provider shells and disabled/read-only adapters earlier, while delaying side-effect authority until the policy, approval, audit, revocation, sandbox, connector, and write layers are ready.

## Capability table

| Capability | What it does | Add when | First safe mode | Keep blocked at first | Notes |
|---|---|---:|---|---|---|
| Firecrawl read-only search/scrape adapter | Searches the web and extracts page content as markdown, HTML, or structured JSON. | After PR 3, around M72.x / M74 prep | Disabled adapter shell, then read-only `search`, `scrape`, `extract_markdown`, `extract_json` through `WebAccessGateway` | Interact, clicks, forms, sessions, downloads, provider object escape | Good first provider because it strengthens read-only web evidence without browser authority. |
| Firecrawl Interact | Continues from a scraped page and can click, fill forms, extract dynamic content, or navigate deeper. | Dry-run only around M75; real use M94+ or later | Action-plan generation only | Live clicks, live forms, checkout, account actions | Treat as browser automation, not scraping. Do not bundle it with the read-only adapter. |
| Browserbase observe-only cloud browser adapter | Provides cloud browser sessions, page fetch, search, and observation capabilities. | M74, after browser observe contract | Observe URL/title/final URL/safe text/accessibility summary | Auth, cookies, clicks, screenshots by default, raw DOM retention | Hosted-browser fallback when normal fetch/scrape is insufficient. |
| Browserbase full browser automation | Uses cloud browsers for agent workflows, multi-step interactions, login-like flows, and form flows. | Dry-run around M75; real low-risk only M94+ | Plan-only adapter consuming an observation bundle | Logins, registrations, form submit, purchases, downloads, account actions | Add platform shell early only if the gateway keeps it disabled or observe-only. |
| Local browser execution / Playwright execution | Controls a real browser locally or in a sandbox, including click/fill/select/upload/download primitives. | M74 observe-only; M75 dry-run; M94 low-risk real clicks | Observe-only first | Any action execution before M94 | More powerful than HTTP fetch; must stay behind the gateway. |
| Browser observe | Renders or inspects a page and returns safe metadata/text. | M74 | Title, final URL, safe text summary, possibly accessibility summary | Clicks, forms, downloads, session state, raw DOM | This is browser capability without browser action authority. |
| Browser action dry-run | Produces a reviewable plan of browser actions without executing them. | M75 | Plan only, no browser control by the planner | Actual clicks/forms/auth/downloads | Dry-run should consume a prior observation bundle; it should not secretly open/control a browser session. |
| Browser clicks | Actually clicks buttons, links, menus, or other page elements. | M94 | Low-risk clicks only inside scoped session | Forms, purchases, downloads, auth, destructive actions | First real browser action tier; keep narrow and auditable. |
| Form filling without submit | Types into inputs, textareas, selects, or similar controls. | Dry-run M75; very narrow real use after M94; broader after connector/write layers | Fill-plan only, then approved low-risk fills | Personal data, credentials, payment data, signup/account mutation | Looks harmless but can leak data or prepare a mutation. |
| Form submission | Sends form data to a site and may create accounts, messages, purchases, settings changes, or other side effects. | M121-M130 for connector-specific writes; broader browser+connector workflows M131+ | Connector-specific write dry-run, then approved low-risk write execution | Generic public-web form submit | Treat as write authority, not browser convenience. |
| Auth / login | Uses credentials or authenticated browser state. | After identity/secrets foundations; practical execution M121-M130+ | Connector-scoped auth contracts and approval-bound sessions | Raw password handling, persistent shared cookies, generic site login | Credentials and sessions are bearer authority. |
| Cookies / session state | Reuses or injects browser state so the browser acts as an authenticated user. | After secrets boundary + identity model; M111-M130+ | Per-connector scoped, revocable, audited session | Global cookie jar, reused personal browser profile | Treat cookies as secrets. |
| Downloads | Saves files initiated by a page or provider. | After sandbox/file quarantine exists; likely M121+ or M131+ | Metadata-only first, quarantine-only second | Auto-open, arbitrary save path, executable files | Adds malware, disk-write, privacy, storage, and file-processing risk. |
| Uploads | Selects local files and sends them to a page. | After scoped file authority; likely M128+ / M131+ | Dry-run file-selection plan | Arbitrary local files, secrets, home directory access | Uploads can exfiltrate local data. |
| POST | Sends data to a server, commonly creating or processing a resource. | Authless only after M95 if truly non-mutating; real writes M127-M128+ | Dry-run request plan, then known API/connector only | Arbitrary public-web POST, cookies, credentials, account mutation | Treat most POST usage as mutation until proven otherwise. |
| PUT / PATCH | Updates or replaces server-side resources. | M127-M128+ for connector-specific writes only | Connector write dry-run, then approved low-risk execution | Generic public-web PUT/PATCH | Requires connector contracts, idempotency thinking, approval, and rollback posture. |
| DELETE | Deletes server-side resources. | Much later than M128; likely M131+ and only for reversible/approved domains | Dry-run for a long time | Irreversible deletes | Highest-risk write method; require strongest approval and audit. |

## Sequencing summary

| Phase | Add | Keep blocked |
|---|---|---|
| Current / PR #39 | WebAccessGateway boundary, policy, audit, static guards | Providers, browser execution, forms, auth, cookies, downloads/uploads, non-GET |
| PR 2 | API/manifest boundary posture wording only | Providers and browser behavior |
| Web Runtime Authority hardening | Canonical web runtime nouns, durable audit prerequisite, side-effect ledger blockers, approval linkage, blocked/degraded/partial labels, provider diagnostics, and metadata-only catalog/manifest visibility | Live providers, browser execution, POST/click/form/download/upload, and callable runtime authority |
| PR 3 | Existing read-only HTTP fetch migrated behind gateway | Browser execution, forms, auth, cookies, downloads/uploads, non-GET |
| M72.x-M74 | Browser observe adapter and browser action dry-run planner behind WebAccessGateway | Clicks, forms, auth, cookies, downloads, raw DOM retention, real execution |
| Phase 4 | Disabled provider adapter shells for Firecrawl, Browserbase, and search diagnostics | Provider SDK imports/calls, credentials, live search, scrape jobs, Browserbase sessions |
| Later provider read-only | Read-only provider adapters after explicit promotion | Firecrawl Interact, sessions, clicks/forms |
| M94 | First real low-risk browser clicks | Forms, purchases, downloads, auth, destructive actions |
| M95 | More authless network tools | Cookies, credentials, accounts, POST mutations |
| M111-M120 | Identity, secrets boundary, credential vault, production threat model | Broad credentialed execution |
| M121-M130 | Connector read-only, approval capture, connector write dry-run, low-risk connector writes | Generic public-web form/account automation |
| M131-M140 | Combined browser + connector workflows under scoped autonomy | Irreversible actions without strong approval/recovery |

## Recommended PR sequence

### PR 1 — Boundary

Already represented by PR #39.

```text
WebAccessGateway contracts
Deny-by-default policy
Normalized audit
Source metadata
Static guards
Governed evidence wrapper
No providers
No browser execution
```

### PR 2 — API and manifest wording

```text
Expose API/manifest wording only; do not add a status or preview endpoint.
Clarify /api/manifest posture:
- web_access_gateway_boundary: implemented
- unrestricted_web_fetching: not_available
- browser_execution: not_available
- providers: not_configured
- content_untrusted: true
No providers.
No browser behavior.
```

### Web Runtime Authority hardening

```text
Add canonical runtime nouns:
web_request, web_observation, web_evidence, web_approval, web_action_plan, web_audit_record.
Require durable safe-ref audit storage before provider or browser execution.
Require blocked side-effect ledger states before POST/click/form/download/upload.
Add approval linkage fields without treating approval refs as execution authority.
Expose blocked/degraded/partial operator labels.
Keep provider diagnostics diagnostic-only.
Keep catalog and manifest visibility metadata-only, not callable runtime.
Bind every promotion step to a named verification lane.
```

### PR 3 — Existing read-only fetch migration

```text
Route existing read-only HTTP fetch through WebAccessGateway.
Preserve behavior.
Shrink legacy tool-runtime fetch exceptions into a named read-only gateway lane if possible.
No Firecrawl yet unless the boundary and static guards are stable.
```

### Phase 4 — Disabled provider shells

```text
Add provider-neutral adapter shell contracts behind WebAccessGateway.
Cover Firecrawl, Browserbase, and search provider diagnostics only.
Keep shells disabled by default.
Return disabled/blocked diagnostics through WebAccessResult and WebAccessAuditRecord.
Mark content_untrusted=true.
Do not import provider SDKs.
Do not configure credentials.
Do not perform network calls.
Do not start scrape jobs.
Do not start Browserbase sessions.
Do not expose Interact.
Do not expose provider sessions.
Do not add clicks/forms.
```

### Later provider read-only — Firecrawl/search

```text
WEB-HYBRID-003 promotes only SearXNG bounded JSON search after its accepted
scoped activation. Every call requires exact policy, approval, lease,
availability, audit, and redaction gates.
WEB-HYBRID-004 separately promotes one self-hosted Firecrawl operation:
one-page, one-attempt, markdown-only extraction for an exact allowlisted public
HTTPS target. The target remains read-only GET semantics even though the fixed
loopback provider transport uses POST. Full markdown is transient and untrusted;
durable output contains safe refs, hashes, reason codes, and a bounded redacted
preview. At this phase, Firecrawl Cloud, search, crawl, map, schema extraction,
screenshots, Interact, sessions, and actions remain blocked.
WEB-HYBRID-005 then promotes cloud extraction independently of routing: one
authenticated free-plan standard scrape, `proxy=basic`, no provider cache,
one atomic reservation, exact request budget/approval/lease scope, and complete
before/after usage proof. This does not authorize automatic fallback, paid or
unknown plans, Keyless, enhanced/auto proxy escalation, or target-page auth.
WEB-HYBRID-006 promotes one automatic choice only: self-host first, followed by
at most one separately authorized cloud attempt for a fixed normalized
availability/render failure. Policy, authority, private-target, redirect,
scope, unknown, and incomplete-cost failures are terminal. Replay is
receipt-only, and an opened cloud circuit requires manual credit reconciliation.
Normalize into WebAccessResult and WebAccessAuditRecord.
Mark content_untrusted=true.
Keep Interact, sessions, clicks/forms, general credential surfaces, and writes blocked.
```

### Browser observe / Browserbase observe

```text
Browser observe is already routed behind WebAccessGateway.
Browserbase may be introduced later only as a disabled/observe-only provider.
Return safe title/final_url/text/accessibility summary.
No cookies.
No auth.
No click.
No raw DOM retention.
No screenshot by default.
```

### Browser action dry-run

```text
Browser action dry-run is already routed behind WebAccessGateway.
Convert an observation bundle into a reviewable action plan.
No browser control from the planner.
No clicks.
No form submission.
No auth.
No downloads/uploads.
No provider sessions escaping the adapter.
```

### Later — Low-risk browser clicks

```text
Only after scoped sessions, approval, audit/replay, revocation, and risk classification are stable.
Allow low-risk clicks only.
No forms, purchases, downloads, auth, destructive actions, or account mutations.
```

### Much later — forms, auth, downloads/uploads, POST/PUT/PATCH/DELETE

```text
Only after connector/write layers are mature.
Require identity/secrets boundary, approval capture, scoped sessions, audit, revocation, sandbox/file quarantine where relevant, and rollback/idempotency posture.
Prefer connector-specific writes over generic public-web mutations.
```

## Codex review prompt

```text
Review `docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md` and keep the architecture strict.

Do not water this down.

Primary recommendation:
Add providers earlier. Add dangerous authority much later.

Firecrawl and Browserbase can appear as disabled/read-only adapters fairly soon after the WebAccessGateway boundary is stable. Browser clicks, form filling, auth/cookies, downloads/uploads, and POST-style mutations must wait until the autonomy, audit, approval, and connector/write layers are mature.

Check that any implementation proposal preserves these rules:
1. Provider shell does not imply execution authority.
2. Firecrawl read-only is separate from Firecrawl Interact.
3. Browserbase observe-only is separate from full browser automation.
4. Browser action dry-run does not secretly open/control a browser session.
5. Cookies/auth/session state are treated as secrets/credential authority.
6. Downloads require sandbox/quarantine planning.
7. Uploads require scoped file authority.
8. POST/PUT/PATCH/DELETE are treated as write/mutation authority.
9. Generic public-web writes are later than connector-specific writes.
10. All web/provider outputs remain untrusted evidence, never instructions.
11. WebAccessGateway remains the single boundary.
12. Static guardrails are not weakened to add providers.

Return findings as P0/P1/P2/P3 and recommend the smallest safe next PR.
```

## Source notes

Official docs to re-check before implementation:

- Firecrawl documentation: Search, Scrape, Interact, Agent, Crawl, Map, and Browser Sandbox capabilities.
- Browserbase documentation: cloud browsers, web search, page fetch, sandbox runtime, browser sessions, and browser automation.
- Playwright documentation: actions, form input, authentication state, downloads, and uploads.
- MDN HTTP methods documentation: method semantics for GET, POST, PUT, PATCH, DELETE, safety, and idempotency.

This document is a sequencing reference. It does not grant runtime authority.
