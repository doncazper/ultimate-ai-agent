# UAA Messenger Matrix Prompt Bundle

Status: stored execution prompts; planning artifacts only; no runtime authority granted.

Bundle id: `messenger-matrix-001`
Bundle contract version: `1.1.0`

This bundle turns the accepted Messenger Matrix design into thirteen finite,
merge-gated milestones. It does not itself add a Matrix dependency, network
access, account authentication, message reads, sends, connector authority, or
product-readiness claim.

The canonical design sources are:

- `docs/design/UAA_MESSENGER_MATRIX_IMPLEMENTATION_PLAN.md`
- `docs/design/control_center_north_star/UAA_COMMUNICATIONS_MATRIX_NORTH_STAR.md`

Element is a visual, behavioral, and interoperability reference only. Future
implementation must remain clean-room UAA code and must not copy Element source,
styles, assets, branding, identifiers, or product copy.

## Execution Contract

Activate the prompts only in the listed order. Every prompt requires the executor to:

1. fetch and inspect the current `origin/main`;
2. create the prompt's dedicated `codex/msg-mx-*` branch from that exact commit,
   preferably in an isolated worktree;
3. implement only the named milestone and preserve unrelated work;
4. keep Python Core authoritative and maintain API/CLI parity for any operator-
   relevant capability;
5. use safe refs, redaction, exact idempotency, content-free receipts, rollback
   or rollback-readiness, and safe-disable for every mutation;
6. stop with an explicit blocked report when any required authority has not been
   separately accepted;
7. run focused tests, documentation integrity, OpenAPI and API-manifest checks,
   applicable frontend checks, Foundation Gate, and `git diff --check`;
8. adversarially review and harden the final diff;
9. commit and push normally, never force-push or move historical tags;
10. open a draft PR rather than merging directly into `main`;
11. perform local review, adversarial hardening, and all required local checks
    while the PR remains draft;
12. mark the PR ready only after local evidence is green, then run only the
    repository-scoped self-hosted macOS CI; never use paid or GitHub-hosted
    compute for this bundle;
13. merge only after required self-hosted checks are green;
14. update local `main` to the exact remote merge, run post-merge verification,
    push verified `main`, and confirm the worktree is clean; and
15. start no later prompt until that predecessor is merged and verified.

Every phase is desktop-only and macOS-first. Do not add, test, capture, or claim
mobile surfaces. Linux and Windows implementation remains outside this bundle.

Activation of a prompt is not acceptance of a runtime authority lane. Approval
refs are identifiers only. UI state, model output, message content, Matrix
events, fixtures, evidence refs, and orchestration state never grant authority.

## Prompt Order

1. `00_baseline_and_authority_gate.prompt.md`
2. `01_design_adr_threat_model.prompt.md`
3. `02_static_messenger_shell.prompt.md`
4. `03_communications_contracts_api_cli.prompt.md`
5. `04_local_synapse_harness.prompt.md`
6. `05_matrix_discovery_and_session.prompt.md`
7. `06_read_only_sync.prompt.md`
8. `07_encryption_verification_recovery.prompt.md`
9. `08_manual_messaging_mvp.prompt.md`
10. `09_rooms_search_media.prompt.md`
11. `10_uaa_intelligence_proposals.prompt.md`
12. `11_messenger_hardening.prompt.md`
13. `12_review_fix_harden_acceptance.prompt.md`

Prompts 00–03 require no new runtime authority. Prompts 04–10 use a two-stage
contract on one branch and PR: Stage A may accept only the exact authority lanes
named by that prompt, with the required contracts and adversarial proofs; Stage B
may implement runtime behavior only after Stage A is accepted and verified.
Acceptance makes a lane eligible for fresh request-scoped evaluation. It never
creates standing authority, caches authorization, or makes UI state callable.
Immediately before every callable Stage B runtime operation, including reads,
mutations, model invocation, content materialization, transfers, and cleanup as
applicable, re-evaluate PolicyEngine; exact LocalApprovalAuthority scope where
required (approval refs alone never authorize); the current exact
AuthorityLease; exact capability, adapter, provider, target, mission, and run;
TTL/deadline; budget; readiness; kill switch; safe-disable; and
idempotency/replay posture. Unknown, stale, expired, or mismatched state fails
closed before the operation starts.
Prompts 11–12 grant no new lane and may exercise only exact previously accepted
authorities.

## Runtime Authority Map

| Prompt | New runtime authority required before execution |
|---|---|
| 00 | None; audit and planning truth only |
| 01 | None; design, ADR, render acceptance, and threat model only |
| 02 | None; fixture-backed desktop UI only |
| 03 | None; contracts and read-only inspection with a disabled adapter only |
| 04 | Stage A accepts exact loopback local-network, dependency/container, and disposable-harness lanes; Stage B implements only those lanes |
| 05 | Stage A accepts exact Matrix discovery/network, connector session, account authentication, system-browser SSO launch, allowlisted loopback callback/redirect, and macOS credential-storage lanes; Stage B implements only those lanes |
| 06 | Stage A accepts exact connector-read/sync, room/account scope, protected encrypted local-cache, and cache-key lifecycle lanes; Stage B implements only those lanes |
| 07 | Stage A accepts exact crypto-store, credential/key lifecycle, verification, backup, and recovery lanes; Stage B implements only those lanes |
| 08 | Stage A accepts exact human-commanded Matrix send/edit/reaction/redaction/receipt-write, encrypted draft/outbox, and desktop-notification lanes; Stage B implements only those lanes |
| 09 | Stage A accepts exact room/DM/invite/Space administration, media filesystem/quarantine/preview/cleanup, authenticated transfer, and encrypted local-search lanes; Stage B implements only those lanes |
| 10 | Stage A separately accepts exact room-content materialization, approved model invocation, proposal persistence, and attachment materialization/scanning/cleanup lanes; Stage B implements only accepted lanes and leaves attachment analysis blocked if its separate lane is absent |
| 11 | No new lane; may exercise only previously accepted exact lanes in bounded tests |
| 12 | No new lane; acceptance may verify only previously accepted exact lanes |

## Product Truth

The first genuinely useful Messenger milestone is prompt 08, and only after its
Element interoperability, encrypted send/restart, failure, and receipt evidence
passes. Calls, agent room participants, hosted infrastructure, public federation,
autonomous sends, hidden context, and automatic Memory writes remain separate
later authority lanes and are not granted anywhere in this bundle.
