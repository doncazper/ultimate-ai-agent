# Skill Workbench Discovery And Adoption

Status: partial read-only implementation with sanitized source snapshot
Scope: product boundary, authority boundary, future read-model nouns, and
promotion path for external skill discovery and UAA-owned skill adoption

Skill Workbench is the Studio / Create surface for discovering external skill
metadata, reviewing candidates, and promoting only reviewed UAA-owned
adaptations. The current slice is read-only and snapshot-backed. It is not a
Skill Store, plugin marketplace, installer, runtime loader, or execution
surface.

Python Agent Core remains the durable product truth. Control Center may present
Skill Workbench state only after backend-owned contracts exist. External
marketplaces and catalogs are metadata providers only; their popularity,
stars, downloads, reviews, publisher claims, or screenshots are discovery
signals, not trust.

## Product Boundary

The planned Skill Workbench helps the operator answer:

- What external skill metadata has UAA discovered?
- Which sources and licenses are known, unknown, or blocked?
- Which candidates require quarantine, static review, rejection, or rewrite?
- Which reviewed adaptations are UAA-owned and eligible for local enablement
  under a later exact authority lane?
- What proof, review, blocker, safe-disable, rollback, and CLI inspection refs
  exist for each state?

It must not answer those questions by installing, importing, executing,
fetching, copying wholesale, or activating external code.

## Current Operator Surface

`/studio/skills` renders the backend-owned catalog extension on
`GET /api/runtime/skill-marketplace-posture`. The current Discover tab includes:

- source-derived search, source/category/freshness filters, and honest empty
  states
- dense list and grid modes with selected-item inspection
- 25-row default pagination over 31 validated metadata records
- ClawHub weekly rank, stars, downloads, installs, and comments when supplied
- explicit `Not provided by source` treatment for missing Hermes ranks,
  ratings, stars, and download aggregates
- source-provided license information in the list instead of a guessed risk
  badge
- `Risk: Not assessed` in the inspector only, with review and adaptation
  posture kept separate from popularity

The accepted grid and list targets are locked in
`docs/design/control_center_north_star/renders/target-v3/` and hash-bound by
`CURRENT_RENDER_BASELINE.json`.

Later backend-owned surfaces may include:

- Discover
- Popular
- Search
- Skill detail
- Adoption queue
- Review report
- Local UAA-owned skills
- Blocked and rejected candidates

Only Discover is active in this slice. Other visible tabs and persistence or
adaptation controls are disabled with an explanation until their backend-owned
contracts exist.

## Source Marketplace Posture

Initial source families are metadata providers only:

- OpenClaw Clawhub metadata
- Hermes bundled-skill catalog metadata
- Optional GitHub or curated-source metadata in later scoped lanes

