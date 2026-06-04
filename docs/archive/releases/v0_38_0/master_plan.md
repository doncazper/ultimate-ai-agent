# v0.38.0 Master Plan

Historical release plan for **v0.38.0 / M34 - Broader File Capability Review**.

This file is archived release evidence. Active docs only may claim current
baseline status after later releases.

## Objective

Freeze the broader file-capability direction before M35 implementation begins.
The release answers which file-review capabilities may be allowed next, in what
order, and under which safety checks.

## Scope

- Create M34 file capability review docs.
- Update active roadmap, version, release, and documentation index files.
- Strengthen documentation integrity checks.
- Strengthen static safety verification.
- Add Foundation Gate criteria and tests for M34.
- Preserve OpenAPI path count and route boundary.

## Non-Goals

- no Safe File Review Workflow Contracts implementation.
- no CCC File Review Surface.
- no Review Approval Capture.
- no context proposals.
- no context injection.
- no raw/full file reads.
- no export/download/copy-raw.
- no file writes/deletes/mutation.
- no backend routes.
- no frontend runtime features.
- no dependencies.
- no production authority.

## Acceptance

The release is acceptable only if the full verifier suite, tests, Foundation
Gate, OpenAPI contract verification, Ruff, frontend checks, safety scans, and
route-count checks pass with M35-M60 still planned/provisional.
