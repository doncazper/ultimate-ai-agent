# WebAccessGateway PR Sequence

Future provider and dangerous-authority sequencing is governed by
`docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md`. Do not treat provider
SDK presence as permission to execute browser actions, auth/session work,
downloads/uploads, or POST-style mutations.

## PR 1 — M72.5 WebAccessGateway Boundary

Purpose: create the central boundary before adding providers.

Allowed:

```text
- contracts
- deny-by-default policy
- normalized audit record
- source metadata
- governed web evidence wrapper
- static guardrails
- explicit network lanes
- temporary exception list for existing direct HTTP/browser modules
```

Forbidden:

```text
- new provider dependencies
- browser execution
- browser observe runtime expansion
- browser dry-run runtime expansion
- low-risk click activation
- form filling
- auth/cookies
- downloads/uploads
- POST/PUT/PATCH/DELETE
- broad direct-HTTP migration
```

## PR 2 — WebAccess API/Manifest Wording Integration

Purpose: align API/manifest wording with the core gateway boundary without
adding routes or runtime behavior.

Tasks:

```text
- Update manifest wording to distinguish unrestricted web fetching from governed web access.
- Preserve side-effect classification as governed/read-only.
- No new API route.
- No status or preview route.
- No runtime fetch wiring.
- No new providers.
- No browser behavior.
```

## PR 3 — Tool Runtime HTTP Fetch Migration

Purpose: make existing read-only HTTP fetch subordinate to the gateway.

Tasks:

```text
- Route tool runtime read-only fetch through WebAccessGateway.
- Preserve current behavior where possible.
- Add deprecation warning or static guard for direct use of old runtime fetch path.
- Remove or narrow TOOL_RUNTIME_LEGACY exception if possible.
```

## PR 4 — Browser Observe Gateway Integration

Purpose: place observe-only browser inspection behind the gateway.

Tasks:

```text
- Add browser_observe adapter contract implementation.
- Use injected transport/provider only.
- Return bounded safe text/accessibility summary.
- Return URL/title/final URL/source metadata.
- No cookies/session persistence.
- No raw DOM by default.
- Screenshots disabled unless policy explicitly allows later.
```

Forbidden:

```text
- clicks
- form fills
- downloads/uploads
- auth/cookies
- persistent browser sessions
- hidden navigation authority
```

## PR 5 — Browser Action Dry-Run Gateway Integration

Purpose: expose browser action plans, not execution.

Tasks:

```text
- Add browser_action_dry_run adapter behind the gateway.
- Dry-run consumes an observation bundle.
- Dry-run does not independently create/control a browser session.
- Output reviewable action plan with risk/reasons/blocked actions.
```

Forbidden:

```text
- real clicks
- form submission
- auth/cookies
- purchases
- downloads/uploads
- low_risk_click activation
```

## Later PRs — Scoped Execution Only

Do not start until all prerequisites exist:

```text
- scoped autonomy sessions
- exact approval records
- domain/method allowlists
- idempotency classification
- audit/replay
- revocation/kill switch
- sensitive-data redaction
- provider sandboxing
- red-team review
```

The earliest real browser clicks should stay aligned with the later low-risk browser click milestone, not PR 1-5.
