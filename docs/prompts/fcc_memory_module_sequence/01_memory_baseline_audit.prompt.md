# Memory Baseline Audit

Goal: verify current Phase 1-6.1 Memory behavior, routes, docs, tests, CLI, and
Control Center UI before implementing `FCC-MEM-001`.

Tasks:
- Inspect current `/memory`, Today, Actions, Briefing, and Evidence read models.
- Identify which UI elements are backend-owned state versus proof/read-only
  posture or mock fallback.
- Inspect routes: review, accept/correct/reject, L1/L2/L3, context packs,
  context-pack action proposals, Evidence Timeline, Today, Actions, Briefing.
- Inspect docs and tests covering Phases 1-6.1.
- Produce a gap list for `/memory`, Today, Actions, Briefing, and Evidence.

Output:
- `docs/control_center/FCC_MEM_001_MEMORY_BASELINE_AUDIT.md`
- The audit must distinguish implemented, partial, planned, blocked, mock-only,
  and intentionally out of scope.

Verification:
- Documentation integrity.
- Product truth scan.
- Focused verifier added later by prompt 14.
