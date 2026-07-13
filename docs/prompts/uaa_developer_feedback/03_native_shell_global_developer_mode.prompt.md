# Phase 03: Native Shell And Global Developer Mode

Implement the minimal local macOS UAA product host needed for a real global
title bar and Developer Mode. This is not a public distribution or production
packaging milestone.

Before editing, inspect the current local launcher, unsigned `.app` proof,
Control Center Vite shell, native SwiftUI deferral docs, and any newer shell
work on integrated `main`. Reuse accepted implementation instead of creating a
competing shell.

Use applicable macOS build, SwiftUI, window-management, AppKit interop, and
test-triage workflows available in the environment.

Deliver:

1. A buildable local macOS app target/package that hosts the first-party UAA
   Control Center and uses the existing Python launcher/service boundary.
2. A real macOS title bar/toolbar containing:
   - visible `DEV` state;
   - Screenshot;
   - Record/Stop;
   - active finding count;
   - open Feedback Inbox;
   - End Session / Prepare for Codex.
3. Backend-bound Developer Mode settings with default `enabled` and extreme
   structured diagnostics default `enabled`.
4. Global behavior across every UAA route and surface. No individual app owns
   the controls.
5. A development fallback in the existing global web shell only when the
   native host is unavailable; label it truthfully and keep the native title
   bar as the acceptance target.
6. Native permission/readiness, shell version, app-run ref, active window ref,
   route/surface bridge, and shutdown lifecycle contracts.
7. Local build/run/debug scripts and safe cleanup without signed/notarized/
   distribution claims.

Rules:

- SwiftUI/AppKit owns window presentation and capture initiation only.
- Python Core remains the owner of settings, sessions, findings, handoff
  eligibility, and receipts.
- Capture is never triggered automatically.
- Do not create a daemon, LaunchAgent, updater, public installer, or broad
  native automation layer.

Verification:

- Swift unit tests for settings binding, toolbar state, route updates, finding
  count, shutdown sequencing, and error states;
- Python launcher/native-host contract tests;
- local macOS build and launch smoke;
- accessibility labels, keyboard navigation, light/dark, compact/fullscreen,
  and multi-window truth tests;
- Control Center frontend tests proving the web fallback is global and
  backend-bound.

Exit gate: a local UAA macOS window launches with global title-bar Developer
Mode controls enabled by default and truthful backend-owned state, without yet
capturing media.
