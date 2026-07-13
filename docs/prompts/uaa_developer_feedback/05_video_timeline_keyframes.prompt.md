# Phase 05: Video, Timeline Notes, And Keyframes

Implement manual UAA-window video recording and a Codex-usable review model.

This phase grants no capture authority. Runtime recording requires a separately
accepted exact video-capture capability, current macOS permission, explicit
operator initiation, and a fresh request-scoped PolicyEngine decision; exact
LocalApprovalAuthority validation where required; current AuthorityLease;
capability, adapter, target, session, mission, and run binding; TTL/deadline;
budget; readiness; kill switch; safe-disable; and idempotency/replay evaluation
immediately before recording starts. Missing, unknown, stale, expired, or
mismatched state fails closed with an explicit blocked receipt.

Deliver:

1. Window-only recording using current supported macOS capture APIs.
2. Visible recording state, elapsed time, Stop command, and failure state in
   the global title bar.
3. Pre-recording description: what is being demonstrated and what Codex should
   watch for.
4. Post-recording summary and playback.
5. Automatic route/surface transition markers throughout the recording.
6. Timestamp notes with category, severity, expected/actual behavior, and
   optional duration range.
7. Deterministic keyframe generation for every timestamp note plus bounded
   contextual frames before/after the marker.
8. Artifact refs/hashes for video and keyframes, finalization only after the
   encoder and file flush complete, and crash/partial-file recovery.
9. Pause/resume if supported reliably; otherwise label it unavailable rather
   than faking state.
10. Microphone/system audio settings default off and remain separately
    configurable later.

Codex handoff compatibility:

- Do not pass video files through `codex exec --image`.
- Supply annotated keyframes through image attachments only after a separate
  exact destination/content-disclosure decision binds artifact hashes,
  redaction/OCR review, bounded content, and explicit operator confirmation.
- Supply timestamp/route/diagnostic metadata through the bundle prompt only
  when the same disclosure decision permits those exact fields; otherwise use
  content-free safe refs.
- Preserve the local video artifact ref for later manual or exact-adapter
  inspection.

Verification:

- recording start/stop/failure/timeout/disk-full/interruption tests;
- timestamp, duration, route marker, and keyframe determinism tests;
- playback and note editor tests;
- artifact hash/finalization/recovery tests;
- multi-route local video proof;
- bounded duration, size, keyframe count, and cleanup tests.

Exit gate: when the exact video-capture lane is separately accepted and passes
fresh evaluation, the operator can record a cross-surface UAA workflow,
explain it, mark multiple timestamps, and produce stable keyframes and findings
suitable for Codex inspection. Otherwise the phase must report the capture
lane blocked without claiming recording proof.
