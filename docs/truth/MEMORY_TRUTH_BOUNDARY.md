# Memory Truth Boundary

Status: Active for v0.29.2 / M25.

Memory is recall, not authority. Memory is not ground truth.

M24 memory metadata supports M25 by carrying source refs, evidence refs, event
refs, receipt refs, user review refs, source priority, review state, conflict
state, staleness state, revocation state, and safe summaries. Those fields make
memory auditable, but they do not make memory authoritative.

Canonical files, evidence manifests, receipts, Event Ledger records, and
user-reviewed sources outrank memory. Source-linked memory may support recall,
but memory-only evidence cannot verify truth.

Memory refs also cannot be used to mask arbitrary or unknown truth refs.
Evidence-supported and verified outcomes require recognized structured
source/evidence refs outside memory-only recall.
