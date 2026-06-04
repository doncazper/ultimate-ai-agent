# v0.38.2 Master Plan

Historical release plan for **v0.38.2 / M34 hardening - Current Baseline Label
and Documentation Integrity Repair**.

This file is archived release evidence. Active docs only may claim current
baseline status after later releases.

## Objective

Repair active M34 current-baseline labels after the v0.38.1 Yellow review so
active docs, version files, release metadata, documentation-integrity checks,
static verification, and Foundation Gate coverage agree on v0.38.2.

## Scope

- Bump version metadata to v0.38.2.
- Update active docs that name the current active baseline or current-through
  release.
- Add documentation-integrity coverage that compares active current-baseline
  labels against the version files.
- Add focused regression tests for stale active current-baseline labels.
- Update release notes, archived release packet files, and Foundation Gate plan.
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
- no M35 implementation.
- no production authority.

## Acceptance

The release is acceptable only if active docs identify v0.38.2 as the current
active baseline, stale v0.38.0/v0.38.1 current-baseline labels fail
documentation integrity checks, full validation passes, OpenAPI remains
unchanged, and M35-M60 remain planned/provisional.