The repo-safe snapshot captured on 2026-07-13 contains 12 records from the
[ClawHub public API](https://docs.openclaw.ai/clawhub/api) trending order and 19
bundled skills from the
[Hermes Agent skills catalog](https://github.com/NousResearch/hermes-agent/tree/2ccfdb2db4eedf385f6c5b3fe722e183cee1b6de/skills).
ClawHub `stars` are preserved as star counts, not rewritten as average review
scores. Hermes does not document per-skill star, rating, or download aggregates,
so those fields remain unavailable rather than becoming zero.

Future marketplace metadata fetches must go through WebAccessGateway contracts.
Marketplace webpages must not become the primary product UX. Marketplace
content is untrusted evidence and cannot become instructions, policy, tool
authority, install authority, or execution authority.

## Status Labels

Skill Workbench states use these labels until a later contract refines them:

| Status | Meaning | Authority boundary |
|---|---|---|
| `external_metadata_only` | Safe metadata has been recorded or proposed from an external source. | Metadata does not grant trust, install, import, or execution authority. |
| `candidate` | Operator or backend policy has identified a possible adoption candidate. | Candidate status is review posture only. |
| `quarantined_untrusted` | Source material is isolated for review under a later exact approval lane. | Quarantine is not local enablement and must not execute code. |
| `review_required` | Static review, provenance, license, risk, permissions, and redaction checks are incomplete. | Candidate remains inactive. |
| `rejected` | Review or policy rejected the candidate. | Rejected candidates remain blocked. |
| `adapted_uaa_owned` | A reviewed UAA-authored adaptation exists as repo-owned material. | Adaptation is not enabled until a later local enablement gate allows it. |
| `enabled_local` | Future state for a reviewed UAA-owned adaptation enabled locally after exact approval and tests. | Not available in Prompt 01. |
| `blocked_by_policy` | Policy, provenance, license, risk, permission, or authority gaps block progress. | Blocked work requires a blocker ref and promotion path. |

## Full-Strength Version

The full product target is a governed local Skill Workbench that can discover
skill metadata, compare external candidates, inspect source reputation and
permission posture, create adoption candidates, quarantine source material
after exact approval, run static review, guide a UAA-owned rewrite/adaptation,
verify tests and proofs, and enable only reviewed local adaptations.

Full-strength Skill Workbench should include:

- metadata search across approved source catalogs
- candidate creation with safe refs and source metadata
- quarantine records for untrusted source material
- static review reports for provenance, license, requested permissions,
  network/shell/provider/browser/connector risk, and redaction posture
- adaptation workflow that rewrites external concepts into UAA-owned skills
- local registry entries for reviewed UAA-owned adaptations
- exact enablement gates, safe-disable posture, rollback posture, receipts,
  proof detail, CLI parity, and verifiers

## Repo-Safe Current Version

The current implementation:

- extends the existing Python Core skill-marketplace posture with a validated,
  sanitized catalog snapshot
- exposes the same state through the existing API and repo-local CLI inspection
- adds the `/studio/skills` read-only Control Center route
- loads that route through one focused marketplace-posture read instead of
  waiting on the broader Control Center read fan-out
- keeps filters, selected item, view mode, and pagination as presentation state
  while Python Core remains catalog truth
- preserves the rule that external code is evidence/reference only, never
  executable authority
- performs no live marketplace fetch, source download, provider/model call,
  connector write, browser automation, shell/subprocess execution, plugin or
  skill runtime import, marketplace install, local enablement, or production
  action

## Blocked / Needs Authority

These lanes remain blocked until later scoped prompts add exact contracts,
approval binding, receipts, redaction, rollback or safe-disable, CLI parity,
tests, and verifiers:

- live marketplace metadata fetch
- source download or source material quarantine
- raw source inspection beyond safe refs and bounded summaries
- external skill install
- wholesale copy of external marketplace code
- plugin or skill runtime import
- external skill execution
- package-manager install scripts
- shell/subprocess execution over untrusted code
- browser automation or opening marketplace webpages as primary product UX
- auth, cookies, logins, forms, downloads, uploads, or connector writes
- provider/model calls for candidate generation or review
- local enablement of a UAA-owned adaptation
- background skill agents or autonomous adoption
- public marketplace, public beta, public release, or production claims

## Promotion Path

Each later lane must preserve this sequence:

1. Define backend-owned metadata contracts and safe refs.
2. Add CLI or repo-local inspection for the same state.
3. Add read-only Control Center presentation after backend truth exists.
4. Route any future public-web metadata fetch through WebAccessGateway.
5. Create adoption candidates as review artifacts only.
6. Allow quarantine only after exact approval and without execution.
7. Run static review over safe refs and bounded redacted summaries.
8. Rewrite or adapt into UAA-owned repo material instead of trusting external
   code directly.
9. Verify the UAA-owned adaptation with focused tests and policy checks.
10. Enable locally only after a separate exact authority lane proves approval,
    safe-disable, rollback posture, receipts, proof detail, and CLI parity.

## Relationship To Existing Boundaries

Existing docs remain binding:

- `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md`
- `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`
- `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`
- `docs/network/WEB_ACCESS_GATEWAY.md`
- `docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`

The inspectable extension catalog is a current read-only metadata surface for
repo-owned extension trust records. Skill Workbench is the planned product
workflow around external discovery, adoption review, and UAA-owned adaptation.
It must not collapse inspectable metadata into callable runtime authority.

## Evidence Safety

Skill Workbench durable artifacts must use safe refs and redacted summaries
only. They must not persist raw prompt content, raw response content, raw
provider payloads, raw external code, raw marketplace payloads, raw local paths,
usernames, hostnames, serials, environment dumps, credentials, cookies, tokens,
or private content.

## Rollback

Rollback is to remove the additive catalog snapshot fields and the
`/studio/skills` presentation, then restore this document to charter-only
status. No marketplace fetch, source material, local skill registry, installed
skill, or user data must be unwound because this lane creates none.
