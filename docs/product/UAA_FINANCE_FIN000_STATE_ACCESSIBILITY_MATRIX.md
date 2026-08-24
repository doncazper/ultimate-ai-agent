# FIN-000 State And Accessibility Review Matrix

Status: planning contract; independent accessibility review pending

Program: `FIN-000`

Candidate pack: `render-pack-ref:finance-compliance-v1`

Static renders can demonstrate language and layout intent, but cannot prove
keyboard behavior, focus management, semantic ordering, zoom reflow, contrast,
or reduced-motion behavior. This matrix defines what an independent reviewer
must find in the design contract and what later implementation must test.

## State Contract

| State | Required presentation | Recovery or next step | Canonical owner |
|---|---|---|---|
| Empty / first run | Explain that no book or source exists; do not show fake metrics | Create a local book or review a manual/file-import proposal | Finance book/source owner |
| Loading | Preserve page and table geometry; name the bounded operation | Wait, cancel if supported, or inspect last known safe state | Owning read model |
| Stale | Show source and exact as-of posture near the value | Refresh only through a separately authorized read lane | Source/read receipt |
| Offline / disconnected | Distinguish local data from unavailable external freshness | Continue local review or inspect connection requirements | Adapter readiness record |
| Conflict | Show both candidate and current revision without silent overwrite | Compare, defer, or propose a new revision | Canonical Finance object |
| Blocked | State the unavailable authority and consequence | Show the exact safe prerequisite; never present a fake action | Policy/approval boundary |
| Error / partial | Identify affected scope without raw payloads or logs | Retry an idempotent read, restore, or inspect a safe evidence ref | Operation receipt |
| Recovery / restore | Keep staged, verified, failed, and rolled-back states separate | Verify integrity before promotion to current truth | Protected storage record |

## Accessibility Contract

| Concern | Review requirement | Later implementation proof |
|---|---|---|
| Keyboard order | Reading and action order follows the visible workflow; inspector opening does not lose queue position | Automated keyboard navigation plus manual full-page pass |
| Focus entry/return | Dialogs and inspectors name their purpose; close/cancel returns focus to the invoking row or control | Focus assertions for open, commit, cancel, error, and restore paths |
| Contrast | Text, icons, focus rings, disabled controls, and every status meet applicable contrast; state is never color-only | Token audit and rendered contrast check |
| 200% zoom | Primary workflow remains usable without clipped actions or horizontal page scrolling; dense tables may use an explicitly labeled contained scroller | Browser/UI zoom test at desktop and narrow widths |
| Reduced motion | No information depends on animation; progress and transitions have a non-motion equivalent | Reduced-motion test and manual observation |
| Screen-reader order | Page title, posture, next action, table/list rows, selected object, inspector details, consequences, and evidence refs form a coherent sequence | Semantic-role/name/state assertions and manual screen-reader pass |
| Errors and recovery | Error summary is announced; invalid fields are associated with instructions; retry does not erase reviewed context | Accessibility-tree and recovery-flow tests |
| Narrow layout | Controls remain named and reachable; inspector content follows the selected record rather than visually overlapping it | Narrow viewport keyboard and screen-reader checks |

## Acceptance Boundary

The accessibility reviewer may accept this planning specification or request
render/contract changes. That decision does not certify an implementation.
FIN-001 and later UI work must turn every “later implementation proof” above
into focused automated and manual verification before claiming the behavior.
