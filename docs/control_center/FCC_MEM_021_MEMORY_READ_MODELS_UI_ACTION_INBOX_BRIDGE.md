# FCC-MEM-021 Memory Read Models UI + Proposal Bridge

Status: Implemented as Control Center UI wiring, bounded feedback controls, and
proposal-only Action Inbox bridge. Actual context use remains blocked.

FCC-MEM-021 wires the FCC-MEM-016 through FCC-MEM-020 memory read models into
the Founder Command Center Memory surface and projects memory quality /
maintenance review work into Action Inbox using the existing
`self_heal_recommendation` envelope. It adds visibility and review posture only.
It does not grant memory write, auto-maintenance, context injection, provider,
connector, shell, or production authority.

The lane makes quality issues, proposal-only maintenance, and context manifest
preview state visible without changing memory authority.

## UI Read Models

The Memory Review surface now receives and renders:

| Section | Route | Operator view |
|---|---|---|
| Retrieval Diagnostics | `GET /control-center/memory/retrieval-diagnostics` | candidate counts, included/excluded refs, rank signals, source mix, pressure counts, token estimate, cache key, cache hit/miss, and blocked reason refs |
| Citation Integrity | `GET /control-center/memory/citation-integrity` | valid and blocked citations, failed reasons, proof refs, reviewed/deleted/superseded/forget-request checks |
| Quality Issue Queue | `GET /control-center/memory/quality-issues` | useful/stale/missing/wrong/duplicate/conflict/irrelevant/privacy groups, issue aging, and feedback refs |
| Maintenance Proposals | `GET /control-center/memory/maintenance-runs` | merge, supersede, forget-request, stale, missing-evidence, and citation-repair proposals, ranked and blocked from execution |
| Context Manifest Preview | `GET /control-center/memory/context-manifest` | what would be used, why, exclusions, citations, risk posture, token budget, cache key, expiration, authority flags, and safe-disable refs |

These sections use structured UI cards and lists. Raw JSON is not the primary
operator surface.

## Feedback Controls

Memory quality feedback posts to `POST /control-center/memory/feedback` with an
idempotency key. Supported feedback kinds are:

- `useful`
- `stale`
- `missing`
- `wrong`
- `duplicate`
- `conflict`
- `irrelevant`
- `privacy_concern`

Feedback creates quality issue signals only. It does not write, edit, merge,
supersede, forget, delete, rerank with hidden authority, inject context, or
execute actions.

## Action Inbox Bridge

MEM-018 and MEM-019 outputs feed Action Inbox through the existing
`self_heal_recommendation` envelope with `health_recommendation_kind` set to
`memory_quality_issue`.

The bridge is proposal-only:

- Action Inbox item refs are deterministic and deduped.
- The item uses `proposal_only_no_execution_path`.
- `approve`, `reject`, or `defer` decisions record operator decision receipts
  only.
- Decisions do not merge, supersede, forget, write memory, inject context, run
  maintenance, or execute an action.
- Memory recommendation authority flags remain false.
- Blocked authority refs and safe-disable refs are visible on the item.

The bridge intentionally reuses the `self_heal_recommendation` envelope instead
of adding a new executable action kind.

## Context Boundary

Context manifests remain preview artifacts. FCC-MEM-021 does not add:

- no context injection
- no hidden prompt context
- no model/provider call
- no automatic retrieval execution
- no vector database
- no embedding path
- no auto-maintenance
- no context manifest apply/use button
- no prompt-pack execution

Actual context use requires a separate accepted milestone with exact approval,
receipt, rollback/safe-disable, redaction, citation validation, and Evidence
Timeline proof.

## Verification

Focused coverage:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_mem_021_memory_ui_action_inbox_bridge.py
npm test -- --run src/App.test.tsx
npm run typecheck
PYTHONPATH=src .venv/bin/python scripts/verify_fcc_mem_021_memory_ui_action_inbox_bridge.py
```

These checks prove UI route wiring, bounded feedback controls, Action Inbox
proposal-only behavior, memory proposal decision receipts without memory
mutation, context manifests blocked from actual context use, and absence of
hidden auto-maintenance authority.
