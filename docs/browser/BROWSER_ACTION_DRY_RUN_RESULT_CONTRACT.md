# Browser Action Dry-Run Result Contract

M75 returns a browser action dry-run plan for review only.

The result includes:

- plan refs, actor refs, target refs, and source observation refs.
- safe URL refs.
- dry-run only status.
- deterministic planned steps.
- a receipt plan with no side effects performed.
- stable reason codes.
- a safe message.

The result never includes raw DOM, screenshots, cookies, credentials,
authenticated browser profile data, raw selector dumps, raw browser state,
network traffic, downloaded content, uploaded content, model output, tool output,
memory writes, or context injection payloads.

A valid result must say `plan_valid_for_review=True`, `dry_run_only=True`, and
all execution and authority fields remain false.

M76 remains future.
