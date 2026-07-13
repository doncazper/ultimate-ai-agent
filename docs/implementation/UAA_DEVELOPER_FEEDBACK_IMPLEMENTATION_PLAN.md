# UAA Developer Feedback And Post-Quit Codex Loop

Status: implementation plan and authority-gated execution sequence; no runtime
behavior is added by this document.

Current as of: 2026-07-12.

Program ID: `UAA-DEV-FEEDBACK-001`.

Prompt bundle: `docs/prompts/uaa_developer_feedback/`.

## Outcome

Build a global, macOS-first Developer Mode for the entire UAA application. The
mode is enabled by default until the operator explicitly changes that product
decision. It places Screenshot and Record controls in the UAA window title bar,
captures high-detail structured diagnostics, lets the operator annotate images
and video timestamps, and finalizes a local feedback bundle when UAA quits.

When a finalized bundle contains actionable findings, the launcher starts one
bounded post-quit Codex run. Codex reviews the operator's annotations, the full
approved visual evidence, video keyframes, route transitions, and diagnostic
journal. Codex may add its own evidence-backed observations; its review is not
limited to the operator's notes. The run creates or updates a dedicated
`codex/developer-feedback-*` branch, applies scoped fixes, runs verification,
and leaves a structured result for the next UAA launch. It never pushes directly
to `main`, force-pushes, mutates tags, or auto-merges.

The complete dogfood loop is:

```text
Launch UAA
  -> Developer Mode and extreme structured diagnostics start
  -> use any UAA surface
  -> capture screenshots and/or video manually
  -> annotate regions and timestamps
  -> quit UAA
  -> finalize local feedback bundle
  -> launch exact codex exec handoff after UAA exits
  -> Codex inspects operator notes plus additional observable defects
  -> patch on a dedicated branch
  -> run focused and broad verification
  -> persist a structured patch receipt
  -> show results in UAA Developer Feedback on next launch
```

## Current Repository Truth

- Control Center is currently a React/Vite browser shell.
- The repo has a local unsigned macOS launcher proof, not a native product
  window with a customizable title bar.
- Private-trial safe-ref ledgers and Evidence/Action Inbox read models exist,
  but they do not capture, annotate, or persist screenshots and videos.
- Screenshot capture is explicitly false in several existing runtime preview
  and Computer Use posture contracts. Those contracts must not be broadened.
  Developer Feedback is a separate exact local developer capability.
- `codex exec` is available locally as the supported non-interactive Codex CLI
  surface. It supports a chosen working directory, `workspace-write` sandbox,
  image attachments, JSONL events, and an output schema.
- No existing component implements a post-quit Codex patch handoff.

## Product Decisions

1. Developer Mode is global. It belongs to the UAA application shell, not to
   Messenger, CRM, Calendar, Today, or any other individual surface.
2. Developer Mode defaults to enabled. Capture remains manual; there is no
   background screenshot or video recording.
3. Extreme diagnostics also default to enabled with Developer Mode. "Extreme"
   means high-cardinality structured telemetry and correlated breadcrumbs, not
   raw prompt, response, provider, credential, message-body, or keystroke logs.
4. The final target is the real macOS title bar. A global web-shell strip may be
   used only as a development fallback while the native host is being built.
5. Operator annotations are first-class findings. Codex-discovered findings
   are allowed only when attached to observable evidence and labeled
   `codex_observation` rather than `operator_annotation`.
6. Raw screenshots, videos, keyframes, and diagnostic journals remain in
   ignored `.uaa` local state. Git receives code, tests, safe fixture metadata,
   and hashes only.
7. No end-user privacy review workflow is required for this solo-developer
   mode. Credential, token, recovery-key, and secret leakage guards remain
   mandatory repository hygiene.
8. Quitting with an empty feedback session does not start Codex.
9. Quitting with actionable findings starts at most one idempotent Codex run
   for that finalized bundle.
