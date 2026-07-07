# UAA Hermes Runtime Voice Media Posture

Status: Phase 41 repo-safe Python Core read model.
Route: `GET /api/runtime/voice-media-posture`
CLI: `scripts/dev/uaa_runtime.py inspect-voice-media-posture`
Core: `src/ultimate_ai_agent/core/runtime_gateway/voice_media_posture.py`

## Full-Strength

UAA should eventually supervise voice, image, TTS, and media lanes across local
and delegated runtimes. A mature lane would expose device permission, local-only
options, provider boundaries, redaction, consent, receipts, proof, retention,
and safe-disable controls before any microphone, camera, media generation,
upload, or external delivery action is possible.

## Repo-Safe

The current implementation is a Python Core read model and CLI inspection path
only. The read model is now bound to AuthorityState as
`lane-ref:runtime-voice-media-posture-read-model`, which evaluates as
Workspace/read under the active read-only lease. That allowed decision applies
only to inspecting safe lane labels, consent refs, redaction refs, receipt refs,
proof refs, safe-disable refs, blocked refs, and unsupported adapter refs.

- voice input posture
- speech-to-text posture
- text-to-speech posture
- image input posture
- image generation posture
- media upload posture
- external media delivery posture

Every lane is marked blocked until authority. The read model includes consent,
device permission, redaction, receipt, proof, safe-disable, blocked authority,
authority path, and next-safe-action refs. Control Center is not granted any
media authority by this phase.

## AuthorityState

The safe inspection capability is governed by:

- route: `GET /api/runtime/voice-media-posture`
- CLI: `repo-local-command:uaa-runtime-inspect-voice-media-posture`
- AuthorityState route: `GET /api/runtime/authority-state`
- AuthorityState CLI: `repo-local-command:uaa-runtime-inspect-authority-state`
- mapping ref: `lane-ref:runtime-voice-media-posture-read-model`
- domain/capability: `workspace/read`
- required mode: `read_only`

Known authority inside the active lease allows only posture inspection. The
following adapters remain unsupported and do not become executable from this
read model: microphone, camera, upload, transcription, generation, provider
call, and external delivery adapters.

## Blocked / Needs Authority

The following remain blocked:

- microphone access
- camera access
- file or media upload
- transcription
- voice or image generation
- provider calls
- external media delivery
- raw media persistence
- Control Center authority minting

## Exact Authority Path

Execution authority requires a later, exact AuthorityLease-governed adapter lane
for each media action. That later lane must prove:

1. exact device permission and operator consent
2. local-only option or explicitly governed provider boundary
3. redaction and retention policy
4. receipt envelope and proof binding
5. safe-disable and revoke posture
6. CLI/API/Core parity before Control Center initiation
7. verifier coverage for blocked raw media, provider payload, path, account,
   device, credential, and secret-like persistence

Planning text and read-model visibility do not grant voice/media runtime
authority.
