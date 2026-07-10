# SearXNG + Firecrawl Hybrid Web Extraction Implementation Plan

Status: active subordinate execution plan; runtime authority remains phase-gated

Parent lane: `WEB-RUNTIME-AUTH-001`

Execution prompt:
`docs/prompts/web_hybrid/00_execute_searxng_firecrawl_hybrid_end_to_end.prompt.md`

Scope: local SearXNG discovery, self-hosted Firecrawl extraction, bounded
Firecrawl Cloud fallback, quota accounting, Docker packaging, UAA gateway
integration, operator inspection, verification, rollout, and rollback

Current implementation posture: WEB-HYBRID-001 provider-neutral contracts and
WEB-HYBRID-002 pinned loopback packaging are implemented. WEB-HYBRID-003 adds
one exact SearXNG read-only search lane through `WebAccessGateway`, gated on
current availability, PolicyEngine, exact local approval, and an exact
resource-constrained AuthorityLease. WEB-HYBRID-004 adds one independent exact
self-hosted Firecrawl lane for a single approved, allowlisted public HTTPS page,
one attempt, and transient markdown-only evidence under the same request-scoped
gates. WEB-HYBRID-005 adds authenticated free-plan credit reconciliation,
atomic local reservations, and one independently governed Firecrawl Cloud
standard markdown attempt with exact approval, lease, budget, idempotency, and
post-call usage proof. WEB-HYBRID-006 promotes only self-host-first markdown routing
with one normalized eligible cloud fallback, receipt-only idempotent replay,
request-time authority/budget re-evaluation, and a manual-reconciliation cloud
circuit breaker. WEB-HYBRID-007 exposes the same backend-owned, safe-ref-only
posture through the existing capability-availability API, a readable CLI, and
the Control Center; these read surfaces perform no runtime probe and grant no
authority. WEB-HYBRID-008 completes bounded local/cloud dogfood, duplicate
dispatch and query-scope hardening, serialized cloud usage attribution,
private-target denial smoke proof, CLI traceback redaction, Foundation Gate,
and promotion review. `cloud_budget_first` remains absent.

Progress evidence is phase-committed. A completed contract or packaging phase
does not grant later provider execution authority.

## Decision Summary

Build one provider-neutral web research path owned by the Python Agent Core:

```text
Operator / CLI / Control Center / future governed MCP surface
  -> WebAccessGateway
  -> WebAccessPolicy + AuthorityLease + LocalApprovalAuthority
  -> SearXNG read-only discovery
  -> hybrid extraction router
       -> self-hosted Firecrawl for ordinary pages
       -> Firecrawl Cloud for exact eligible escalation while credits remain
  -> normalized untrusted evidence
  -> redacted audit, quota, receipt, and source refs
```

The recommended steady-state routing policy is
`self_host_first_cloud_escalation`. It preserves scarce managed credits for
JavaScript-heavy pages, provider transport failures, and difficult extraction
cases where the managed Fire-engine path adds value. `cloud_budget_first` was
not accepted for WEB-HYBRID-001 through WEB-HYBRID-008 and is absent from the
implemented routing-policy contract.

SearXNG is the default search/discovery provider. Firecrawl Cloud search is not
part of the first promotion because local SearXNG discovery avoids spending
Firecrawl credits on a capability already available locally. The first cloud
promotion is one-page, markdown-only scrape fallback.

This plan is subordinate to:

- `docs/network/WEB_ACCESS_GATEWAY.md`
- `docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md`
- `docs/network/WEB_RUNTIME_AUTHORITY_HARDENING.md`
- `docs/control_center/PROVIDER_BILLING_AUTHORITY_BOUNDARY.md`
- `docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md`

If those boundaries conflict with this plan, the stricter boundary wins.

## Why This Shape

SearXNG and Firecrawl solve different problems:

| Component | Primary responsibility | What it must not become |
|---|---|---|
| SearXNG | Search aggregation and candidate URL discovery | A direct agent-controlled network bypass |
| Self-hosted Firecrawl | Ordinary read-only page extraction, local Playwright rendering, bounded crawl/map later | A claim of cloud feature parity or unlimited extraction |
| Firecrawl Cloud | Managed read-only extraction escalation while an exact credit budget is available | A broad provider, browser, Interact, or spend authority toggle |
| `WebAccessGateway` | Target policy, authority, audit, source metadata, untrusted-content enforcement | A provider-selection UI shim |
| Hybrid router | Deterministic backend selection from policy, health, capability, and budget state | An autonomous fallback loop or authority mint |

Firecrawl's official self-hosting guide currently states that self-hosted
instances do not receive Fire-engine and require manual configuration beyond
basic fetch and Playwright. It documents optional SearXNG integration and
experimental Ollama support. Re-check the pinned upstream release before each
implementation PR:

- <https://github.com/firecrawl/firecrawl/blob/main/SELF_HOST.md>
- <https://docs.searxng.org/admin/installation-docker.html>
- <https://docs.searxng.org/dev/search_api.html>
- <https://docs.firecrawl.dev/api-reference/endpoint/credit-usage>
- <https://www.firecrawl.dev/pricing>

Provider pricing, endpoint support, credit costs, and self-host feature parity
are external facts. Store a reviewed versioned capability/cost snapshot; do not
silently fetch pricing or promote new endpoints at runtime.

Reviewed 2026-07-10 against the official pricing and v2 API references: the
free plan advertises 1,000 monthly plan credits and two concurrent requests;
standard scrape costs one credit per page. The promoted cloud request fixes
`proxy=basic` because `auto` may escalate to an enhanced five-credit attempt.
It also fixes `storeInCache=false`. Provider zero-data-retention was observed
as unavailable for the tested free-plan posture and is not claimed; UAA still
keeps markdown transient and persists no raw page/provider payload.

## Goals