10. The post-quit process uses an exact argv-only `codex exec` wrapper. It must
    use `--sandbox workspace-write`; dangerous approval/sandbox bypass flags,
    ignored rules, ignored user configuration, and unrestricted shell strings
    are forbidden.

## Architecture

```text
Native UAA macOS shell
  title-bar controls, ScreenCaptureKit, permission state, shutdown signal
        |
        v
DeveloperFeedbackService in Python Core
  sessions, issues, artifact refs, diagnostics, lifecycle, idempotency
        |
        +--> protected local API and CLI parity
        |
        +--> ignored local artifact registry under .uaa
        |
        +--> Developer Feedback Inbox / Evidence / Action Inbox refs
        |
        v
PostQuitCodexHandoff
  exact codex exec argv, images/keyframes, prompt bundle, output schema
        |
        v
Dedicated codex/developer-feedback-* branch
  fixes, tests, structured receipt, optional draft PR
```

### Ownership

- The macOS shell owns title-bar presentation, window-only capture, recording,
  capture permissions, and the signal that the UAA process has exited.
- Python Core owns durable session and finding truth, artifact resolution,
  state transitions, issue taxonomy, diagnostic correlation, handoff
  eligibility, idempotency, receipts, and safe-disable state.
- React owns the annotation and playback interaction, filters, selected issue,
  expanded details, and other presentation state. It cannot mint a completed
  capture, finalized bundle, handoff eligibility, or Codex result.
- The launcher owns the exact post-quit child-process boundary. UAA runtime must
  not run Codex while the application is still using the files being patched.
- Codex owns only the scoped repository task described by the finalized bundle.

## Core Contracts

### DeveloperFeedbackSettings

Required fields:

- `developer_mode_enabled`, default `true`;
- `diagnostic_level`, default `extreme_structured`;
- `screenshot_capture_manual_only`, fixed `true`;
- `video_capture_manual_only`, fixed `true`;
- `post_quit_handoff_enabled`, default `true`;
- `post_quit_patch_branch_prefix`, fixed
  `codex/developer-feedback-`;
- `auto_merge_enabled`, fixed `false`;
- `direct_main_push_enabled`, fixed `false`;
- `dangerous_codex_flags_allowed`, fixed `false`;
- `safe_disable_ref` and `rollback_ref`.

Settings are backend/config-owned. React local state may mirror them but cannot
be their source of truth.

### DeveloperFeedbackSession

Required fields:

- `session_ref`, `app_run_ref`, `started_at`, `finalized_at`;
- `app_version_ref`, `commit_ref`, `branch_ref`;
- `window_ref`, viewport, scale, theme, and active surface refs;
- `capture_refs`, `finding_refs`, `diagnostic_bundle_ref`;
- `state`: `active`, `finalizing`, `ready_for_codex`, `codex_queued`,
  `codex_running`, `patched`, `partially_patched`, `blocked`, `failed`, or
  `resolved`;
- idempotency, receipt, Evidence, rollback, and safe-disable refs.

### DeveloperFeedbackCapture

Common fields:

- `capture_ref`, `capture_kind`, `created_at`;
- `surface_ref`, `route_ref`, `window_ref`, viewport and theme;
- `artifact_ref`, content hash, size bucket, and media metadata;
- `annotation_refs`, `finding_refs`, `diagnostic_window_ref`;
- `capture_state` and failure reason ref.

Screenshot-specific fields include full-window/content/region scope and
normalized annotation geometry. Video-specific fields include duration,
recording state, route transition markers, timestamp-note refs, and keyframe
refs.

### DeveloperFeedbackAnnotation

Required fields:

- `annotation_ref`, `capture_ref`, `ordinal`;
- `annotation_kind`: rectangle, arrow, freehand, pin, crop, blur, or text;
- normalized geometry independent of pixel resolution;
- operator note, expected behavior, observed behavior, category, severity;
- optional component/surface safe refs;
- linked finding ref.

