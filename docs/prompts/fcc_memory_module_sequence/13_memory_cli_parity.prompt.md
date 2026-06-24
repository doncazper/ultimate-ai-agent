# CLI Parity

Goal: add repo-local script commands to inspect Memory state.

Commands:
- Inspect Memory Review queue.
- Inspect reviewed records.
- Inspect decision receipts.
- Inspect quality states and health counts.
- Optionally create manual candidate and record lifecycle receipts with
  idempotency, using safe refs only.

Boundaries:
- CLI is an operator inspection/mutation parity surface for approved backend
  contracts, not a separate authority path.

Verification:
- CLI tests or verifier checks for command availability and safe output.
