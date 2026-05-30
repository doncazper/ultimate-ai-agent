# 59 — Truth, Grounding, and Evidence Governance

Status: Active foundation specification for v0.5.6.

## Purpose

This module makes the source-of-truth policy explicit.

The model is never the source of truth. It is a reasoning and language layer that retrieves, validates, cites, explains, and acts through governed systems.

## Core principle

The model is not the authority. Governed sources are the authority. The model explains what governed sources support.

```text
Authoritative source
  -> retrieval / API / database / canonical file access
  -> evidence manifest
  -> model reasoning and explanation
  -> verification contract
  -> receipt / audit record
```

## Truth hierarchy

Use the strongest applicable authority for the task:

1. Current explicit user instruction, when lawful and safe.
2. Approved canonical project files for project truth.
3. Direct APIs/databases/provider adapters for live structured facts.
4. Approved source documents through hybrid RAG for written knowledge.
5. Event Ledger / World State for what the agent actually did.
6. Source-linked memory for recall and personalization.
7. General model knowledge only for low-risk background knowledge and creative reasoning.

Memory is recall, not authority. Fine-tuning improves style and behavior, not truth freshness or auditability.

## Truth Source Router

Every factual task must choose a grounding route.

| Question type | Preferred route | Notes |
|---|---|---|
| Project architecture, roadmap, decisions | Canonical files + ADRs | Canonical files outrank memory. |
| User/project history | Memory + source links + Event Ledger | Surface uncertainty if memory lacks source. |
| Live structured facts | API/database/provider adapter | Do not use RAG for prices, inventory, status, metrics, dates, or availability when APIs exist. |
| Documents, policies, contracts | Hybrid RAG + citations | Human review for legal/compliance interpretation. |
| Metrics/finance/inventory | SQL/API + deterministic calculation | The model may explain but must not invent numbers. |
| Complex relationships | Knowledge graph + RAG | Use entity provenance and access control. |
| Fast-changing information | Live retrieval/API + timestamped evidence | Include freshness and stale-source handling. |
| News/breaking events | Live sources + clustering + credibility protocol | Reddit/social posts are signals, not facts. |
| Weather | Weather provider API + timestamp | Prefer free/no-key provider when adequate. |
| Code status | Git/filesystem/tests/build logs | Cite commit/file/test result. |
| High-risk workflow | AI assist + approval queue | Human approval is required for final authority. |

## Grounding modes

Execution Contracts must support a `grounding_mode` field.

```text
none_allowed_for_creative
sources_preferred
sources_required
canonical_api_required
human_review_required
```

## Hybrid retrieval requirement

Vector search alone is insufficient for truth-sensitive work.

The default approved-document retrieval stack is:

```text
keyword search
+ vector search
+ metadata filters
+ access control filters
+ semantic reranking
+ source freshness scoring
+ conflict detection
```

Keyword search is required for exact identifiers, SKUs, dates, policy names, legal language, issue IDs, file names, and record IDs. Vector search is useful for semantic recall and fuzzy phrasing. Reranking chooses the best evidence set.

## Evidence Manifest

Every verified factual answer should be able to produce an Evidence Manifest.

The Evidence Manifest links answer IDs, claim IDs, source types, source locators, retrieval timestamps, publication/update/effective dates, freshness status, confidence, permission scope, conflicts, and unsupported claims.

## Claim-level evidence

Important answers should be decomposed into claims:

```text
claim -> evidence -> confidence -> freshness -> conflicts -> verification status
```

The agent must not cite a source merely because it was retrieved. The cited source must support the specific claim.

## Conflict handling

If sources disagree, the agent must not silently choose the convenient answer. It must rank by source authority, primary-source status, effective date, version status, permissions, confidence, and human review status.

## Unsupported claim handling

If no approved source supports a claim, the agent must say evidence is unavailable, ask permission to retrieve more sources, label the answer as a hypothesis, refuse high-stakes unsupported output, or route to human review.

The agent must never invent missing numbers, dates, policies, prices, statuses, legal obligations, quotes, or citations.

## Structured data rule

For hard facts, prefer structured systems over document search.

Examples:

```text
prices -> pricing API/database
inventory -> inventory database
customer status -> CRM/API
calendar availability -> calendar API
weather -> weather provider API
cost totals -> Event Ledger/cost database calculation
GitHub issue status -> GitHub API
account balances -> approved financial API, if user consents
```

RAG can explain policy text, but API/database grounding supplies operational facts.

## Access control rule

The Evidence Manifest must never reveal information the user could not access directly. Retrieval must apply permissions before ranking. Private-source citations must be scoped and redacted.

## Retrieval log

Every grounded answer should log question/task, run/trace IDs, retrieval route, query filters, retrieved sources, source timestamps, reranking scores, used vs ignored evidence, model output ID, evidence manifest ID, confidence, and verification status.

## Fine-tuning boundary

Fine-tuning and learned preferences may improve style, format, workflow selection, domain language, skill selection, and retrieval weighting. They must not replace live approved sources for factual truth.

## High-stakes truth

For legal, medical, finance, compliance, HR, security, or customer-impacting decisions, the agent is a research assistant. It must provide evidence, uncertainty, and recommended review path, not final authority.

## Foundation Gate impact

M4.5 Truth Source Router and Evidence Governance must pass before the Minimum Lovable Kernel can claim verified factual output.