### DeveloperFeedbackFinding

Required fields:

- `finding_ref`, `origin` (`operator_annotation` or `codex_observation`);
- title, bounded description, category, severity, confidence;
- capture, annotation, timestamp, keyframe, route, and diagnostic refs;
- reproduction steps and expected/actual behavior;
- status: `open`, `triaged`, `patching`, `patched`, `verified`, `deferred`,
  `duplicate`, `blocked`, or `wont_fix`;
- patch, test, receipt, Evidence, and PR refs when available.

Codex observations require an evidence ref and must never overwrite or rewrite
the operator's original note.

### DeveloperDiagnosticJournal

The journal is a bounded, structured, correlated event stream. It records:

- app lifecycle and shutdown phases;
- route and surface transitions;
- command/control activation and resulting state transitions;
- React error-boundary events and sanitized exception class/message codes;
- API operation IDs, response classes, latency buckets, retry state, and
  correlation refs;
- render timing, long-task, layout-shift, dropped-frame, memory-pressure, and
  event-loop-lag buckets when supported;
- native window, capture, permission, encoder, and file-flush state;
- backend receipt, policy, approval, idempotency, and safe-disable decisions;
- Matrix or connector event refs and state transitions without raw message
  bodies or credentials;
- Git/patch/test command refs and bounded result summaries for the Codex phase.

The journal must not become a keylogger or raw payload recorder. Passwords,
tokens, recovery material, raw prompts, raw responses, provider payloads, raw
message bodies, environment dumps, full raw console logs, and user-specific
absolute paths remain denied.

## Local Artifact Layout

All runtime artifacts live under an ignored root:

```text
.uaa/developer-feedback/
  registry.json
  sessions/<opaque-session-id>/
    bundle.json
    captures/
    videos/
    keyframes/
    annotations/
    diagnostics/
    codex-input/
    codex-output/
```

Manifests use opaque artifact refs and relative artifact names. Durable docs,
Evidence, and receipts contain refs, hashes, state, bounded summaries, and
counts only. Artifact resolution to a filesystem path happens transiently
through an exact local resolver.

## Global Title-Bar Experience

When Developer Mode is enabled, the UAA window shows:

- a visible `DEV` state indicator;
- Screenshot button;
- Record/Stop button with unmistakable active state;
- active finding count;
- open Developer Feedback Inbox button;
- End Session / Prepare for Codex command.

Screenshot supports the whole UAA window, content only, or selected region.
The capture controls may hide for one frame by default, with an explicit option
to include UAA chrome when debugging the shell itself.

The annotation editor supports numbered pins, rectangle, arrow, freehand,
text, crop, and blur. Each markup can have its own note, category, severity,
expected behavior, and observed behavior.

Video records the UAA window only by default. It supports a pre-recording
description, a post-recording summary, route-transition markers, timestamped
notes, and generated keyframes for every note. Microphone and system audio are
off by default unless a later explicit setting changes them.

## Feedback Inbox

The global Developer Feedback workspace groups findings by:

- session;
- surface and route;
- operator annotation versus Codex observation;
- screenshot versus video versus diagnostic-only;
- severity and category;
- open, patching, patched, verified, deferred, blocked, or failed state;
- patch branch, tests, and draft PR.

Every card shows the source evidence, operator wording, Codex analysis,
proposed/actual fix, verification, and next safe action without reducing the
primary experience to raw JSON.

## Shutdown And Codex Handoff

The app process finalizes captures and the diagnostic journal, fsyncs the
bundle, records a finalization receipt, and exits. Only after confirmed process
exit may the launcher evaluate the handoff.

Eligibility requires:

- finalized bundle;
- at least one open finding or diagnostic failure candidate;
- stable content hash and artifact registry;
- no active recorder or incomplete file flush;
- clean idempotency state;
- configured Codex authentication;
- safe-disable not active;
- no concurrent handoff for the same bundle;
- a usable Git repository.

