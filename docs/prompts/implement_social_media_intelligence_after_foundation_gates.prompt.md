# Implement Social Media Intelligence After Foundation Gates

Status: stored operator-run prompt; deferred until prerequisite product gates
are accepted complete.

Use this prompt only when UAA is evaluating Social Media Intelligence as a
possible next product lane. Its presence in the repository is not permission
to implement the feature early and grants no runtime, connector, publishing,
reply, provider/model, browser, background, public-release, or production
authority.

```text
Implement UAA Social Media Intelligence as the next dependency-gated product
lane, but only after proving that its three owning foundation products are
fully implemented and accepted.

Start by reading AGENTS.md and inspecting the working tree. Preserve all
unrelated user changes. Then read these sources completely before changing
code or product truth:

- README.md
- docs/product/UAA_SOCIAL_MEDIA_INTELLIGENCE_PRODUCT_CONTRACT.md
- docs/implementation/UAA_COHERENT_APP_ECOSYSTEM_IMPLEMENTATION_PLAN.md
- docs/decisions/ADR-0054-canonical-application-object-ownership.md
- docs/prompts/kanban_board/README.md
- docs/implementation/UAA_FIRST_CLASS_CRM_IMPLEMENTATION_PLAN.md
- docs/control_center/CRM_LOCAL_COMMAND_CENTER_M2.md
- docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md
- docs/design/control_center_north_star/UAA_COMMUNICATIONS_MATRIX_NORTH_STAR.md
- docs/design/control_center_north_star/renders/social-media-v1/README.md
- docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
- docs/control_center/PRODUCT_LANGUAGE_RULES.md
- docs/README.md
- docs/DOCUMENTATION_INDEX.md

PHASE 0 — FAIL-CLOSED ACTIVATION GATE

Collect current, repository-owned completion evidence for all three gates:

1. Work Board/Kanban is accepted as fully implemented: durable backend-owned
   truth, complete operator workflow, API and CLI inspection parity, tested
   Control Center UI, visual acceptance evidence, and aligned product truth.
2. First-class CRM is accepted as fully implemented: its planned workspaces,
   durable local workflows, API and CLI inspection parity, tested Control
   Center UI, visual acceptance evidence, and aligned product truth.
3. Communications/Messenger is accepted as fully implemented: canonical
   conversation ownership, complete local operator workflow, API and CLI
   inspection parity, tested Control Center UI, visual acceptance evidence,
   and aligned product truth.

Do not infer completion from a planning document, mockup, partial route, local
fixture, isolated test, or the word "done" in a non-canonical note. Cite the
accepted implementation contract, verifier/test evidence, and current product
truth for each gate.

If any gate is missing, partial, blocked, stale, or cannot be proved, STOP.
Report the missing evidence and recommend the owning Work Board, CRM, or
Communications lane instead. Do not add a Social route, navigation item,
schema, fixture, component, connector, or dependency. Leave Social Media
Intelligence deferred.

Passing all three gates makes Social eligible for prioritization; it does not
make Social automatically next. Reconcile the active roadmap, current board,
operator pain, and any P0/P1 safety work before beginning implementation.

IF ACTIVATED — IMPLEMENT THE READ-ONLY MILESTONE

Use the accepted render pack as the visual target and the product contract as
the behavior and naming authority:

- Global destination: Social
- Descriptive name: Social Media Intelligence
- Social tabs: Overview, Performance, Audience, Campaigns, Sources
- Calendar saved view: Social publishing
- Work Board saved view: Social Content
- Communications tab: Social Media
- Communications selected filter: Needs attention

Preserve canonical ownership:

Social owns interpretation. Calendar owns time. Work Board owns production.
Communications owns conversations. CRM owns relationships. Studio owns assets.
Evidence owns proof.

Implement in bounded phases, verifying and updating product truth after each:

1. Reconcile the baseline, write or amend the necessary ADRs, and define typed
   data/schema contracts without granting source access.
2. Build a local fixture/manual-import read model with source, coverage,
   freshness, redaction, and correction posture.
3. Add classified read-only API routes and CLI inspection over the same Python
   core contracts; update OpenAPI and /api/manifest truth.
4. Build the /social Control Center destination with Overview, Performance,
   Audience, Campaigns, and Sources, including empty, fixture, stale, partial,
   blocked, and success states.
5. Add the Calendar "Social publishing" saved projection without introducing
   a second calendar or changing external schedules.
6. Add the Work Board "Social Content" saved projection without introducing a
   second Kanban engine or copying task lifecycle state.
7. Add Communications > Social Media > Needs attention as a typed projection
   over canonical communication items without send/reply behavior.
8. Add typed links into CRM, Studio, Evidence, and Memory while preserving
   their ownership and redaction rules.
9. Update README, knowledge/index docs, boards, recommendation state, and
   product-release truth from planned to the exact proven state only.
10. Run focused unit/API/CLI/frontend/accessibility/visual tests, OpenAPI and
    route-classification checks, documentation integrity, product-language
    checks, and the Foundation Gate. Compare the final UI against every image
    in the accepted render pack and record material deviations.

AUTHORITY BOUNDARIES

The initial milestone is read-only. Do not add live connector access unless a
separate accepted exact read lane explicitly grants the selected source,
fields, account scope, retention, freshness, revocation, cost, and receipts.
Do not publish, schedule externally, reply, delete, moderate, follow/unfollow,
change account settings, perform OAuth, scrape with a browser, call provider
SDKs/models, run background sync, or create recurring automation. Do not put
product behavior only in React state. No UI control may mint authority.

DEFINITION OF DONE

- All three activation gates were proved before implementation began.
- Python Agent Core owns the read contracts; UI, API, and CLI agree.
- All required Social and cross-app states are readable and tested.
- Every metric exposes source, time window, freshness, and missing coverage.
- Every recommendation explains why it was shown and links safe evidence refs.
- External social actions are absent or visibly blocked.
- No raw private content, prompt, response, provider payload, local path, log,
  credential, or secret-like value enters fixtures, docs, tests, or evidence.
- README, the knowledge base, boards, indexes, and release truth match the
  implementation exactly.
- Focused checks and repository-defined verifiers pass, or blockers are
  reported without claiming completion.

Finish with a concise report of activation-gate evidence, files changed,
behavior delivered, authority still blocked, tests/verifiers run, visual QA,
skipped checks, and remaining work. Do not commit, push, open a PR, trigger
GitHub Actions, deploy, or publish unless the operator separately requests it.
When requested, use the repository's bounded-cost, dependency-aware execution
policy; do not require incremental cost to be zero, and do not change account
billing or spending settings.
```
