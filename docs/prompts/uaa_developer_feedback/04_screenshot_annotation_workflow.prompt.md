# Phase 04: Screenshot Capture And Annotation

Implement manual screenshot capture and the complete annotation-to-finding
workflow across the entire UAA window.

Deliver:

1. Window-only screenshot capture from the native UAA shell using current
   supported macOS capture APIs.
2. Capture scopes: complete UAA window, content surface, and selected region.
3. A one-frame option to hide capture controls, plus an explicit option to
   include shell chrome when debugging the title bar.
4. Artifact hashing/registration and backend confirmation before the UI shows
   capture success.
5. Annotation editor with numbered pin, rectangle, arrow, freehand, text,
   crop, and blur.
6. Independent note, expected behavior, observed behavior, category, and
   severity for each markup.
7. Normalized annotation geometry that survives display scale and window-size
   changes.
8. Multiple findings from one screenshot and one finding linked to multiple
   annotations when explicitly grouped.
9. Undo/redo, keyboard controls, focus return, autosave, discard, capture
   failure, storage failure, and interrupted-edit recovery.
10. Feedback Inbox refresh and CLI inspection of capture/finding refs.

No mandatory consent or privacy review UI is required. Secret-like values,
credentials, recovery material, unsafe paths, and attempts to store media in
Git remain blocked.

Verification:

- Swift capture lifecycle and failure tests;
- annotation geometry/reducer/persistence tests;
- artifact integrity, replay, and restart tests;
- frontend/native accessibility and visual tests;
- full-window, content, region, shell-chrome, scaled-display, light/dark, and
  compact-width local capture proof;
- adversarial file, size, hash, annotation, and malformed-note tests.

Exit gate: the operator can capture any UAA surface, add multiple precisely
located and independently described findings, restart, and inspect the same
backend-owned findings.
