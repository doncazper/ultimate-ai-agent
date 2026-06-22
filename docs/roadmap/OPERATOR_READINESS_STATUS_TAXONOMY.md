# Operator Readiness Status Taxonomy

Status: active UAA-P1-060 operator-readiness status taxonomy
Baseline: v0.102.3 / 0.102.3
Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` M177

This taxonomy is the shared product/readiness vocabulary for docs, route
manifests, Control Center state language, release evidence packets, and
Foundation Gate summaries. It is a language and evidence contract only. It does
not add routes, runtime authority, provider/model calls, shell/subprocess
behavior, web fetching, connector writes, plugin runtime import, mobile control,
public distribution, or production authority.

## Canonical Statuses

| Status | Meaning | Required evidence posture |
|---|---|---|
| `shipped` | The repository contains the claimed capability and accepted tests/docs/evidence for the exact scope. This is not a public release or production-readiness claim by itself. | Evidence refs, tests/verifiers, rollback or non-goal notes when applicable. |
| `planned` | A roadmap, board, or spec names future work, but it is not implemented product behavior. | Roadmap/task refs and explicit non-goals. |
| `blocked` | A required gate, approval, dependency, route, evidence ref, or safety condition is missing. | Blocking gate and next safe action. |
| `skipped` | A check or optional prerequisite did not run and records a safe reason code. | Reason code, owner/reviewer ref when release-facing, and no completion claim. |
| `mock_only` | The surface or artifact is backed by mock, fixture, or planning data only. | Mock/fixture ref and visible not-product-ready language. |
| `not_scoped` | The capability is intentionally outside the current milestone, release packet, or product claim. | Scope boundary and future milestone ref if one exists. |
| `partial` | Some docs, routes, backend, UI, tests, or evidence exist, but the end-to-end product loop is incomplete. | Missing pieces and blocker refs. |
| `status_only` | The surface reports status or metadata only; it does not prove completion or authorize action. | Source route/report refs and authority boundary. |
| `preview_only` | The surface can show a proposed action or policy preview, but it cannot execute or grant authority. | Preview route/ref and explicit no-execution state. |
| `validation_only` | The route or script validates inputs/contracts without performing the represented operation. | Validation route/ref and no-side-effect evidence. |
| `review_only` | The operator can inspect or record review posture, but no execution or authority follows from the view alone. | Review ref and approval/receipt boundary. |
| `local_ui_state_only` | The frontend changes presentation or local state only and creates no backend/product evidence. | UI-only label and missing backend route/ref where relevant. |
| `unknown` | The repository cannot prove the state from current evidence. | Unknown reason and next inspection step. |
| `needs_review` | Evidence exists but requires human review before readiness can be upgraded. | Reviewer ref, open question, or accepted-failure binding. |
| `accepted_failure` | A release-facing check failed but is explicitly owner-bound, reviewer-bound, expiry-bound, and evidence-bound. | Release evidence packet entry; never implicit. |

## Cross-Surface Mapping

Control Center route status manifest values map to the canonical statuses:

| Manifest value | Canonical status |
|---|---|
| `status_available_not_completion` | `status_only` |
| `preview_available_not_execution` | `preview_only` |
| `partial_backend_not_product_ready` | `partial` |
| `founder_loop_v1_proofed` | `shipped` |
| `mock_only_not_product_ready` | `mock_only` |
| `local_ui_state_only_not_evidence` | `local_ui_state_only` |
| `blocked_missing_backend` | `blocked` |

The planned FCC-V1 release surface manifest uses a narrower route-promotion
vocabulary:

| Release surface value | Canonical status |
|---|---|
| `ship` | `shipped` for the exact route behavior only; not public release or production readiness. |
| `partial` | `partial` |
| `blocked` | `blocked` |
| `experimental` | `needs_review` or `partial`, depending on the proof lane. |

Release verification and release evidence packet values map to readiness
language this way:

| Evidence value | Canonical status posture |
|---|---|
| `pass` | A check passed; it can support `shipped` only with exact capability evidence. |
| `fail` | `blocked` |
| `skipped` | `skipped` |
| `blocked` | `blocked` |
| `accepted_failure` | `accepted_failure` |

Release blocker states map as follows:

| Release blocker value | Canonical status posture |
|---|---|
| `open` | `blocked` |
| `closed` | status resolved for that blocker only; it is not a product-readiness claim by itself. |
| `not_scoped` | `not_scoped` |

Foundation Gate statuses map as follows:

| Foundation Gate value | Canonical status posture |
|---|---|
| `passed` | A gate passed; it can support `shipped` only with exact capability evidence. |
| `failed` | `blocked` |
| `warning` | `needs_review` |
| `blocked` | `blocked` |

## Usage Rules

- Use `shipped` only for the exact repository capability backed by accepted
  tests, docs, safe refs, and applicable rollback/non-goal evidence.
- Use `planned`, `blocked`, `skipped`, `mock_only`, `not_scoped`, `partial`,
  `status_only`, `preview_only`, `validation_only`, `review_only`,
  `local_ui_state_only`, `unknown`, or `needs_review` when evidence is missing
  or the capability is incomplete.
- A passing verification lane, Foundation Gate status, route response, mock
  fixture, or frontend state never upgrades a product claim by itself.
- `accepted_failure` is allowed only in release evidence packets with owner,
  reviewer, expiry, reason code, impact summary, and safe evidence refs.
- Model lifecycle words such as loaded, running, switched, and updated identity
  still require Python Agent Core backend receipt/evidence refs under
  `docs/control_center/PRODUCT_LANGUAGE_RULES.md`.

## Bound Surfaces

The current taxonomy is bound into:

- `docs/control_center/ROUTE_STATUS_MANIFEST.md`
- `docs/control_center/route_status_manifest.json`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/production/RELEASE_VERIFICATION_LANES.md`
- `docs/production/RELEASE_EVIDENCE_PACKET.md`
- `docs/schemas/release_evidence_packet.schema.json`
- `docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json`
- `scripts/run_foundation_gate.py` release lane status summaries

## Verification

Run:

```bash
.venv/bin/python scripts/verify_operator_readiness_taxonomy.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py --root .
```

The taxonomy verifier is deterministic and inspection-only. It checks that the
taxonomy doc, route status manifest, product-language rules, release evidence
packet, release lane manifest, and Foundation Gate release-lane summaries keep
the expected status vocabulary and safe cross-surface mappings.

## Rollback

Rollback is to remove this document, remove its links and metadata fields from
the route status manifest and release evidence packet, remove the taxonomy
verifier/tests, remove the `verify_all` scan hook, and move `UAA-P1-060` out of
Done on the active Kanban board. No runtime state, route, authority, migration,
or persistent user data is changed.
