# Phase 02: Work Board UI Interactions

Goal: Make `/work-board` feel like a real UAA-native Kanban cockpit while
keeping durable workflow truth in Python Core.

Required scope:
- Render backend-owned board, columns, cards, proof refs, evidence refs,
  blocked lanes, promotion paths, CLI refs, and route refs.
- Provide board/list/proof views.
- Provide search and priority/authority filters.
- Provide selection/inspection surfaces that visibly update proof/detail state.
- Provide drag/drop and keyboard/card-button move controls as unsaved local
  layout preview only.
- Provide local draft preview only, clearly labeled non-authoritative and
  resettable.
- Provide blocked persistence controls that open proof/blocked-lane detail
  instead of mutating anything.
- Label mock fallback and degraded data as non-authoritative.
- Keep text contained and responsive across desktop and mobile-ish widths.

Non-goals:
- No durable reorder or card create/archive.
- No mutation controls that appear executable.
- No fake success paths.
- No UI-only durable workflow truth.
- No connector, issue tracker, provider, shell, browser, or production authority.

Acceptance:
- All visible safe controls have user-visible outcomes.
- Disabled or blocked controls explain blocked authority and do not mutate.
- Drag/drop, keyboard move, filters, list view, proof view, reset, local draft,
  and blocked-lane buttons are tested.
- Mock fallback is visibly non-authoritative.
