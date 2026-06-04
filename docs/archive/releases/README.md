# Archived Release Packets

Status: active archive index
Current through: v0.37.2
Purpose: Locate historical release import and master-plan packets.

Historical release import and master-plan packets live under versioned folders:

```text
docs/archive/releases/vX_Y_Z/README_IMPORT.md
docs/archive/releases/vX_Y_Z/master_plan.md
```

Active release notes remain under `docs/release_notes/`. Active implementation
and Foundation Gate plans remain under `docs/implementation/` while the project
keeps that convention.

New root release artifacts should be avoided. Prefer versioned archive folders
for release packets, and keep the root limited to current entrypoints such as
`README.md`, `VERSION.md`, `AGENTS.md`, `pyproject.toml`, `src/`, `tests/`,
`scripts/`, `docs/`, and `apps/`.

Root stubs are temporary compatibility aids only. Historical docs must not claim
to be the current active baseline unless they are clearly marked as historical.
Only active docs may claim current status.

Future release packets and review prompts must follow
`docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md`. Historical version
verifiers belong in the matching release archive and are not current release
gates.
