# WebAccessGateway Boundary

Status: proposed boundary slice / M72.5  
Scope: contracts, policy, audit, source metadata, static guardrails, governed evidence wrapper  
Out of scope: new providers, browser execution, browser clicks, form filling, auth, cookies, downloads, uploads, non-GET methods

## Decision

Ultimate AI Agent should use one central, policy-controlled `WebAccessGateway` for agent-facing public web access.

```text
Agent / Tool / API Route
  -> WebAccessGateway
  -> WebAccessPolicy
  -> Audit + Source Metadata
  -> Adapters
```

The system remains API-first and browser-fallback, but browser capability is not a default execution path. Browser observe and browser dry-run are future-controlled modes; real browser actions are later scoped-authority work.

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

The core rule is: add providers earlier, add dangerous authority much later.
Firecrawl and Browserbase may appear as disabled/read-only adapters after this
gateway is stable. Browser clicks, form filling, auth/cookies,
downloads/uploads, and POST-style mutations must wait for mature autonomy,
audit, approval, revocation, sandbox, and connector/write layers.

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
- optional injected read-only HTTPS GET adapter in tests
- normalized WebAccessAuditRecord for allowed and denied paths
- SourceMetadata with content_untrusted=true
- quarantined WebAccessEvidenceBundle for adapter payloads
- static guard tests against new direct public-web/browser imports
```

Denied:

```text
- POST / PUT / PATCH / DELETE
- browser observe execution
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
```

## Network lanes

`WebAccessNetworkLane` prevents treating all network behavior as the same authority.

```text
AGENT_PUBLIC_WEB       agent-facing public web access; must use gateway
GOVERNED_WEB_EVIDENCE existing governed evidence path; wrapped first
LOCAL_MODEL_LOOPBACK  local model runtime calls; temporary exception
MODEL_ACQUISITION     Hugging Face/model acquisition; temporary exception
TOOL_RUNTIME_LEGACY   existing runtime fetch; migrate behind gateway later
```

Temporary exceptions are not permission to add more direct access. They should shrink over time.

## Adapter rules

Adapters must be invoked only after policy allows the request, normalize provider results into `WebAccessResult`, mark web content as untrusted, and avoid leaking provider objects or runtime authority to agent logic. Adapter payloads must be wrapped as quarantined `WebAccessEvidenceBundle` data, not exposed as tool, shell, browser, connector, memory, or policy instructions.

Adapters must not execute browser actions, hide redirects/source metadata, treat fetched web content as instructions, or introduce provider dependencies in this boundary PR.

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
PR 3: migrate existing read-only http_fetch behind gateway
PR 4: browser observe behind gateway, no cookies/clicks/raw DOM
PR 5: browser dry-run plans only, consuming observation bundles
Later: scoped execution only after approval, audit/replay, revocation, sandboxing, and red-team review
```

## Key constraint

Do not make the tool weaker by bypassing the gateway for convenience. The power comes from hybrid capability; the safety comes from one policy/audit boundary.
