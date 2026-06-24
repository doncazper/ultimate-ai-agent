# FCC-MEM-022 Ranked Retrieval / Recall Tuning

Status: implemented ranked recall read-model slice.

FCC-MEM-022 adds deterministic ranked recall diagnostics to the existing Memory
Workbench and Memory Search read models. It makes recall ordering inspectable
for the operator without adding a new route or any new authority.

## Implemented Shape

- `GET /control-center/memory/workbench` now includes a `ranking` read model
  with candidate count, included/excluded refs, rank signal refs, source mix,
  pressure counts, cache key, cache hit state, token estimate, and blocked
  authority refs.
- Each Memory Workbench item now includes `rank_score`, bounded
  `rank_components`, included/excluded reason refs, pressure flags, source mix,
  cache key, token estimate, `why_ranked_refs`, and ranking blocked authority
  refs.
- `GET /control-center/memory/search` preserves exact safe-ref filtering and
  returns the same ranked recall diagnostics for filtered results.
- The Control Center Memory surface shows Ranked recall diagnostics, Recall
  rank, Rank components, source mix, why-ranked refs, included/excluded reason
  refs, and blocked authority refs without raw JSON as the primary UI.

## Ranking Signals

Ranking is lexical/tag/ref-only and deterministic. Score components are bounded
integer values for:

- lexical safe-summary/title match
- tag ref match
- entity ref match
- relationship ref match
- recency
- reviewed status
- evidence quality
- citation integrity
- duplicate, conflict, stale, and missing-evidence pressure
- loop impact
- source diversity
- operator feedback or quality issue pressure

Excluded refs remain visible with reason refs. Exclusion explains why an item
should not be treated as ready recall; it does not delete, suppress, mutate, or
execute anything.

## Safety Boundaries

No embeddings, vector DB, semantic provider, model/provider calls, context
injection, memory writes, auto-maintenance, or action execution are introduced.
Connector writes, background indexing, prompt stuffing, truth authority, public
beta, and production authority remain blocked.

The ranking cache key is a deterministic read-model fingerprint only. It is not
a durable cache, hidden retrieval run, context manifest apply step, or prompt
construction path.

## Verification

- `scripts/verify_fcc_mem_022_ranked_retrieval_recall_tuning.py`
- `tests/test_fcc_mem_022_ranked_retrieval_recall_tuning.py`
- Existing Memory Workbench/Search and API manifest tests remain valid.
