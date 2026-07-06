# UAA Hermes Runtime Voice Media Posture

Status: Phase 41 repo-safe Python Core read model.  
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
only:

- voice input posture
- speech-to-text posture
- text-to-speech posture
- image input posture
- image generation posture
- media upload posture
- external media delivery posture

Every lane is marked blocked until authority. The read model includes consent,
device permission, redaction, receipt, proof, safe-disable, blocked authority,
promotion path, and next-safe-action refs. Control Center is not granted any
media authority by this phase.

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

## Exact Promotion Path

Promotion requires:

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
