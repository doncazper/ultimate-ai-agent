# Control Center Render Review

This local-only gallery presents one Control Center design render at a time for
critique and iteration. Review status and notes are presentation-only data kept
in browser `localStorage`; they do not change application state or grant
runtime authority.

Run from the repository root:

```bash
.venv/bin/python scripts/dev/serve_control_center_render_review.py
```

Open `http://127.0.0.1:4179/render-review/`.

The gallery supports:

- target, Messenger-client, and legacy render sets;
- search and keyboard previous/next navigation;
- side-by-side current/previous comparison for revised surfaces;
- Draft, Needs revision, Approved, and Superseded states;
- per-render-version critique notes;
- version history for iterative replacements; and
- JSON export/import so review notes can be preserved outside browser storage.

Add a new iteration by copying the render into a versioned render folder, adding
the new image to the surface's `versions` array in `renders.json`, and changing
the surface-level `image` to the current version. Never overwrite an approved
version.