1. Run SearXNG and the supported Firecrawl self-host dependencies locally in a
   reproducible, loopback-first Docker Compose stack.
2. Add one exact read-only SearXNG search lane through `WebAccessGateway`.
3. Add one exact self-hosted Firecrawl markdown extraction lane through the
   same gateway.
4. Add one exact Firecrawl Cloud markdown extraction fallback with a free-plan
   API key, authoritative remaining-credit reconciliation, and a local
   reservation ledger.
5. Route deterministically between local and cloud extraction without policy
   bypass, retry storms, double charging, or browser-action expansion.
6. Give CLI, API, and Control Center the same backend-owned provider, health,
   quota, routing, and receipt truth.
7. Preserve source metadata, content-untrusted posture, bounded previews,
   durable safe refs, redaction, idempotency, and exact rollback/safe-disable
   controls.
8. Keep a future MCP surface subordinate to UAA rather than connecting an agent
   directly to Firecrawl or SearXNG.

## Explicit Non-Goals

- No runtime change in this planning PR.
- No provider dependency, provider SDK, credential, or network call in this
  planning PR.
- No Firecrawl Keyless integration. The first cloud lane uses an authenticated
  free-plan account because its remaining-credit and billing-period endpoints
  can be reconciled.
- No automatic paid upgrade, credit pack, auto recharge, payment method,
  subscription management, or provider billing authority.
- No Firecrawl `/agent`, `/browser`, Interact, session, or remote browser
  execution.
- No clicks, forms, auth, cookies, downloads, uploads, screenshots by default,
  or persistent browser profiles.
- No generic public-web POST/PUT/PATCH/DELETE authority.
- No direct Firecrawl MCP registration that bypasses `WebAccessGateway`.
- No local Ollama extraction in the first runtime lane.
- No unrestricted proxy rotation or anti-bot bypass.
- No raw page, DOM, provider payload, prompt, response, credential, local path,
  environment, or log persistence.
- No automatic context injection or memory writes from extracted content.
- No background scheduler, recurring crawl, monitoring job, autonomous retry,
  or public/production authority.

## Current Repository Baseline

The plan must build on, not replace, the existing boundary:

| Existing element | Current state | Required treatment |
|---|---|---|
| `WebAccessRequestKind.SEARCH` | Contract exists; policy denied | Promote only in the exact SearXNG PR |
| `WebAccessRequestKind.EXTRACT_SCHEMA` | Contract exists; policy denied | Keep denied in the first extraction lane |
| `WebAccessAdapterKind.FIRECRAWL` | Contract exists | Split deployment identity in receipt metadata without leaking provider objects |
| Firecrawl provider shell | Disabled and diagnostic-only | Preserve until the exact adapter promotion PR |
| `WebAccessGateway` | Central policy/audit boundary | Remains the only agent-facing web entrypoint |
| Read-only HTTPS target policy | Implemented | Preserve target `GET` semantics and SSRF protections |
| Web evidence preview | Exact allowlisted product slice | Reuse redaction and safe-ref patterns; do not broaden it implicitly |
| Provider billing boundary | Planning-only | Apply unknown/incomplete credit blocking; do not add spend authority |
| Context injection | Blocked | Keep extracted markdown transient and untrusted |

## Architecture

### Logical Request Flow

```text
1. Receive a search or extract request.
2. Validate exact AuthorityLease scope and LocalApprovalAuthority posture.
3. Validate target/query limits, domain policy, method, and network lane.
4. Produce an audit record even if the request is denied.
5. For search:
   a. Call the fixed SearXNG service endpoint.
   b. Normalize bounded candidate results.
   c. Mark every candidate untrusted.
6. For extraction:
   a. Evaluate configured routing policy.
   b. Evaluate local provider health/capability.
   c. Evaluate cloud quota freshness, reservation, and circuit state.
   d. Select exactly one first attempt.
   e. Allow at most one eligible fallback attempt.
7. Revalidate every final URL and redirect before content acceptance.
8. Normalize the result into WebAccessResult/WebAccessEvidenceBundle.
9. Return transient markdown or a bounded preview to the authorized caller.
10. Persist safe refs, hashes, decisions, usage, and redacted receipts only.
```

### Target Semantics Versus Provider Transport

Do not weaken the current `GET`-only public target rule merely because
Firecrawl's provider API uses a POST request to create a read-only scrape job.
Represent these as two distinct contracts:

| Dimension | Meaning |
|---|---|
| Target request | The public URL being read; HTTPS, read-only, no body, no auth/cookies, private-network denied |
| Provider transport | A fixed internal or cloud service endpoint with an exact operation schema, bounded request body, cost/credit classification, and no caller-controlled endpoint |

Add a provider-transport receipt/envelope rather than treating the Firecrawl
service URL as the public target URL. The provider endpoint must come from
trusted configuration, never from an agent request. Private/local denial must
continue to apply to target URLs and redirects.

Suggested contract additions:

- `WebAccessRequestKind.EXTRACT_MARKDOWN`
- `WebProviderDeploymentKind.SEARXNG_SELF_HOSTED`
- `WebProviderDeploymentKind.FIRECRAWL_SELF_HOSTED`
- `WebProviderDeploymentKind.FIRECRAWL_CLOUD`
- `WebProviderOperation.SEARCH`
- `WebProviderOperation.SCRAPE_MARKDOWN`
- `WebProviderTransportReceipt`
- `WebProviderCapabilityState`
- `WebProviderHealthState`
- `WebProviderCreditSnapshot`
- `WebProviderCreditReservation`
- `WebProviderRoutingDecision`

Names are provisional. The implementation PR must prefer the smallest schema
that preserves exact transport, provider, credit, and audit truth.

### Provider Capability State

Do not reduce capability state to a single `available` boolean. Each provider
operation must expose:

