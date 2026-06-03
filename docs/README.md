# Ultimate AI Agent Docs

Status: active
Current through: v0.29.5
Purpose: Human-facing entrypoint for active documentation and historical archive navigation.

Active docs are few, indexed, and current. Historical docs are preserved under
`docs/archive/`, clearly treated as audit artifacts, and are not current source
of truth.

Start with:

```text
docs/DOCUMENTATION_INDEX.md
docs/canonical/09_roadmap.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/roadmap/README.md
docs/archive/README.md
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md
```

Current release packet:

```text
docs/archive/releases/v0_29_5/README_IMPORT.md
docs/archive/releases/v0_29_5/master_plan.md
docs/release_notes/v0_29_5.md
docs/implementation/foundation_gate_implementation_plan_v0_29_5.md
```

Use active canonical docs and active roadmap docs for current work. Use archive
docs only for historical review. Git tags and release history preserve exact
historical snapshots.

v0.29.5 removes duplicated wording from the documentation organization policy
only. v0.29.4 remains the documentation archive reference repair release.
v0.29.3 remains a preserved historical archive-organization release, but its
post-release review found stale legacy verifier references and it was superseded
by v0.29.4. M25 remains implemented/hardened. v0.29.2 remains the accepted
pre-M26 security hardening baseline. M26 remains planned/provisional and future.
