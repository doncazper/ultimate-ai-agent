# UAA Developer Feedback Prompt Bundle

Status: stored end-to-end implementation prompts for
`UAA-DEV-FEEDBACK-001`.

These prompts implement the global UAA Developer Mode, screenshot and video
annotation, extreme structured diagnostics, Feedback Inbox, post-quit Codex
handoff, evidence-backed patching, and whole-app acceptance described in
`docs/implementation/UAA_DEVELOPER_FEEDBACK_IMPLEMENTATION_PLAN.md`.

The prompts are operator-run development instructions, not runtime system
prompts. The documents themselves grant no capture, native window,
subprocess, Codex, Git push, or external authority.

## Required Defaults

- Developer Mode: enabled.
- Extreme structured diagnostics: enabled.
- Screenshot capture: manual only.
- Video capture: manual only.
- Post-quit Codex handoff: enabled when a finalized session contains
  actionable findings.
- Direct push to `main`: disabled.
- Auto-merge: disabled.
- Dangerous Codex bypass flags: disabled.

These defaults remain binding until the operator explicitly changes them.

## Prompt Order

1. `01_contract_authority_and_schema.prompt.md`
2. `02_core_storage_api_cli.prompt.md`
3. `03_native_shell_global_developer_mode.prompt.md`
4. `04_screenshot_annotation_workflow.prompt.md`
5. `05_video_timeline_keyframes.prompt.md`
6. `06_extreme_diagnostics_and_feedback_inbox.prompt.md`
7. `07_post_quit_codex_handoff.prompt.md`
8. `08_codex_patch_workflow.prompt.md`
9. `09_whole_app_acceptance_hardening.prompt.md`

Use `00_execute_all_review_verify_harden.prompt.md` only when the operator wants
one persistent run through the entire sequence. Each phase should still land as
its own focused commit or PR checkpoint where practical.

## Authority Boundary

This bundle promotes only the exact local developer-feedback capabilities
defined in the implementation plan. It does not grant background capture,
keystroke logging, unrestricted shell execution, provider/model routing inside
UAA, connector writes, external uploads, direct-main pushes, force-pushes,
tag mutation, automatic merge, public distribution, or production authority.

The post-quit Codex lane must invoke the installed supported `codex exec`
surface with an exact argv list and `workspace-write` sandbox. It must never use
dangerous approval/sandbox bypass flags.

## Definition Of Done

The bundle is complete only when a real local UAA app run can:

1. capture and annotate screenshots across the entire UAA shell;
2. capture video with descriptions, timestamp notes, route markers, and
   keyframes;
3. correlate captures with extreme structured diagnostic events;
4. track operator annotations and separate Codex observations in a global
   Feedback Inbox;
5. finalize the session during shutdown;
6. start exactly one bounded Codex run after the app exits;
7. create scoped fixes on a dedicated branch with tests and a structured
   result;
8. show the result accurately on the next UAA launch.