```text
supported_by_pinned_version
configured
healthy
authorized
safe_disabled
budget_available
```

An operation is callable only when all required dimensions allow it. Provider
catalog visibility remains metadata; it never grants callable authority.

### Routing Policies

Support exact backend-owned policies, not a global autonomy toggle:

| Policy | Behavior | Initial posture |
|---|---|---|
| `sealed` | No provider calls | Default before promotion and safe-disable fallback |
| `self_host_only` | SearXNG plus self-hosted Firecrawl only | Allowed after local lanes are proven |
| `self_host_first_cloud_escalation` | Local extraction first; one cloud attempt for eligible failures | Recommended steady state |
| `cloud_budget_first` | Cloud first while an exact credit reservation succeeds; local fallback after quota/provider failure | Not accepted and out of scope for WEB-HYBRID-001 through WEB-HYBRID-008 |

The Control Center may display the selected policy but cannot change it until
a separately scoped settings mutation defines exact approval, receipt,
idempotency, and rollback behavior. Initial configuration is operator-owned
and backend-read-only.

## Local Docker Packaging

### Placement

Use a sibling of the existing local runtime package:

```text
packaging/local-web-services/
  README.md
  compose.yaml
  compose.macos.yaml              # only if a platform override is required
  provider_lock.json              # pinned upstream refs/digests/checksums
  searxng/
    settings.yml
    limiter.toml
  firecrawl/
    README.md
  scripts/                        # bounded health/setup helpers if needed
```

Do not create a new root-level infrastructure tree. Do not merge this stack
into `packaging/local-runtime/compose.yaml` until both stacks work separately
and an explicit overlay design is reviewed.

### Services

The pinned upstream version determines the final service list. The expected
shape is:

| Service | Purpose | Exposure |
|---|---|---|
| `searxng` | Search API with JSON enabled | Loopback port for native UAA; internal DNS for containerized UAA |
| `searxng-valkey` | Limiter/bot-detection state where enabled | Internal only |
| `firecrawl-api` | Self-hosted extraction API | Loopback port for native UAA; internal DNS for containerized UAA |
| Firecrawl worker/queue services | Upstream job execution | Internal only |
| Firecrawl PostgreSQL | Required job/state storage for the pinned version | Internal only, strong local secret |
| Firecrawl Redis/RabbitMQ or pinned equivalents | Required queue/cache services | Internal only |
| Firecrawl Playwright service | JavaScript rendering and optional screenshot capability | Internal only |

Do not invent or preserve a stale service list. Capture the exact pinned
upstream Compose topology in `provider_lock.json` and the package README.

### Network and Port Rules

- Publish only the two adapter-facing APIs needed by a native host UAA process.
- Bind published ports to `127.0.0.1`, never `0.0.0.0`.
- Keep databases, queues, Playwright, and admin surfaces internal.
- If an admin/queue UI is needed for manual diagnostics, expose it only through
  an explicit loopback diagnostic profile with a generated secret.
- Use separate internal networks or service aliases where needed; do not use
  host networking.
- The UAA adapter accepts only configured service endpoints. It must reject an
  endpoint supplied by the caller.
- When UAA runs inside `packaging/local-runtime`, use Compose service DNS through
  a reviewed overlay; when UAA runs natively, use the loopback endpoint.

### SearXNG Configuration

First promotion configuration:

- Enable `json` in `search.formats`.
- Keep result count, page count, categories, and engines bounded.
- Use a generated SearXNG secret.
- Configure timeouts and engine suspension behavior.
- Enable the limiter only with a healthy Valkey configuration and correct
  proxy/header posture.
- Keep the instance private; do not list or expose it as a public SearXNG
  instance.
- Do not enable authenticated search engines or send UAA credentials upstream.
- Record engine/category configuration as reviewed metadata without raw local
  paths or secrets.

### Firecrawl Self-Host Configuration

First promotion configuration:

- Pin an upstream tag/commit and image digest where available.
- Configure `SEARXNG_ENDPOINT` to the internal SearXNG service.
- Keep database authentication bypass acceptable only because the API remains
  loopback/internal; do not expose that posture remotely.
- Generate strong PostgreSQL and Bull/admin secrets.
- Keep PostgreSQL and queue ports internal.
- Set bounded CPU and RAM thresholds.
- Keep proxy variables unset by default.
- Keep local webhooks disabled.
- Keep Ollama/OpenAI-compatible extraction variables unset.
- Start Playwright only for the exact local extraction capability.
- Do not enable persistent browser profiles, cookies, auth sessions, or
  interactive browser endpoints.
- Bound job concurrency and queue depth independently from cloud concurrency.

### Secrets

- Extend the existing ignored `.uaa/` local-state convention or use Compose
  secrets; never commit the Firecrawl key, database password, admin key, or
  SearXNG secret.
- Prefer file-based secret injection to plaintext Compose environment values.
- Resolve the cloud Firecrawl key only inside the exact cloud adapter.
- UI, CLI, API, audit, and health surfaces expose a credential safe ref and
  readiness state, never the secret or a reversible preview.
- Keyless mode remains unsupported because it cannot supply the same
  authenticated credit reconciliation contract.

### Upgrades and License Review

- Record Firecrawl's AGPL-3.0 posture and SearXNG's license in the package
  review. Confirm obligations before distributing a modified network service.
- Review upstream release notes and Compose changes before each update.
- Rebuild the capability matrix after an update; do not assume `/agent`,
  `/browser`, Interact, or other cloud features became locally supported.
- Run an isolated migration rehearsal before updating persistent volumes.
- Preserve a rollback ref to the last proven provider lock and compatible
  volume schema.

## Search Lane Contract

### Initial Scope

Promote only:

```text
provider: searxng_self_hosted
operation: search
method: GET against fixed local service
output: bounded JSON result normalization
categories: reviewed allowlist
page: 1
results: bounded
auth/cookies/body/download/upload: denied
```

