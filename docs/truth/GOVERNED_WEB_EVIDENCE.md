# Governed Web Evidence

Status: Active contract for evidence-first web evidence intake.

This capability is evidence-first, not browsing-first. Phase 1 is explicitly:

```text
web evidence intake, no live fetch
```

The current contract accepts only operator-supplied metadata about a web source.
It does not retrieve the URL, open a browser, call OpenWebUI search, call a
model/provider, download content, store page bodies, follow redirects, use auth,
use cookies, or create a backend route.

## Phase 1 Intake

The intake record must contain:

- URL/source metadata with HTTPS source URL, title, publisher, source ref, and
  operator source ref.
- Safe source summary bounded to the contract limit.
- Short bounded quote supplied by the operator.
- Optional bounded redacted preview supplied by the operator.
- Freshness fields: observed time, checked time, freshness status, freshness
  basis, and source publish/update/effective metadata where available.
- Source authority classification and authority rationale.
- Source receipt ref, evidence receipt ref, intake receipt ref, and optional
  policy receipt ref.

The contract rejects raw or auth-bearing source content in dynamic metadata,
including page bodies, page HTML, source body dumps, cookies, authorization
headers, download paths, and secret-like assignments.

## No Live Fetch Boundary

The policy defaults to disabled-by-default contract posture and requires:

- operator-supplied metadata only
- live fetch denied
- browser automation denied
- OpenWebUI web search denied
- model/provider calls denied
- raw body storage denied
- downloads denied
- auth denied
- cookies denied
- redirects denied
- backend route addition denied

Evidence intake can validate supplied metadata. It cannot prove the live state of
the URL unless a human/operator or a later governed lane supplies fresh reviewed
evidence.

## Freshness

Freshness is explicit evidence metadata, not an implicit side effect. Intake
records must identify when the operator observed the source, when the freshness
check was recorded, the freshness status, and the basis used for that status.

The contract can represent current, stale, or expired web evidence. Unknown or
not-applicable freshness is rejected for this intake lane because the purpose is
to make temporal trust visible.

## Source Authority

Source authority is a classification, not automatic truth. Supported classes
include primary source, official source, government source, standards body,
academic source, reputable secondary source, vendor source, community source,
operator-supplied context, and untrusted source. The authority level and
rationale must be carried in the metadata so reviewers can decide whether the
evidence supports a specific claim.

## Later Lane: Allowlisted HTTPS GET

A later scoped milestone may define an allowlisted HTTPS GET lane. That lane is
future work and must remain disabled until reviewed. Its minimum boundary is:

- HTTPS GET only
- allowlisted targets only
- no auth
- no cookies
- no redirects
- no downloads
- no raw body storage
- bounded redacted previews only
- source receipts required
- freshness checks required
- rollback plan required
- non-goal docs required

The later lane must include policy checks, source receipts, freshness checks,
bounded redacted preview rules, abuse cases, failure modes, rollback docs, and
non-goal docs before any transport exists.

## OpenWebUI Search Boundary

OpenWebUI web search is outside UAA governance unless routed through the future
allowlisted HTTPS GET lane.

OpenWebUI remains a shell. Search results from OpenWebUI cannot become UAA truth
authority, cannot write memory, cannot inject context, and cannot bypass
PolicyEngine, LocalApprovalAuthority, evidence receipts, or Foundation Gate
coverage.

## Rollback And Non-Goals

Rollback for Phase 1 is removal or revocation of supplied evidence refs and
receipt refs from the consuming review packet. Because Phase 1 performs no fetch,
download, browser action, model call, route addition, or persistence migration,
there is no network or downloaded artifact to unwind.

Non-goals:

- no live web fetching
- no browser navigation, click, type, form-fill, screenshot, or DOM read
- no OpenWebUI web search execution
- no provider/model calls
- no raw page body storage
- no downloads or exports
- no auth, cookies, redirects, credentials, or session handling
- no backend route
- no production authority
- no memory write or context injection
