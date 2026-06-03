# Claim Verification Policy

Status: Active for v0.29.2 / M25.

Verified status requires primary or source-backed evidence from canonical docs,
evidence manifests, receipts, Event Ledger records, or user-reviewed sources.
Evidence-supported status requires recognized structured evidence/source refs.
Arbitrary refs cannot verify truth. Inferred unknown source kinds are denied.
Explicit `TruthSourceKind.unknown` evidence is denied. Claims cannot
self-verify.

Memory-only evidence cannot verify truth. Unreviewed memory cannot verify
truth. Model output cannot verify truth. Runtime output cannot verify truth.
OpenWebUI output cannot verify truth. Control Center output cannot verify
truth.

Stale, conflicted, revoked, deleted, or superseded sources cannot verify truth.
Raw content is forbidden. Secret content is forbidden.

M25 validation is local validation over provided refs. It is not autonomous fact
checking and it is not external verification.
