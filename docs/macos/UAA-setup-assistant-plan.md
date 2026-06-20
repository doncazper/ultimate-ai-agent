# UAA macOS Setup Assistant Plan

Status: first foundation slice for review.

## Product Intent

UAA is macOS-first. The first-run experience should feel like a native Setup
Assistant, not a raw terminal script. The user should be able to see setup
progress, inspect bounded terminal-style details, compare local model choices,
ask setup questions in a later reviewed slice, approve important changes, and
see receipt, audit, latency, rollback, and uninstall refs before any local
mutation is allowed.

## Current Slice

This slice adds dry-run setup contracts and a read-only Control Center preview.
It does not add a signed or notarized app bundle, model download, installer
execution, LaunchAgent mutation, background service mutation, provider/model
call, credential capture, shell/subprocess execution, or production authority.

## Flow

1. First launch setup
   - Show local-first posture, setup timeline, and bounded details.
   - No command is executed.
2. Runtime health
   - Inspect existing `/health`, `/version`, `/runtime/readiness`, and
     `/runtime/capability-matrix` refs.
   - No lifecycle controls are exposed.
3. Local model readiness
   - Show `/v1/models` and `/v1/chat/completions` as gated local UAA routes.
   - No prompt probe runs by default.
4. Model selection
   - Present local model classes as recommendation records.
   - Any download or safe-ref import remains approval-gated.
5. Setup questions
   - Planned assistant behavior can answer from setup state and docs only.
   - Model output is advice, never authority.
6. Optional OpenWebUI bridge
   - Disabled by default and explicit approval only.
7. Optional Mattermost Agent Rooms bridge
   - Disabled by default, speak-only by default, explicit room approval only.
8. Approvals
   - Visual shell cannot grant authority.
   - Exact local approval is required before future mutations.
9. Receipts, audit, and latency
   - Every proposed action must have receipt, audit, and latency refs.
   - Raw logs, raw prompts, raw provider payloads, tokens, cookies, and
     credentials must not be persisted.
10. Rollback and uninstall
   - Future model files, LaunchAgents, local config, and bridge state need
     explicit rollback refs before any setup mutation ships.

## Implementation Map

- Core contracts:
  - `src/ultimate_ai_agent/core/macos_setup_assistant/contracts.py`
  - `src/ultimate_ai_agent/core/macos_setup_assistant/planner.py`
- Visual preview:
  - `apps/control-center/src/components/MacOSSetupAssistantPanel.tsx`
  - `apps/control-center/src/routes.tsx`
  - `apps/control-center/src/mocks/controlCenterData.ts`
- Tests:
  - `tests/test_macos_setup_assistant.py`
  - `apps/control-center/src/App.test.tsx`

## Current UI Surface

The current visual surface is the web Control Center because the repo does not
yet contain a native macOS SwiftUI app. The Control Center panel is a product
prototype and review surface for the future native window. It remains
read-only, mock-backed when the local backend is unavailable, and non-authority.

## Native macOS Direction

The next implementation slice should create a small SwiftUI app scaffold only
after the dry-run contract shape is reviewed. Recommended shape:

- `apps/uaa-macos/Package.swift`
- `apps/uaa-macos/Sources/UAASetupAssistant/App/UAASetupAssistantApp.swift`
- `apps/uaa-macos/Sources/UAASetupAssistant/Views/SetupAssistantView.swift`
- `apps/uaa-macos/Sources/UAASetupAssistant/Models/SetupAssistantModels.swift`
- `apps/uaa-macos/Sources/UAASetupAssistant/Services/UAASetupPreviewClient.swift`

The native app should initially read the same dry-run setup plan and should not
execute installer actions. Signing and notarization should wait for a reviewed
distribution slice.

## Hardening Suggestions

- Add a read-only `/control-center/setup-assistant/summary` route after the
  contract is reviewed.
- Add bounded setup-log redaction tests before any real log source appears.
- Add a per-step approval envelope before model download, LaunchAgent, bridge,
  or background-service changes are allowed.
- Add rollback rehearsals before shipping any mutation.
- Add a native SwiftUI visual QA pass once `apps/uaa-macos/` exists.
- Add signing, hardened runtime, and notarization validation only when a real
  distributable artifact exists.

## Morning Review Checklist

- Confirm the Control Center route is truthful and does not imply completed
  setup.
- Confirm all model choices are recommendation classes, not live downloads.
- Confirm every approval-required step has receipt and rollback refs.
- Confirm terminal details are bounded previews and not raw logs.
- Confirm no raw path, credential, token, prompt, transcript, or provider
  payload is stored.
- Decide whether the next slice should be native SwiftUI scaffold, read-only
  backend summary route, or dry-run approval envelope.
