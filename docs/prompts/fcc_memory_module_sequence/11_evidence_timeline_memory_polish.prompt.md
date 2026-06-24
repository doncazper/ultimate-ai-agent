# Evidence Timeline Memory Polish

Goal: every memory decision event answers the operator-history questions.

Required answers:
- What was reviewed.
- What changed.
- What did not change.
- What remains blocked.
- What receipt was created.

Scope:
- Update Evidence Timeline memory decision events for accept, correct, reject,
  defer, merge, supersede, and forget_request.
- Preserve safe refs only.

Verification:
- Evidence Timeline tests assert the five answers for every decision family.