The query is transient input. Durable records store a query hash/safe ref,
request ref, result count, provider/engine summary refs, policy decision,
latency, and audit/receipt refs. Do not persist raw search queries in durable
logs, tests, fixtures, docs, or evidence.

Every returned candidate URL is untrusted. Before extraction, validate the URL
again through target policy, including DNS/private-range and redirect checks.

### Normalized Result

Each result should expose only the fields required by downstream review:

- rank
- transient URL and final URL where available
- title
- bounded snippet
- engine/source labels
- published/freshness metadata where supported
- source safe ref and content hash where available
- `content_untrusted=true`

Provider-specific objects must not escape the adapter.

## Self-Hosted Extraction Lane

### Initial Scope

Promote only:

```text
provider: firecrawl_self_hosted
operation: scrape_markdown
target: one allowlisted public HTTPS URL
target semantics: read-only GET
formats: markdown plus bounded metadata
page count: 1
attempts: 1
auth/cookies/interact/download/upload: denied
```

Do not start with crawl, map, screenshots, JSON/LLM extraction, or Firecrawl
search. Add each later as an exact operation only after the single-page lane is
stable.

### Output and Retention

- Treat markdown as untrusted provider output.
- Return it transiently only to the exact authorized caller.
- Persist a content hash, source refs, final URL/host metadata, bounded redacted
  preview, extraction status, provider/deployment ref, policy decision ref,
  and audit/receipt refs.
- UAA-owned stores do not persist full markdown, raw HTML, raw DOM,
  screenshots, or raw provider payloads. The pinned self-hosted provider uses
  a persistent PostgreSQL volume; provider-internal page retention is not yet
  proven absent and remains a deployment/cleanup risk rather than a UAA
  zero-retention claim.
- Do not inject the markdown into prompts, memory, tools, shell, browser,
  connector, filesystem, or policy channels.
- If durable corpus/RAG storage is later needed, define a separate quarantined
  artifact, retention, deletion, access, and context-injection milestone.

## Firecrawl Cloud Credit Lane

### Initial Scope

Promote only standard, one-page, markdown-only scrape. Advanced extraction,
Stealth/Enhanced modes, search, crawl, map, browser, Interact, screenshots, and
AI formats remain blocked until a later versioned cost/capability review.

The free-plan lane must hard-block any request that could incur paid usage or
has unknown credit cost. It must never auto-upgrade, recharge, or retry into a
paid plan.

### Authoritative Credit Snapshot

Credit reconciliation is one exact authenticated, read-only provider-account
diagnostic against a fixed endpoint. It returns only normalized credit fields
and a safe reconciliation receipt ref; it is not public-target web access,
execution authority, budget authority, or a general provider API exception.
Credential absence, unknown plan/cost, stale balance, and incomplete receipts
fail closed.

Use the authenticated Firecrawl credit-usage endpoint to normalize:

- plan credits
- remaining credits
- billing period start
- billing period end
- fetched-at timestamp
- provider account/team safe ref
- credential safe ref
- response receipt/hash ref
- freshness status

Raw account payloads and keys are never persisted.

### Local Reservation Ledger

The provider snapshot is authoritative for account balance. The local ledger
coordinates in-flight requests and provides UAA-owned audit truth.

Each reservation records:

- request and idempotency refs
- exact operation and provider deployment ref
- versioned cost-policy ref
- estimated credits
- reserved credits
- in-flight state
- actual provider usage ref when available
- reconciliation state
- billing-period ref
- routing decision ref
- attempt number and fallback relation
- receipt completeness
- safe-disable/revocation state

No row stores a raw query, page body, provider payload, credential, or local
path.

### Reservation Algorithm

```text
1. Load the latest credit snapshot.
2. If missing, stale beyond the accepted window, or from a prior billing
   period, synchronously reconcile before a cloud call.
3. Resolve the exact static cost policy for the requested operation.
4. If cost is unknown, block with unknown_cost_blocked.
5. In one local transaction/lock, calculate:
     spendable = remaining - in_flight_reservations - safety_reserve
6. If spendable < estimated cost, route local or return quota-blocked.
7. Create a reservation before dispatch.
8. Respect the plan concurrency ceiling independently from credit balance.
9. Dispatch one cloud attempt.
10. Complete or release the reservation and record receipt completeness.
11. Reconcile immediately after quota/rate errors and near the reserve floor.
12. Block further cloud use if actual usage/cost is incomplete or inconsistent.
```

Use a conservative configurable safety reserve during private dogfood. Do not
claim all advertised credits are safely spendable while requests are in flight.

### Billing-Period Refresh

Do not use a calendar-month cron or assume a local timezone reset. Re-enable
cloud routing only after a user-triggered status check or request confirms a
new provider billing period and a valid positive balance. This plan adds no
background scheduler.

### Cloud Circuit Breaker

Open the exact cloud circuit after a bounded threshold of provider transport,
rate-limit, or quota failures. Circuit state contains safe refs, reason codes,
opened-at/expiry, and a manual inspection path. It does not create a background
probe. A later user-triggered status/reconcile request may close the circuit
after health and quota are confirmed.

## Failover Policy

Allow at most one fallback attempt. Fallback eligibility is based on normalized
reason codes, not arbitrary exception text.

