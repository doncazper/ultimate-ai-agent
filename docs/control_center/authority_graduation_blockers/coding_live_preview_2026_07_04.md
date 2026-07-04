# Coding Live Preview Authority Blocker

Date: 2026-07-04

Lane: Coding Cockpit Prompt 07 Live Preview

## Full-Strength Version

UAA Coding Cockpit should show local dev server status, browser preview,
console errors, screenshot capture, visual regression proof, route checklists,
and mobile/desktop preview evidence with Proof Detail links.

## Repo-Safe Current Version

`GET /control-center/coding/live-preview` and
`scripts/dev/uaa_coding.py inspect-live-preview` expose backend-owned safe refs
only. The model records dev-server status refs, preview URL refs, screenshot
refs, console-error refs, visual-proof refs, route-checklist refs, viewport
refs, proof refs, blocker refs, and promotion-path refs.

No dev server is started or inspected. No browser is opened. No raw URL,
console output, screenshot artifact, browser state, file path, command output,
or private data is persisted.

## Blocked / Needs Authority

- Dev-server status detection.
- Dev-server start/stop.
- Preview URL persistence and redaction.
- Browser observe or preview.
- Browser clicks, forms, auth, cookies, downloads, and uploads.
- Screenshot artifact capture.
- Console capture.
- Visual regression comparison.
- Receipt creation and Proof Detail binding.
- Shell/subprocess execution.

## Exact Promotion Path

Promote only after UAA has:

- exact scope for dev-server status and preview URL refs
- approval binding where runtime observation is not read-only
- safe-disable posture
- idempotency and retry posture
- screenshot and console redaction rules
- receipt and proof contracts
- CLI parity
- frontend truth labels
- focused backend/frontend tests and verifiers

Until then, Trust and `/coding` must keep live preview execution blocked.
