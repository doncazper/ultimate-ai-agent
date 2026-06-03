# Documentation Organization Policy

Status: active
Current through: v0.29.4
Purpose: Keep active documentation current while preserving historical release artifacts safely.

## Root Directory Policy

The repository root must stay minimal and current. Prefer only current operating
docs and project files at root:

```text
README.md
VERSION.md
AGENTS.md
pyproject.toml
src/
tests/
scripts/
docs/
apps/
```

Do not add historical release packets to root unless a reviewed compatibility
requirement explicitly needs a temporary stub. Do not add active-looking
historical verifiers to root. If root historical stubs exist, they must be
clearly marked historical and point to archived files.

## Active And Historical Docs

Active docs may claim the current active baseline. Historical docs must not
claim current baseline status unless clearly describing their captured version
inside a historical archive context. Historical docs must include clear
historical/archive status.

The current roadmap source of truth is:

```text
docs/canonical/09_roadmap.md
```

Archived roadmap snapshots are not active roadmap sources.

## Release Artifacts

Prefer future historical release packets under:

```text
docs/archive/releases/vX_Y_Z/README_IMPORT.md
docs/archive/releases/vX_Y_Z/master_plan.md
```

Active release notes remain under:

```text
docs/release_notes/vX_Y_Z.md
```

Active implementation and Foundation Gate plans remain under `docs/implementation/`
while the project keeps that convention. Git tags and GitHub releases preserve
exact historical snapshots.

## Historical Verifiers

Historical version-specific verifiers must not live at root or in active
`scripts/` as if they are current validation. If preserved, historical verifiers
belong under:

```text
docs/archive/releases/vX_Y_Z/
```

Historical verifiers must be clearly marked historical. Active verifiers must
not depend on root historical release packet files.

Current validation entrypoints are:

```text
scripts/verify_current_baseline.py
scripts/verify_documentation_integrity.py
scripts/verify_all.py
scripts/run_foundation_gate.py
scripts/verify_openapi_contract.py
scripts/verify_skill_package_security_rule.py
scripts/verify_control_center_frontend.py
```

Legacy historical verifiers are not current release gates.

## Roadmap Policy

Active roadmap docs are:

```text
docs/canonical/09_roadmap.md
docs/roadmap/MILESTONE_CHARTERS.md
docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md
docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md
```

Frozen roadmap projections belong under `docs/roadmap/archive/`, or must carry
a historical banner if compatibility requires the original path. The next
milestone must remain planned/provisional until implemented by a dedicated
reviewed milestone.

## Future Milestone Prompt Policy

Every future implementation prompt must include this documentation organization
policy:

- Root directory must remain current and minimal.
- Do not add historical release artifacts to root unless explicitly required by
  current verifier conventions.
- Do not add active-looking historical verifiers to root or active scripts.
- Prefer `docs/archive/releases/vX_Y_Z/README_IMPORT.md` and
  `docs/archive/releases/vX_Y_Z/master_plan.md`.
- Active release notes stay under `docs/release_notes/vX_Y_Z.md`.
- Active Foundation Gate implementation plans stay under
  `docs/implementation/foundation_gate_implementation_plan_vX_Y_Z.md` if
  convention still requires them.
- Historical docs must be clearly marked historical.
- Archived docs must not claim current baseline status.
- Active docs only may claim "current active baseline."
- Update `docs/DOCUMENTATION_INDEX.md` and
  `docs/canonical/CANONICAL_DOC_MAP.md` for any new docs.
- Update `scripts/verify_documentation_integrity.py` if the docs structure
  changes.
- Do not treat archived roadmap snapshots as active source-of-truth.
- Do not treat archived historical verifiers as active release gates.

## Future Review Prompt Policy

Every future strict release review prompt must include this documentation
organization review:

- Confirm no new stale root release artifacts were added.
- Confirm no active-looking historical verifiers were added to root or active
  scripts.
- Confirm current release docs are indexed.
- Confirm archived docs do not claim current baseline.
- Confirm archived verifiers are not current release gates.
- Confirm active docs point to `docs/canonical/09_roadmap.md` as current
  roadmap.
- Confirm the next milestone remains planned/provisional.
- Confirm historical roadmap snapshots are not treated as active roadmap docs.

## Verifier Policy

`scripts/verify_documentation_integrity.py` must enforce this policy
conservatively. It should fail when active docs drift, root release artifacts
return without explicit historical stubs, historical verifiers appear in root or
active `scripts/`, or active docs mark future milestones as implemented.