| First-attempt outcome | Cloud/local fallback allowed? | Reason |
|---|---:|---|
| Provider timeout, connection failure, or provider `5xx` | Yes | Provider availability failure |
| Cloud quota exhausted, reservation denied, or circuit open | Yes, to local | Budget/availability posture |
| Local Playwright/render failure or empty normalized content | Yes, to cloud if budgeted and authorized | Managed extraction may add value |
| Recognized bot challenge | Cloud escalation may be proposed if policy/terms allow | Fire-engine may add value; not automatic policy bypass |
| Target domain not allowlisted | No | Policy denial is terminal |
| Private/local target or redirect | No | SSRF boundary is terminal |
| Robots/terms policy denied | No | Provider switching cannot evade policy |
| Auth, cookies, session, click, form, download, or upload required | No | Authority not granted |
| Target `4xx` or unsupported content type | No by default | Avoid bypass/retry loops; exact exceptions require review |
| Content/page/byte/timeout ceiling exceeded | No | Request scope exhausted |
| Unknown or incomplete cloud credit/cost receipt | No further cloud use | Billing boundary stop condition |

Retries and fallback attempts must not reuse authority, budget, or receipt refs
outside their exact parent request. A replayed idempotency key must not trigger
another cloud charge.

## Authority and Approval Model

### Initial Private Dogfood

Require an active, exact AuthorityLease plus LocalApprovalAuthority validation
for each promoted operation. Suggested scope fields:

- capability ref: `web/search/read` or `web/extract/read`
- provider/deployment refs
- allowed domain set
- operation set
- max result/page count
- max attempts
- max cloud credits
- expiry
- idempotency ref
- revocation and safe-disable refs
- expected receipt refs
- blocked follow-on authorities

The cloud fallback attempt must be covered explicitly. A local extraction
approval does not silently authorize cloud credit use.

### Later Bounded Session Promotion

Only after private dogfood evidence may a separate milestone consider a
bounded read-only session window. It must define a credit ceiling, request and
attempt ceilings, domain allowlist, expiry, revocation, kill switch, receipt
completeness, and operator inspection. It is not background or autonomous
authority.

## API, CLI, and Control Center Parity

Core and CLI ship before new Control Center mutation surfaces.

### CLI

Proposed repo-local entrypoint:

```text
scripts/dev/uaa_web.py provider-status
scripts/dev/uaa_web.py reconcile-cloud-credits
scripts/dev/uaa_web.py search
scripts/dev/uaa_web.py extract
scripts/dev/uaa_web.py inspect-receipt
```

The final names must follow existing CLI conventions. Search/extract accept
raw operator input transiently but emit bounded results and durable safe refs.
Inspection output must not expose secrets, raw provider payloads, raw page
content, raw queries, or local paths.

### API

Do not add routes until the core/CLI lanes and route classification are proven.
Possible later routes:

- `GET /control-center/web-providers/status`
- `POST /control-center/web/search`
- `POST /control-center/web/extract`
- `GET /control-center/web/receipts/{receipt_ref}`

Before adding them:

- assign stable unique operation IDs
- update OpenAPI and `/api/manifest`
- classify provider calls as protected, expensive governed external reads with
  quota/cost side effects
- require local auth, exact AuthorityLease scope, rate limits, and idempotency
  where appropriate
- update the route inventory and side-effect documentation
- preserve bounded response schemas and redacted errors

### Control Center

The first UI is a backend-owned read model, not raw JSON and not a control that
mints authority. It should show:

- SearXNG configured/healthy/safe-disabled state
- self-hosted Firecrawl configured/healthy/capability state
- Firecrawl Cloud credential readiness without secret display
- remaining/plan credits and billing-period end from the latest valid snapshot
- in-flight reserved credits
- routing policy and cloud circuit state
- last routing/fallback/receipt safe refs
- exact blocked reasons and next safe action

Any later routing-policy or credential mutation requires a separate exact
settings/secret workflow with approval, receipt, idempotency, and rollback.

## MCP Posture

Do not point an agent directly at Firecrawl's MCP server or a raw SearXNG MCP
wrapper. That would bypass UAA policy, quota, audit, redaction, and source
normalization.

After the API/CLI lane is stable, a separate optional containerized MCP surface
may expose only UAA-owned tools such as:

```text
uaa_web_search_read_only
uaa_web_extract_markdown_read_only
uaa_web_provider_status
```

Those tools must call the UAA Python boundary, preserve the same AuthorityLease
and LocalApprovalAuthority validation, and return the same normalized result
and receipt refs. Plugin/MCP runtime import remains blocked until its own exact
promotion is accepted.

## Security and Abuse Controls

The implementation must prove:

- URL parsing, scheme enforcement, credential-in-URL rejection, DNS resolution,
  private/reserved range denial, redirect revalidation, and DNS-rebinding-safe
  transport posture
- exact domain allowlists and subdomain matching
- bounded redirects, connect/read/total timeout, response bytes, content types,
  result counts, pages, concurrency, attempts, and queue depth
- no caller-controlled provider endpoint or arbitrary headers
- no cookies, session reuse, auth headers to targets, downloads, uploads, forms,
  browser actions, or persistent profiles
- no direct `requests`, `httpx`, `urllib`, Playwright, SearXNG, or Firecrawl
  calls outside approved adapter/transport modules
- untrusted-content flags forced on all search/extraction outputs
- prompt-injection strings remain evidence data and cannot enter tool, shell,
  browser, connector, memory, filesystem, or policy instructions
- provider and target error messages normalized and redacted
- no raw provider/page/query/log/credential persistence
- exact safe-disable, revocation, and kill-switch behavior
- no fallback loop, retry amplification, or credit-drain race

## Observability and Evidence

Every allowed, denied, blocked, failed, and fallback attempt must emit a
normalized audit/receipt event with:

- request, session, actor, and idempotency safe refs
- operation and target/source refs
- adapter and deployment refs
- authority mode and lease/approval decision refs
- risk and policy status/reasons
- route decision and fallback relation
- provider health/circuit state refs
- credit snapshot/reservation/actual-usage refs where applicable
- latency and bounded size/count metadata
- final source metadata and content hash
- redacted preview where allowed
- `content_untrusted=true`
- rollback/safe-disable posture

Audit/replay is inspection-only. Replaying a receipt must never re-execute a
network/provider call.