The exact command shape is based on the supported local Codex CLI:

```text
codex exec
  --cd <workspace>
  --sandbox workspace-write
  --json
  --output-schema <developer-feedback-result-schema>
  --output-last-message <result-summary-file>
  --image <approved-screenshot-or-keyframes>...
  -
```

The prompt is provided on standard input from a generated, bounded handoff
document. The wrapper must not use `--dangerously-bypass-approvals-and-sandbox`,
`--dangerously-bypass-hook-trust`, `--ignore-rules`, `--ignore-user-config`,
`--skip-git-repo-check`, `danger-full-access`, or a shell command string.

Videos are represented to the initial Codex run through annotated keyframes,
timestamp notes, media metadata, and the diagnostic timeline. A later exact
local video-inspection adapter may expose the file when the running Codex
surface can consume it safely; the first implementation must not pretend that
`codex exec --image` accepts video.

The Codex task must:

1. preserve existing user changes;
2. inspect all operator findings;
3. inspect all supplied screenshots/keyframes and relevant diagnostics for
   additional observable issues;
4. label additional findings `codex_observation` with evidence and confidence;
5. create or reuse the bundle-specific branch;
6. implement only evidence-supported fixes;
7. add regression tests where practical;
8. run focused checks and then the broadest practical repo checks;
9. write a schema-valid result receipt;
10. never force-push, push `main`, mutate tags, or auto-merge.

## CLI And API Parity

Minimum CLI:

```text
uaa developer-feedback status
uaa developer-feedback start-session
uaa developer-feedback inspect-session <session-ref>
uaa developer-feedback list-findings
uaa developer-feedback finalize-session <session-ref>
uaa developer-feedback handoff-status <session-ref>
uaa developer-feedback retry-handoff <session-ref>
uaa developer-feedback resolve-artifact <artifact-ref>
uaa developer-feedback cleanup --session-ref <session-ref>
```

Minimum protected local API:

- read settings and current status;
- start/finalize a session;
- create capture metadata after native capture succeeds;
- create/update annotations and findings;
- append validated structured diagnostics;
- read the Feedback Inbox;
- read handoff and patch result status;
- retry or safe-disable a failed handoff.

Every mutating route requires authentication, idempotency, rate-limit,
side-effect classification, manifest/OpenAPI coverage, exact scope, and tests.

## Delivery Sequence

### Phase 0: contract and authority gate

Accept this program as the exact local developer-feedback lane. Define schemas,
state machines, route classifications, settings defaults, artifact posture,
safe-disable, rollback, and post-quit Codex command boundary. Add no capture or
subprocess runtime yet.

### Phase 1: Python Core, storage, API, and CLI

Implement the backend-owned settings, session, capture, annotation, finding,
diagnostic, artifact-registry, inbox, and handoff-posture contracts with
temporary-repository tests and CLI/API parity.

### Phase 2: native UAA shell and global Developer Mode

Implement or promote the minimal local macOS UAA host needed for a real title
bar and toolbar. Bind it to the existing launcher and Control Center without
moving product authority into SwiftUI. Developer Mode and extreme structured
diagnostics default to enabled.

### Phase 3: screenshot capture and annotation

Implement manual window/content/region capture, artifact registration,
annotation editor, per-markup notes, finding creation, failure recovery, and
visual/accessibility tests.

### Phase 4: video capture, notes, and keyframes

Implement manual recording, stop/finalize state, descriptions, route markers,
timestamp notes, playback, keyframe generation, encoder failure recovery, and
bounded cleanup.

### Phase 5: extreme structured diagnostics

Instrument native shell, React, API client, Python service, and relevant
runtime gateways with a bounded correlated journal. Add crash-recovery and
shutdown-flush proof. Prove denied content does not enter diagnostics.

### Phase 6: Feedback Inbox and evidence binding

