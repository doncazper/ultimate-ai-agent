# Memory Health Dashboard

Goal: add Memory health counts and needs-attention ordering.

Counts:
- Pending review.
- Stale.
- Conflicts.
- Duplicates.
- Missing evidence.
- Reviewed recall records.
- Rejected candidates.

Requirements:
- Add a backend-owned health summary to the Workbench read model.
- Add needs-attention ordering.
- Render the summary in `/memory` without implying authority.

Verification:
- Tests for counts and ordering.
