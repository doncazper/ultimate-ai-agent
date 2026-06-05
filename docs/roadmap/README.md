# Roadmap Docs

Status: active
Current through: v0.48.1
Purpose: Entry point for active roadmap docs and historical roadmap references.

Current roadmap source of truth:

```text
docs/canonical/09_roadmap.md
```

Active roadmap support docs:

```text
docs/roadmap/MILESTONE_CHARTERS.md
docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md
docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md
docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md
docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md
docs/roadmap/ECOSYSTEM_WATCHLIST.md
docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md
```

Historical roadmap snapshots live under `docs/roadmap/archive/` or
`docs/archive/roadmap_snapshots/` when they are no longer required at their
original paths.

`docs/roadmap/NEXT_SEQUENCE_v0_17_5.md` remains in place for compatibility with
active verifier and Foundation Gate checks, but it is a historical roadmap
projection and not the current roadmap source of truth.

M25 is implemented/hardened. M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1 for source_ref/source_kind consistency. M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization. M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion policy-only contracts. M29 is implemented/released by v0.33.0 as Agent Task Planning Engine. M30-M33 are implemented/released. v0.37.4 supersedes the old active post-M33 projection, v0.38.0 implements M34 Broader File Capability Review as planning/docs/verifier only, v0.39.0 implements M35 Safe File Review Workflow Contracts, v0.40.0 implements M36 CCC File Review Surface, Review-Only, v0.40.1 hardens M36 read-only surface safety, v0.41.0 implements M37 Review Approval Capture, Review-Only Persistence, v0.42.0 implements M38 Safe Context Proposal From Approved Review, v0.43.0 implements M39 CCC Context Proposal Surface, v0.44.0 implements M40 Context Handoff Approval, No Injection, v0.45.0 implements M41 Local Prototype Safety Freeze, v0.46.0 implements M42 Mobile Companion Product Contract Refresh, v0.47.0 implements M43 Mobile API Boundary, Read-Only, v0.48.0 implements M44 CCC iOS Skeleton, No Authority, and v0.48.1 hardens the M44 verifier allowance. M45-M60 remain planned/provisional.

Documentation organization and historical-roadmap handling rules live in
`docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md`.
