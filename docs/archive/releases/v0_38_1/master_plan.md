# v0.38.1 Master Plan

Historical release plan for **v0.38.1 / M34 hardening - File Capability Review
Boundary Clarity**.

This file is archived release evidence. Active docs only may claim current
baseline status after later releases.

## Objective

Repair M34 active-doc currentness and verifier coverage so v0.38.0 is clearly
recognized as the released M34 Broader File Capability Review baseline while
M35 and later file-review implementation milestones remain future.

## Scope

- Mark active README roadmap status for v0.38.0 / M34 as implemented/released
  planning/docs/verifier-only work.
- Update active M33 redacted-preview docs that still described M34 as future.
- Strengthen documentation integrity checks for stale active M34 labels.
- Strengthen static safety verification for stale active M34 labels.
- Strengthen Foundation Gate coverage for M34 active currentness.
- Add focused regression tests.
- Preserve OpenAPI path count and route boundary.

## Non-Goals

- no Safe File Review Workflow Contracts.
- no File Review Control Center Surface.
- no review approval capture or approval persistence.
- no context proposal.
- no context injection.
- no raw file output, full-file output, or unredacted preview.
- no export/download/copy-raw.
- no memory writes.
- no execution.
- no file writes/deletes/mutation.
- no backend routes.
- no frontend runtime features.
- no dependencies.
- no production authority.

## Acceptance

The release is acceptable only if the full verifier suite, tests, Foundation
Gate, OpenAPI contract verification, Ruff, frontend checks, safety scans, and
route-count checks pass with M35-M60 still planned/provisional.
