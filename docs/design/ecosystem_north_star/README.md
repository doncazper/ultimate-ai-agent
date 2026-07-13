# ECO-000 Coherent App Ecosystem North-Star Concepts

These assets are reviewed design concepts, not implementation evidence. They
add no route, control, storage, connector, model call, authority, packaging, or
release claim. All displayed records are deterministic synthetic examples.

The concepts follow the accepted Control Center shell and design language.
Calendar, Tasks, Boards, Inbox, Organizer, global search, and ChangeSet entries
are planned future destinations under ADR-0061. Existing routes remain the
compatibility baseline until separately migrated.

## Review result

- Twelve required concepts were generated and inspected for shell consistency,
  readable hierarchy, synthetic data, complete concept controls, privacy and
  authority visibility, traceable IDs, and non-shipping labels.
- Status is `reviewed design draft`, not `accepted implementation`.
- The desktop Today, narrow Today, and wallboard assets received direct visual
  inspection; the generator and manifest provide deterministic coverage for
  the remaining concepts.
- Browser interaction and pixel-regression acceptance are blocked because these
  are SVG planning assets, not wired frontend routes.

Use:

```bash
.venv/bin/python scripts/design/generate_eco_000_north_star_renders.py
```

Canonical supporting artifacts:

- `RENDER_MANIFEST.md` and `render_manifest.json`
- `SURFACE_COVERAGE.md`
- `RENDER_VARIATION_MATRIX.md`
- `RENDER_BRIEFS.md`
- `docs/quality/ECO_000_QUALITY_BUDGETS.md`
