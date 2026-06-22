# UAA-P1-087 Private Operator Boot And UI Trial Sequence

Status: planned docs-only sequencing for the post-UAA-P1-086 private trial lane.

This document splits UAA-P1-087 into ordered sub-milestones so the milestone
conveyor can continue after the API boundary hardening lane without mistaking
later native app work for the first boot-readiness step.

## Sequence

1. `UAA-P1-087.1` Local Launcher Dual-Surface Boot Readiness is implemented.
   The existing repo-local launcher and clickable macOS `.command` path now
   boot the backend, Control Center, and OpenWebUI local shell with clear
   readiness, stop, log-ref, and blocked-state guidance. Control Center opens
   as the first-party product surface; OpenWebUI may open beside it as the
   secondary local chat shell when prerequisites are ready.
2. `UAA-P1-087.2` In-Person Private Operator UI Functional Tuning.
   Use the real local boot flow to run hands-on founder testing and record
   friction, manual smoke evidence, UI/copy tasks, blocked-state confusion,
   Today/Actions/Memory/Evidence/Chat handoff issues, and CRM-lite follow-up
   gaps.
3. `UAA-P1-087.3` Native SwiftUI Boot Cockpit Planning And Source-Only Scaffold.
   After the `.command` boot contract is proven, plan and then implement a
   source-only native SwiftUI macOS cockpit over the same fixed launcher
   contracts. This is not a signed installer, LaunchAgent, daemon, public
   distribution artifact, OpenWebUI plugin, or product authority surface.

## Authority Boundary

Allowed by this docs-only sequence:

- milestone planning and conveyor ordering.
- later use of existing repo-local launcher commands for local/private boot.
- later use of the existing approval-bound OpenWebUI pinned-image pull path.
- local/private manual testing evidence and UI tuning tasks.

Not allowed by this docs-only sequence:

- new backend routes, OpenAPI operations, middleware, auth, CORS, headers, rate
  limits, or runtime authority.
- Docker installation, arbitrary shell execution, Homebrew installation,
  LaunchAgent creation, background daemon setup, signing, notarization, public
  distribution, or production readiness claims.
- OpenWebUI plugin, function, pipeline, admin mutation, product-state
  ownership, connector writes, memory writes, provider/model authority, Code
  apply, or hidden automation.

## Conveyor Guidance

After `UAA-P1-086`, run `UAA-P1-087` through these sub-milestones in order.
Do not jump to `UAA-P1-087.3` until `UAA-P1-087.1` has proven the launcher
contract and `UAA-P1-087.2` has produced usable private-trial findings.
The next planned productization conveyor is `FCC-V1-000` through
`FCC-V1-007`, recorded in
`docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`, so private boot/UI trial
work should feed the release surface manifest, backend-owned decisions,
durable receipts, Evidence Timeline updates, and proof-lane promotion rather
than broad P2/provider, packaging, public distribution, or commercialization
expansion.

If a sub-milestone is too large, split it as `UAA-P1-087.1a`,
`UAA-P1-087.1b`, and so on, but keep the `.command`/launcher boot path before
native SwiftUI.
