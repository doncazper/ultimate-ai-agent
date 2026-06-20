# Release Process

Status: active local maintenance process for the v0.102.0 version-repair baseline.

## Normal Flow

1. Confirm the worktree is clean or understand every existing change.
2. Run the version truth checker:

```bash
.venv/bin/python scripts/release/check_version_truth.py
```

3. Preview the next version:

```bash
.venv/bin/python scripts/release/bump_version.py --kind patch
```

4. Apply only after review:

```bash
.venv/bin/python scripts/release/bump_version.py --kind patch --apply --yes
```

5. Run the repo's normal verification commands before any release tag is considered.

## Bump Examples

Documentation-only pre-implementation repair:

```bash
.venv/bin/python scripts/release/bump_version.py --kind docs
```

First code-bearing release:

```bash
.venv/bin/python scripts/release/bump_version.py --kind first-code
```

Incremental improvement:

```bash
.venv/bin/python scripts/release/bump_version.py --kind patch
```

New capability or product surface:

```bash
.venv/bin/python scripts/release/bump_version.py --kind minor
```

First or next release candidate:

```bash
.venv/bin/python scripts/release/bump_version.py --kind rc
```

Stable promotion:

```bash
.venv/bin/python scripts/release/bump_version.py --kind stable
```

## Guardrails

- Do not manually edit `VERSION` unless repairing the tooling itself.
- Do not create tags manually unless a later approved release phase explicitly asks for it.
- Do not use `v2.x.x` before a real accepted `v1.x` stable history exists.
- Do not tag release candidates as `v1.0.0`.
- Do not push, force-push, delete remote tags, or mutate GitHub Releases from the version helper.
- Preserve historical tags; repair current claims through reviewed commits, not history rewrite.