## Evaluation Plan

### Deterministic Tests

Use injected transports and fixtures; CI must not require live public web or
provider credentials.

Required test groups:

1. SearXNG normalization, result limits, error mapping, and untrusted flags.
2. Self-hosted Firecrawl request schema, fixed endpoint, normalization, and
   raw-payload quarantine.
3. Cloud Firecrawl credential resolution, credit snapshot normalization,
   unknown/incomplete credit blocking, and secret omission.
4. Atomic reservation behavior with concurrent requests.
5. Billing-period rollover based on provider timestamps.
6. Cloud plan concurrency ceiling.
7. Exact routing behavior for all supported policies.
8. One-fallback maximum and normalized eligibility reasons.
9. No fallback after policy, robots/terms, auth, private-target, or scope denial.
10. SSRF, redirect, DNS, content-type, byte, timeout, and result/page limits.
11. Idempotent replay does not create a second provider call or reservation.
12. Safe-disable/revocation races block before dispatch.
13. Prompt injection and provider-object escape tests.
14. Durable receipt redaction and no raw local path/log/query/page/payload data.
15. API manifest, OpenAPI operation ID, route classification, auth, rate-limit,
    and idempotency tests when routes are added.
16. CLI/API/read-model parity and Control Center product-language tests.

### Local Stack Smoke Tests

After packaging is accepted, add opt-in local smoke commands that verify:

- Compose config validation
- generated secrets exist without printing them
- all required services become healthy
- SearXNG JSON search works through a fixed local fixture/query
- Firecrawl self-hosted markdown extraction works against an allowlisted public
  fixture or controlled local fixture approved by the transport design
- UAA reaches fixed provider endpoints without weakening public-target private
  network denial
- stack shutdown and restart preserve only intended state

### Cloud Private-Dogfood Tests

Never run these in default CI. With explicit local credentials and approval:

- reconcile the real free-plan credit snapshot
- execute one standard one-page markdown scrape
- verify one expected reservation and one complete redacted receipt
- simulate quota floor and circuit-open routing without draining the account
- confirm provider billing-period timestamps drive refresh posture
- compare local/cloud normalized shapes, not raw content in durable evidence

## PR and Task Sequence

Each PR must be independently reviewable and reversible. Do not combine
packaging, two provider adapters, quota authority, API/UI, and MCP in one PR.

### WEB-HYBRID-000 — Planning and Acceptance

Deliverables:

- this subordinate implementation plan
- the gated end-to-end execution prompt under `docs/prompts/web_hybrid/`
- cross-links from provider sequencing, active roadmap/board, canonical map,
  and documentation index
- accepted decisions for default routing policy, cloud authentication, content
  retention, and local package placement

Exit criteria:

- plan is indexed and docs integrity passes
- no runtime, route, dependency, provider, credential, or Compose behavior added

Rollback:

- revert documentation-only changes

### WEB-HYBRID-001 — Contracts, Ledger, and Router Simulation

Status: implemented and locally verified; providers remain policy-denied and
no network transport is present in this phase.

Scope:

- add provider deployment/operation, health, capability, credit snapshot,
  reservation, routing decision, and transport receipt contracts
- add an in-memory or injected repository for deterministic tests
- add proposal/simulation-only routing with no network transports
- keep all new providers disabled

Likely files:

- `src/ultimate_ai_agent/core/web_access/contracts.py`
- new focused modules under `src/ultimate_ai_agent/core/web_access/`
- focused contract and simulation tests
- verifier and docs updates

Exit criteria:

- all invalid states fail closed
- reservation concurrency and receipt redaction are proven
- provider catalog presence remains non-callable
- static network guards remain unchanged or stricter

Rollback:

- remove new inert contracts/modules; existing gateway behavior remains intact

### WEB-HYBRID-002 — Local Web Services Packaging

Scope:

- add `packaging/local-web-services/`
- pin SearXNG and Firecrawl upstream refs/digests
- add generated-secret setup and loopback-only Compose configuration
- add health/config inspection scripts
- do not wire UAA runtime adapters

Exit criteria:

- Compose validation and opt-in smoke checks pass
- only reviewed adapter APIs publish loopback ports
- databases, queues, Playwright, and admin surfaces remain internal
- no credential or raw path appears in durable evidence
- shutdown and documented rollback work

Rollback:

- `docker compose down`; preserve volumes for review or remove them only through
  an explicit operator cleanup command; revert packaging files

### WEB-HYBRID-003 — Exact SearXNG Read-Only Search

Scope:

- implement one injected/fixed transport adapter
- promote only `SEARCH` for the exact SearXNG lane
- add AuthorityLease, approval, domain/result/category limits, audit, source
  metadata, CLI inspection, and safe-disable behavior
- no Firecrawl calls

Exit criteria:

- focused adapter/policy/static-guard/redaction tests pass
- denied requests never call the transport
- candidate URLs are revalidated before later extraction
- CLI/core parity is proven

Rollback:

- safe-disable the SearXNG lane and return to diagnostic-only provider posture

### WEB-HYBRID-004 — Exact Self-Hosted Firecrawl Markdown Extraction

Scope:

- add `EXTRACT_MARKDOWN`
- implement fixed self-hosted Firecrawl transport
- distinguish target GET semantics from provider POST transport
- allow one public HTTPS page, markdown only, one attempt
- keep crawl/map/search/schema/Interact/browser/screenshots blocked

Exit criteria:

- target SSRF/redirect protections remain unchanged or stronger
- provider endpoint cannot be caller controlled
- raw payloads remain quarantined/transient
- CLI/core parity and local smoke proof pass

Rollback:

- safe-disable local extraction; stop extraction profile; keep SearX search
  independently available if still accepted

### WEB-HYBRID-005 — Authenticated Firecrawl Cloud Credit Adapter

Scope:

