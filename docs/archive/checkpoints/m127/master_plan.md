# Checkpoint M127 Master Plan

Goal: add deterministic, local, review-only Connector Write Dry-Run Planner
contracts bound to M126 Connector Approval Capture records.

Definition of done:

- connector write dry-run request, plan, decision, and no-effect receipt plan
  models
- exact binding to approval ref, connector read-only runtime ref, actor ref,
  user ref, workspace ref, connector scope refs, connector allowlist refs,
  source operation refs, metadata preview refs, audit refs, replay refs, and
  idempotency keys
- allowlisted dry-run operation refs for safe review-only write planning
- denial of approval_test_ refs, denied approvals, rejected approvals, expiry,
  revocation, replay, mismatches, unsafe refs, unallowlisted operations, secret
  metadata, and authority flag mutation
- tests, docs, release notes, static verifier coverage, and Foundation Gate
  coverage

Non-goals: live connector runtime, account auth, network access, credential
handling, raw connector content, full content read, connector write execution,
connector send execution, connector delete execution, connector export,
connector bulk export, attachment download, model call, memory write, context
injection, execution, backend routes, Control Center controls, dependencies,
M128 work, beta release, or production authority.
