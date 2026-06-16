# Checkpoint M127 - Connector Write Dry-Run Planner

Checkpoint M127 adds deterministic local connector write dry-run planner
contracts. The product baseline remains v1.7.2.

Included:

- M127 connector write dry-run request, plan, decision, and no-effect receipt
  plan contracts.
- Exact binding to M126 connector approval capture records and M125 connector
  read-only runtime records.
- Safe write target refs, safe payload summary refs, dry-run operation allowlist
  refs, redaction refs, audit refs, replay refs, and idempotency keys.
- Denial paths for denied/rejected M126 approvals, approval_test_ refs, expiry,
  revocation, replay, binding mismatches, unsafe refs, unallowlisted dry-run
  operations, unsafe metadata, and model-copy authority flag mutation.
- Test coverage, documentation, static verifier coverage, and Foundation Gate
  coverage for the M127 boundary.

M127 adds no live connector runtime, no account auth, no network access, no
credential handling, no raw connector content, no full content read, no
connector write execution, no connector send execution, no connector delete
execution, no connector export, no connector bulk export, no attachment
download, no model call, no memory write, no context injection, no execution,
no backend routes, no Control Center controls, no dependencies, no M128 work,
no beta release, and no production authority.
