# Roadmap Docs

Status: active
Current through: v1.2.0
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
docs/roadmap/M61_M100_ROADMAP.md
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

M25 is implemented/hardened. M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1 for source_ref/source_kind consistency. M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization. M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion policy-only contracts. M29 is implemented/released by v0.33.0 as Agent Task Planning Engine. M30-M33 are implemented/released. v0.37.4 supersedes the old active post-M33 projection, v0.38.0 implements M34 Broader File Capability Review as planning/docs/verifier only, v0.39.0 implements M35 Safe File Review Workflow Contracts, v0.40.0 implements M36 CCC File Review Surface, Review-Only, v0.40.1 hardens M36 read-only surface safety, v0.41.0 implements M37 Review Approval Capture, Review-Only Persistence, v0.42.0 implements M38 Safe Context Proposal From Approved Review, v0.43.0 implements M39 CCC Context Proposal Surface, v0.44.0 implements M40 Context Handoff Approval, No Injection, v0.45.0 implements M41 Local Prototype Safety Freeze, v0.46.0 implements M42 Mobile Companion Product Contract Refresh, v0.47.0 implements M43 Mobile API Boundary, Read-Only, v0.48.0 implements M44 CCC iOS Skeleton, No Authority, v0.48.1 hardens the M44 verifier allowance, v0.49.0 implements M45 CCC iOS Local Read-Only Connection, v0.50.0 implements M46 iOS Review/Receipt Read-Only Surfaces, v0.51.0 implements M47 TestFlight Pipeline, Internal Only, v0.52.0 implements M48 First Internal TestFlight Build, v0.53.0 implements M49 Mobile Review Approval Capture, v0.54.0 implements M50 Mobile Approval Audit Hardening, v0.55.0 implements M51 OpenWebUI Bridge Adapter Pilot, v0.56.0 implements M52 OpenWebUI Safe Conversation Surface, v0.57.0 implements M53 Controlled Tool Expansion Review, v0.58.0 implements M54 Safe Media Metadata Inspector, v0.59.0 implements M55 Redacted Observability Export, v0.60.0 implements M56 Agent Eval Regression Harness, v0.61.0 implements M57 Runtime Sandbox Architecture Review, v0.62.0 implements M58 Dry-Run Execution Audit Harness, v0.63.0 implements M59 Public GitHub Readiness as review-only public-readiness contracts, v0.64.0 implements M60 Local Developer Beta Freeze, v0.65.0 implements M61 Autonomy Mode Charter + Authority Levels, v0.66.0 implements M62 Scoped Autonomy Session Contracts, v0.67.0 implements M63 Autonomy Policy Engine v1, v0.68.0 implements M64 Autonomous Plan Simulator, v0.69.0 implements M65 Autonomy Audit + Replay Viewer, v0.70.0 implements M66 Scoped Approval Bundles, v0.71.0 implements M67 Revocation + Kill Switch, v0.72.0 implements M68 Autonomy Risk Classifier, v0.73.0 implements M69 Low-Risk Autonomous Dry Run, v0.74.0 implements M70 Autonomy Foundation Freeze, v0.75.0 implements M71 Network Tool Contract Review, v0.76.0 implements M72 Read-Only HTTP Fetch Tool, Allowlisted, v0.77.0 implements M73 Browser Automation Contract Review, v0.78.0 implements M74 Browser Observe-Only Adapter, v0.79.0 implements M75 Browser Action Dry-Run Planner, v0.80.0 implements M76 OpenWebUI Runtime Bridge v1, v0.81.0 implements M77 OpenWebUI Safe Handoff Execution, v0.82.0 implements M78 Plugin Manifest Security Model, v0.83.0 implements M79 Plugin Install Review, Disabled by Default, v0.84.0 implements M80 Network/Browser/OpenWebUI Hardening Freeze, v0.84.1 repairs M80 active currentness wording, v0.85.0 implements M81 Runtime Sandbox Spec, v0.86.0 implements M82 Command Proposal Contracts, v0.87.0 implements M83 Shell Dry-Run Classifier, v0.88.0 implements M84 Sandboxed Echo/No-Op Command, v0.89.0 implements M85 Read-Only Command Allowlist, v0.90.0 implements M86 Shell Approval Gate v1, v0.91.0 implements M87 Sandboxed Command Audit Replay, v0.92.0 implements M88 Mutating Command Proposal, No Execution, v0.93.0 implements M89 Emergency Stop + Process Kill Safety, v0.94.0 implements M90 Shell/Subprocess Hardening Freeze, v0.95.0 implements M91 Autonomous Tool Execution Contract, v0.96.0 implements M92 Low-Risk Tool Autonomy, Single Session, v0.97.0 implements M93 Multi-Tool Dry-Run to Real Run Promotion, v0.98.0 implements M94 Autonomous Browser Clicks, Low-Risk Only, v0.99.0 implements M95 Network Tool Expansion, Authless Only, v1.0.0 implements M96 Plugin Execution Sandbox, No External Plugins, v1.1.0 implements M97 Recurring Automation Contracts, and v1.2.0 implements M98 Scoped Recurring Low-Risk Automation. M99-M100 remain planned/provisional in `docs/roadmap/M61_M100_ROADMAP.md`.

Documentation organization and historical-roadmap handling rules live in
`docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md`.
