# Version Repair Ledger

Status: active repair record
Date of repair: 2026-06-19

## Purpose

Repair the repository's current version truth after the premature `v2.0.0`
jump. The repair preserves history and old tags, establishes a pre-1.0 SemVer
source of truth, and adds tooling to keep future version updates consistent.

## Correction

| Field | Value |
|---|---|
| Original mistaken current version | `v2.0.0` / `2.0.0` |
| Corrected current version | `v0.100.0` / `0.100.0` |
| Machine-readable source of truth | `VERSION` |
| Human-facing explanation | `VERSION.md` |
| Current release notes | `docs/release_notes/v0_100_0.md` |
| Current release packet | `docs/archive/releases/v0_100_0/` |

The corrected current version remains pre-1.0. It does not claim stable
release, public beta, public distribution, production readiness, or a `v1.x` or
`v2.x` maturity line.

## SemVer Policy Summary

- `v0.0.x` is documentation-only before implementation.
- `v0.1.0` is the first code-bearing implementation release.
- `v0.x.patch` is incremental repair, hardening, tests, docs, or cleanup.
- `v0.next.0` is a new feature or meaningful capability milestone.
- `v1.0.0-rc.N` is release-candidate sequencing.
- `v1.0.0` requires explicit stable promotion approval.
- `v2.x.x` is forbidden until real `v1.x` stable history exists and a major
  break is justified.

## Tag And Ref Mapping

Detailed audit files:

- `.version-repair/audit/proposed-version-map.csv`
- `.version-repair/audit/proposed-version-map.md`
- `.version-repair/audit/remaining-old-version-classification.md`

Summary:

| Old tag/ref | Old SHA | New tag | Corrected version | Rationale |
|---|---|---|---|---|
| `v0.1` | See proposed map | `v0.1.0` proposed | `0.1.0` | Short pre-1.0 tag should use patch-zero SemVer. |
| `v0.2` | See proposed map | `v0.2.0` proposed | `0.2.0` | Short pre-1.0 tag should use patch-zero SemVer. |
| `v0.3` | See proposed map | `v0.3.0` proposed | `0.3.0` | Short pre-1.0 tag should use patch-zero SemVer. |
| `v0.4` | See proposed map | `v0.4.0` proposed | `0.4.0` | Short pre-1.0 tag should use patch-zero SemVer. |
| `v1.0.0` through `v1.7.2` | See proposed map | Preserve pending approval | Superseded internal labels | Premature stable-version labels under repaired policy. |
| `v1.2.0-alpha` | See proposed map | Preserve pending approval | Superseded internal label | Alpha-target tag was not final stable approval. |
| `v2.0.0` | `4e0623ad9e6e4292a01ee1f95e61acf27daecbd9` | `v0.100.0` current snapshot | `0.100.0` | Premature major-version jump corrected to next pre-1.0 minor. |

## Files Changed

- `VERSION`
- `VERSION.md`
- `README.md`
- `pyproject.toml`
- `src/ultimate_ai_agent/__init__.py`
- `apps/control-center/package.json`
- `apps/control-center/package-lock.json`
- `apps/control-center/src/mocks/controlCenterData.ts`
- `SECURITY.md`
- `AGENTS.md`
- active docs indexes, roadmap docs, product truth, and release packet refs
- release automation under `scripts/release/`
- repair audit files under `.version-repair/`

## Files Renamed

- `docs/release_notes/v2_0_0.md` -> `docs/release_notes/v0_100_0.md`
- `docs/implementation/foundation_gate_implementation_plan_v2_0_0.md` ->
  `docs/implementation/foundation_gate_implementation_plan_v0_100_0.md`
- `docs/archive/releases/v2_0_0/` -> `docs/archive/releases/v0_100_0/`

## Tags Preserved

All old tags are preserved locally and remotely by default. Checkpoint tags such
as `checkpoint-m166`, `checkpoint-m167`, and `checkpoint-m168` are preserved.

## Old Tags Proposed For Deletion

Remote deletion is not approved in this repair. If a later remote repair is
approved, candidate old SemVer tags include:

- `v1.0.0`
- `v1.1.0`
- `v1.2.0`
- `v1.2.0-alpha`
- `v1.3.0`
- `v1.4.0`
- `v1.4.1`
- `v1.5.0`
- `v1.6.0`
- `v1.7.0`
- `v1.7.1`
- `v1.7.2`
- `v2.0.0`

Do not delete, move, or overwrite any remote tag unless the remote rewrite gate
is explicitly satisfied.

## Remote Rewrite Warning

Remote tag deletion or replacement is forbidden unless both are true:

1. `ALLOW_REMOTE_TAG_REWRITE=YES_I_UNDERSTAND` is set.
2. The user explicitly says `APPROVE_REMOTE_VERSION_REPAIR`.

## Recovery Instructions

Local backup refs were created:

- `backup/version-repair-original-main`
- `backup/version-repair-original-head`
- `backup/version-repair-original-v*` tags for existing SemVer tags

To inspect the original state:

```bash
git show backup/version-repair-original-head
git tag --list 'backup/version-repair-original-*'
```

To abandon the repair branch locally:

```bash
git switch main
git branch -D version-repair/semver-reset
```

## Future Release Process

Use `scripts/release/bump_version.py` for future bumps and
`scripts/release/check_version_truth.py` for verification. See
`docs/maintenance/RELEASE_PROCESS.md`.
