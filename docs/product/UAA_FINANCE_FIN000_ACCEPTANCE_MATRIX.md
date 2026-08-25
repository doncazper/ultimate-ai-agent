# FIN-000 Acceptance Matrix

Status: founder direction accepted for private dogfood; independent acceptance pending for promotion
Baseline: v0.104.0 / 0.104.0
Date: 2026-08-23

## Purpose

This matrix makes FIN-000 completion truth explicit. The product, ownership,
security, storage, schema, adapter, workflow, state, reference, and render
requirements are defined; no Finance runtime is implemented. The founder has
accepted the exact candidate pack as a private-dogfood direction with iterative
polish expected. That decision clears the visual prerequisite for a future
synthetic-only FIN-001 lane; the dependency checklist and explicit board
reservation are now recorded for the separately bounded synthetic work item
`dev-task:finance-fin001-synthetic-kernel`. A fresh lane-vacancy check and exact
claim receipt still precede implementation. FIN-000 independent promotion
remains pending until the render brief is signed off under its stricter gate.

## Planning Deliverables

| Deliverable | Evidence | Status |
|---|---|---|
| Product and ownership contract | `docs/product/UAA_FINANCE_COMPLIANCE_PRODUCT_CONTRACT.md` | defined |
| Privacy-safe real-workflow case | `docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md` | defined |
| Dependency-correct implementation sequence | `docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md` | defined |
| Security/privacy threat model | `docs/security/UAA_FINANCE_COMPLIANCE_THREAT_MODEL.md` | defined |
| Protected storage/key decision | `docs/decisions/ADR-0063-finance-protected-local-data-boundary.md` | defined |
| Schema/migration contract | this matrix and ADR-0063 | planning-only |
| Disabled adapter contract | this matrix and product contract | planning-only |
| Desktop/narrow state contract | render brief | defined |
| Twelve desktop plus four narrow render candidates | `docs/design/control_center_north_star/renders/finance-compliance-v1/README.md`, `tests/test_fin000_render_evidence.py`, and `docs/product/UAA_PRIVATE_DOGFOOD_DIRECTION_ACCEPTANCE.md` | founder direction accepted for private dogfood; independent promotion pending |
| Locked candidate manifest and acceptance ledger | `docs/design/control_center_north_star/renders/finance-compliance-v1/acceptance-ledger-v1.json`, `docs/product/UAA_FINANCE_FIN000_INDEPENDENT_REVIEW_PACKET.md`, and `scripts/verify_fin000_render_acceptance.py` | review-ready; five independent role decisions pending |
| Render gallery and state/accessibility review contract | `docs/design/control_center_north_star/renders/finance-compliance-v1/REVIEW_GALLERY.md` and `docs/product/UAA_FINANCE_FIN000_STATE_ACCESSIBILITY_MATRIX.md` | review-ready; implementation proof remains future |
| Reference parity and clean-room exclusions | product contract and this matrix | defined |
| Queue placement | `docs/roadmap/UAA_FINANCE_COMPLIANCE_QUEUE_INSERTION.md` | defined |

## Schema And Migration Contract

The first runtime schema name is reserved as `finance-schema:v1`; reservation is
not implementation. The minimum ownership groups are book/entity/jurisdiction,
account, protected source/statement, immutable observation, candidate, transfer,
journal/posting, classification/review/rule, evidence, reconciliation/close,
obligation/filing, accountant question, readiness packet, export, and audit.

Every future record requires a stable safe ref, schema version, canonical owner,
book/entity/workspace scope, revision, provenance, retention class, and redacted
created/updated actor refs. Migrations require preflight, staged generation,
integrity and balanced-ledger validation, restart/resume, rollback generation,
backup/restore proof, and explicit locked/corrupt/unsupported states.

## Disabled Adapter Contract

The planning catalog reserves separate adapter classes for financial account
read, compliance-source read, accountant packet handoff, filing handoff, and
payment. All are `blocked` or `configuration_required`; none is enabled by this
packet. Each future adapter must name one exact capability and prove consent,
credential-handle isolation, provider/account scope, lease, approval if
required, freshness, budgets, idempotency, revocation, safe-disable, audit,
redaction, and terminal/unknown outcome behavior. A read never implies sync or
write, and a provider integration never implies authority.

## Required Product States

Every Finance surface must distinguish, using text as well as color:

- loading, empty, first-run/no-book, no-source, ready, and verified;
- imported, extracted, source-period-complete, reconciled, closed, and
  closure-proven as separate states;
- candidate, suggested, low-confidence, unknown, needs evidence, ask accountant,
  reviewed, posted, reversed, adjusted, conflicted, and stale;
- connector blocked, configuration required, consent expired, credential locked,
  offline, rate-limited, partial, unknown outcome, and safe-disabled;
- migration required/in-progress/failed/rolled-back, corrupt, backup stale,
  restore staged/verified/failed, key unavailable, and unrecoverable;
- packet draft, exclusions present, unresolved items, ready for review, exported,
  expired, revoked, and deletion incomplete.

Keyboard order, focus, contrast, 200% zoom, reduced motion, screen-reader order,
empty/error recovery, and narrow layout are acceptance requirements, not polish
debt.

## Reference Parity Scorecard

| Reference | UAA target lesson | Clean-room exclusion |
|---|---|---|
| Actual Budget | local ownership, rules, schedules, reconciliation | no screen/code copying; reuse only under a separate license review |
| Beancount | durable double-entry, validation, assertions | no GPL code or adapted implementation |
| Copilot Money | focused review and correction-led learning | no proprietary text, assets, scoring, or layout copying |
| Ramp | timely receipt, memo, and accounting context | no card/spend platform or proprietary workflow copying |
| QuickBooks | transaction-linked questions and period review | no proprietary schemas, UI, exports, or implied compatibility |
| Keeper | approachable readiness and document collection | no advice, tax conclusion, filing claim, or proprietary flow copying |
| Harbor Compliance | sourced entity/jurisdiction obligations | no scraping or reproduced maintained requirement dataset |

## Exit Truth

Founder private-dogfood acceptance means the render direction is coherent
enough to implement and refine through use. It does not mean independent render
promotion is complete, Finance exists in the product, real books are stored,
accounts connect, calculations are professionally validated, an accountant can
access data, or UAA can advise, pay, transfer, sign, submit, or file. FIN-001
has cleared dependency review and is reserved only for the separately bounded
synthetic local kernel under the activation record and implementation plan. It
is not active until the exact post-merge claim receipt exists. The broader
Queue V2 Q26 task remains blocked, as do independent acceptance, real-data use,
and every higher-authority lane.
