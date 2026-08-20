# UAA macOS Setup Assistant Plan

Status: Queue03 Phase03 lifecycle foundation implemented; live activation
blocked by authority.

## Product Intent

UAA is macOS-first. The first-run experience should feel like a native Setup
Assistant, not a raw terminal script. The user should be able to see setup
progress, inspect bounded terminal-style details, compare local model choices,
ask setup questions in a later reviewed slice, approve important changes, and
see receipt, audit, latency, rollback, and uninstall refs before any local
mutation is allowed.

## Current Slice

This slice adds dry-run setup contracts, approval-envelope metadata for every
approval-required setup step, a typed lifecycle foundation, and a read-only
Control Center preview. The lifecycle foundation names every required state
from `prerequisites` through `failed`, the shared Python Core service, the CLI,
API, and Control Center surfaces, the complete future health-proof envelope,
and exact receipt, idempotency, rollback, and safe-disable refs.

`plan`, `status`, and `receipts` are safe-ref-only inspection commands.
`install`, `verify`, `repair`, `stop`, and `rollback` return
`blocked_by_authority` and perform no file, process, credential, network, or
subprocess action. Approval envelopes validate exact proposed setup action
refs, safe approval scope refs, receipt/audit/latency refs, rollback refs,
idempotency refs, stale-state handling, and denied side-effect flags for review
only. They do not authorize or perform installer execution, signed or notarized
installer readiness, public distribution, production readiness, model
selection persistence, model downloads, LaunchAgent installation/load/start,
background-service installation/load/start, bridge enablement, provider/model
calls, credential capture, shell/subprocess execution, receipt persistence,
audit persistence, rollback execution, or production authority.

Queue-of-Record V2 Q07 hardens that preview with backend-owned readiness
diagnostics that explicitly separate `ready`, `missing`, and `blocked` setup
posture. It also corrects rollback language: rollback contract refs are defined,
but approval alone cannot make rollback executable. Rollback execution,
rehearsal proof, and restore proof remain false and visibly blocked pending a
separately accepted exact mutation lane. Diagnostics are safe-ref-only and do
not run live probes or change setup state.

The separate M167 CLI setup mutation lanes remain parity contracts beneath any
future macOS shell: they show the exact preview and require the exact
interactive operator confirmation. Deprecated unattended `--yes` and setup
token inputs are fail-closed and cannot be submitted by the Setup Assistant.
The read-only Control Center preview neither mints nor consumes setup approval
tokens.

## Queue03 Phase03 Authority-Blocked Lifecycle Foundation

Implemented:

- typed lifecycle states: prerequisites, ready to install, approval required,
  installing, installed, starting, healthy, degraded, repairable, stopping,
  rollback required, rolled back, and failed;
- typed operation contracts for plan, status, install, verify, repair, stop,
  rollback, and receipts;
- one Python Core lifecycle builder shared by the Setup API summary and
  `scripts/dev/uaa_setup_lifecycle.py`;
- human-readable CLI output plus safe-ref JSON inspection;
- Control Center lifecycle, health-check, authority, receipt, rollback, and
  safe-disable visibility without execution buttons; and
- read-only readiness diagnostics for the implemented plan, missing native app,
  blocked live health proof, and blocked rollback proof;
- required future health proof for exact process identity, API
  manifest/version, loopback bind, Control Center compatibility, and absence of
  forbidden broad authority.

Blocked by authority:

- installation or mutation of any local artifact;
- app, service, or LaunchAgent process launch/control;
- live health or readiness probes;
- repair, stop, and rollback execution;
- credential writes; and
- any claim that the unsigned package proof is installed, healthy,
  distribution-ready, or production-ready.

The blocking prerequisite is
`authority-prerequisite:macos-setup-exact-lifecycle`. It must be replaced by a
separate accepted mutation milestone with current PolicyEngine,
LocalApprovalAuthority, AuthorityLease, exact artifact/process scope,
idempotency, interruption recovery, rollback, safe-disable, redaction, and
durable receipt proof before any blocked operation can be promoted.

## Beta 02 Setup Assistant And Local Package Hardening

Full-strength version:
UAA first run should guide a local operator from setup posture into the daily
loop: Start Here, Today, Action Inbox, exact local task receipt, Evidence,
Proof, Memory, Trust, and Settings. A future native macOS shell can make this
feel like an Apple-grade local app, but the durable truth still belongs to the
Python Agent Core and inspected local receipts.

