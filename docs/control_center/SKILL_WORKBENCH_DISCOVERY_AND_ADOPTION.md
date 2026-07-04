# Skill Workbench Discovery And Adoption

Status: planned / Prompt 01 charter only
Scope: product boundary, authority boundary, future read-model nouns, and
promotion path for external skill discovery and UAA-owned skill adoption

Skill Workbench is the planned Control Center surface for discovering external
skill metadata, reviewing candidates, and promoting only reviewed UAA-owned
adaptations. It is not a Skill Store, plugin marketplace, installer, runtime
loader, or execution surface.

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

## Planned Operator Surfaces

The full Skill Workbench product may include these Control Center surfaces
after backend read models exist:

- Discover
- Popular
- Search
- Skill detail
- Adoption queue
- Review report
- Local UAA-owned skills
- Blocked and rejected candidates

Prompt 01 does not create those routes or controls. These names are product
surface targets only.

## Source Marketplace Posture

Initial source families are metadata providers only:

- OpenClaw Clawhub metadata
- Hermes skill catalog metadata, with exact source naming verified in a later
  lane
- Optional GitHub or curated-source metadata in later scoped lanes

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

Prompt 01 is docs/contracts only:

- Adds this charter and product boundary.
- Links the planned Skill Workbench to existing plugin/skill ecosystem,
  inspectable extension catalog, activation grant, WebAccessGateway, and
  Control Center product-language rules.
- Defines user-visible planned surfaces and status labels.
- Preserves the rule that external code is evidence/reference only, never
  executable authority.

Prompt 01 adds no backend route, frontend route, Control Center control,
catalog fetch, source download, provider/model call, connector write, browser
automation, shell/subprocess execution, plugin runtime import, skill runtime
import, marketplace install, local enablement, public distribution claim, or
production authority.

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

Rollback for Prompt 01 is to remove this document and its active documentation
links. No runtime state, route, Control Center behavior, marketplace fetch,
source material, local skill registry, or user data is changed by this lane.
