# UAA-P1-088 Agent Module Maturity Review V2

Status: implemented review/scoring/read-model lane only.
Baseline: `v0.104.0`.
Structured artifact: `docs/registry/agent_module_maturity_review_v2.json`.
Source V1 map: `docs/registry/agent_module_maturity_map.json`.

This review scores each requested core AI-agent module against repository
evidence only and refreshes the scorecard after the requested `FCC-MEM-015`
through `FCC-MEM-021` memory hardening sequence. This branch does not contain
tracked `FCC-MEM-015` through `FCC-MEM-021` artifacts, so those lanes are
recorded as absent current evidence rather than scored as implemented work. It
does not add runtime model calls, provider SDK calls, web fetching, browser
automation, shell/subprocess execution, connector writes, memory writes,
context injection, action execution, workflow execution, autonomous routing
authority, public beta claims, or production authority.

Plain-language status: FCC-MEM-015 through FCC-MEM-021 are treated as requested
refresh context, not tracked implementation evidence in this branch.

Snapshot timing: the module score table is the `UAA-P1-088` review snapshot
captured before applying the ranked follow-up lanes in this same work batch.
The queue below records follow-up outcomes for `UAA-P1-089`, `UAA-P1-090`,
`FCC-LOOP-002`, and `FCC-MEM-022`; those completed follow-ups do not rescore
the V2 snapshot. A post-follow-up rescore is a separate future review lane.

## Scoring Model

Each module receives eight integer dimension scores from 0 to 5:

- product usefulness
- safety boundary clarity
- test depth
- UI visibility
- CLI parity
- evidence quality
- operator ergonomics
- implementation maturity

The composite score is deterministic:

```text
floor(sum(dimension_scores) * 100 / 40)
```

The V1 maturity map remains valid and remains the benchmark score source. V2 is
the richer evidence review and ranked improvement queue.

Queued follow-up prompts from this review require subagents. Each follow-up
must use at least one independent repo-evidence reviewer and one
safety/product-language reviewer unless the task is explicitly split into
disjoint implementation workers plus a final safety reviewer. The main agent
still owns integration, verification, and final truth.

## Summary

| Module | V1 maturity | Composite | Next checkpoint |
|---|---|---:|---|
| Agent runtime skeleton | `constrained_local_runtime` | 75 | Separate the minimum kernel from a future general runtime contract. |
| Orchestration layer | `validated_contract` | 52 | Add a top-level route/orchestration contract before broad runtime flow. |
| Decision router | `contract_only` | 47 | Snapshot follow-up: build `UAA-P1-089` as a unified contract/read-model only router. |
| Planning module | `validated_contract` | 67 | Bind planning to review-only decomposition proposals. |
| Task decomposition module | `contract_only` | 47 | Snapshot follow-up: build `UAA-P1-090` as a proposal-only decomposition engine. |
| Workflow engine | `validated_contract` | 60 | Keep execution blocked while proposals and routing mature. |
| State manager | `validated_contract` | 62 | Unify state refs through route/proposal read models before resumption work. |
| Context manager | `validated_contract` | 67 | Improve inspection and ranking while keeping context use blocked. |
| Memory module | `constrained_local_runtime` | 92 | Tune ranked retrieval with lexical/tag/ref scoring only. |
| Tool registry | `constrained_local_runtime` | 80 | Bind tool choices into route proposals without execution. |
| Capability registry | `constrained_local_runtime` | 80 | Expose capability choices as reviewable route candidates. |
| Multi-agent coordinator | `constrained_local_runtime` | 67 | Keep remote coordination blocked and subordinate to route proposals. |
| Human-in-the-loop module | `constrained_local_runtime` | 87 | Make ask-human, defer, and escalation route choices explicit. |

At the V2 review snapshot, the weakest modules were `decision_router` and
`task_decomposition_module`. Both had useful substrates, but both lacked the
unified proposal/read-model layer needed to make the Founder Loop feel
intelligent without quietly granting authority. The ranked queue records the
follow-up lanes that now address those gaps as contract/read-model work; this
artifact remains the audit snapshot, not the post-follow-up rescore.

The memory module remains the strongest module in this review because current
tracked evidence includes Memory Workbench V1, Memory Review decisions,
loop-binding refs, source provenance, recall-only stores, search/workbench
behavior, CLI parity, and safety tests. It is not scored as if
`FCC-MEM-015` through `FCC-MEM-021` are tracked current implementation.

## Ranked Improvement Queue

1. Done: `UAA-P1-089 Top-Level Decision Router Contract`
   - Unifies route decisions across direct answer, memory, tool, human,
     workflow, defer, and escalation.
   - Contract/read-model only.
   - No model calls, tool execution, workflow execution, memory writes, or
     autonomous routing authority.
   - Implemented at `src/ultimate_ai_agent/core/decision_router/contracts.py`
     with verifier and tests.
   - Use a repo-evidence subagent for router substrate comparison and a
     safety/product-language subagent before final hardening.

2. Done: `UAA-P1-090 Task Decomposition Proposal Engine`
   - Produces review-only decomposition proposals from bounded safe inputs.
   - Feeds Plans and Action Inbox as proposals only.
   - No shell/subprocess execution, connector writes, workflow execution, model
     calls, or auto-execution.
   - Implemented at
     `src/ultimate_ai_agent/core/task_decomposition/proposals.py` with Founder
     Loop Plans/Action Inbox read-model projection, UI/CLI inspection parity,
     verifier, and tests.
   - Use a planning-contract subagent and a proposal-only safety subagent.

3. `FCC-LOOP-002 Founder Loop Ergonomics Pass`
   - Improves operator usability across Today, Inbox, Plans, Actions, Memory,
     and Evidence.
   - Uses existing backend truth and blocked-state refs.
   - No new backend authority unless a separate scoped milestone grants it.
   - Use a UX/readability subagent and a product-truth subagent.

4. `FCC-MEM-022 Ranked Retrieval / Recall Tuning`
   - Uses retrieval evidence to improve memory ranking.
   - Lexical, tag, source, review, recency, and ref scoring only.
   - No embeddings, vector DB, provider calls, context injection, or memory
     truth authority.
   - Use a memory-evidence subagent and a retrieval-safety subagent.

## Evidence Anchors

- V1 scorecard: `docs/registry/agent_module_maturity_map.json`
- V1 verifier: `scripts/verify_agent_module_maturity_map.py`
- V2 structured review: `docs/registry/agent_module_maturity_review_v2.json`
- V2 verifier: `scripts/verify_uaa_p1_088_agent_module_maturity_review_v2.py`
- Benchmark evidence: `scripts/benchmark_repo_awareness.py`

## Boundary

This lane is intentionally quiet. It gives the repo a sharper self-portrait
and a ranked build queue, but it does not wire any new runtime path. The next
valuable build is the decision-router contract because it can connect existing
memory, tool, planning, approval, and workflow substrates while preserving the
same proposal-only posture.