Repo-safe version:
The current lane exposes backend-owned first-run loop refs and local package
proof refs in the setup plan, then renders them in Control Center. The local
package proof is available as local-only evidence: Docker/local-runtime loopback
proof plus an unsigned `.app` bundle artifact proof that wraps
`./scripts/dev/uaa trial-boot`. The `.app` verifier checks bundle structure,
Info.plist posture, launcher command, and boundary text without launching the
app. The runtime packaging proof generates ignored local secret material with
`token_urlsafe`, applies `chmod(0o600)`, and keeps proof summaries safe-ref only.

Blocked / needs authority:
Signing, notarization, installer side effects, LaunchAgent or daemon changes,
model downloads, bridge enablement, provider calls, browser automation,
arbitrary shell/subprocess execution from UAA runtime, public distribution,
production readiness, and production authority remain blocked. The Control
Center route and UI are read-only setup preview surfaces.

Exact promotion path:
1. Keep setup proof refs backend-owned and covered by
   `scripts/verify_beta_02_setup_assistant_local_package.py`.
2. Add a local rehearsal receipt that proves Start Here -> Today -> Action
   Inbox -> receipt -> Evidence -> Proof -> Memory -> Trust without public or
   production claims.
3. Add operator review notes for native-shell language, blocked state labels,
   and package-proof copy.
4. Add explicit approval binding, idempotency, rollback, safe-disable,
   redaction, CLI parity, and proof refs before any setup mutation is promoted.

First-run operator path:
1. Run setup doctor or inspect the setup route.
2. Launch the local Control Center or private trial boot.
3. Confirm backend health and Founder Loop refs.
4. Optionally generate local unsigned app proof as evidence.
5. Open Proof and Trust refs before treating setup as complete.

Local package proof labels:
- Implemented: Control Center setup preview, backend first-run loop refs,
  local loopback runtime packaging proof, and local unsigned `.app` artifact
  proof.
- Planned: native SwiftUI shell that reads the same backend plan.
- Blocked: signed app, notarization, installer, auto-update, LaunchAgent,
  daemon, public distribution, and production authority.

## Flow

1. First launch setup
   - Show local-first posture, setup timeline, and bounded details.
   - No command is executed.
2. Runtime health
   - Inspect existing `/health`, `/version`, `/runtime/readiness`, and
     `/runtime/capability-matrix` refs.
   - Typed lifecycle and health-proof contracts are visible, but no execution
     control or live probe is exposed.
3. Local model readiness
   - Show `/v1/models` and `/v1/chat/completions` as gated local UAA routes.
   - No prompt probe runs by default.
4. Model selection
   - Present local model classes as recommendation records.
   - Create a dry-run approval envelope with exact future model-choice scope
     refs.
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
   - Create a dry-run approval envelope for future bridge review.
11. Optional Mattermost Agent Rooms bridge
   - Disabled by default, speak-only by default, explicit room approval only.
   - Create a dry-run approval envelope for future room bridge review.
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
  - `src/ultimate_ai_agent/core/macos_setup_assistant/lifecycle.py`
  - `src/ultimate_ai_agent/core/macos_setup_assistant/planner.py`
- CLI parity:
  - `scripts/dev/uaa_setup_lifecycle.py`
- Visual preview:
  - `apps/control-center/src/components/MacOSSetupAssistantPanel.tsx`
  - `apps/control-center/src/routes.tsx`
  - `apps/control-center/src/mocks/controlCenterData.ts`
- Tests:
  - `tests/test_macos_setup_assistant.py`
  - `tests/test_macos_setup_lifecycle.py`
  - `apps/control-center/src/App.test.tsx`

## Current UI Surface

The current visual surface is the web Control Center because the repo does not
yet contain a native macOS SwiftUI app. The Control Center panel is a product
prototype and review surface for the future native window. It remains
read-only, mock-backed when the local backend is unavailable, and non-authority.
It can use `GET /control-center/setup-assistant/summary` when the local backend
is available; the route returns the dry-run setup summary and embedded typed
lifecycle contract and does not execute installer, probe, process, repair,
stop, or rollback actions.

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
- Keep per-step dry-run approval envelopes as validation/review metadata only.
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
