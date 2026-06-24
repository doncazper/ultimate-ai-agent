# FCC-MEM-022 Ranked Retrieval / Recall Tuning

Status: implemented P0-P4 memory feature-mine umbrella with HRR milestone blocked.

FCC-MEM-022 implements the current safe subset of the Honcho, Hindsight, and
Holographic feature mine as UAA-native memory infrastructure. Those systems are
design references only. UAA does not import, depend on, sync with, or delegate
authority to external memory providers, cloud memory, model extraction,
automatic retain/recall, semantic/vector search, HRR retrieval, hidden context
injection, connector writes, or memory-derived execution.

## Implementation Lanes

| Lane | Purpose | Implemented Surface | Authority Boundary |
| --- | --- | --- | --- |
| FCC-MEM-022A | UAA-native adoption guardrail | Governed memory docs and manifest blockers record Honcho, Hindsight, and Holographic as design references only | No external memory runtime, cloud sync, automatic recall, model extraction, semantic/vector search, HRR retrieval, or context injection |
| FCC-MEM-022B | Safe local ranked retrieval | `safe_query` hash refs, deterministic score components, retrieval strategy refs, and SQLite FTS5 status over safe summaries/refs only | No raw query echo, embeddings, vector DB, semantic provider, background indexing authority, context injection, or memory writes |
| FCC-MEM-022C | Feedback receipts and trust tuning | `POST /control-center/memory/feedback` records idempotent local feedback receipts and updates reviewed recall trust/stale/conflict posture | No recall record creation, delete/export execution, connector write, cloud sync, context injection, action execution, or production authority |
| FCC-MEM-022D | Epistemic roles and observations | `MemoryEpistemicRole` plus `GET /control-center/memory/observation-candidates` over reviewed L1/L2 refs | Observations are candidates, not truth or automatic opinions |
| FCC-MEM-022E | Perspective, probe, contradiction preview, HRR path | L3 observer/observed perspective fields, `GET /control-center/memory/probe`, `GET /control-center/memory/contradictions`, and HRR readiness | Probe/contradictions are inspection only; HRR/algebraic retrieval is disabled until `milestone-ref:fcc-mem-hrr-001-explicit-authority` |

## Public Interfaces

- Existing read-only memory routes accept optional `safe_query` and reject
  requests that provide both `query_ref` and `safe_query`:
  - `GET /control-center/memory/workbench`
  - `GET /control-center/memory/search`
  - `GET /control-center/memory/l1-index`
  - `GET /control-center/memory/l2-index`
  - `GET /control-center/memory/l3-index`
  - `GET /control-center/memory/context-packs`
- `safe_query` is never echoed. Read models return only `safe_query_ref`,
  `query_mode`, `retrieval_strategy_refs`, `score_components`, and
  `search_index_status`.
- `POST /control-center/memory/feedback` is an idempotent, approval-bound,
  local-only feedback receipt route.
- `GET /control-center/memory/observation-candidates` derives read-only
  observation candidates from reviewed L1/L2 refs.
- `GET /control-center/memory/probe?entity_ref=...` inspects reviewed recall,
  L1/L2/L3, context-pack, feedback, and observation refs for one safe entity ref.
- `GET /control-center/memory/contradictions` returns deterministic
  contradiction previews from duplicate/conflict/stale posture and feedback
  receipts.

## Retrieval Signals

Ranking remains deterministic and local. Score components include safe summary
and title matches, tags, entity/relationship refs, source/evidence/receipt
coverage, confidence, trust score, recency, stale/conflict pressure,
duplicate/missing-evidence pressure, review state, loop impact, and source
diversity.

SQLite FTS5 may be enabled inside the local reviewed recall store, but only over
safe summaries and safe refs. If FTS5 is unavailable, the system falls back to
deterministic lexical/ref scoring. The search index status always reports that
raw content, embeddings, vector DB, semantic search, HRR, and algebraic
retrieval are disabled.

## Feedback And Epistemic Roles

`MemoryFeedbackRequest` requires `memory_record_ref`, `feedback_kind`, reviewer,
source refs, evidence refs, and the full feedback blocked-state ref set.
Helpful feedback adds `+0.05` trust, unhelpful or not-relevant feedback subtracts
`0.10`, and stale/conflict feedback updates posture without deleting or
exporting memory.

`MemoryEpistemicRole` defaults to `unknown`. Founder Loop candidate kinds map
deterministically:

| Candidate Kind | Epistemic Role |
| --- | --- |
| profiles, projects, organizations, deals | `world_fact` |
| decisions, promises, follow-ups, commitments | `experience_fact` |
| preferences, relationships | `observation` |
| all other kinds | `unknown` |

No automatic `opinion` records are created.

## HRR Safe Path

FCC-MEM-022 does not implement HRR retrieval. Read models expose:

- `hrr_enabled=false`
- `algebraic_retrieval_enabled=false`
- `required_milestone_ref=milestone-ref:fcc-mem-hrr-001-explicit-authority`

Future `FCC-MEM-HRR-001` must explicitly authorize local algebraic
vector-like retrieval and still require safe-summary/ref-token inputs only, no
raw content, no embeddings provider, no vector DB, disabled-by-default config,
shadow-mode evaluation, no ranking influence until separately approved, audit
receipts, rollback/safe-disable posture, and Foundation Gate coverage.

## Safety Boundaries

No embeddings, vector DB, semantic provider, model/provider calls, context
injection, prompt stuffing, memory-derived execution, connector writes,
CRM/account sync, delete/export execution, automatic memory maintenance,
background indexing authority, external memory provider runtime, cloud sync,
public beta, or production authority are introduced.

Memory remains recall, not truth, approval, execution, connector, CRM, account,
or prompt authority.

## Verification

- `tests/test_fcc_mem_022_ranked_retrieval_recall_tuning.py`
- `scripts/verify_fcc_mem_022_ranked_retrieval_recall_tuning.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- Existing Memory Workbench/Search, governed memory index, API manifest, and
  Foundation Gate checks remain applicable.
