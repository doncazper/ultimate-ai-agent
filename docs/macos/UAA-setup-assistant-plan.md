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

This slice adds dry-run setup contracts, per-step approval-envelope metadata,
and a read-only Control Center preview. Approval envelopes validate exact
proposed setup action refs, safe approval scope refs, receipt/audit/latency refs,
rollback refs, idempotency refs, stale-state handling, and denied side-effect
flags for review only. They do not authorize or perform installer execution,
signed or notarized installer readiness, public distribution, production
readiness, model downloads, LaunchAgent installation/load/start,
background-service installation/load/start, bridge enablement, provider/model
calls, credential capture, shell/subprocess execution, receipt persistence, audit
persistence, rollback execution, or production authority.

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
5. Model download planning
   - Create a dry-run approval envelope with exact future scope refs.
   - No model URL is fetched and no model file is written.
6. LaunchAgent setup planning
   - Create a dry-run approval envelope that remains blocked until a reviewed
     native packaging milestone exists.
   - No LaunchAgent file, load action, start action, or launch control command is
     available.
7. Local bridge setup planning
   - Create a dry-run approval envelope for disabled-by-default bridge scope.
   - No bridge is enabled, no credential is captured, and no connector write
     occurs.
8. Background-service setup planning
   - Create a dry-run approval envelope that records background-service setup as
     not scoped.
   - No daemon, scheduler, worker, service, or auto-start mechanism is created.
9. Setup questions
   - Planned assistant behavior can answer from setup state and docs only.
   - Model output is advice, never authority.
10. Optional OpenWebUI bridge
   - Disabled by default and explicit approval only.
11. Optional Mattermost Agent Rooms bridge
   - Disabled by default, speak-only by default, explicit room approval only.
12. Approvals
   - Visual shell cannot grant authority.
   - Exact local approval is required before future mutations.
13. Receipts, audit, and latency
   - Every proposed action must have receipt, audit, and latency refs.
   - Raw logs, raw prompts, raw provider payloads, tokens, cookies, and
     credentials must not be persisted.
14. Rollback and uninstall
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
It can use `GET /control-center/setup-assistant/summary` when the local backend
is available; the route returns the existing dry-run setup summary and does not
execute installer actions.

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

- Keep the read-only `/control-center/setup-assistant/summary` route truthful,
  dry-run only, and covered by currentness tests.
- Add bounded setup-log redaction tests before any real log source appears.
- Harden per-step dry-run approval envelopes as validation/review metadata only.
  They may describe future exact approval requirements, but they do not make
  model download, LaunchAgent installation/load/start, bridge enablement,
  background-service installation/load/start, rollback, or installer actions
  available.
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
- Decide whether the next slice should be bounded setup-log redaction tests,
  rollback rehearsal, native SwiftUI scaffold, or additional dry-run approval
  envelope hardening.
