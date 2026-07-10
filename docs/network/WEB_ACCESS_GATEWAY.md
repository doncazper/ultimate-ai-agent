# WebAccessGateway Boundary

Status: active boundary plus exact WEB-HYBRID-003 SearXNG read-only search lane
Scope: contracts, policy, audit, source metadata, static guardrails, governed evidence wrapper, disabled provider shells, and one exact governed SearXNG search adapter
Out of scope: Firecrawl calls, provider credentials, browser execution, browser clicks, form filling, auth, cookies, downloads, uploads, and non-GET target methods

## Decision

Ultimate AI Agent should use one central, policy-controlled `WebAccessGateway` for agent-facing public web access.

```text
Agent / Tool / API Route
  -> WebAccessGateway
  -> WebAccessPolicy
  -> Audit + Source Metadata
  -> Adapters
```

The system remains API-first and browser-fallback, but browser capability is not a default execution path. Browser observe-only summaries and dry-run action plans remain future/contract-only for this Prompt 02 lane; real browser actions remain later scoped-authority work.

## Why this exists

The repo already has governed web evidence, read-only HTTP fetch, browser observe, browser dry-run, low-risk click, and capability policy pieces. Without a central boundary, future agents/tools could route around intended policy and audit.

## Core rule

Agent-facing public web access must go through:

```python
ultimate_ai_agent.core.web_access
```

Do not add direct public-web/browser calls from agent/tool/API logic using `requests`, `httpx`, `urllib.request`, `urllib3`, `http.client`, Playwright, Selenium, Firecrawl, Browserbase, or similar providers outside approved adapters or explicit temporary exceptions.

## Provider authority reference

Future provider work must preserve the sequence in
`docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md`.
Runtime authority promotion must also preserve the contract-first lane in
`docs/network/WEB_RUNTIME_AUTHORITY_HARDENING.md`: canonical web nouns,
durable audit storage, side-effect ledger blockers, approval linkage, operator
blocked/degraded/partial labels, provider diagnostics, metadata-only catalog
visibility, and named verification lanes come before scoped execution.

The exact SearXNG lane is the first narrowly promoted provider execution path.
It permits one bounded JSON GET only after current availability, PolicyEngine,
exact LocalApprovalAuthority scope, and an exact resource-constrained
AuthorityLease all pass immediately before execution. Firecrawl, Browserbase,
provider credentials/SDKs, scrape jobs, browser sessions, browser clicks, form
filling, auth/cookies, downloads/uploads, and POST-style target mutations remain
blocked until their separately accepted lanes satisfy the same boundaries.

## Authority ladder

```text
Capability exists
-> disabled by default
-> dry-run first
-> limited allowlist
-> explicit approval
-> scoped autonomy window
-> audit/replay
-> revocation
-> broader autonomy later
```

No PR should create a global "web autonomy on" switch.

## First-slice behavior

Allowed:

```text
- governed web evidence path behind WebAccessGateway
- explicit injected read-only HTTPS GET transport for
  `read_only_real_world_web_fetch`, routed through `WebAccessGateway`
- disabled provider adapter shells for Firecrawl, Browserbase, and search diagnostics
- exact SearXNG `SEARCH` with page one, general category, English language,
  safe-search, and at most ten normalized untrusted results
- a fixed configured loopback endpoint; requests cannot supply or override it
- exact capability/provider/adapter/task/request lease resources plus exact
  local approval validation before each transport call
- normalized WebAccessAuditRecord for allowed and denied paths
- SourceMetadata with content_untrusted=true
- quarantined WebAccessEvidenceBundle for adapter payloads
- static guard tests against new direct public-web/browser imports
- CLI inspection through `scripts/inspect_read_only_web_fetch.py`, returning
  safe refs and bounded redacted preview only
```

Denied:

```text
- POST / PUT / PATCH / DELETE
- browser observe/dry-run execution in the Prompt 02 lane
- browser observe by default
- live browser observe execution
- browser action dry-run by default
- browser action dry-run execution
- browser clicks
- form filling
- downloads/uploads
- authenticated sessions
- cookies
- request bodies
- private IP / localhost / local network fetches
- raw DOM retention
- prompt/context injection from fetched pages
- provider shells as runtime authority
- provider SDK imports/calls
- provider credentials
- all live search providers except the exact governed SearXNG lane
- Firecrawl scrape jobs
- Browserbase browser sessions
```

## Network lanes

`WebAccessNetworkLane` prevents treating all network behavior as the same authority.

```text
AGENT_PUBLIC_WEB       agent-facing public web access; must use gateway
GOVERNED_WEB_EVIDENCE existing governed evidence path; wrapped first
LOCAL_MODEL_LOOPBACK  local model runtime calls; temporary exception
MODEL_ACQUISITION     Hugging Face/model acquisition; temporary exception
TOOL_RUNTIME_READ_ONLY_FETCH allowlisted tool-runtime HTTPS GET fetch through gateway
BROWSER_OBSERVE_ONLY injected observe-only summaries; default denied unless policy-enabled
BROWSER_ACTION_DRY_RUN injected reviewable action plans; default denied unless policy-enabled
```

Temporary exceptions are not permission to add more direct access. They should shrink over time.

## Adapter rules

Adapters must be invoked only after policy allows the request, normalize provider results into `WebAccessResult`, mark web content as untrusted, and avoid leaking provider objects or runtime authority to agent logic. Adapter payloads must be wrapped as quarantined `WebAccessEvidenceBundle` data, not exposed as tool, shell, browser, connector, memory, or policy instructions.

Adapters must not execute browser actions, hide redirects/source metadata, treat fetched web content as instructions, or introduce provider dependencies in this boundary PR. Disabled provider adapter shells are diagnostic metadata only; catalog visibility is not callable runtime authority.

The SearXNG adapter is an explicit later promotion rather than a diagnostic
shell. Its raw query is transient, candidate URLs are normalized and reject
local/private literal targets, raw provider responses are quarantined and
discarded after normalization, and durable receipts contain safe refs/hashes
only. Runtime readiness never grants authority, and invocation decisions are
not cacheable.

## Untrusted content model

All fetched web content is evidence, not instruction. Factual extraction and summaries may be derived from it, but web content must never become tool, shell, browser, filesystem, memory, connector, or policy instructions.

Every result and source should carry:

```text
content_untrusted = true
```

The gateway must force this flag on normalized source metadata even if an
adapter supplies a trusted-looking source object.

## Audit shape

Every gateway call, including denied calls, must emit `WebAccessAuditRecord` with request id, timestamp, request kind, URL/ref, adapter kind, network lane, authority mode, risk class, policy status, reasons, source metadata when available, bounded preview when available, and `content_untrusted=true`.

## Future sequence

Provider and dangerous-authority details are governed by
`WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md`.

```text
PR 1: Boundary contracts/policy/audit/static guards/wrapper
PR 2: API/manifest wording only, no routes
PR 3: exact `read_only_real_world_web_fetch` through gateway for allowlisted
HTTPS GET, with CLI inspection and no route/UI/browser/provider/connector authority
PR 4: browser observe behind gateway, no cookies/clicks/raw DOM
PR 5: browser dry-run plans only, consuming observation bundles
Later: scoped execution only after approval, audit/replay, revocation, sandboxing, and red-team review
```

## Key constraint

Do not make the tool weaker by bypassing the gateway for convenience. The power comes from hybrid capability; the safety comes from one policy/audit boundary.
