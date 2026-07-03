# Authority Lane 10: Background Worker / Scheduler

Goal: Add time-based or background work only after the same foreground action is
proven.

Allowed next promotion: Level 4 limited automation for one exact level-3 action.

Scope:

- Schedule only an already proven foreground action.
- Explicit operator setup.
- Pause/cancel/revoke.
- Run observability.
- Approval renewal/expiry posture.
- Receipts for each run.

Still blocked:

- Open-ended autonomy.
- Self-selected tasks.
- Background provider calls.
- Background connector sends.
- Hidden loops.

Promotion condition:

One exact action can run later with pause/cancel/revoke, observability, renewal,
and blocked-state receipts.

Tests/verifiers:

- worker contract tests.
- scheduler tests.
- approval renewal/expiry tests.
- pause/cancel/revoke tests.
- run observability tests.

If blocked:

Generate an unblock prompt for the missing foreground proof, scheduler contract,
approval renewal, observability, or revocation control.