Implement the global review workspace, finding taxonomy, operator/Codex origin
labels, Evidence refs, Action Inbox proposal posture, status refresh, CLI
inspection, and readable results.

### Phase 7: post-quit Codex handoff

Implement the launcher-side exact `codex exec` wrapper, bundle prompt builder,
image/keyframe attachment resolution, output schema, JSONL/result capture,
idempotency, concurrency lock, retry, timeout, cancellation, and safe-disable.

### Phase 8: Codex patch workflow

Implement and prove branch creation/reuse, preservation of dirty user work,
evidence-backed operator and Codex findings, focused patches, tests, structured
result receipts, and optional draft PR creation. No direct-main or auto-merge.

### Phase 9: whole-app acceptance and hardening

Run the mechanism across Today, Messenger, CRM, Calendar, Work Board,
Knowledge, Activity & Trust, Settings, and shell chrome. Exercise screenshots,
video, route transitions, extreme diagnostics, shutdown, Codex patching, next-
launch status, failure recovery, and cleanup.

## Acceptance Criteria

The program is usable only when all of the following are proven:

- Developer Mode and extreme structured diagnostics are enabled by default.
- Screenshot and Record controls exist in the global UAA macOS title bar.
- A screenshot can contain multiple independently noted markups.
- A video can contain a description, timestamp notes, route markers, and
  generated keyframes.
- Findings can be categorized, prioritized, filtered, and tracked across
  sessions and surfaces.
- The diagnostic journal correlates UI, native shell, API, backend, capture,
  and shutdown events without forbidden raw content.
- Quitting with no findings starts no Codex run.
- Quitting with actionable findings starts exactly one bounded Codex run after
  the UAA process exits.
- Codex receives the annotations, screenshots/keyframes, diagnostic window,
  and reproduction context.
- Codex may add evidence-backed observations that are visibly distinct from
  operator annotations.
- Codex patches only a dedicated branch, preserves user work, adds tests, and
  writes a structured result.
- The next UAA launch shows patched, partially patched, blocked, failed, and
  verified findings accurately.
- Failures in capture, encoding, flush, Codex auth, Codex execution, tests,
  push, or draft PR creation are recoverable and never reported as success.

## Verification Strategy

- Python contract/state-machine/storage/API/CLI tests.
- TypeScript component, reducer, annotation geometry, route-marker, and inbox
  tests.
- Swift unit tests for shell state, capture lifecycle, permission posture,
  artifact registration, shutdown sequencing, and exact argv construction.
- Local ScreenCaptureKit integration tests using synthetic UAA surfaces.
- Playwright visual tests for Feedback Inbox and annotation UI.
- End-to-end local app tests for screenshot, video, diagnostics, quit, Codex
  handoff, patch receipt, and next-launch status.
- Adversarial tests for duplicate shutdown events, partial video, corrupt
  bundle, stale artifact refs, huge diagnostics, symlink/path escape, malicious
  notes, secret-like values, Codex timeout, failed tests, dirty worktree, and
  concurrent handoffs.
- Required repo checks: documentation integrity, product truth, OpenAPI,
  manifest/route inventory, security/redaction, frontend, macOS build/tests,
  Foundation Gate, and `git diff --check`.

## Explicit Non-Goals

- No background screenshot or video capture.
- No keystroke logging.
- No automatic external upload or telemetry service.
- No direct push to `main`.
- No force-push, tag mutation, or automatic merge.
- No dangerous Codex bypass flags.
- No unrestricted shell command string.
- No production distribution claim, notarization claim, or public beta claim.
- No assumption that video is accepted by the Codex image attachment flag.

## Authoritative Codex Reference

The post-quit lane is based on the installed `codex exec` command and the
official Codex developer-command documentation:

- `https://learn.chatgpt.com/docs/developer-commands#codex-exec`

The implementation must verify the installed CLI help and version during the
phase because supported flags may evolve.
