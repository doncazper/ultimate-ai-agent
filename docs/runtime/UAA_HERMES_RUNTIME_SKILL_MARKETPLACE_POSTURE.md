# UAA Hermes Runtime Skill Marketplace Posture

Status: Phase 45 repo-safe Python Core read model.
Route: `GET /api/runtime/skill-marketplace-posture`
CLI: `scripts/dev/uaa_runtime.py inspect-skill-marketplace-posture`
Core: `src/ultimate_ai_agent/core/runtime_gateway/skill_marketplace_posture.py`

## Full-Strength

UAA should eventually discover external skills, stage agent-created skill
proposals, review diffs, convert approved ideas into UAA-owned adaptations, and
enable them safely. A mature lane would require quarantine, review, local
registry entries, static and product review, approvals, rollback, safe-disable,
receipts, and proof before activation.

## Repo-Safe

The current implementation is a signal, review, and adaptation posture only,
owned by Python Core and visible through the API route, CLI inspection, and
Control Center display:

- external discovery signals
- quarantine
- review
- adaptation proposal
- UAA-owned adaptation
- activation grant posture
- execution block posture

External popularity, stars, downloads, reviews, screenshots, publisher claims,
and marketplace copy are discovery signals only, not trust. Every external or
agent-created skill must become a reviewed UAA-owned adaptation before it can
request any future activation grant.

## AuthorityState

Skill marketplace posture inspection is mapped to
`lane-ref:runtime-skill-marketplace-posture-read-model` as `workspace/read`
under Read-only mode. `GET /api/runtime/skill-marketplace-posture` and
`scripts/dev/uaa_runtime.py inspect-skill-marketplace-posture --json` report the
active AuthorityState mapping, decision ref, decision outcome, reason refs, and
unsupported adapter refs. Known read-only inspection inside the default active
lease is allowed; unknown skill marketplace authority and unsupported external
skill adapters are denied.

## Blocked / Needs Authority

The following remain blocked:

- external code execution
- direct marketplace install
- runtime import
- automatic skill writes
- provider calls
- browser automation
- connector writes
- raw marketplace payload persistence
- Control Center authority minting

## Exact Authority Path

Any future skill marketplace activation capability requires:

1. reviewed UAA-owned adaptation
2. local registry entry
3. static review
4. product review
5. exact approval
6. safe-disable and rollback posture
7. receipt and proof binding
8. CLI/API/Core parity before Control Center initiation
9. verifier coverage that raw marketplace payloads, external code, account
   material, credentials, local paths, provider payloads, and secret-like
   material are not persisted

Planning text and external discovery signals do not grant skill execution
authority.
