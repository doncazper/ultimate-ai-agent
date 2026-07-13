# Phase 05: Web Research And Provider Observability

Goal: build on and never replace the exact implemented SearXNG/Firecrawl
hybrid while adding cited bounded aggregation and honest provider truth.

## Preservation Baseline

Preserve WebAccessGateway, bounded SearXNG search, self-hosted Firecrawl
one-page markdown extraction, free-plan Firecrawl Cloud, self-host-first
routing with at most one separately authorized eligible cloud fallback, cloud
budget serialization/credit reconciliation, local web-service packaging and
configuration, activation prompt and implementation plan, and WEB-HYBRID
CLI/API/Control Center truth.

## Required Work

1. Add cited bounded research aggregation with source, evidence, audit,
   adapter, retrieval, exclusion, redaction, and budget refs.
2. Mark all external content `content_untrusted=true` and
   `not_instruction_authority=true`. Aggregation produces evidence summaries,
   never memory truth, instructions, approval, or action authority.
3. Preserve uncertainty in provider readiness, configuration, compatibility,
   health, latency, cost, context, routing, and budget metadata. Configured is
   not healthy; healthy is not authorized; free-plan is not unmetered;
   readiness is not request authority; missing/unknown metered budget blocks.
4. Use deterministic injected observations for tests. Do not add broad or
   background network probes.
5. Revalidate inside the final locked transport-start boundary using a fresh trusted clock
   and re-evaluate PolicyEngine, exact LocalApprovalAuthority, current
   AuthorityLease, capability and adapter, provider and target, mission and
   run, TTL and deadline, budget, kill switch, safe-disable, readiness,
   idempotency, replay posture, and exact request fingerprint.
6. A self-hosted attempt does not authorize its cloud fallback. Fallback uses a new
   trusted time and an independent exact evaluation.
7. Expose readable backend-owned citations, degraded/blocked reasons, costs,
   readiness, and audit refs through current CLI/API/macOS UI surfaces.

## Required Proofs

- cited bounded aggregation and excluded-source reasons;
- injection-shaped content cannot change authority;
- approval/lease/kill/budget/safe-disable/readiness/adapter/provider/target/
  mission/run/fingerprint/deadline changes after preflight produce zero network
  calls;
- fallback is self-host-first, eligible only, independently authorized, and at
  most one attempt;
- exact free/cloud reservation and reconciliation survives concurrency/crash;
- raw pages, provider payloads, queries, logs, paths, and secrets are not
  durably persisted; and
- existing WEB-HYBRID focused tests and verifier remain green.

## Non-Goals

No browser clicks/forms/auth/cookies/downloads/uploads, new arbitrary live web
fetch, cloud-first or multi-hop fallback, paid or unknown-plan use, provider
SDK authority, connector writes, hidden context injection, or external
mutation. The existing exact Firecrawl scrape POST remains one read-only
provider transport and grants no generic POST authority.

## Exit

The preserved hybrid is final-start hardened, cited, cost-reconciled,
operator-readable, and still narrow read-only untrusted evidence.