- resolve one free-plan credential through the secrets boundary
- implement credit-usage reconciliation
- implement atomic reservations and plan concurrency limits
- implement standard one-page markdown cloud scrape only
- keep router fallback disabled until this adapter is independently proven

Exit criteria:

- missing/stale/unknown/incomplete credit states block before provider use
- no paid usage path exists
- credential and provider payload redaction tests pass
- one approved private-dogfood call produces complete usage and audit refs

Rollback:

- safe-disable cloud extraction and revoke/remove the credential ref; local
  lanes remain independent

### WEB-HYBRID-006 — Hybrid Routing and One-Step Failover

Scope:

- promote `self_host_first_cloud_escalation`
- keep `cloud_budget_first` absent because it was not separately accepted
- add exact failure taxonomy, one-fallback ceiling, cloud circuit breaker,
  reservation handoff, and idempotent replay handling
- no background health probes or scheduler

Exit criteria:

- full routing decision table is covered by deterministic tests
- no policy-denied request falls back
- concurrency cannot oversubscribe cloud credits
- retry/fallback cannot double-charge an idempotent request
- safe-disable and revocation races fail closed

Rollback:

- set exact route mode to `self_host_only` or `sealed`; retain audit history

### WEB-HYBRID-007 — API, Manifest, CLI, and Control Center Read Model

Status: implemented; deterministic and operator-surface verification recorded
before WEB-HYBRID-008 promotion review.

Scope:

- finalize CLI commands
- add protected API routes only if core/CLI evidence is accepted
- update OpenAPI, `/api/manifest`, route inventory, side-effect classification,
  auth, rate limits, and idempotency
- add a non-JSON-primary provider/quota/routing status UI

Exit criteria:

- CLI/API/UI show the same backend-owned state and receipt refs
- Control Center cannot mint authority or expose secrets/raw content
- frontend, OpenAPI, API manifest, route classification, product-language, and
  focused security tests pass

Rollback:

- remove or safe-disable route/UI exposure while retaining core diagnostic and
  audit state; no provider work depends on React state

### WEB-HYBRID-008 — Private Dogfood, Hardening, and Promotion Review

Status: completed for the exact private/local scope. The accepted posture
remains `self_host_first_cloud_escalation`; no crawl, map, screenshot, schema,
MCP, browser-action, paid, Keyless, cloud-first, or background lane is
justified by this evidence.

Redacted verification evidence:

| Evidence ref | Result | Safe observation |
|---|---|---|
| `proof-ref:web-hybrid:local-stack-lifecycle` | passed | Seven pinned services reached healthy state, survived restart, and stopped cleanly after review. |
| `proof-ref:web-hybrid:live-local-search` | passed | One exact SearXNG request returned bounded untrusted source evidence. |
| `proof-ref:web-hybrid:live-local-markdown` | passed | One exact self-hosted request returned transient bounded markdown; raw provider output was not stored by UAA. |
| `proof-ref:web-hybrid:playwright-private-target-denied` | passed | The pinned Playwright SSRF boundary denied the link-local metadata target. Formal adversarial DNS-rebinding/firewall proof remains future hardening. |
| `proof-ref:web-hybrid:live-cloud-one-credit` | passed | One exact standard scrape reconciled one free-plan credit with safe refs only; paid usage remained denied. |
| `proof-ref:web-hybrid:foundation-gate` | passed | Report-only gate recorded 627 passed, zero failed/warning/blocked criteria. |

Cloud execution is intentionally serialized to one UAA-owned in-flight
reservation even though the reviewed free plan advertises concurrency two;
shared account-balance deltas cannot safely attribute overlapping requests.

Scope:

- execute the bounded local and cloud smoke matrices
- record redacted success/failure, latency, extraction-quality, quota, and
  failover evidence
- run red-team cases and Foundation Gate/report-only checks
- decide whether `self_host_first_cloud_escalation` remains default
- decide whether any later crawl/map/screenshot/schema/MCP lane is justified

Exit criteria:

- Definition of Done below is met
- no blocked capability was enabled to improve a score
- remaining gaps are explicitly planned, blocked, or rejected

Rollback:

- return route mode to `sealed`, revoke the cloud credential, stop the local
  stack, and preserve redacted audit/decision evidence

### WEB-HYBRID-009 — Optional UAA-Governed MCP Surface

This is a separate future milestone, not part of initial completion.

Scope:

- expose only UAA-owned read-only search/extract/status tools
- route every call through the accepted Python core/API boundary
- preserve the same lease, approval, quota, redaction, audit, and safe-disable
  contracts

Exit criteria:

- no raw provider MCP connection is registered with the agent
- disabling UAA web authority disables MCP use
- plugin/MCP runtime authority is separately accepted and verifier-backed

## Suggested Verification Commands

Run the focused commands added by each implementation PR plus the existing
gateway and documentation gates. Expected baseline commands include:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_web_access_gateway.py tests/test_web_access_static_guards.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/verify_web_runtime_authority.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

When Control Center code changes, also run the repo-defined frontend checks.
When packaging changes, add a deterministic Compose config verifier and an
opt-in local smoke command. Missing Docker, credentials, or network access is a
reported blocker, not a passing claim.

## Rollout Strategy

1. Keep all new providers `sealed` after merge.
2. Start local containers manually and verify health through CLI diagnostics.
3. Enable SearXNG for one exact private-dogfood AuthorityLease scope.
4. Enable self-hosted markdown extraction for one exact allowlisted domain set.
5. Add the cloud credential and reconcile credits without scraping.
6. Approve one cloud markdown scrape and verify receipt completeness.
7. Enable hybrid routing for one bounded private-dogfood session.
8. Observe quota, latency, failure classification, redaction, and route decisions.
9. Promote API/UI read models only after core/CLI evidence is accepted.
10. Keep background, MCP, crawl/map, schema extraction, screenshots, and browser
    authority blocked pending separate decisions.

