# FIN-000 Independent Render Review Packet

Status: review-ready packet; independent decisions pending

Baseline: v0.104.0 / 0.104.0

Candidate manifest: `manifest-ref:fin000-render-pack:v1`

Ledger: `docs/design/control_center_north_star/renders/finance-compliance-v1/acceptance-ledger-v1.json`

Gallery: `docs/design/control_center_north_star/renders/finance-compliance-v1/REVIEW_GALLERY.md`

State/accessibility matrix: `docs/product/UAA_FINANCE_FIN000_STATE_ACCESSIBILITY_MATRIX.md`

## Review Boundary

Review the sixteen locked render candidates against the ten checks in the
render brief. This review can accept a planning-only design target or request
changes. It cannot claim that Finance runtime, account connectivity, advice,
payment, filing, production authority, or supported distribution exists.

The ledger binds every candidate filename, bytes, width, and height into a pack
digest. A separate acceptance-subject digest binds the full asset manifest,
including path refs and viewport classes, plus the render brief, gallery,
trusted-reviewer registry, review packet, state/accessibility matrix, schema,
and verifier. Reviewers should
run `PYTHONPATH=src .venv/bin/python scripts/verify_fin000_render_acceptance.py`
before inspecting the pack so the reviewed files are known to match the locked
manifest.

## Required Independent Roles

Record one decision for each role:

- `reviewer-role-ref:fin000:product-design`
- `reviewer-role-ref:fin000:accounting-domain`
- `reviewer-role-ref:fin000:privacy-security`
- `reviewer-role-ref:fin000:accessibility`
- `reviewer-role-ref:fin000:implementation`

A reviewer records only safe identifiers in `reviewer_ref` and `receipt_ref`.
Names, email addresses, account identifiers, local paths, raw notes, and other
sensitive content do not belong in the ledger. Detailed review notes may remain
outside the repository; the durable receipt ref is the linkable evidence.

Each accepting or changes-requested decision must be signed with the reviewer's
Ed25519 key enrolled for that exact role in `trusted-reviewers-v1.json`. The
signature binds the ledger ref, current pack and acceptance-subject digests,
role, reviewer, trusted key, decision, receipt, and ordered finding refs. The
verifier rejects missing, unknown,
mismatched, stale, or invalid signatures and requires five distinct reviewer
identities. Adding a trusted key is itself a reviewable repository change; an
arbitrary safe-shaped ref is not evidence. Key enrollment and signatures prove
cryptographic key distinction, not independent human identity. The current
verifier therefore keeps promotion blocked until a separately reviewed external
human-identity authority is anchored; candidate-authored keys cannot self-certify
this gate.

Allowed role decisions are `accepted`, `changes_requested`, and `pending`.
Any pending or changes-requested role keeps `promotion_ready` false.
The candidate author ref cannot also appear as an accepting reviewer ref.
Accepted decisions must have no open finding refs; a requested change remains
`changes_requested` until the candidate and acceptance subject are revised and
reviewed again.

## Checklist Decisions

The inventory checks are automation-verifiable. The other checks require human
inspection and may be set to `accepted` or `changes_requested` with one or more
safe evidence refs. A check must not be accepted without evidence.

Promotion is valid only when all ten checklist entries are either
`verified_by_automation` or `accepted`, all five roles are `accepted`, every
accepted human check has evidence, every role signature verifies against the
trusted registry, and `promotion_ready` is true. The verifier rejects
inconsistent promotion claims and preserves the planning-only boundary.

## Review Order

1. Verify the locked manifest and automated inventory checks.
2. Inspect desktop renders 01 through 12 in order.
3. Inspect narrow renders 13 through 16.
4. Compare the fixture story and record ownership across all surfaces.
5. Inspect state language, unavailable-authority posture, consequences, and
   synthetic-data safety.
6. Review keyboard, focus, contrast, 200% zoom, reduced-motion, and screen-reader
   requirements as design specifications; request changes for missing detail.
7. Record role and checklist decisions in the ledger and rerun the verifier.

The verifier exits successfully for an honest pending ledger and reports
`PENDING` rather than treating required independent judgment as a code failure.
The current verifier does not emit `ACCEPTED`, even for five valid distinct-key
signatures, because no externally anchored human-identity authority is
configured. `--require-accepted` remains the future promotion gate and fails
closed until that separate trust boundary is implemented and reviewed.
Use `--require-accepted` as the actual promotion gate; it exits nonzero until
the external identity authority is anchored, the current subject has five
independently verified acceptances, and no requested changes remain.
