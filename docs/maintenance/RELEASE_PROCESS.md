# Release Process

Status: active version bump process
Source of truth: `VERSION`

Do not manually edit `VERSION` unless repairing release tooling. Use the release
tool so package metadata, current docs, and release notes stay aligned.

## Common Commands

Documentation-only change before implementation:

```bash
python scripts/release/bump_version.py --kind docs
```

First implementation release:

```bash
python scripts/release/bump_version.py --kind first-code
```

Incremental improvement, bug fix, test, hardening, or cleanup:

```bash
python scripts/release/bump_version.py --kind patch
```

New feature, capability, product surface, runtime subsystem, or integration:

```bash
python scripts/release/bump_version.py --kind minor
```

First release candidate:

```bash
python scripts/release/bump_version.py --kind rc --yes
```

Next release candidate:

```bash
python scripts/release/bump_version.py --kind rc
```

Final stable `v1.0.0` promotion:

```bash
python scripts/release/bump_version.py --kind stable --yes
```

Create a local annotated tag during a bump:

```bash
python scripts/release/bump_version.py --kind patch --tag
```

Preview a bump without changing files:

```bash
python scripts/release/bump_version.py --kind patch --dry-run
```

## Verification

Run:

```bash
python scripts/release/check_version_truth.py
python scripts/release/bump_version.py --self-test
```

## Warnings

- Do not create tags manually unless the release tool fails and the repair is
  documented.
- Do not use `v2.x.x` before a real `v1.x` stable history exists.
- Do not tag release candidates as `v1.0.0`.
- Do not claim public release, public beta, production readiness, or final
  stability unless an explicit release gate approves that claim.
- The release tool creates local tags only. It does not push to remote.