## Rollback and Safe-Disable Matrix

| Failure | Immediate action | Preserved capability |
|---|---|---|
| SearXNG unhealthy or upstream engines blocked | Safe-disable search lane; show degraded/blocked state | Direct governed fetch remains independent |
| Self-hosted Firecrawl unhealthy | Disable local extraction; cloud remains blocked or exact-approved only | SearX search remains independent |
| Cloud quota/receipt inconsistent | Open cloud circuit and block cloud use | Local search/extraction may remain available |
| Cloud credential suspected compromised | Revoke credential and disable cloud deployment ref | Local lanes remain independent |
| Router/fallback defect | Route mode `sealed` or `self_host_only` | Provider diagnostics and audit inspection remain |
| Redaction or raw-payload leak | Emergency safe-disable all new web provider lanes and quarantine evidence | Existing gateway denial posture |
| Compose upgrade failure | Restore pinned provider lock and compatible volumes | UAA core remains independent |
| Policy/static guard regression | Block merge or revert offending PR | Existing gateway boundary |

Rollback never deletes audit history. Cleanup of provider volumes, caches, or
credentials is an explicit operator action with evidence and no raw output in
durable records.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Self-host quality is lower on protected sites | Use local-first/cloud-escalation and an exact failure taxonomy |
| SearXNG upstream engines CAPTCHA or rate-limit the host | Bound concurrency, use engine suspension/limiter posture, expose degraded state |
| Firecrawl upstream topology changes | Pin version/digest, maintain provider lock, rehearse upgrades |
| Cloud pricing or credit semantics change | Versioned static cost policy, authenticated balance reconciliation, unknown-cost block |
| Concurrent requests overspend credits | Atomic reservations plus provider concurrency ceiling and safety reserve |
| Fallback bypasses policy | Terminal policy reasons never fall back; target revalidation on every attempt |
| Docker services become an ungoverned local network | Fixed configured endpoints, loopback-only ports, internal databases/queues |
| Raw content becomes implicit prompt context | Quarantine, transient output, no automatic context/memory injection |
| Direct provider MCP bypasses UAA | Expose only a future UAA-governed MCP wrapper |
| Experimental Ollama degrades quality or adds hidden authority | Keep blocked until a separate evaluated model lane |
| Free tier silently becomes paid | No payment/upgrade/recharge integration; hard block unknown or paid usage |
| AGPL/distribution obligations are missed | License review before distributing modified services |

## Open Decisions Before WEB-HYBRID-001

1. Use `self_host_first_cloud_escalation` as the accepted steady-state policy;
   keep `cloud_budget_first` out of scope.
2. Confirm authenticated free-plan Firecrawl API key use and reject Keyless for
   the governed lane.
3. Confirm that full markdown remains transient; durable corpus storage is out
   of scope.
4. Confirm `packaging/local-web-services/` as the package location.
5. Select the pinned SearXNG and Firecrawl upstream versions only during the
   packaging PR after current release/security review.
6. Decide the initial domain allowlist and bounded result/timeout/byte limits
   without putting private targets or credentials in docs.
7. Confirm no proxy and no Ollama in the first runtime promotion.
8. Confirm MCP work stays outside initial completion.

## End-to-End Definition of Done

The hybrid web extraction lane is complete only when:

- SearXNG and self-hosted Firecrawl run from a pinned, loopback-first,
  documented, reversible Compose package.
- Search and one-page markdown extraction route only through
  `ultimate_ai_agent.core.web_access`.
- Target URL policy remains HTTPS/read-only/private-network-denied across
  redirects and both provider deployments.
- Provider transport endpoints are fixed configuration and cannot be supplied
  by the caller.
- The cloud lane uses authenticated credit reconciliation, atomic reservations,
  a concurrency ceiling, a safety reserve, and no paid-usage path.
- Billing-period refresh is provider-confirmed and user-triggered, not assumed
  by cron/calendar.
- Routing is deterministic, auditable, safe-disable-aware, and limited to one
  eligible fallback.
- Policy, robots/terms, auth, private-target, content-limit, and unknown-cost
  failures never fall back.
- Every attempt has a redacted audit/receipt with provider, deployment,
  authority, route, quota, source, content hash, and rollback refs.
- No durable raw query, page, DOM, provider payload, prompt, response,
  credential, local path, environment, or log data exists.
- Search and extraction outputs remain untrusted and cannot become instructions,
  memory, context, or execution authority.
- CLI/API/Control Center expose the same backend-owned state; UI does not mint
  authority or use raw JSON as the primary workflow.
- Firecrawl `/agent`, `/browser`, Interact, clicks, forms, auth/cookies,
  downloads/uploads, proxy escalation, local Ollama, background work, and MCP
  runtime remain explicitly blocked unless separately promoted.
- Focused tests, web authority verifier, documentation integrity, OpenAPI/API
  manifest checks where applicable, frontend checks where applicable, and
  Foundation Gate report-only pass or have explicit reported blockers.
- Rollback has been exercised: route mode can return to `sealed`, cloud
  credential can be revoked, local services can stop, and audit history remains.

This plan alone does not authorize implementation. When the operator invokes
`docs/prompts/web_hybrid/00_execute_searxng_firecrawl_hybrid_end_to_end.prompt.md`
with `start`, `execute`, or equivalent language, that invocation authorizes the
exact `WEB-HYBRID-001` through `WEB-HYBRID-008` program, including its bounded
local Docker work, free-credit cloud smoke budget, phase commits, push, PR,
review/CI remediation, merge, post-merge verification, and final push. The run
continues between child tasks without repeated approval while remaining inside
the parent web-runtime WIP limit, tests, redacted evidence, and rollback
posture. Material capabilities outside that activation contract still require
a separately scoped decision.
